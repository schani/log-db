# Transactions, Concurrency Control, Consistency and Replication: Research Not (Yet) in Mature Production Databases (2019-2026)

Method note: ~17 search/fetch calls. Items marked **[verified]** were confirmed against a search result or fetched page this session. Items marked **[prior knowledge, URL not re-fetched]** come from the researcher's background knowledge with a canonical URL; the report writer should treat them as lower-confidence and avoid quoting exact numbers from them without hedging.

---

## Q1. Deterministic databases (Calvin, Aria, Caracal, Detock; Fauna's shutdown) — what's the state?

### Takeaway
Deterministic concurrency control is academically alive (Caracal, Detock, Aria, follow-ons) but commercially weaker in 2026 than in 2020: its one flagship commercial user, Fauna (Calvin-inspired), shut down its hosted service on May 30, 2025 for capital reasons, and no mature production DB uses Calvin-style determinism as its core. Adoption: **none at maturity; one dead startup.**

### Cited Findings
- **Fauna shutdown.** Fauna announced in March 2025 it would shut down its serverless database, citing the capital required to scale a globally distributed service; service ended May 30, 2025, with accounts deleted. It promised an open-source release of its core tech and FQL; a forum reply said the open-source version would not be ready before shutdown. **[verified]** — [The Register](https://www.theregister.com/2025/03/24/faunadb_shut_down/); [Fauna forum](https://forums.fauna.com/t/fauna-service-is-ending-on-may-30-2025/4164)
- Fauna's design lineage traces to Calvin (Thomson/Abadi, SIGMOD 2012), a deterministic transaction scheduling and replication layer. **[verified via secondary]** — [highscalability Calvin summary](https://highscalability.com/paper-calvin-fast-distributed-transactions-for-partitioned-d/); [Fauna webinar page referencing Calvin](https://www2.fauna.com/l/517431/2018-10-02/6fz9sj)
- **Caracal** (Qin, Brown, Goel; **SOSP 2021**, not 2023): shared-memory deterministic DB targeting skewed + contended workloads; batches transactions into epochs and splits contended vs. uncontended pieces. Claims 1.9x–9.7x over prior deterministic schemes in most workloads. A follow-on (Serval) targets residual write-lock overhead. Adoption: **prototype**. **[verified]** — [Caracal paper (U. Toronto)](https://www.eecg.utoronto.ca/~ashvin/publications/caracal.pdf)
- **Detock** (Nguyen, Miller, Abadi; **SIGMOD 2023**): geo-replicated strictly serializable multi-region transactions built on SLOG/Calvin; contribution is abort-free *deterministic deadlock resolution*. Claims near-zero degradation at extreme conflict, an order of magnitude higher throughput than state-of-the-art geo-replication, up to 5x lower latency. Code on GitHub. Adoption: **prototype**. **[verified]** — [UMD DRUM](https://drum.lib.umd.edu/items/8c710897-0b8c-4693-9041-e75209e792d7/full); [GitHub ctring/Detock](https://github.com/ctring/Detock); critical review: [A. Jesse Jiryu Davis review](https://emptysqua.re/blog/review-detock/)
- Abadi's publication list includes a CACM overview of deterministic database systems co-authored with Jose Faleiro (recent). **[verified existence; date not confirmed]** — [Abadi publications](https://cs.umd.edu/~abadi/pubs/pubs.html)
- Ongoing academic deterministic CC work continues (e.g., "Gria" deterministic CC protocol in Frontiers of CS). **[verified existence]** — [Gria](https://journal.hep.com.cn/fcs/EN/1159669497416179855)
- **Aria** (Lu, Yu, Cao, Madden; VLDB 2020): deterministic execution *without* requiring read/write sets in advance — batch execution against a snapshot, then deterministic reordering/abort. Adoption: **prototype**. **[prior knowledge, URL not re-fetched]** — [PVLDB 13 Aria](https://www.vldb.org/pvldb/vol13/p2047-lu.pdf)

### Inferences
- Why not adopted: (1) Calvin requires read/write sets up front (or reconnaissance queries), which clashes with interactive SQL sessions — the dominant client model; Aria relaxes this but still requires one-shot/stored-procedure transactions. (2) Batching/epoch latency floor (milliseconds) is unattractive for OLTP p99. (3) Sequencer layer is an extra global component to operate. (4) Fauna's failure was attributed to capital, not technology — but it removed the only commercial proof-point, which will make investors and buyers more skeptical.
- Determinism ideas *are* leaking in indirectly: log-ordered/"sequence-then-execute" designs (e.g., shared-log architectures, Accord's dependency-ordered execution, Tiga's timestamp-ordered execution) borrow the "agree on order first, execute deterministically" principle without full Calvin.

### Gaps
- Did Fauna actually publish the promised open-source core? No source found confirming release as of Oct 2026.
- No 2024–2026 Abadi blog post explicitly on "is determinism dead?" was found; the "debate" framing could not be sourced.

---

## Q2. Coordination-free / CALM-based systems; local-first and CRDT databases — is there a mature CRDT-native SQL DB?

### Takeaway
Berkeley's Hydro stack remains a research program (papers through POPL/ICDT 2025, dissertations 2025) with no production database built on it. The local-first/CRDT space is consolidating into "sync engines over Postgres/SQLite" rather than CRDT-native SQL databases; the leading Postgres sync startup (Electric) was acquired by Databricks in Aug 2026 to serve AI-agent sandboxes, not CRDT semantics. **No mature CRDT-native SQL DB exists.**

### Cited Findings
- **Hydro / Hydroflow**: Berkeley compiler stack for distributed programs; lowest layer Hydroflow is a Rust dataflow runtime with a semilattice-based IR. Goals include automatic refactoring, replication and partitioning of code. **[verified]** — [UCI ISG talk abstract (Hellerstein)](https://isg.ics.uci.edu/event/joseph-hellerstein-uc-berkeley-hydro-a-compiler-stack-for-distributed-programs/); [Hydroflow TR 2021](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-201.html); [Hydroflow, OOPSLA/SPLASH 2023](https://2023.splashcon.org/details/splash-2023-oopsla/112/Hydroflow-A-Compiler-Target-for-Fast-Correct-Distributed-Programs)
- Hydro publication list (fetched): *Keep CALM and CRDT On* (VLDB 2023), *Optimizing Distributed Protocols with Query Rewrites* (SIGMOD 2024 — rewrites Paxos-like protocols into decoupled/partitioned forms), *Flo* (POPL 2025), *Free Termination Property of Queries Over Time* (ICDT 2025), *Katara: Synthesizing CRDTs with Verified Lifting* (OOPSLA 2022), *Automatic Compartmentalization of Distributed Protocols* (SOSP SRC 2021), 2025 PhD dissertations (Laddad, Power). Page lists no production users. **[verified]** — [hydro.run/research](https://hydro.run/research)
- *Keep CALM and CRDT On* (VLDB 2023): argues CRDTs as typically defined lack a principled query model — reads of CRDT state can be non-monotone and thus not coordination-free — and proposes extending CALM-style monotonicity analysis to queries over CRDTs. **[prior knowledge for summary; venue verified]** — [PVLDB 16 paper](https://www.vldb.org/pvldb/vol16/p856-power.pdf)
- **Anna KVS** (Wu, Hellerstein et al., ICDE 2018 / VLDB 2019 "autoscaling tiered cloud storage"): lattice-based coordination-free KV store. Predates the 2021+ window; not commercialized. **[prior knowledge, URL not re-fetched]** — [Anna VLDB 2019](https://www.vldb.org/pvldb/vol12/p624-wu.pdf)
- **ElectricSQL**: started as CRDT-based ("rich-CRDT") Postgres↔SQLite sync; later rebuilt as a read-path sync engine ("Electric") plus PGlite (Wasm Postgres); the legacy CRDT docs are archived. **[legacy site verified; pivot details prior knowledge]** — [legacy.electric-sql.com](https://legacy.electric-sql.com/docs/reference)
- **Databricks acquired Electric** (announced ~Aug 11–12, 2026): to integrate Electric sync and PGlite into Lakebase; each AI agent runs local PGlite that syncs to central Lakebase Postgres; team joins Databricks' Neon team; managed Electric Cloud being wound down; PGlite claimed to grow 1M→13M weekly downloads in a year; terms undisclosed. **[verified, secondary coverage only]** — [InfoWorld](https://www.infoworld.com/article/4209184/databricks-acquires-electric-to-bring-local-postgres-databases-to-agentic-apps.html); [Techzine](https://www.techzine.eu/news/analytics/143565/databricks-acquires-electric-and-brings-postgres-to-ai-agents/); [Blocks & Files](https://blocksandfiles.com/ai-ml/2026/08/12/oh-no-not-another-one-databricks-buys-electric/5286721)
- **cr-sqlite** (vlcn.io): SQLite loadable extension implementing CRDTs for multi-writer sync. Maintenance status in 2025–2026 unverified. **[verified existence]** — [cr-sqlite docs index](https://docsearch.algolia.com/mcp/docs/repo/vlcn-io/cr-sqlite)

### Inferences
- Why CRDT-native SQL hasn't matured: (1) *Keep CALM and CRDT On* itself shows the semantic gap — SQL queries (aggregates, NOT EXISTS, constraints) are non-monotone, so CRDT merge alone cannot preserve invariants like uniqueness or foreign keys; you need invariant-confluence analysis (Bailis et al. 2014) or coordination. (2) Commercial demand has gone toward "Postgres as source of truth + partial replication/sync" (Electric, PowerSync, Zero) where server authority resolves conflicts — simpler than full multi-master CRDT. (3) The Electric→Databricks deal shows the market value was PGlite/sync for agents, not CRDT convergence.
- Hydro's ideas most likely to transfer: automatic decoupling/partitioning of protocols (SIGMOD 2024) — i.e., compiler-assisted protocol optimization — rather than a new database.

### Gaps
- Ditto (embedded CRDT DB for edge/mobile, used in airline/defense contexts) — no source retrieved; its status and whether it supports SQL semantics could not be verified this session.
- Automerge 2/3 and Automerge-repo production usage — not researched in this session.
- No source found confirming whether any Hydro-compiled service runs in production.

---

## Q3. Leaderless / modern consensus — what's productionized?

### Takeaway
Leader-based Raft/Multi-Paxos still dominates production. The only leaderless-consensus transaction protocol close to a mature product is **Accord** in Apache Cassandra, and as of mid-2026 it ships only in **Cassandra 6.0-alpha1** (production line is 5.0.x). EPaxos remains notorious for specification bugs; Tempo, Mencius, Compartmentalized Paxos remain prototypes. Flexible Paxos quorum ideas are the main research idea that has quietly diffused.

### Cited Findings
- **Accord / CEP-15**: leaderless consensus protocol giving strict-serializable multi-partition ACID transactions in Cassandra. CEP-15 tracking ticket created 2021-10-30, merged to trunk 2025-01-21. Ships in Cassandra **6.0 alpha** (alpha1 ~March/April 2026); production line was 5.0.8 (2026-04-16); no GA date found. Requires CMS (cluster metadata service) for upgrade; syntax `BEGIN TRANSACTION … COMMIT TRANSACTION` "may evolve before GA". **[verified, secondary]** — [The New Stack](https://thenewstack.io/apache-cassandra-6-features/); [Instaclustr](https://www.instaclustr.com/blog/apache-cassandra-6-accord-transactions-what-you-need-to-know/); [youngju.dev status write-up (secondary blog)](https://www.youngju.dev/transcribe/2026-07-17-cassandra-6-accord-alpha1-status.en)
  - Note: Accord was originally pitched for Cassandra 5.0 and slipped to 6.0 — ~5 years from CEP to alpha. **[the 5.0 target is prior knowledge]**
- **EPaxos**: OPODIS 2025 paper (Ryabinin, Gotsman, Sutra; arXiv v2 Jan 2026) states EPaxos "is complex, ambiguously specified, and suffers from nontrivial bugs", despite 500+ citations. **[verified]** — [arXiv 2511.02743](https://arxiv.org/abs/2511.02743)
  - Earlier: *EPaxos Revisited* (Tollman, Park, Ousterhout; NSDI 2021) found the original evaluation overstated benefits and identified issues. **[prior knowledge, URL not re-fetched]** — [NSDI'21](https://www.usenix.org/conference/nsdi21/presentation/tollman)
- **Tempo** (Enes, Baquero, Gotsman, Sutra; **EuroSys 2021**): leaderless SMR assigning scalar timestamps to commands, executing in timestamp order; claims higher throughput than EPaxos and Janus. No production deployment found. **[verified]** — [Tempo paper](https://software.imdea.org/~gotsman/papers/tempo-eurosys21.pdf)
- **Compartmentalized Paxos** (Whittaker et al., VLDB 2021): decouple Paxos roles (proxy leaders, read/write quorum grids, batchers) to scale throughput; Hydro's later work automates this. Adoption: **prototype**. **[prior knowledge, URL not re-fetched]** — [PVLDB 14](https://www.vldb.org/pvldb/vol14/p2203-whittaker.pdf)
- 2019 comparative study (Ailijiang, Charapko, Demirbas) of single-leader, multi-leader, hierarchical and leaderless Paxos in LAN/WAN. **[verified]** — [UB tech report](https://cse.buffalo.edu/tech-reports/2017-03.pdf)

### Inferences
- Why leaderless hasn't been adopted: (1) correctness risk — recovery paths for dependency-graph protocols are notoriously subtle (the EPaxos bug history is the canonical warning); (2) the latency win (one WAN RTT from any region) matters only for multi-leader geo-writes, a niche relative to single-region primaries; (3) execution requires dependency-graph resolution with livelock/tail-latency risk under conflict; (4) Raft has a mature ecosystem (etcd-raft, hashicorp/raft, openraft) and well-understood ops. Accord's 4+ year path inside a well-funded Apache project shows the engineering cost.
- Flexible Paxos (Howard et al., 2016) — quorum intersection only needed between phase-1 and phase-2 — is the idea most likely to appear quietly inside production systems; not verified this session.

### Gaps
- No Jepsen or formal verification result for Accord-in-Cassandra found.
- No source confirming which production systems explicitly use Flexible Paxos quorums.
- Mencius, Raft variants (e.g., Raft*, PigPaxos) not researched in this session.

---

## Q4. Transactions over disaggregated memory/storage; serverless transactions

### Takeaway
The serverless-transaction line (Beldi → Boki → Halfmoon, 2020–2023, journal 2025) produced clear results on exactly-once stateful functions via shared logs, but is **not adopted**; the commercial realization of the same idea is durable-execution products (Temporal, DBOS, AWS Lambda Durable Functions-style offerings) that use a conventional database/log rather than these research protocols.

### Cited Findings
- **Halfmoon** (SOSP 2023; journal version 2025 "Efficient Fault Tolerance for Stateful Serverless Computing with Asymmetric Logging"): logging both reads and writes is unnecessary for exactly-once serverless state; log only one side → two protocols (read-heavy vs write-heavy). Claims 20–40% lower latency and 1.5–4.0x lower logging overhead vs. Boki. Built on Boki's log layer and Beldi codebase. Adoption: **prototype**. **[verified]** — [DOI 10.1145/3600006.3613154](https://doi.org/10.1145/3600006.3613154); [journal DOI](https://api.crossref.org/works/10.1145%2F3725985); [Halfmoon-bench](https://github.com/pkusys/Halfmoon-bench)
- **Boki** (SOSP 2021): shared-log API exported to serverless functions; a "metalog" provides ordering, consistency and fault tolerance. Adoption: **prototype**. **[verified]** — [Boki paper (NSF PAR)](https://par.nsf.gov/servlets/purl/10357172)
- **Beldi** (Zhang et al., OSDI 2020): log-based fault tolerance and transactions for stateful serverless functions atop DynamoDB. **[venue: prior knowledge]** — [USENIX OSDI'20](https://www.usenix.org/conference/osdi20/presentation/zhang-haoran); context in [serverless survey](https://arxiv.org/pdf/2206.12275)

### Inferences
- Why not adopted: cloud providers own the FaaS runtime and the log; academic designs require a custom shared log (Boki) co-located with functions, which a third party cannot deploy into Lambda/Cloud Run. Industry instead converged on library-level durable execution against an existing DB (see Q7). The asymmetric-logging insight (Halfmoon) is a cheap, transferable optimization that durable-execution engines could adopt — no evidence they have.
- Disaggregated-memory transactions (e.g., FaRM/FaRMv2, Motor OSDI 2024, RDMA/CXL-based designs) — not researched this session; production adoption appears limited to vendor-internal systems (e.g., Microsoft FaRM lineage, Alibaba PolarDB-MP) — **unverified**.

### Gaps
- Unum (decentralized serverless orchestration, NSDI 2023) and "transactional serverless" (e.g., Hydro's "Cloudburst"/"AFT", Apiary from DBOS team) not verified this session.
- Disaggregated-memory CC (Motor, FORD, Sherman, CXL-based) adoption status not verified.

---

## Q5. Multi-version CC innovations, learned CC, snapshot isolation at scale, geo-distributed transactions

### Takeaway
In-memory OCC/MVCC research (Silo, TicToc, Cicada, Polyjuice) mostly hasn't been adopted as-is; the most visible 2025 production adoption of an "old research" CC idea is **Aurora DSQL**: OCC with snapshot isolation (≈ Postgres REPEATABLE READ), commit-time validation, and clock-based snapshots — i.e., a deliberately *weaker-than-serializable*, abort-on-conflict design. Geo-distributed transaction protocols (Detock, Natto, Chablis, Tiga) are all prototypes; Tiga (SOSP 2025) is the strongest recent result.

### Cited Findings
- **Aurora DSQL**: ACID via snapshot isolation (≈ PostgreSQL repeatable read); reads from start-time snapshot; conflicts detected at commit (OCC, no locks); loser receives a Postgres serialization error and must retry with backoff/jitter. Under high key contention OCC can raise abort rates. **[verified]** — [AWS docs](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-concurrency-control.html); [AWS DB blog](https://aws.amazon.com/blogs/database/concurrency-control-in-amazon-aurora-dsql/); [Brooker series part 1](https://aws.amazon.com/blogs/database/everything-you-dont-need-to-know-about-amazon-aurora-dsql-part-1-setting-the-scene)
  - Relies on AWS Time Sync Service for snapshot timestamps (per competitor glossary — treat as vendor-adjacent). **[verified, secondary]** — [Cockroach Labs glossary](https://www.cockroachlabs.com/glossary/distributed-db/dsql/)
  - SI permits write skew (doctors on-call example from Brooker's re:Invent talk, via third-party summary). **[verified, secondary]** — [advancedweb.hu](https://advancedweb.hu/a-first-look-into-awss-new-aurora-dsql-database/)
- **Tiga** (Geng, Mu, Sivaraman, Prabhakar; **SOSP 2025**): merges concurrency control and consensus; assigns each transaction a *future timestamp* using synchronized clocks so most transactions arrive before their timestamp and commit strictly serializably in **1 WAN RTT**; late arrivals take a 1.5–2 WRTT slow path. Claims 1.3–7.2x throughput, 1.4–4.6x lower latency vs. baselines. Open source. Adoption: **prototype**. **[verified]** — [arXiv 2509.05759](https://arxiv.org/abs/2509.05759); [NSF PAR](https://par.nsf.gov/biblio/10649793)
- **Natto** (Yang, Yan, Wong; **SIGMOD 2022**): geo-distributed DB with transaction *prioritization*; uses network-delay measurements to timestamp transactions and selectively abort/preempt low-priority ones; lower tail latency for high-priority transactions vs. Carousel and TAPIR. Adoption: **prototype**. **[verified]** — [Natto paper](https://cs.uwaterloo.ca/~bernard/natto.pdf)
- **Chablis** (Eldeeb, Bernstein, Cidon, Yang; **CIDR 2024**): geo-distributed multi-versioned transactional KV; low-latency RW transactions for regionally-homed data plus global strictly-serializable snapshot reads. Adoption: **prototype**. **[verified]** — [CIDR 2024](https://vldb.org/cidrdb/2024/chablis-fast-and-general-transactions-in-geo-distributed-systems.html); [paper](https://mail.vldb.org/cidrdb/papers/2024/p4-eldeeb.pdf)
- **Detock** (SIGMOD 2023): see Q1.
- **Polyjuice** (Wang et al., OSDI 2021): learns a per-(transaction type, access) CC policy via evolutionary search over a policy space spanning OCC/2PL/IC3-style early-validation and waiting; claims gains over hand-designed CC on TPC-C/TPC-E under contention. Adoption: **prototype**. **[prior knowledge, URL not re-fetched]** — [USENIX OSDI'21](https://www.usenix.org/conference/osdi21/presentation/wang-jiachen)
- Recent production-adjacent CC research continues to target contention under 2PL rather than novel MVCC: e.g., TXSQL (Tencent, lock optimizations for high-contention, 2025) and Brook-2PL (deadlock-free 2PL, 2025). **[verified existence]** — [TXSQL arXiv 2504.06854](https://arxiv.org/pdf/2504.06854); [Brook-2PL arXiv 2508.18576](https://arxiv.org/pdf/2508.18576)

### Inferences
- Why Silo/TicToc/Cicada/Polyjuice aren't in mature DBs: they assume in-memory, stored-procedure, one-shot transactions on a single multi-core box with no network round trips; production OLTP is interactive (client RTT inside transaction), disk/WAL-bound, and cloud-replicated, so CC CPU cost is rarely the bottleneck. Polyjuice-style learned CC adds training/workload-drift risk and non-explainable abort behavior — hard to support.
- DSQL is evidence of a pattern: production systems *choose simpler, weaker* designs (OCC + SI + retries) over research protocols that guarantee serializability with fewer aborts. The adoption gap is driven by operability and Postgres compatibility, not by performance.
- Tiga, Detock, Natto all depend on either clock sync or deterministic sequencing and on one-shot transactions; the interactive-transaction assumption again blocks adoption. Improved cloud clock sync (AWS Time Sync microsecond accuracy, see [Yugabyte on clock sync](https://www.yugabyte.com/blog/evolving-clock-sync-for-distributed-databases/)) lowers one barrier for Tiga-style designs.

### Gaps
- TicToc (SIGMOD 2016), Cicada (SIGMOD 2017) are pre-2019; their incorporation into any production engine was not verified.
- Whether DSQL offers any serializable mode, or its exact GA date (believed May 2025), not verified this session.

---

## Q6. Formal methods-first DBs, verified storage, and Jepsen findings that show gaps

### Takeaway
Jepsen keeps finding isolation violations in mature, widely-trusted systems (Amazon RDS for PostgreSQL multi-AZ, 2025; MariaDB Galera, 2026), showing that production systems lag behind *even 1990s–2000s* isolation theory. Verified-storage research (FSCQ lineage, Verus, etc.) has not produced a verified production DB; industrial formal methods are lightweight (TLA+, P, deterministic simulation testing).

### Cited Findings
- **Jepsen: Amazon RDS for PostgreSQL 17.4** (Apr 29, 2025): multi-AZ clusters violate Snapshot Isolation; healthy clusters occasionally exhibit Long Fork and other G-nonadjacent cycles; seen in every version tested (13.15–17.4); RDS may instead provide Parallel Snapshot Isolation. **[verified]** — [Jepsen](https://jepsen.io/analyses/amazon-rds-for-postgresql-17.4); explainer: [Justin Jaffray](https://buttondown.com/jaffray/archive/how-to-understand-that-jepsen-report)
- **Jepsen: MariaDB Galera Cluster 12.1.2** (Mar 16, 2026): allows P4 Lost Update even without faults, failing its claimed isolation ("between Serializable and Repeatable Read"); can lose committed transactions under some crash/partition scenarios. **[verified]** — [Jepsen blog](https://jepsen.io/blog/2026-03-16-mariadb-galera-cluster-12.1.2)
- MySQL Repeatable Read violations (G2, lost update, non-monotonic reads) are widely cited; date of the underlying Jepsen work not confirmed. **[verified existence, secondary]** — [Vonng blog](https://blog.vonng.com/en/db/bad-mysql/)
- EPaxos bugs (OPODIS 2025) — see Q3 — are a formal-methods-style finding about a research protocol. **[verified]** — [arXiv 2511.02743](https://arxiv.org/abs/2511.02743)

### Inferences
- The production gap is not "missing novel research" but "not meeting the documented guarantee"; checkers like Elle (Kingsbury & Alvaro, VLDB 2020) are research that *has* been adopted (Jepsen itself, vendor CI) — a counterexample useful for the report.
- Fully verified storage/DB engines remain research because verification cost scales poorly with performance optimizations (concurrency, caching, async I/O) that production engines need.

### Gaps
- Verus-based or FSCQ-style verified storage systems from 2023–2026 (e.g., verified KV stores, AWS's use of Dafny/Lean in storage) not researched this session.
- Deterministic simulation testing adoption (FoundationDB, TigerBeetle, Antithesis) not researched this session.

---

## Q7. Database-native workflows / durable execution (DBOS, Temporal) — research vs product

### Takeaway
DBOS is a rare case of a 2020s research idea (MIT/Stanford "DBMS-oriented OS", VLDB 2022) becoming a funded startup within ~2 years, but it pivoted from "OS on a database" to a lightweight durable-execution library checkpointing workflow steps to Postgres. Adoption: **startup**; Temporal (not research-derived) is the market leader in durable execution.

### Cited Findings
- **DBOS research paper**: "DBOS: a DBMS-oriented operating system", PVLDB vol. 15, pp. 21–30. **[verified]** — [Wikipedia: DBOS](https://en.wikipedia.org/wiki/DBOS)
- **DBOS Inc.** founded April 2023; $8.5M seed (Engine Ventures, Construct Capital lead) announced March 2024 with DBOS Cloud launch. **[verified]** — [Pulse 2.0](https://pulse2.com/dbos-cloud-native-operating-system-company-raises-8-5-million); [The Next Platform](https://www.nextplatform.com/2024/03/12/the-cloud-outgrows-linux-and-sparks-a-new-operating-system/)
- **DBOS Transact**: open-source Python/TypeScript library that checkpoints program state into Postgres after each step, running inside the existing app with the existing Postgres. **[verified, secondary]** — [Wikipedia: DBOS](https://en.wikipedia.org/wiki/DBOS)

### Inferences
- The research→product path shows the pattern: the radical claim (replace the OS with a DBMS) was dropped; the deployable kernel (durable workflows = transactions + idempotent step log in Postgres) survived. This mirrors Beldi/Boki/Halfmoon (Q4): exactly-once via logging is valuable, but only when delivered as a library on an existing DB.
- Remaining unexploited research: making durable execution *transactional with the application's own data* (step and data write in one DB transaction) is DBOS's distinctive claim vs. Temporal; asymmetric logging (Halfmoon) could reduce checkpoint overhead in such engines.

### Gaps
- DBOS later funding, customer counts, and Temporal's funding/valuation not verified this session.
- Apiary (DBOS group, transactional FaaS) and "Restate" not researched.

---

## Cross-cutting summary table (for report writer)

| Idea | Paper / venue / year | Adoption (Oct 2026) | Main blocker |
|---|---|---|---|
| Calvin-style determinism | Calvin SIGMOD'12; Aria VLDB'20; Caracal SOSP'21; Detock SIGMOD'23 | none (Fauna dead May 2025) | needs read/write sets / one-shot txns; batching latency |
| Leaderless consensus txns | Accord (CEP-15); EPaxos; Tempo EuroSys'21 | Accord: Cassandra 6.0 alpha only | correctness complexity; EPaxos bugs (OPODIS'25) |
| Compartmentalized/auto-optimized Paxos | VLDB'21; Hydro SIGMOD'24 | prototype | ops complexity; Raft "good enough" |
| CALM / CRDT queries | Keep CALM and CRDT On VLDB'23; Hydro POPL/ICDT'25 | research | non-monotone SQL, invariants |
| CRDT/local-first SQL | ElectricSQL, cr-sqlite | Electric pivoted to sync; acquired by Databricks Aug 2026 | server-authoritative sync won |
| Serverless exactly-once txns | Beldi OSDI'20; Boki SOSP'21; Halfmoon SOSP'23 | prototype | needs custom shared log inside FaaS |
| Learned CC | Polyjuice OSDI'21 | prototype | drift, explainability, interactive txns |
| Clock-based 1-RTT geo txns | Tiga SOSP'25; Natto SIGMOD'22; Chablis CIDR'24 | prototype | one-shot txns; clock assumptions |
| OCC + SI at cloud scale | Aurora DSQL (2024–25) | mature-ish product | weaker isolation (write skew), aborts under contention |
| Durable execution in DB | DBOS PVLDB'22 | startup | competes with Temporal |
