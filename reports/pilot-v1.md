# Lesson acceptance: bounded SQL pilot

Study date: 19 September 2026 (America/New_York). Completed a bounded 54-request
phase, including one interrupted request. Cheap schema review and paid probing
both prevented initial join-fanout errors; paid evidence added no measured benefit
over competent cheap review. Ordinary raw-experience repair recovered all current
task outputs, but one returned program retained a latent fanout defect. Corrected
SQL could be reused directly without further inference. This is a constructed
feasibility study, not an estimate of natural error rates.

## Outcomes

Six task cases (three per source history) were each evaluated in three arms.
The two numerical behavioral checks per final program were registered before
final evaluation and were never exposed for repair.

| Arm | Correct initial results | Correct final results | Final programs passing both independent checks | Fixed acquired-program replay |
|---|---:|---:|---:|---:|
| Raw experience | 2/6 | 6/6 | 5/6 | 2/6 |
| Cheap grounded curation | 6/6 | 6/6 | 6/6 | 6/6 |
| Paid probe curation | 6/6 | 6/6 | 6/6 | 6/6 |

All four raw initial failures occurred on multiplicity cases and were repaired
after ordinary execution feedback. The raw billing-801 final SQL remained the
original unsafe join: correct on its no-fanout task slice, wrong on both independent
numerical checks. Thus final output accuracy alone would hide one program-level
generalization failure. The extra checks are correlated tests of six programs,
not twelve independent source histories. No candidate or policy was selected on
these final outcomes.

After whitespace/case normalization, all six raw initial queries exactly matched
their retained source SQL. Five were changed during revision. No cheap or paid
initial query matched the unsafe source SQL, and none changed during revision.
This is observable code reuse, not proof of an internal causal memory mechanism.
Each task received two calls, including an audit of correct initial answers; the
reader-policy costs are not claimed to be a minimum necessary delivery cost.

Fixed replay used the original source SQL or the last complete SQL block produced
by the corresponding curation, selected before final outcomes. Raw fixed replay
is a diagnostic of unchecked source-code deployment, not a substitute for the
competent raw arm with ordinary repair. Cheap and paid corrected programs both
completed every case without later model calls. This bounded follow-up explains
why the same-schema workload does not require continual model regeneration.

Full records: [paired task results](../evidence/pilot-v1/results.json),
[offline and fixed-program checks](../evidence/pilot-v1/offline-verification.json),
[summary](../evidence/pilot-v1/summary.json), and
[native-unit cost ledger](../evidence/pilot-v1/cost-ledger.json).

## Costs over the measured reuse horizon

The horizon is three tasks per history, six tasks total. These standalone arm
accounts include source collection once, proposal/curation for acceptance arms,
and all initial/revision calls. Do not sum alternative deployment accounts.
SQLite time, cached/uncached tokens and stage-separated repair costs are in the
ledger; model wall time below is not total engineering time or a money estimate.

| Deployment | Model calls | Prompt tokens | Completion tokens | Model seconds |
|---|---:|---:|---:|---:|
| Raw reader plus repair | 14 | 11,833 | 5,473 | 346.91 |
| Cheap curation plus reader | 18 | 39,269 | 8,154 | 613.55 |
| Paid curation plus reader | 18 | 45,745 | 9,026 | 696.55 |
| Cheap curation, direct program replay | 6 | 3,104 | 4,243 | 212.00 |
| Paid curation, direct program replay | 6 | 3,731 | 4,563 | 233.00 |

Paid versus cheap added 7,348 model tokens and 83.00 model seconds in the reader
comparison, with no observed output or behavioral benefit. In direct replay it
added 947 tokens and 21.00 model seconds, again without an outcome improvement.
The two paid SQL probes took 0.0014735 seconds; their construction and reviewer
interpretation were not free. No paid-versus-cheap repayment occurred over this
horizon. Unknown investigator/engineering costs prevent a full economic claim.
No break-even extrapolation beyond this horizon is asserted.

Across the actual experiment, 53 completed response artifacts account for 103,511
prompt tokens, 32,207 completion tokens and 1,978.49 model seconds. One of those
responses had empty final content; a further interrupted request has unknown
tokens/time. The total is 54 requests, below the 60-call ceiling. Failed 8B review
development accounts for 8 calls / 14,095 tokens / 113.74 seconds, and the empty
27B attempt for 5,008 tokens / 232.76 seconds. These search costs are separate
from the hypothetical deployment rows above; shared collection is not counted
again per experimental arm in the actual experiment total. Money remains unknown.

## LA1–LA3 and phase closure

