# Focused method discovery: grounded checks and paid probes

Prepared 19 September 2026 for the independent lesson-acceptance study. This
bounded pass examined one closest prior method and one executable-check lead for
SQL or database lessons. It did not start inference, acquire a model, clone a
repository, or run an experiment. Exact arXiv metadata is cached in
[`metadata.xml`](metadata.xml); request provenance and its hash are in
[`retrieval.json`](retrieval.json).

## Inspected methods

### Grounding Agent Memory, `2609.11060v1`

Paper: [arXiv HTML, v1](https://arxiv.org/html/2609.11060v1), published 10
September 2026. I inspected §§1, 3.2–3.3, 4–5 and Appendices B and D. The method
keeps the task agent, retriever, memory schema, CRUD policy and task-time budget
fixed, then gives an asynchronous post-task curator a least-privilege,
read-only environment interface. Its process is propose, probe, then commit:
the curator can test an asserted relation on another slice, inspect omitted
states, check preconditions, compare a shorter procedure, or refresh a stale
mapping before creating, narrowing, updating, deleting or skipping a record.
For CLBench, the probe surface is a database query interface; the paper names
tables, join keys, encodings and post-migration fields as targets. Probes are
not allowed to solve a future task, alter the environment, consume task-agent
budget, or expose future tasks or labels.

The closest SQL evidence is author-reported CLBench: a 40-question hidden
SQLite stream with an unannounced migration after question 20, five paired
seeded runs per configuration, and gpt-5.4 for task, distillation and curation
sessions. Their pass-discounted reward is `p * (1 - q/B)` with `B = 15` SQL
queries. Environment-probed memory is reported at 73% pass and 22.60 reward,
versus trajectory-only memory at 70% and 20.00, with 4.7 versus 5.6 SQL
queries per question and $1.68 versus $1.99 task-agent cost. Their reported
task-agent costs exclude distillation and curation; those phases are tracked
separately. These numbers are author reports, not local reproduction.

Relevance: this is direct prior art for a paid, read-only probe that checks a
candidate reusable rule before durable acceptance. It supplies a useful probe
boundary and reminds the study to count probe calls and curation separately from
later task execution. It does not establish that probing beats a competent
cheap grounded checker: the paper's comparison is no-memory, full in-context
learning, trajectory-only memory, and probing, and its curator is prompted to
probe whenever uncertainty remains. It also does not test raw source-experience
reuse under the lesson-acceptance protocol, or show that its reported probe
costs repay over a fresh-history horizon. The hidden CLBench database, GHCP
harness and author runs were not acquired here.

### Causal Agent Replay, `2606.08275v1`

Paper: [arXiv HTML, v1](https://arxiv.org/html/2606.08275v1), published 6 June
2026. I inspected §§2–5 and §7 and the public [repository README](https://github.com/jaineet17/causal-agent-replay); I did not clone or run the repository.
CAR reconstructs an exact decision state and re-executes the trajectory after a
targeted intervention. Its operations include `do_resample`, `do_action`,
`do_observation`, `do_context` and `do_policy`. It reports outcome
distributions, confidence intervals and a point-of-commitment rule; a
budget-bounded Monte Carlo Shapley estimator handles interacting steps. The
paper validates the estimators on synthetic structural causal models with
planted ground truth.

Relevance: a SQL lesson checker could use the same discipline on an owned,
read-only SQLite fork: replay the source procedure, change one suspected join,
key, encoding or missing-value condition, and grade the intended computation on
an independently held slice. The replay record would make an execution check a
targeted purchase rather than an opaque “run it again.” Preserve the original
source episode and candidate wording, and charge every replay/tool call to the
paid-check arm.

Limits: CAR attributes the cause of an executed failure rather than deciding
whether a proposed lesson transfers. The paper's demonstrations use mocked,
reproducible tools; real side effects are out of scope. Hosted providers may
not replay deterministically, direct effects are confounded by stochastic
downstream rerolls, Shapley variance grows with budget, and judge-based outcome
functions add noise. Its synthetic validation therefore supports the replay
instrument, not a claim about lesson acceptance or SQL-history transfer.

## Leads and unavailable evidence

The method pages above were inspected. The corresponding CLBench database,
GitHub Copilot SDK harness, and CAR source tree were not locally acquired, so no
implementation or public result was reproduced. Grounding Agent Memory cites
Reflexion, ExpeL, ACE, ReasoningBank and ReMe as broader reflection or memory
leads; they remain leads in this pass because their exact method versions and
SQL-relevant execution protocols were not separately inspected. No inaccessible
source is treated as evidence.

## Implication for the SQL comparison

The smallest useful follow-up keeps identical candidate proposals, source
traces, acquired code, ordinary SQL parsing/arithmetic and task requirements in
all arms. An inexpensive grounded arm should settle what deterministic schema,
provenance and competent checks can settle. The paid arm may buy a bounded,
read-only counterexample or execution replay only for a named unresolved
condition, then record the observation, outcome, calls, wall time and any token
or monetary cost. Neither method justifies using a successful source episode or
the probe's agreement as proof of a broad lesson. Later fresh tasks must grade
the accepted scope and the unchanged responsibilities separately from the
acceptance decision.
