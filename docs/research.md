# Deterministic execution on rented cloud logs leads the unbuilt frontier

Production cloud databases have converged on about nine architectural patterns. The most common is "log is the database": stateless compute ships redo to page servers that sit on object storage. Experts treat the storage question as settled. The open ground lies elsewhere. **No production OLTP system commits directly through object storage**: every one still puts a fast replicated WAL tier in front of S3. **No disaggregated OLTP system maintains views in its storage layer.** **Branching is snapshot-only, with no row-level merge.** **Robust join algorithms that make join ordering irrelevant exist only as DuckDB forks and extensions.** **DBMS-owned OS kernels exist only as a vision paper.** Most 2019–2026 research has stalled for commercial reasons, not technical ones. Interactive SQL sessions, Postgres compatibility and "never regress" guarantees block deterministic transactions, clock-based geo protocols and learned optimizers. A hobby build can ignore all three. The best candidate scores high on both novelty and feasibility. It is a Calvin/Aria-style deterministic epoch log committed through a rented conditional-append log (S3 Express append, S2, Azure append blobs). These primitives arrived in 2024–2025. Replicas, recovery and incremental views all become replays of that one log.

## Nine patterns cover nearly every production cloud database

Stonebraker and Pavlo expect shared-disk to "dominate DBMS architectures" and see no return of shared-nothing ([Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)). Production bears that out. The table below lists the patterns in production as of October 2026.

| Family | Mechanism | Exemplars |
|---|---|---|
| Log-is-the-database, single writer | Compute ships redo only; storage materializes pages, serves GetPage@LSN | Aurora, Socrates/Hyperscale, Taurus, PolarDB, Neon, AlloyDB, HorizonDB |
| Storage-side extras | Filter pushdown, columnar replicas built from redo, copy-on-write branching/PITR | Taurus NDP, PolarDB IMCI, Neon/Lakebase |
| Memory disaggregation | Remote buffer pool over RDMA or CXL | PolarDB Serverless, PolarCXLMem, GaussDB-MP |
| Shared-nothing distributed SQL | Raft/Paxos per shard, MVCC, HLC/TrueTime | Spanner, CockroachDB, YugabyteDB, TiDB (now TiDB X on S3) |
| Unbundled transaction tier | Central OCC conflict resolution, separate log and storage | FoundationDB, Aurora DSQL |
| Object-store immutable data + manifest CAS | Immutable files, one pointer swapped per commit | Snowflake, Delta/Iceberg, DuckLake, SlateDB, WarpStream, turbopuffer |
| Serverless scale-to-zero | Stateless compute, or a tiny SQLite per tenant | Neon, Aurora Serverless v2, DSQL, Turso, D1/Durable Objects |
| Sharding middleware | Router over unmodified Postgres/MySQL | Vitess, Citus, Multigres, Neki, PgDog, Aurora Limitless |
| Separate IVM/streaming engines | Dataflow fed by CDC, state on S3 | Materialize, Feldera, RisingWave, Arroyo |

