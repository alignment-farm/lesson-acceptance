"""Build a native-unit cost ledger from the pilot artifacts.

This program is deliberately offline: it reads saved JSON records and writes
only evidence/pilot-v1/cost-ledger.json. It never calls the model endpoint and
does not rewrite an existing evidence record.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('LESSON_ACCEPTANCE_EVIDENCE', str(ROOT / 'evidence' / 'pilot-v1'))).resolve()
CALLS = OUT / "calls"
LEDGER = OUT / "cost-ledger.json"

MODEL_CATEGORIES = [
    "shared-source",
    "shared-proposal",
    "search8b",
    "failed27b",
    "deployed-cheap",
    "deployed-paid",
    "later-raw-initial",
    "later-raw-revision",
    "later-cheap-initial",
    "later-cheap-revision",
    "later-paid-initial",
    "later-paid-revision",
    "followup",
    "unclassified",
]

SQLITE_CATEGORIES = [
    "source",
    "probe",
    "grades_initial",
    "grades_final",
    "fixed_program_replay",
    "offline",
]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def add_unknown(target: dict[str, Any], reason: str) -> None:
    values = target.setdefault("unknown", [])
    if reason not in values:
        values.append(reason)


def empty_model_aggregate() -> dict[str, Any]:
    return {
        "calls": 0,
        "completed_calls": 0,
        "failed_or_incomplete_calls": 0,
        "status_counts": {},
        "prompt_tokens_known": 0,
        "prompt_tokens_unknown_calls": 0,
        "completion_tokens_known": 0,
        "completion_tokens_unknown_calls": 0,
        "total_tokens_known": 0,
        "total_tokens_unknown_calls": 0,
        "cached_prompt_tokens_known": 0,
        "cached_prompt_tokens_unknown_calls": 0,
        "uncached_prompt_tokens_known": 0,
        "uncached_prompt_tokens_unknown_calls": 0,
        "wall_seconds_known": 0.0,
        "wall_seconds_unknown_calls": 0,
        "money_usd": None,
        "money_status": "unknown; no price schedule is recorded for this serving path",
        "unknown": [],
    }


def empty_sqlite_aggregate() -> dict[str, Any]:
    return {
        "executions": 0,
        "successful_or_returned_executions": 0,
        "error_executions": 0,
        "wall_seconds_known": 0.0,
        "wall_seconds_unknown_executions": 0,
        "money_usd": None,
        "money_status": "unknown; local SQLite has no assigned monetary price",
        "unknown": [],
    }


def add_native(aggregate: dict[str, Any], field: str, value: Any) -> None:
    if is_number(value):
        aggregate[field + "_known"] += value
    else:
        suffix = "calls" if field != "wall_seconds" else "calls"
        aggregate[field + "_unknown_" + suffix] += 1


def model_status(path: Path, data: dict[str, Any]) -> str:
    if path.stem.endswith("-failed") or data.get("error"):
        return "failed"
    response = data.get("response") or {}
    choices = response.get("choices") or []
    finish = choices[0].get("finish_reason") if choices and isinstance(choices[0], dict) else None
    message = choices[0].get("message") if choices and isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if content == "":
        return "empty"
    if finish == "length":
        return "truncated"
    if not isinstance(content, str):
        return "missing-content"
    return "completed"


def classify_call(stem: str, histories: list[str]) -> dict[str, Any]:
    core = stem[:-7] if stem.endswith("-failed") else stem

    if "followup" in core:
        return {"category": "followup", "history": None, "arm": None, "stage": None}

    match = re.match(r"^final-(.+)-(\d+)-(raw|cheap|paid)-(initial|revision)$", core)
    if match:
        history, seed, arm, stage = match.groups()
        return {
            "category": f"later-{arm}-{stage}",
            "history": history,
            "arm": arm,
            "stage": stage,
            "seed": int(seed),
        }

    for history in sorted(histories, key=len, reverse=True):
        if core == history + "-source":
            return {"category": "shared-source", "history": history, "arm": None, "stage": "source"}
        if core == history + "-proposal":
            return {"category": "shared-proposal", "history": history, "arm": None, "stage": "proposal"}
        if core == history + "-cheap-27b-direct":
            return {"category": "deployed-cheap", "history": history, "arm": "cheap", "stage": "acceptance"}
        if core == history + "-paid-27b-direct":
            return {"category": "deployed-paid", "history": history, "arm": "paid", "stage": "acceptance"}
        if core == history + "-cheap-27b" or core == history + "-paid-27b":
            return {"category": "failed27b", "history": history, "arm": core.split("-")[-2], "stage": "attempt"}
        if core in {
            history + "-cheap",
            history + "-paid",
            history + "-cheap-developed",
            history + "-paid-developed",
        }:
            arm = "cheap" if "cheap" in core else "paid"
            return {"category": "search8b", "history": history, "arm": arm, "stage": "search"}

    return {"category": "unclassified", "history": None, "arm": None, "stage": None}


def model_record(path: Path, data: dict[str, Any], histories: list[str]) -> dict[str, Any]:
    classification = classify_call(path.stem, histories)
    response = data.get("response") or {}
    usage = response.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    timings = response.get("timings") or {}
    request = data.get("request") or {}

    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    cached = details.get("cached_tokens")
    uncached = timings.get("prompt_n")
    uncached_derived = False
    if uncached is None and is_number(prompt) and is_number(cached):
        uncached = prompt - cached
        uncached_derived = True

    request_hash = data.get("request_sha256")
    request_hash_derived = False
    if request_hash is None:
        request_hash = digest(request)
        request_hash_derived = True

    record = {
        "artifact": relative(path),
        "category": classification["category"],
        "history": classification.get("history"),
        "arm": classification.get("arm"),
        "stage": classification.get("stage"),
        "seed": classification.get("seed"),
        "status": model_status(path, data),
        "request_model": request.get("model"),
        "response_model": response.get("model"),
        "response_id": response.get("id"),
        "system_fingerprint": response.get("system_fingerprint"),
        "request_sha256": request_hash,
        "request_sha256_derived": request_hash_derived,
        "tokens": {
            "prompt": prompt,
            "completion": completion,
            "total": total,
            "cached_prompt": cached,
            "uncached_prompt": uncached,
            "uncached_prompt_derived": uncached_derived,
        },
        "wall_seconds": data.get("wall_seconds"),
        "money_usd": None,
    }
    if prompt is None:
        record.setdefault("unknown", []).append("prompt tokens not returned")
    if completion is None:
        record.setdefault("unknown", []).append("completion tokens not returned")
    if total is None:
        record.setdefault("unknown", []).append("total tokens not returned")
    if cached is None:
        record.setdefault("unknown", []).append("cached prompt tokens not returned")
    if uncached is None:
        record.setdefault("unknown", []).append("uncached prompt tokens not returned")
    if not is_number(data.get("wall_seconds")):
        record.setdefault("unknown", []).append("model wall time not returned")
    record.setdefault("unknown", []).append("money in USD has no recorded price")
    return record


def add_model_record(aggregate: dict[str, Any], record: dict[str, Any]) -> None:
    aggregate["calls"] += 1
    status = record["status"]
    aggregate["status_counts"][status] = aggregate["status_counts"].get(status, 0) + 1
    if status == "completed":
        aggregate["completed_calls"] += 1
    else:
        aggregate["failed_or_incomplete_calls"] += 1
    fields = {
        "prompt_tokens": record["tokens"]["prompt"],
        "completion_tokens": record["tokens"]["completion"],
        "total_tokens": record["tokens"]["total"],
        "cached_prompt_tokens": record["tokens"]["cached_prompt"],
        "uncached_prompt_tokens": record["tokens"]["uncached_prompt"],
        "wall_seconds": record["wall_seconds"],
    }
    for field, value in fields.items():
        if is_number(value):
            aggregate[field + "_known"] += value
        else:
            suffix = "calls"
            aggregate[field + "_unknown_" + suffix] += 1
    for reason in record.get("unknown", []):
        add_unknown(aggregate, reason)


def add_sql_record(
    aggregate: dict[str, Any],
    record: dict[str, Any],
) -> None:
    aggregate["executions"] += 1
    if record.get("status") == "error":
        aggregate["error_executions"] += 1
    else:
        aggregate["successful_or_returned_executions"] += 1
    wall = record.get("wall_seconds")
    if is_number(wall):
        aggregate["wall_seconds_known"] += wall
    else:
        aggregate["wall_seconds_unknown_executions"] += 1
        add_unknown(aggregate, "SQLite wall time missing for one or more checks")


def sql_record(
    category: str,
    artifact: str,
    execution: Any,
    history: str | None = None,
    arm: str | None = None,
    seed: int | None = None,
    stage: str | None = None,
    snapshot_paths: list[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(execution, dict):
        execution = {}
    return {
        "category": category,
        "artifact": artifact,
        "snapshot_paths": snapshot_paths or [artifact],
        "history": history,
        "arm": arm,
        "seed": seed,
        "stage": stage,
        "status": "error" if "error" in execution else "returned",
        "wall_seconds": execution.get("wall_seconds"),
        "money_usd": None,
        "unknown": ["money in USD has no recorded price"],
    }


def strip_measurements(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_measurements(item)
            for key, item in value.items()
            if key not in {"wall_seconds", "sqlite_wall_seconds", "wall_time"}
        }
    if isinstance(value, list):
        return [strip_measurements(item) for item in value]
    return value


def history_from_stem(stem: str, histories: list[str]) -> str | None:
    for history in sorted(histories, key=len, reverse=True):
        if stem.startswith(history + "-"):
            return history
    return None


def collect_sqlite(histories: list[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    aggregates = {category: empty_sqlite_aggregate() for category in SQLITE_CATEGORIES}
    records: list[dict[str, Any]] = []

    source_seen: dict[str, int] = {}
    for path in sorted(OUT.glob("*-source.json")):
        data = read_json(path)
        history = path.stem[: -len("-source")]
        execution = data.get("execution") if isinstance(data, dict) else None
        fingerprint = digest(
            strip_measurements(
                {
                    "history": history,
                    "query": data.get("query") if isinstance(data, dict) else None,
                    "execution": execution,
                }
            )
        )
        if fingerprint in source_seen:
            records[source_seen[fingerprint]]["snapshot_paths"].append(relative(path))
            continue
        record = sql_record("source", relative(path), execution, history=history, stage="source")
        source_seen[fingerprint] = len(records)
        records.append(record)
        add_sql_record(aggregates["source"], record)

    probe_seen: dict[str, int] = {}
    snapshot_paths = sorted(
        list(OUT.glob("*-acceptance.json"))
        + list(OUT.glob("*-developed.json"))
        + list(OUT.glob("*-27b.json"))
    )
    for path in snapshot_paths:
        data = read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("probe"), dict):
            continue
        history = history_from_stem(path.stem, histories)
        probe = data["probe"]
        fingerprint = digest(strip_measurements({"history": history, "probe": probe}))
        if fingerprint in probe_seen:
            records[probe_seen[fingerprint]]["snapshot_paths"].append(relative(path))
            continue
        record = sql_record(
            "probe",
            relative(path),
            probe.get("execution"),
            history=history,
            stage="probe",
        )
        probe_seen[fingerprint] = len(records)
        records.append(record)
        add_sql_record(aggregates["probe"], record)

    grades_dir = OUT / "grades"
    if grades_dir.exists():
        for path in sorted(grades_dir.glob("*.json")):
            data = read_json(path)
            if not isinstance(data, dict):
                continue
            history = data.get("history")
            arm = data.get("arm")
            seed = data.get("seed")
            for category, key, stage in (
                ("grades_initial", "initial_execution", "initial"),
                ("grades_final", "final_execution", "revision"),
            ):
                record = sql_record(
                    category,
                    relative(path),
                    data.get(key),
                    history=history,
                    arm=arm,
                    seed=seed,
                    stage=stage,
                )
                records.append(record)
                add_sql_record(aggregates[category], record)

    def add_offline(artifact: str, execution: Any, history: str | None, stage: str) -> None:
        record = sql_record("offline", artifact, execution, history=history, stage=stage)
        records.append(record)
        add_sql_record(aggregates["offline"], record)

    verification = OUT / "offline-verification.json"
    if verification.exists():
        data = read_json(verification)
        if isinstance(data, dict):
            for index, entry in enumerate(data.get("source_and_probe", [])):
                if not isinstance(entry, dict):
                    continue
                acquired = entry.get("acquired")
                add_offline(
                    relative(verification),
                    acquired,
                    entry.get("history"),
                    f"{entry.get('split', 'unknown')}-{index}",
                )
                add_offline(relative(verification), entry.get('oracle_execution'), entry.get('history'), 'independent-oracle')

            def walk_final_checks(node: Any, path_label: str) -> None:
                if isinstance(node, list):
                    for index, item in enumerate(node):
                        walk_final_checks(item, f"{path_label}[{index}]")
                elif isinstance(node, dict):
                    if "wall_seconds" in node or "sqlite_wall_seconds" in node:
                        execution = node if "wall_seconds" in node else {"wall_seconds": node.get("sqlite_wall_seconds")}
                        add_offline(relative(verification), execution, node.get("history"), path_label)
                    for key, item in node.items():
                        if key not in {"wall_seconds", "sqlite_wall_seconds"}:
                            walk_final_checks(item, f"{path_label}.{key}")

            walk_final_checks(data.get("final_checks", []), "final_checks")

            for index, entry in enumerate(data.get("fixed_program_replay", [])):
                if not isinstance(entry, dict):
                    continue
                record = sql_record(
                    "fixed_program_replay",
                    relative(verification),
                    entry.get("execution"),
                    entry.get("history"),
                    entry.get("arm"),
                    entry.get("seed"),
                    "fixed-program-replay",
                )
                record["snapshot_paths"] = [relative(verification)]
                record["program_pass"] = entry.get("pass")
                record["query_sha256"] = digest(entry.get("query")) if entry.get("query") is not None else None
                records.append(record)
                add_sql_record(aggregates["fixed_program_replay"], record)

    diagnostic = OUT / "cheap-repair-diagnostic.json"
    for archived in sorted((OUT / 'verification-history').glob('*.json')):
        for entry in read_json(archived).get('source_and_probe', []):
            add_offline(relative(archived), entry.get('acquired'), entry.get('history'), 'prior-source-probe-recheck')
    if diagnostic.exists():
        data = read_json(diagnostic)
        if isinstance(data, dict) and "sqlite_wall_seconds" in data:
            add_offline(
                relative(diagnostic),
                {"wall_seconds": data.get("sqlite_wall_seconds")},
                None,
                "cheap-repair-diagnostic",
            )

    return aggregates, records


def aggregate_model_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = empty_model_aggregate()
    for record in records:
        add_model_record(aggregate, record)
    return aggregate


def aggregate_sql_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = empty_sqlite_aggregate()
    for record in records:
        add_sql_record(aggregate, record)
    return aggregate


def model_record_matches(record: dict[str, Any], category: str, history: str, arm: str | None = None) -> bool:
    return (
        record.get("category") == category
        and record.get("history") == history
        and (arm is None or record.get("arm") == arm)
    )


def sql_record_matches(record: dict[str, Any], category: str, history: str, arm: str | None = None) -> bool:
    return (
        record.get("category") == category
        and record.get("history") == history
        and (arm is None or record.get("arm") == arm)
    )


def deployment_ledger(
    histories: list[str],
    model_records: list[dict[str, Any]],
    sql_records: list[dict[str, Any]],
) -> dict[str, Any]:
    planned_horizon = 3
    by_history_arm: dict[str, dict[str, Any]] = {}

    for history in histories:
        by_history_arm[history] = {}
        for arm in ("raw", "cheap", "paid"):
            observed_seeds = sorted(
                {
                    record["seed"]
                    for record in model_records + sql_records
                    if record.get("history") == history
                    and record.get("category", "").startswith("later-")
                    and record.get("arm") == arm
                    and isinstance(record.get("seed"), int)
                }
            )
            horizon_seeds = observed_seeds[:planned_horizon]
            selected_models: list[dict[str, Any]] = []
            selected_sql: list[dict[str, Any]] = []

            selected_models.extend(
                record for record in model_records if model_record_matches(record, "shared-source", history)
            )
            selected_sql.extend(
                record for record in sql_records if sql_record_matches(record, "source", history)
            )

            if arm in {"cheap", "paid"}:
                selected_models.extend(
                    record for record in model_records if model_record_matches(record, "shared-proposal", history)
                )

            deployed_category = f"deployed-{arm}"
            if arm in {"cheap", "paid"}:
                selected_models.extend(
                    record for record in model_records if model_record_matches(record, deployed_category, history, arm)
                )

            for stage in ("initial", "revision"):
                category = f"later-{arm}-{stage}"
                selected_models.extend(
                    record
                    for record in model_records
                    if model_record_matches(record, category, history, arm)
                    and (not horizon_seeds or record.get("seed") in horizon_seeds)
                )

            selected_sql.extend(
                record
                for record in sql_records
                if sql_record_matches(record, "grades_initial", history, arm)
                and (not horizon_seeds or record.get("seed") in horizon_seeds)
            )
            selected_sql.extend(
                record
                for record in sql_records
                if sql_record_matches(record, "grades_final", history, arm)
                and (not horizon_seeds or record.get("seed") in horizon_seeds)
            )
            if arm == "paid":
                selected_sql.extend(
                    record for record in sql_records if sql_record_matches(record, "probe", history)
                )

            model = aggregate_model_records(selected_models)
            sqlite = aggregate_sql_records(selected_sql)
            unknown: list[str] = []
            if arm in {"cheap", "paid"} and not any(
                model_record_matches(record, deployed_category, history, arm) for record in model_records
            ):
                unknown.append(f"no deployed-{arm} acceptance calls recorded for {history}")
            if len(horizon_seeds) < planned_horizon:
                unknown.append(
                    f"only {len(horizon_seeds)} of planned {planned_horizon} later seeds recorded for {history}"
                )
            if arm == "paid" and not any(sql_record_matches(record, "probe", history) for record in sql_records):
                unknown.append(f"no deduplicated paid probe execution recorded for {history}")

            by_history_arm[history][arm] = {
                "planned_horizon_tasks": planned_horizon,
                "observed_horizon_seeds": horizon_seeds,
                "model": model,
                "sqlite": sqlite,
                "money_usd": None,
                "unknown": unknown,
            }

    return {
        "planned_horizon_tasks_per_history": planned_horizon,
        "by_history_arm": by_history_arm,
        "allocation_note": (
            "Each arm view allocates shared source work once, and allocates the proposal only to cheap and paid. "
            "These arm views are hypothetical standalone reuse accounts; do not sum them as an experiment grand total. "
            "No arm is selected here and no precise dollar repayment claim is made."
        ),
        "unknown": [
            "investigator and engineering time",
            "delegated model or teacher costs not present in records",
            "remote energy, hardware occupancy and network costs",
            "monetary serving price is not recorded",
        ],
    }


def fixed_program_deployment_ledger(
    histories: list[str],
    model_records: list[dict[str, Any]],
    sql_records: list[dict[str, Any]],
) -> dict[str, Any]:
    by_history_arm: dict[str, dict[str, Any]] = {}
    for history in histories:
        by_history_arm[history] = {}
        for arm in ("raw", "cheap", "paid"):
            selected_models = [
                record for record in model_records if model_record_matches(record, "shared-source", history)
            ]
            selected_sql = [
                record for record in sql_records if sql_record_matches(record, "source", history)
            ]
            if arm in {"cheap", "paid"}:
                selected_models.extend(
                    record for record in model_records if model_record_matches(record, "shared-proposal", history)
                )
                selected_models.extend(
                    record
                    for record in model_records
                    if model_record_matches(record, f"deployed-{arm}", history, arm)
                )
            selected_sql.extend(
                record
                for record in sql_records
                if sql_record_matches(record, "fixed_program_replay", history, arm)
            )
            if arm == "paid":
                selected_sql.extend(
                    record for record in sql_records if sql_record_matches(record, "probe", history)
                )

            replay_seeds = sorted(
                {
                    record["seed"]
                    for record in sql_records
                    if sql_record_matches(record, "fixed_program_replay", history, arm)
                    and isinstance(record.get("seed"), int)
                }
            )
            unknown: list[str] = []
            if arm in {"cheap", "paid"} and not any(
                model_record_matches(record, f"deployed-{arm}", history, arm) for record in model_records
            ):
                unknown.append(f"no deployed-{arm} acceptance calls recorded for {history}")
            if not replay_seeds:
                unknown.append(f"no fixed-program replay executions recorded for {history}/{arm}")
            by_history_arm[history][arm] = {
                "replay_seeds": replay_seeds,
                "model": aggregate_model_records(selected_models),
                "sqlite": aggregate_sql_records(selected_sql),
                "money_usd": None,
                "unknown": unknown,
            }
    return {
        "by_history_arm": by_history_arm,
        "allocation_note": (
            "This view includes source collection once, proposal and direct cheap/paid curation only for those arms, "
            "the paid probe only for paid, and fixed-program replay executions. It excludes all later model calls "
            "and is separate from the cumulative horizon view. Arm views must not be summed."
        ),
        "unknown": [
            "investigator and engineering time",
            "delegated model or teacher costs not present in records",
            "remote energy, hardware occupancy and network costs",
            "monetary serving price is not recorded",
        ],
    }


def interruption_records() -> list[dict[str, Any]]:
    records = []
    for path in sorted(OUT.glob("*serving-interruption*.json")):
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        records.append(
            {
                "artifact": relative(path),
                "attempt": data.get("attempt"),
                "status": data.get("status"),
                "calls": data.get("calls"),
                "tokens": data.get("tokens"),
                "wall_seconds": data.get("wall_seconds"),
                "money_usd": data.get("money_usd"),
                "server_cancellation_confirmed": data.get("server_cancellation_confirmed"),
                "unknown": [
                    "consumed tokens unknown",
                    "wall time unknown",
                    "money in USD unknown",
                    "server cancellation not confirmed",
                ],
            }
        )
    return records


def main() -> None:
    if not OUT.exists():
        raise SystemExit(f"missing evidence directory: {OUT}")

    histories = sorted(
        path.stem[: -len("-source")]
        for path in OUT.glob("*-source.json")
        if path.stem.endswith("-source")
    )

    model_records: list[dict[str, Any]] = []
    for path in sorted(CALLS.glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        model_records.append(model_record(path, data, histories))

    model_categories = {category: empty_model_aggregate() for category in MODEL_CATEGORIES}
    for record in model_records:
        category = record["category"]
        if category not in model_categories:
            category = "unclassified"
            record["category"] = category
        add_model_record(model_categories[category], record)

    sqlite_categories, sqlite_records = collect_sqlite(histories)
    interruptions = interruption_records()
    interruption_calls = sum(
        record["calls"] for record in interruptions if is_number(record.get("calls"))
    )

    ledger = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ledger_script": relative(Path(__file__)),
        "ledger_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": {
            "evidence_root": relative(OUT),
            "histories": histories,
            "model_call_artifacts_read": len(model_records),
            "sqlite_check_records_counted": len(sqlite_records),
            "existing_records_modified": False,
            "native_units": ["model tokens", "model wall seconds", "SQLite wall seconds", "USD"],
        },
        "model_calls": {
            "categories": model_categories,
            "records": model_records,
            "serving_interruption": {
                "records": interruptions,
                "calls_known": interruption_calls,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "cached_prompt_tokens": None,
                "wall_seconds": None,
                "money_usd": None,
                "unknown": [
                    "serving interruption is recorded separately from failed27b and deployed calls",
                    "consumed tokens, wall time and money are unknown",
                ],
            },
            "unknown": [
                "delegated investigator and engineering time",
                "remote serving price, energy and hardware occupancy",
                "network and queue costs not exposed by the endpoint",
            ],
        },
        "sqlite_checks": {
            "categories": sqlite_categories,
            "records": sqlite_records,
            "deduplication": {
                "probe_snapshots": "identical probe rows/query/output are counted once; snapshot_paths records every copied acceptance snapshot",
                "source_snapshots": "identical source rows/query/output are counted once",
                "grades": "initial and revision executions are separate checks",
                "fixed_program_replay": "fixed-program replays are separate from grade executions and final/offline checks",
                "offline": "offline rechecks are separate from source/probe snapshots",
            },
            "unknown": [
                "SQLite wall time is an execution measure, not a monetary price",
                "investigator time for constructing fixtures and reference rows is unknown",
            ],
        },
        "deployment_cumulative_horizon3": deployment_ledger(histories, model_records, sqlite_records),
        "deployment_fixed_program": fixed_program_deployment_ledger(
            histories, model_records, sqlite_records
        ),
    }

    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(relative(LEDGER))


if __name__ == "__main__":
    main()