- **LA1:** Narrowed in this workload. Extra probes were not needed once a competent
  cheap reviewer analyzed the visible schema. The weak-reviewer failures establish
  an evidence-interpretation limitation, not a paid-probing advantage.
- **LA2:** Source replay passed both unsafe programs while multiplicity challenges
  exposed both defects. Replay did not establish scope. However, cheap schema
  reasoning exposed the same defects, so these data do not establish an incremental
  transfer advantage for challenge probes over competent cheap review.
- **LA3:** Paid probing did not repay its incremental measured cost over cheap
  curation at three reuses per history. Raw repair had lower model costs than
  either curation-plus-reader arm but retained one latent unsafe final program.
  Direct deployment of cheaply repaired code was the strongest measured option
  for this unchanged-schema workload; this is not a representation-learning claim.

The useful bounded next step was assessed and executed: fixed acquired-program
replay. It resolved a limitation of the reader comparison by showing that subsequent
model calls were unnecessary. Expanding numeric variants of this schema-solvable
catalog would add little explanatory value. Close this phase on that demonstrated
limit. A subsequent workload should have consequential uncertainty about an actual
environment contract or provenance that ordinary specifications/schema checks do
not settle. It needs new source acquisition and confirmation; this pilot does not
establish that such a workload is available or justify weakening ordinary checks.

## Provenance and acquisition

The investigator authored two SQLite reporting histories: customer invoice and
payment totals, and event registrations and tags. Every schema, row and requirement
was visible. Foreign keys were explicit; uniqueness of child foreign keys was not
promised. The 8B proposer generated actual source SQL and two lessons per history.
Both source queries passed their source slices, but both joined independent child
tables before aggregation. The flaw was model-produced; no bad lesson was injected.
The workload, however, was deliberately constructed to examine this known risk.

Source/proposal and initial reviewer development used
`docker.io/ai/qwen3:8B-Q4_K_M`. Final curation and every fresh reader call used
`docker.io/ai/qwen3.8:27b-q4_K_M` with explicit `enable_thinking: false`, temperature
zero and a 4096-completion-token ceiling. Returned model paths and fingerprints
are retained in each response and the cost ledger; model tags alone are not
assumed immutable. No weights were downloaded, trained or adapted by this study.

The fixed development probe retained requirements and expanded child multiplicity.
Billing returned 100 billed / 42 paid instead of 50 / 14; attendance returned 18
seats / 6 tags instead of 9 / 2. A separate Python reference and correlated-subquery
SQLite reference agree. Reference answers were controller-only; reviewers received
only input records and the actual execution, never the reference outputs.

Original lessons are subtler than “the whole query is correct”: COALESCE and
ID-based grouping are useful principles. The problematic statements are broad
scope and endorsements of the whole SQL. Consequently this study does not label
all accepted narrow principles harmful or compute a spurious acceptance accuracy.

## Preserved unsuccessful development

Initial billing paid review invented correct-looking probe totals 50/14 instead
of acknowledging returned 100/42. A developed shared checklist asked for explicit
cardinality analysis and reconciliation of returned values. Billing still called
100/42 valid. Developed attendance paid review did identify 18/6 versus 9/2 and
declined whole-query reuse while accepting its narrow component lessons.
Thus even within this tiny set, buying evidence and interpreting it are different
operations. All initial and developed reviews are retained in the call records.

The first 27B attempt exhausted 4096 tokens in its reasoning field and returned
empty answer content (232.76 seconds). The next pending call was interrupted;
its consumed tokens and duration are unknown. Explicitly disabling thinking via
the documented request parameter produced usable reviews. This is a serving
repair, not evidence that an empty response demonstrates model incompetence.
All four direct-mode reviews returned complete answers.

Both 27B cheap reviews independently identified the schema-permitted fanout and
supplied correct pre-aggregated SQL without probe evidence. Paid reviews identified
the same flaw and supplied equivalent repairs. Billing cheap accepted the narrow
zero-fill lesson and declined the broader join lesson; paid declined both while
retaining corrected component techniques. Attendance cheap and paid both declined
the broad aggregation lesson and accepted ID grouping. These are reviewer
decisions, not an investigator claim that declining a useful component is correct.
The selected cheap and paid billing SQL blocks had no material executable
difference; their prose acceptance decisions differed.

Before final tasks, fixed-program replay was added as an ordinary deployment
baseline. Repeated same-schema tasks need not invoke a language model again once
a correct general query has been acquired. This avoids attributing same-schema
regeneration overhead to retained-program deployment.

## Methods and limits