Sources: ([transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp)), ([Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)), ([TiDB X docs](https://docs.pingcap.com/tidbcloud/tidb-x-architecture/)), ([DSQL paper](https://www.alphaxiv.org/abs/2607.13276)).

Two boundaries matter. First, **single-writer is the norm**. Multi-primary over shared storage exists only at Chinese hyperscalers (PolarDB-MP, Taurus MM, GaussDB-MP). Aurora Multi-Master suffered slow commits and high abort rates and was deprecated in 2023 ([transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp)). Second, **object storage holds data, never the commit path**. Neon, Lakebase, Aurora, Hyperscale and TiDB X all front S3 with a low-latency replicated log. A VLDB 2026 paper calls object storage "impractical for OLTP due to high latency and per-append cost" ([VLDB 2026 program](https://vldb.org/2026/program.html)). The newest entrant, Aurora DSQL, is OCC with snapshot isolation. It coordinates once per transaction at commit and caps transactions at 3,000 rows or 10 MiB ([DSQL paper](https://www.alphaxiv.org/abs/2607.13276)). Under key contention it aborts and the client retries ([AWS docs](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-concurrency-control.html)). High-contention, multi-writer, serverless OLTP is therefore still unserved.

Demand is shifting toward agents. **Agents create 80% of Neon's databases** ([Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)). Databricks bought Electric in August 2026 to run per-agent PGlite synced to Lakebase ([InfoWorld](https://www.infoworld.com/article/4209184/databricks-acquires-electric-to-bring-local-postgres-databases-to-agentic-apps.html)). Branching is now commodity. Merging is not.

## Cloud log primitives make the WAL tier rentable

Every system above builds its own fast log tier. That tier is now becoming a managed service. The primitive that matters is a **conditional append**: append only if the log is at position N, or only if the writer's fencing token is current. One call gives ordering, durability and stale-writer fencing.

| Primitive | Conditional append | Latency | Constraint |
|---|---|---|---|
| S3 Express One Zone append ([AWS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-buckets-objects-append.html)) | Yes: `x-amz-write-offset-bytes` must equal current object size | Single-digit ms | One AZ; each append billed as a PUT |
| GCS Rapid zonal buckets, appendable objects ([Google](https://docs.cloud.google.com/storage/docs/rapid/rapid-bucket)) | Unconfirmed | Sub-ms (Google's claim) | One zone; built on Colossus ([InfoQ](https://www.infoq.com/news/2025/05/google-cloud-rapid-storage)) |
| Azure append blobs | Yes: append-position condition | ms | 50k-block cap per blob |
| S2 streams ([S2](https://s2.dev/docs/concepts/concurrency-control)) | Yes: `match_seq_num` plus fencing tokens | ms | Startup |
| Kinesis, Kafka/MSK, Event Hubs | No compare-and-append | 10s of ms | Streaming, not WAL |
| Diskless Kafka (WarpStream, AutoMQ, KIP-1150) | No | 100s of ms | Kafka API over S3 |
| AWS internal Journal ([AWS Fundamentals](https://awsfundamentals.com/blog/aurora-dsql-introduction)) | Presumably | Low | Not sold; backs DSQL, reportedly S3, DynamoDB, Kinesis, Lambda |

Azure append-blob semantics are from prior knowledge, not re-fetched. The Journal's reach rests on one secondary source.

The idea has research lineage: Corfu/Tango, Delos (Meta, OSDI 2020), Boki, LazyLog (SOSP 2024) (prior knowledge, not re-fetched). Only AWS runs a shared log as a production OLTP commit path, and it is internal. **No database uses a rentable conditional-append log as its only commit path.** The catch: the low-latency options (S3 Express, GCS Rapid) are single-zone. Zone-failure tolerance needs a multi-AZ log or self-built replication, which reintroduces consensus.

## Research stalls on compatibility, not correctness

Recent research that never reached mature systems fails in a few repeated ways. The first is **interactive SQL**. Calvin needs read/write sets up front, Aria and Tiga need one-shot transactions, and Silo-class OCC assumes stored procedures. Production clients hold transactions open across network round trips, so none of these fit. Fauna, the one commercial Calvin descendant, shut down on May 30, 2025, citing capital rather than technology ([The Register](https://www.theregister.com/2025/03/24/faunadb_shut_down/)). Its demise left deterministic databases without a proof point. The second is **"never worse than today"**. Under rigorous train/test splits, "PostgreSQL outperforms these LQOs in almost all experiments" ([Lehmann et al., PVLDB 2024](https://www.vldb.org/pvldb/vol17/p1565-lehmann.pdf)). The only at-scale deployment, SCOPE's QO-Advisor, merely steers hints and falls back to the default plan ([Microsoft Research](https://www.microsoft.com/en-us/research/publication/deploying-a-steered-query-optimizer-in-production-at-microsoft/)). The third is **retrofit cost**. Full IVM requires an engine that operates on deltas. Postgres's IVM patch narrowed to simple SPJ views in May 2026 ([pgsql-hackers](https://postgrespro.com/list/id/20260529231417.7cd817f97347dfa048608517@sraoss.co.jp)). SQL/PGQ was committed for Postgres 19 and reverted in September 2026 ([pgsql-hackers](https://www.postgresql.org/message-id/CAGRkXqSA0Aos=J0Q==2exRst7bHmsFxOgNR_C7rgzAxH2pLCGw@mail.gmail.com)). Hardware follows the same rule: optional hints such as FDP beat interfaces that demand rewrites, such as ZNS and one-sided RDMA ([Meta/Samsung FDP, EuroSys 2025](https://arxiv.org/abs/2503.11665); [Lotus](https://arxiv.org/html/2512.16136v1)).

When research does ship, it ships narrowed. DBOS began as "replace the OS with a DBMS" and became a durable-workflow library on Postgres ([DBOS docs](https://docs.dbos.dev/architecture)). The Beldi/Boki/Halfmoon serverless-transaction line ended up as durable-execution products built on ordinary databases ([Halfmoon](https://doi.org/10.1145/3600006.3613154)). Strong academic spin-outs die anyway: Apple bought Kùzu, the leading WCOJ/factorized graph engine, and archived it in October 2025 ([The Register](https://www.theregister.com/2025/10/14/kuzudb_abandoned/)).

| Research line (2019–2026) | Status, Oct 2026 | Blocker | Matters to a hobbyist? |
|---|---|---|---|
| Deterministic CC: Aria, Caracal, Detock ([Caracal](https://www.eecg.utoronto.ca/~ashvin/publications/caracal.pdf), [Detock](https://drum.lib.umd.edu/items/8c710897-0b8c-4693-9041-e75209e792d7/full)) | Prototypes; Fauna dead | Interactive SQL, epoch latency | No |
| S3 conditional-write commit ([AWS](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-functionality-conditional-writes); [Milliscale](https://arxiv.org/abs/2603.02108)) | Startups use it for manifests only | Latency, single-key CAS | Partly |
| Shared log as commit path: Delos, LazyLog; rentable via S3 Express append, S2 | AWS internal only (DSQL Journal) | Single-zone primitives, vendor lock-in | No |
| DBSP full-SQL IVM ([DBSP](https://www.vldb.org/pvldb/vol16/p1601-budiu.pdf)) | Startup (Feldera), separate system | Engine rewrite, state size | No |
| Robust Predicate Transfer, Free Join ([RPT](https://arxiv.org/abs/2502.15181v1), [Free Join](https://arxiv.org/abs/2301.10841v2)) | DuckDB forks, community extension | Two join paradigms, costing | No |
| CALM / CRDT query semantics ([Keep CALM and CRDT On](https://www.vldb.org/pvldb/vol16/p856-power.pdf)) | Research | Non-monotone SQL, invariants | No |
| vmcache/exmap, unikernel DBMS ([vmcache](https://www.cs.cit.tum.de/fileadmin/w00cfj/dis/_my_direct_uploads/vmcache.pdf), [Leis & Dietrich](https://vldb.org/pvldb/vol17/p2115-leis.pdf)) | Research | Out-of-tree kernel module, drivers | Partly |
| Clock-based 1-RTT geo transactions: Tiga ([SOSP 2025](https://arxiv.org/abs/2509.05759)) | Prototype | One-shot txns, clock trust | Partly |
| Leaderless consensus: Accord ([The New Stack](https://thenewstack.io/apache-cassandra-6-features/)) | Cassandra 6.0 alpha only | Correctness; EPaxos bugs ([OPODIS 2025](https://arxiv.org/abs/2511.02743)) | Yes |
| CXL tiering ([Weisgut et al.](https://www.vldb.org/pvldb/vol18/p3119-weisgut.pdf)) | Alibaba gray release only | Hardware access | Yes |
| Cost-optimal cloud execution ([Leis & Kuschewski](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)) | Vision; Athena ~50x costlier than hand-sized EC2 | Pricing complexity | No |

The last column carries the argument. Most blockers are commitments a vendor has already made to its customers. A hobby database has no customers, no Postgres wire protocol to honor and no regression budget. It can choose stored-procedure transactions, a fresh query language subset or a custom kernel at no cost. The real barriers that remain for a small team are hardware access (CXL, RDMA) and correctness risk in subtle protocols (leaderless consensus). The shortlist avoids both.

## Five candidate designs, ranked by novelty × feasibility

Scores run from 1 to 5. Novelty means distance from anything shipped. Feasibility means a usable v1 from one or two people in months.

| Rank | Design | Novelty | Feasibility | Score |
|---|---|---|---|---|
| 1 | Deterministic epoch log on a rented conditional-append log | 5 | 4 | 20 |
| 2 | Views-in-the-log: DBSP over the commit log | 4 | 4 | 16 |
| 3 | Merge-checked branching for agent sandboxes | 3 | 5 | 15 |
| 4 | Optimizer-free robust join engine with graph patterns | 3 | 4 | 12 |
| 5 | Unikernel data plane that owns its page tables | 5 | 2 | 10 |

Designs 1–3 compose into one system: a deterministic log, views derived from it, and branches as forks of it.

### 1. Deterministic epoch log on a rented conditional-append log

**Core idea.** Transactions are stored procedures (WASM or Lua) that batch into epochs. A sequencer commits each epoch's input batch with one conditional append to a managed log: S3 Express append at the expected offset, or an S2 append with `match_seq_num` and a fencing token. That is the entire commit protocol. There is no self-built WAL tier, consensus cluster or replication protocol. Every node executes the ordered log deterministically, Aria-style: it runs the batch against the prior snapshot, then reorders or aborts deterministically. Any node that can read the log is a replica. Recovery is replay from the last checkpoint on S3 Standard. Compute scales to zero.

**Draws on.** Calvin/Aria/Caracal deterministic execution ([Aria](https://www.vldb.org/pvldb/vol13/p2047-lu.pdf), [Caracal](https://www.eecg.utoronto.ca/~ashvin/publications/caracal.pdf)). Detock's abort-free deterministic deadlock resolution, with near-zero degradation under extreme conflict ([Detock](https://drum.lib.umd.edu/items/8c710897-0b8c-4693-9041-e75209e792d7/full)). Shared-log designs (Corfu/Tango, Delos, LazyLog) and DSQL's Journal ([AWS Fundamentals](https://awsfundamentals.com/blog/aurora-dsql-introduction)). Conditional-append APIs ([S3 Express append](https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-buckets-objects-append.html), [S2](https://s2.dev/docs/concepts/concurrency-control)). Milliscale's commit-latency analysis on S3 Express ([arXiv 2603.02108](https://arxiv.org/abs/2603.02108)).

**Why nobody ships it.** In conventional OLTP, determinism's batching latency floor was a liability against a local fsync. On a cloud log, batching is mandatory anyway, because per-request cost and millisecond latency force group commit. **The two costs merge**, and determinism adds no extra latency. Conditional-append primitives are under two years old, and Fauna's death left no one carrying the Calvin line. DSQL pairs a shared log with OCC; nobody pairs one with deterministic execution. Determinism also addresses DSQL's weak spot: contention produces ordering, not aborts.

**Minimal v1.** The log sits behind a three-call interface (`append_if(pos, batch)`, `read(from)`, `tail()`), with S3 Express append and S2 backends. The scope is single region, one sequencer fenced by the conditional append, and a 20–50 ms epoch. When the log object nears its size limit, the sequencer seals it and starts the next one. Transactions are stored procedures over a KV or simple relational model. Execution is in-memory and periodically checkpoints an LSM snapshot to S3 Standard; checkpointed log segments are truncated. Read-only replicas tail the log. Testing uses deterministic simulation, which comes almost free when the engine is deterministic.

**Main risk.** Durability scope. The lowest-latency logs (S3 Express, GCS Rapid) are single-zone. A zone outage halts commits; losing the zone loses epochs not yet checkpointed. Options: accept it for v1, choose a multi-AZ log (S2's replication scope unverified), or dual-append to two zones and wait for both, which costs latency but needs no consensus while a single fenced sequencer remains. No source quantifies sustained conditional-append throughput on one log, which bounds epoch rate. The one-shot transaction model gives up SQL-session compatibility, by design.

### 2. Views-in-the-log: DBSP over the commit log

**Core idea.** Incrementally maintained SQL views run as first-class consumers of design 1's logical, epoch-ordered log. They are not a separate system fed by CDC. Every view is consistent at an epoch boundary by construction. A query reads base tables and views "as of epoch N" with no coordination.

**Draws on.** DBSP's compositional IVM for full SQL including recursion ([VLDB 2023](https://www.vldb.org/pvldb/vol16/p1601-budiu.pdf)). Differential Dataflow. PolarDB IMCI and AlloyDB, which show redo consumers can build derived structures in production ([transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp)).

**Why nobody ships it.** Every disaggregated OLTP system ships *physical* redo, which says nothing about logical row changes. IVM engines therefore sit downstream of CDC ([RisingWave docs](https://docs.risingwave.com/reference/risingwave-materialize-comparison)). Incumbents cannot retrofit delta-native execution. Snowflake's incremental refresh rejects set operators, EXISTS subqueries and many outer joins ([Snowflake docs](https://docs.snowflake.com/en/user-guide/dynamic-tables-limitations)). A deterministic logical log removes the impedance mismatch.

**Minimal v1.** Compile a SQL subset (select, project, join, group-by) into Z-set operators. Tail the epoch log. Checkpoint view arrangements to S3 next to base snapshots. Serve point reads of views.

**Main risk.** State size. Joins and aggregates keep indexed arrangements of their inputs, so storage grows with the number of views. Non-deterministic functions must be banned or captured into the log.

### 3. Merge-checked branching for agent sandboxes

**Core idea.** A branch is a copy-on-write fork of a Prolly-tree store. Merging is a three-way, row-level diff whose cost scales with the diff, not the data. Before applying the merge, a checker classifies each constraint and view by monotonicity. Monotone ones merge freely. Non-monotone ones (uniqueness, counts, NOT EXISTS) are re-validated incrementally against the merged delta, reusing design 2's engine.

**Draws on.** *Keep CALM and CRDT On*, which shows CRDT queries are often non-monotone and need monotonicity analysis ([VLDB 2023](https://www.vldb.org/pvldb/vol16/p856-power.pdf)). Prolly trees, from Noms and Dolt. DBSP for incremental constraint checking.

**Why nobody ships it.** Relational merge semantics have no general solution. Snapshot branches without merge already satisfy dev/test demand. Neon/Lakebase branch at the storage level and do not merge. Dolt merges but checks only row conflicts, not semantic invariants. Agent workloads make merge newly valuable: 80% of Neon databases come from agents ([Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)).

**Minimal v1.** An embedded single-node store with `BRANCH`, `DIFF` and `MERGE`. The checker handles NOT NULL, UNIQUE, FOREIGN KEY and CHECK, plus one aggregate constraint, and reports a merge as safe, re-validated or conflicting.

**Main risk.** Semantic conflicts that no declared constraint captures. Prolly-tree write amplification and scan speed also trail B-trees and columnar layouts. This design is the least novel at the storage layer; the novelty is the checker.

### 4. Optimizer-free robust join engine with graph patterns

**Core idea.** An analytics engine with no cost-based join enumeration. Acyclic joins run Robust Predicate Transfer, which is provably order-robust. Cyclic joins, including SQL/PGQ graph patterns, run Free Join, which unifies worst-case-optimal and binary hash joins in one operator. The planner shrinks to rewriting rules.

**Draws on.** RPT holds the worst ratio across random join orders to 1.6x and gives a 1.5x geomean speedup ([SIGMOD 2025](https://arxiv.org/abs/2502.15181v1)). Its dynamic-execution follow-up avoids regressions ([VLDB 2026](https://arxiv.org/html/2601.00098v2)). Free Join ([SIGMOD 2023](https://arxiv.org/abs/2301.10841v2)). DuckPGQ ([PVLDB 2023](https://duckdb.org/science/duckpgq)).

**Why nobody ships it.** Running two join paradigms in one engine "hindered the broader adoption of WCOJ methods" ([arXiv 2505.19918](https://arxiv.org/html/2505.19918v1)). Industrial optimizers have stayed structurally stable for about 50 years ([Tian 2025](https://arxiv.org/abs/2510.20082)), and no vendor will gamble its regression budget on removing one.

**Minimal v1.** In-memory columnar tables, a SQL subset with `GRAPH_TABLE` match patterns, RPT for acyclic plans and Free Join for cyclic ones. Benchmark on JOB.

**Main risk.** Filter pre-passes waste time on unselective queries, and deciding when to apply them is an open problem ([arXiv 2601.00098](https://arxiv.org/html/2601.00098v2)). Vectorized analytics is commodity ([Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)), so the novelty is algorithmic, not architectural.

### 5. Unikernel data plane that owns its page tables

**Core idea.** The storage engine runs as a unikernel in a microVM. It implements vmcache-style buffer management by editing its own page tables directly, so the exmap kernel module is unnecessary. It boots in under a second per tenant or query.

**Draws on.** Leis & Dietrich: on a modern cloud VM the DBMS needs only an NVMe and a network driver, and OSv's whole VM subsystem is about 2,100 lines ([PVLDB 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)). vmcache ([SIGMOD 2023](https://www.cs.cit.tum.de/fileadmin/w00cfj/dis/_my_direct_uploads/vmcache.pdf)) and its multi-tier successor vmcache_n, which reports up to 4x TPC-C throughput ([arXiv 2603.03271](https://arxiv.org/html/2603.03271v1)). DSQL already runs query processors in Firecracker microVMs ([DSQL paper](https://www.alphaxiv.org/abs/2607.13276)).

**Why nobody ships it.** Users never installed custom OSes, and drivers were unmaintainable. The cloud removes both blockers, but the proponents call the idea "largely unrealized" ([Leis & Dietrich](https://vldb.org/pvldb/vol17/p2115-leis.pdf)).

**Minimal v1.** A single-threaded B-tree KV store on Firecracker or QEMU with virtio-blk and virtio-net, using direct page-table translation, measured against the same engine on Linux.

**Main risk.** Building the OS consumes the project, and debugging and profiling tools disappear. The architectural payoff only shows on real NVMe and EFA hardware.

## Conclusion

The cloud database frontier is not where the vision papers point. Disaggregation is done, and hardware co-design is gated by access to CXL and RDMA. The open space is ideas that died commercially because they broke interactive SQL. Rented cloud logs change the cost model for exactly those ideas: when every commit is a millisecond-scale, per-request-billed append, batching is forced, and the main argument against deterministic execution disappears. Conditional-append primitives are under two years old, the only production shared-log commit path (DSQL's Journal) is internal to AWS, and the only commercial carrier of the Calvin lineage is gone.

Build in the order 1 → 2 → 3. One log, appended once, then serves as WAL, replication stream, recovery source, view input and branch point. No production system has that property today, and a small team can reach v1 without special hardware. The unknowns to measure first are conditional-append latency and sustained throughput on S3 Express and S2, and whether a multi-AZ option exists at acceptable latency. No source quantifies them, and they bound the whole design.