See the [initial protocol](../protocols/pilot-v1.md),
[fresh plan](../protocols/fresh-v1.md),
[competence escalation](../protocols/competence-v2.md), and
[fresh amendment](../protocols/fresh-v2.md). Source, candidate generation,
curation, and later task sessions are separate stateless calls. Raw retains source
requirements, rows, code and execution. Acceptance arms additionally retain common
candidates and their respective curation; paid retains probe inputs and execution.
Later complete tasks include a uniform execution/revision opportunity. Differences
therefore estimate curation bundles, including scope repair and evidence exposure,
not a pure acceptance bit or learned representation.

The two domains share the same relational failure mechanism. They are independent
source calls, not broad independent workload samples. Temperature zero does not
guarantee replay determinism. Model identifiers, returned backend fingerprints,
full request/response content and token counters are preserved per call.
Calls run serially in fixed raw/cheap/paid order. Prompt-cache reuse, model warmup,
and unobserved remote load can affect wall time; this is recorded deployment work,
not a randomized hardware-latency benchmark. Token totals and cached tokens are
reported separately. The shared cardinality checklist was investigator-authored
during development; its engineering/teacher costs are unknown and disclosed.
Context exposure is logged, but prose output cannot establish a causal internal
memory-use mechanism. Outcome comparison and SQL behavior establish usefulness
only on the measured fixtures. No gradient, adapter, router or authority mechanism
was used.

The fresh cases contain parents empty on either child side, but no parent empty
on both sides; that condition occurs in source and probe data only. Same-valued
records within a parent are challenged in seeds 802/803, while seed 801's equal
values belong to different parents. Inputs use non-null integer amounts/seats and
the declared status strings; null-status semantics, decimals, migrations, missing
specifications, and large-scale query performance are outside this phase.
Extra offline numerical checks use the Python reference; complete primary fresh
tasks are additionally cross-checked by the independent SQL reference.

Public-method discovery is documented in the
[exact-version ledger](../sources/followup-2026-09-19/README.md).
Grounding Agent Memory is direct prior art; its reported results are not locally
reproduced. This study asks whether probes add value beyond cheap grounded review
and retained experience, with curation costs included.

## Reproduction and evidence

Run offline verification without a model:

```sh
uv run scripts/verify.py
uv run scripts/pilot.py summarize
uv run scripts/costs.py
```

The runner validates cached requests. To run a new independent experiment in a
new evidence directory (this launches inference), use:

```sh
export LESSON_ACCEPTANCE_EVIDENCE="$PWD/evidence/replication-01"
uv run scripts/pilot.py collect
uv run scripts/pilot.py develop
uv run scripts/pilot.py competence
uv run scripts/pilot.py evaluate
uv run scripts/verify.py
uv run scripts/pilot.py summarize
uv run scripts/costs.py
```

Use a fresh path, preserve failed attempts, and inspect competence before evaluation.
The default path remains the preserved pilot; new paths get their own 45-minute
budget start. These path/budget ergonomics were added after the experiment; the
executed phase source snapshots remain in timestamped instrument manifests.
Live execution uses the documented private Tailscale endpoint,
so saved-evidence replay is more portable than live reproduction. Code is stdlib
Python and SQLite; no public code or dataset was copied. The prepared runtime was
absent, and neither it nor any sibling checkout was modified.

Primary records: [source/probe verification](../evidence/pilot-v1/offline-verification.json),
[billing source](../evidence/pilot-v1/billing-source.json),
[attendance source](../evidence/pilot-v1/attendance-source.json),
and the full `evidence/pilot-v1/calls/` directory. Initial instrument hashes are
recorded, but initial source snapshots were not saved; the final runner preserves
those phase paths, and later manifests include the source snapshot. This is a
reproduction limitation, not an exact historical-code claim.

Known costs are calls, provider prompt/completion tokens, inference wall seconds,
and SQLite execution seconds. These are not a monetary conversion. Investigator
and delegated-agent inference, engineering, remote hardware/energy and exact
server occupancy are unknown costs. The API listing succeeded; SSH occupancy
inspection failed host-key verification without changing trust settings. Shared
source costs are paid once per deployment, not once per arm; proposal cost is
needed by curation arms, not intrinsically by raw reuse. Experimental reviewer
development is separated from the deployed curation recipe. Probe construction
is investigator work with unknown cost, not free evidence.

Investigator work used this Codex session and two delegated `gpt-5.6-luna` agents
at `max` reasoning for independent design review, focused public-method reading,
and cost-ledger implementation/audit. They did not serve as experiment proposers,
reviewers or task executors. Their inference and engineering costs are unknown.
