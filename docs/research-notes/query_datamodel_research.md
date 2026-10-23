# Query Processing, Data Models and Programming Models: Research (2019–2026) Not (or Barely) Adopted in Mature Production Databases

Scope note: 19 tool calls were used. Items marked "[background, not re-verified]" come from the researcher's prior knowledge and were not confirmed by a source fetched in this session. The report writer should treat them as lower-confidence or drop them.

## 1. Incremental view maintenance (DBSP, differential dataflow, F-IVM, DBToaster): how far has IVM reached general-purpose DBs?

### Takeaway
IVM theory is mature: DBSP (VLDB 2023) gives a general, compositional algorithm for full SQL including recursion. Production use, though, sits mostly in specialized startups (Feldera, Materialize, RisingWave). The big general-purpose systems ship only restricted IVM. Snowflake dynamic tables pick incremental or full refresh once, at creation, and set operators, many outer-join/window patterns and EXISTS subqueries force full refresh. PostgreSQL core still has no IVM: the patch has been bounced between commitfests for years, and in 2026 its scope narrowed to simple SPJ views.

### Cited Findings
- **DBSP / Feldera.** The DBSP paper was presented at VLDB 2023. Feldera compiles SQL views to Rust through a SQL-to-DBSP compiler — [Feldera docs](https://docs.feldera.com/sql/intro/); [paperswithcode DBSP](https://cs.paperswithcode.com/paper/dbsp-automatic-incremental-view-maintenance)
- Feldera claims incremental support for joins, aggregates, correlated subqueries, window functions, recursive queries and nested views without falling back to recomputation. It also claims production pipelines with "500+ joins" at sub-second latency on TB scale. These are vendor claims — [feldera.com/llms.txt](https://www.feldera.com/llms.txt)
- A May 2025 Feldera post by the CTO says it runs multi-billion-record datasets on a single node. Scale-out is described as upcoming work, meaning not yet shipped at that time — [Feldera blog: Universal IVM](https://www.feldera.com/blog/universal-ivm)
- Feldera raised $21.5M (Seed + Series A). The "95% compute cost reduction" is a marketing figure, not an independent benchmark — [CXO Digital Pulse](https://www.cxodigitalpulse.com/?p=62402)
- No independent 2025 production case studies of Feldera were found. Production claims are vendor-reported only (search result assessment).
- **Snowflake dynamic tables.** In AUTO mode, the refresh mode is decided once, at creation. If an upstream change later makes incremental refresh unsupported, refreshes fail instead of silently switching to full, and the fix is CREATE OR REPLACE — [Snowflake docs: refresh modes](https://docs.snowflake.com/en/user-guide/dynamic-tables-refresh)
- Snowflake incremental refresh does not support:
  - set operators (UNION, MINUS, EXCEPT, INTERSECT);
  - some UNION ALL, outer-join and window-function patterns;
  - non-deterministic functions;
  - subqueries outside FROM, such as WHERE EXISTS.

  Structured OBJECT/ARRAY/MAP types are unsupported in both modes — [Snowflake docs: known limitations](https://docs.snowflake.com/en/user-guide/dynamic-tables-limitations); [supported queries](https://docs.snowflake.com/en/user-guide/dynamic-tables-supported-queries)
- Snowflake recommends keeping changes under about 5% between refreshes for good incremental performance. This is a performance guideline, not a hard limit — [Snowflake docs](https://docs.snowflake.com/en/user-guide/dynamic-tables-refresh). Older third-party material (select.dev) describes a runtime fallback to full refresh, which contradicts the current docs — [select.dev](https://select.dev/posts/snowflake-dynamic-tables)
- **PostgreSQL core IVM.** The "Incremental View Maintenance (IVM), take 2" commitfest entry (#4337) has been carried across many commitfests. Snapshots show it in "needs review" for the PG20 cycle, and also needing a rebase with CFBot failing — [CF 55/4337](https://commitfest.postgresql.org/55/4337/); [CF 53/4337](https://commitfest.postgresql.org/53/4337)
- A May 2026 pgsql-hackers design post by the patch author proposes to "initially focus on simple SPJ views", deferring DISTINCT and aggregates, and to switch to transition tables — [postgrespro mailing-list archive](https://postgrespro.com/list/id/20260529231417.7cd817f97347dfa048608517@sraoss.co.jp)
- **Materialize / RisingWave.** Materialize runs on Timely/Differential Dataflow (additions/retractions) and is licensed under the BSL. RisingWave is Apache 2.0. Materialize offers strict serializability. RisingWave offers snapshot consistency with a default 1s checkpoint. These come from RisingWave-authored comparisons, which have a commercial bias — [RisingWave docs comparison](https://docs.risingwave.com/reference/risingwave-materialize-comparison); [RisingWave blog](https://risingwave.com/blog/risingwave-vs-materialize-comparison/)
- Sources conflict on whether Materialize offers a self-managed option. One RisingWave page lists self-managed Kubernetes plus an emulator. Another RisingWave blog says SaaS only. A third-party profile dates "Self-Managed & Emulator" to 2024 — [RisingWave docs](https://docs.risingwave.com/reference/risingwave-materialize-comparison) vs [RisingWave blog](https://risingwave.com/blog/incremental-materialized-views-complete-guide/); [yespress](https://yespress.io/materialize)

### Inferences
- **Adoption status:**
  - DBSP: startup (Feldera).
  - Differential dataflow: startup (Materialize).
  - F-IVM, higher-order IVM, DBToaster: research or prototype only [background, not re-verified].
  - General-purpose DBs: restricted IVM, i.e. Snowflake dynamic tables and, per background, Databricks materialized views via Enzyme, BigQuery incremental MVs, and Oracle fast-refresh MVs, each with a long list of unsupported constructs.
- **Why IVM hasn't been adopted more widely:**
  1. Full IVM needs the whole query engine to operate on deltas (Z-sets with weights), which is effectively a new engine rather than a feature added to an existing one.
  2. State size: joins and aggregates must keep indexed arrangements of their inputs, and memory and storage costs rise with the number of views.
  3. Non-determinism, NULL and outer-join semantics, and window functions are hard to handle incrementally.
  4. Incumbents' snapshot and transaction architectures are not built around change streams.
  5. "Refresh fails rather than falls back" (Snowflake) shows vendors prefer predictability over generality.
- [background, not re-verified] The DBSP authors are Budiu, Chajed, McSherry, Ryzhyk and Tannen, and the paper won the VLDB 2023 best paper award. F-IVM (Nikolic and Olteanu, SIGMOD 2018 / VLDB Journal 2023) uses factorized ring-based higher-order IVM. pg_ivm is a separate extension maintained by SRA OSS that supports a subset of SPJ+aggregate views with immediate maintenance.

### Gaps
- No independent benchmark comparing Feldera, Materialize, RisingWave and Snowflake dynamic tables was found.
- pg_ivm extension release status and adoption numbers were not retrieved.
- Databricks Enzyme and BigQuery incremental MV limitations were not retrieved this session.

## 2. Worst-case optimal joins, Free Join, Yannakakis revisited, (Robust) Predicate Transfer, factorized DBs: adoption in mainstream engines

### Takeaway
The robust-join family (predicate transfer, RPT, Yannakakis variants) is the most active 2023–2026 thread, and DuckDB is its main testbed. It exists there as forks, papers and a community extension ("robust"), not in DuckDB core. WCOJ is in production only in Umbra (and so presumably CedarDB) as a sub-plan option, and in graph and Datalog systems such as RelationalAI and Kùzu. Kùzu, the most prominent open-source WCOJ/factorized graph DB, was archived in October 2025 after Apple acquired it.

### Cited Findings
- **Robust Predicate Transfer (RPT), SIGMOD 2025** ("Debunking the Myth of Join Ordering: Toward Robust SQL Analytics").
  - The paper introduces the LargestRoot and SafeSubjoin algorithms, which make semi-join reduction provably robust to join order for acyclic queries.
  - It is integrated into DuckDB and evaluated on TPC-H, JOB and TPC-DS.
  - The worst max/min runtime ratio across random join orders is 1.6x, and the end-to-end speedup is about 1.5x geometric mean.

  — [arXiv 2502.15181](https://arxiv.org/abs/2502.15181v1); [paper PDF](https://people.iiis.tsinghua.edu.cn/~huanchen/publications/rpt-sigmod25.pdf)
- The same source states that the classic Yannakakis algorithm guarantees cost linear in input plus output for acyclic queries but saw little adoption because its semi-joins are expensive. Predicate Transfer replaces those semi-joins with Bloom filters but loses the guarantee — [arXiv 2502.15181v2](https://arxiv.org/html/2502.15181v2)
- A VLDB 2026 follow-up, "Robust Predicate Transfer with Dynamic Execution", reduces RPT's overhead, is implemented in DuckDB, and reports avoiding regressions on JOB/TPC-H/SQLStorm — [arXiv 2601.00098](https://arxiv.org/html/2601.00098v2)
- An open issue flagged in the same work: integrating bitvector filters into a cost-based optimizer is still unsolved, because pre-filtering does not pay off for unselective queries — [arXiv 2601.00098](https://arxiv.org/html/2601.00098v2)
- A DuckDB **community extension "robust"** implements predicate transfer by deriving filters from join keys and propagating them across the join graph. It is a community extension, not core — [duckdb.org community extension](https://duckdb.org/community_extensions/extensions/robust.html)
- Yannakakis theory is still active at ICDT 2026 — [ICDT 2026 LIPIcs paper](https://drops.dagstuhl.de/storage/00lipics/lipics-vol365-icdt2026/html/LIPIcs.ICDT.2026.25/LIPIcs.ICDT.2026.25.html)
- **Free Join (SIGMOD 2023, Wang, Willsey, Suciu)**:
  - It unifies WCOJ (Generic Join) and binary hash joins with a new plan type and a new data structure, the COLT trie/hash hybrid.
  - Its Rust implementation matches or beats both binary joins and Generic Join on standard benchmarks.

  The authors note that WCOJ is typically slower than binary joins on the acyclic queries common in practice — [arXiv 2301.10841](https://arxiv.org/abs/2301.10841v2); [NSF PAR](https://par.nsf.gov/biblio/10472614)
- A 2025 paper states that running two separate join algorithms in one system "introduces additional complexity, which has hindered the broader adoption of WCOJ methods", and that Free Join covers only hash-based WCOJ — [arXiv 2505.19918](https://arxiv.org/html/2505.19918v1)
- **Umbra** integrates WCOJ into its optimizer for sub-plans with large intermediate results. It is a hybrid, not a replacement — [DBDB.io Umbra](https://dbdb.io/db/umbra)
- **Kùzu**:
  - Its GitHub repo was archived on 10 Oct 2025 with the note "Kuzu is working on something new" — [The Register](https://www.theregister.com/2025/10/14/kuzudb_abandoned/)
  - An EU DMA filing shows that Apple agreed on 9 Oct 2025 to buy all shares and hire select employees. Kùzu had about 10 employees — [BetaKit](https://betakit.com/apple-strikes-deal-to-acquire-canadian-database-software-startup-kuzu/); [UWaterloo news](https://cs.uwaterloo.ca/news/waterloo-based-graph-database-start-up-kuzu-acquired-apple)
  - There will be no further fixes from the original authors, and community forks continue the work — [PuppyGraph blog](https://www.puppygraph.com/blog/what-is-kuzudb)

### Inferences
- **Adoption status:**

  | Technique | Status |
  |---|---|
  | RPT / predicate transfer | Prototype (DuckDB forks, community extension) |
  | Free Join | Research prototype |
  | WCOJ | Mature only as a hybrid in Umbra/CedarDB; startup-level in RelationalAI; Kùzu discontinued as an open-source product |
  | Factorized query processing | Shipped in Kùzu (now archived) and in RelationalAI [background, not re-verified]; otherwise research (FDB, Olteanu) |

- **Why these haven't been adopted:**
  1. Benchmarks such as TPC-H/DS are acyclic and well served by binary hash joins plus decent cardinality estimation, so the asymptotic gain rarely appears.
  2. Two join paradigms in one engine double the complexity (memory management, spilling, parallelism).
  3. Bloom-filter pre-passes cost time on unselective queries, and choosing when to apply them remains an unsolved costing problem.
  4. Mainstream engines already use partial sideways information passing (runtime/bloom filters in Spark, Snowflake, Photon, Velox), which captures part of the benefit [background, not re-verified].
- The Kùzu exit is a cautionary data point: a technically strong academic spin-out with WCOJ and factorization did not survive independently as an OSS business.
- [background, not re-verified] "Adopting Worst-Case Optimal Joins in Relational Database Systems" (Freitag et al., VLDB 2020) is the basis of Umbra's hybrid approach. "Yannakakis+" (Hu et al., SIGMOD 2025) and Birler/Kemper/Neumann's "Robust Join Processing with Diamond Hardened Joins" (VLDB 2024) are related robust-join work from the Umbra group.

### Gaps
- No source was found confirming whether CedarDB ships Umbra's WCOJ.
- No source was found on DuckDB core plans to merge predicate transfer.
- RelationalAI's internal join algorithms were not confirmed from primary sources this session.

## 3. Datalog-based and relational-programming DBs, semiring provenance, PL–DB fusion

### Takeaway
Datalog and relational programming live on in niches: program analysis (Soufflé), compilers and term rewriting (egglog), and one well-funded commercial knowledge-graph product (RelationalAI). That product now ships as a Snowflake Native App coprocessor rather than a standalone DB. None of these has entered mainstream SQL engines beyond the WITH RECURSIVE that already exists.

### Cited Findings
- **egglog (PLDI 2023)**, "Better Together: Unifying Datalog and Equality Saturation" (Zhang, Wang, Flatt, Cao, Zucker, Rosenthal, Tatlock, Willsey; PACMPL 7, art. 125). Reimplementing two case studies (a pointer analysis and a floating-point rewriter) made them faster and simpler and fixed bugs in the originals — [PLDI 2023](https://pldi23.sigplan.org/details/pldi-2023-pldi/20/Better-Together-Unifying-Datalog-and-Equality-Saturation); [arXiv 2304.04332](https://arxiv.org/abs/2304.04332v3)
- egglog has since gained scheduling, proofs, Python bindings and plugins, and had a PLDI 2025 tutorial — [PLDI 2025 tutorial](https://pldi25.sigplan.org/details/pldi-2025-tutorials/4/Unlocking-Optimizations-with-egglog-Equality-Saturation-Meets-Datalog)
- **RelationalAI**:
  - It previewed at Snowflake Summit 2024, became publicly available as a Snowflake Native App in June 2024, and was GA on AWS and Azure by June 2025 — [RelationalAI blog](https://www.relational.ai/post/rai-now-available-in-snowflake); [BigDataWire, June 2025](https://www.hpcwire.com/bigdatawire/2025/06/10/the-relational-model-always-wins-relationalai-ceo-says/)
  - It runs as a "knowledge graph coprocessor" inside the customer's Snowflake account — [RelationalAI architecture white paper](https://www.relational.ai/post/relationalai-snowflake-native-app-architecture-white-paper)
  - Thoughtworks Tech Radar placed it in "Trial" (Nov 2025) — [Thoughtworks Radar](https://www.thoughtworks.com/radar/tools/relationalai)
  - Verdantix says it uses Rel, a proprietary declarative language, and not RDF or property-graph standards — [Verdantix](https://atlas.verdantix.com/relationalai/relationalai)

### Inferences
- **Adoption status:**
  - Soufflé: mature in its niche, static analysis (e.g., the Doop framework).
  - egglog: research, adopted inside compiler projects.
  - RelationalAI: startup, distributed via Snowflake.
  - CozoDB, Logica (Google): small open-source or research projects.
  - Differential Datalog (VMware): effectively discontinued; its authors moved on to DBSP/Feldera.
  - Semiring provenance: theory, with prototypes such as ProvSQL.
  - Hydro (Berkeley): research.

  All of the above except RelationalAI's distribution channel are [background, not re-verified].
- **Why Datalog hasn't been adopted:**
  1. SQL's network effects and the lack of a compelling killer workload; recursive queries are rare in BI.
  2. Datalog engines optimize for fixpoint and semi-naive evaluation, not for columnar scans and aggregates.
  3. RelationalAI's pivot from standalone DB to a coprocessor inside Snowflake suggests that new data models must ride on existing data gravity rather than replace the warehouse.
- PL–DB fusion: Feldera's DBSP grew out of the Differential Datalog effort at VMware, so "Datalog research → IVM product" is the realistic transfer path. Datalog-as-primary-query-language has not been one [background, not re-verified].

### Gaps
- No current sources were fetched on CozoDB activity, Logica adoption, Soufflé usage stats, Hydro/Hydroflow status, or semiring provenance in any product.
- Whether RelationalAI still exposes Rel or has moved to a Python front-end (PyRel) was not verified.

## 4. Learned query optimization and LLM/semantic-operator query engines: production status

### Takeaway
Learned optimizers that replace the planner (Neo, Balsa, LOGER) remain research. The one documented at-scale production deployment is a "steering" approach: Microsoft's QO-Advisor recommends rule hints to SCOPE, descending from Bao. An independent VLDB 2024 evaluation found that PostgreSQL's native optimizer beats the learned optimizers in almost all experiments under rigorous train/test splits. Semantic operators (LOTUS etc.) moved into products fast: Snowflake Cortex AISQL is deployed in production. This is the fastest research-to-product transfer in this whole area.

### Cited Findings
- **Bao → SCOPE**:
  - Bao treats rule configurations as bandit arms, with a tree-convolutional cost model.
  - The SIGMOD 2021 SCOPE adaptation was evaluated on production workloads of about 150K daily jobs, with reported 7–30% latency savings.
  - QO-Advisor (SIGMOD 2022) externalizes steering to an offline pipeline and is "enabled by default on production SCOPE workloads".

  — [arXiv 2210.13625](https://arxiv.org/pdf/2210.13625); [Microsoft Research](https://www.microsoft.com/en-us/research/publication/deploying-a-steered-query-optimizer-in-production-at-microsoft/)
- **Lehmann, Sulimov, Stockinger, "Is Your Learned Query Optimizer Behaving As You Expect? A Machine Learning Perspective", PVLDB 17(7) 2024.**
  - The learned-optimizer literature uses inconsistent training data generation and self-selected benchmark splits.
  - Under the authors' standardized framework, "PostgreSQL outperforms these LQOs in almost all experiments depending on the train/test splits."

  — [PVLDB PDF](https://www.vldb.org/pvldb/vol17/p1565-lehmann.pdf); [arXiv 2309.01551](https://arxiv.org/pdf/2309.01551)
- Yuanyuan Tian, "Query Optimization in the Wild: Realities and Trends" (arXiv Oct 2025, to appear in SIGMOD Record 2026). Industrial optimizers have stayed structurally "remarkably stable" on System R and Volcano/Cascades for about 50 years. The trends it names are tighter optimize/execute feedback loops, workload-level optimization, and composable optimizers, not learned QO by name — [arXiv 2510.20082](https://arxiv.org/abs/2510.20082)
- **LOTUS / semantic operators** (Patel et al., Stanford/Berkeley; PVLDB 18):
  - It offers a DataFrame API with semantic map, filter, extract, aggregate, group-by, rank, join and search operators.
  - It provides statistical accuracy guarantees.
  - It claims up to 400x speedups over other methods.
  - It is open source under Apache 2.0.

  — [VLDB paper](https://www.vldb.org/pvldb/vol18/p4171-patel.pdf); [arXiv 2407.11418](https://arxiv.org/html/2407.11418v3); [BigDataWire](https://bigdatawire.com/2025/02/03/lotus-promises-fast-semantic-processing-on-llms)
- **Snowflake Cortex AISQL**:
  - The vendor paper states AISQL is deployed in production.
  - It reports AI-aware query optimization at 2–8x, adaptive model cascades at 2–6x while keeping 90–95% of oracle quality, and semantic join rewriting from quadratic to linear at 15–70x.
  - The challenge it addresses: the cost and selectivity of LLM predicates are unknown at compile time.

  These are vendor-measured numbers — search summary of the AISQL paper (search results did not give a direct URL; see the [LOTUS VLDB entry](https://vldb.org/pvldb/volumes/18/paper/Semantic%20Operators%20and%20Their%20Optimization%3A%20%20Towards%20AI-Based%20Data%20Analytics%20with%20Accuracy%20Guarantees) for the related research line)

### Inferences
- **Adoption status:**
  - Neo, Balsa, LOGER, Kepler: research.
  - Bao-style hint steering: mature at one hyperscaler (SCOPE, internal).
  - Learned cardinality estimation: research, with partial vendor experiments [background, not re-verified].
  - Semantic operators: mature-ish in Snowflake (AISQL), with analogues in Databricks ai_query and BigQuery AI functions [background, not re-verified].
  - LOTUS, Palimpzest, DocETL: research/OSS.
- **Why learned QO isn't adopted:**
  1. Regressions: vendors need "never worse than today", and full learned planners give no such guarantee. That is why steering and hinting, which fall back to the default plan, won.
  2. Training needs representative workloads, and the cold start is per customer.
  3. Results are fragile to train/test splits (Lehmann et al.).
  4. Debuggability and explainability.
  5. Classic cost models are "good enough" when combined with adaptive execution.
- **Why semantic operators transferred quickly:** they add new capability (LLM over text) rather than replacing a mature component, and vendors have a direct revenue motive (LLM token resale). The research ideas still mostly unexploited are optimizer-level: accuracy-guaranteed cascades, cost-based reordering of LLM predicates, and semantic join rewriting. Snowflake publishes some of these. Others lag [inference].

### Gaps
- The AISQL paper URL and arXiv ID were not retrieved directly.
- The status of Databricks AI Functions and BigQuery AI.GENERATE optimizations was not covered.
- No public evidence of Neo, Balsa or LOGER in any product was found. Absence of evidence is not proof.

## 5. Query compilation advances (Umbra adaptive compilation, Tidy Tuples) and unified OLTP/OLAP (HTAP)

### Takeaway
Little new evidence was gathered this session. Umbra's compilation techniques are being commercialized through CedarDB, a startup, but mainstream engines largely stayed with vectorized interpretation (DuckDB, Velox, Photon). HTAP research has not displaced separate OLTP and OLAP systems.

### Cited Findings
- Umbra is documented as a research system from TUM, with WCOJ integrated for sub-plans — [DBDB.io Umbra](https://dbdb.io/db/umbra)

### Inferences
- [background, not re-verified]:
  - Umbra adaptive compilation (Kersten, Leis, Neumann, VLDB 2021 / ICDE 2018 "adaptive execution") and Tidy Tuples / Flying Start (Kersten et al., VLDB 2021) address compile latency with a low-latency direct-to-machine-code backend.
  - CedarDB (spun out of TUM, around 2024) is the commercialization path.
  - Mainstream engines chose vectorization because it is easier to debug, profile and maintain, which limits adoption of data-centric compilation.
  - In HTAP, SAP HANA, SingleStore, TiDB (TiFlash) and Oracle Dual Format are production, but "true" single-copy HTAP research (HyPer-style) remains largely unadopted. The industry trend is toward zero-ETL replication between separate OLTP and OLAP engines instead.

### Gaps
- No sources were fetched on CedarDB's production status, customers, or whether Umbra's compiler features ship in it.
- No 2021–2026 HTAP adoption sources were fetched. The report writer should treat this section as thin.

## 6. Versioned, branchable, time-travel and bitemporal DBs ("git for data", Prolly trees, verifiable DBs)

### Takeaway
Copy-on-write branching went mainstream through Neon. Databricks bought Neon for about $1B in May 2025, and it became Lakebase, GA on AWS in February 2026 and Azure in March 2026. Neon branching, though, is storage-level snapshot branching, not row-level merge. True git-style diff and merge of data (Dolt/Prolly trees, TerminusDB) and full bitemporal SQL (XTDB v2 stable since June 2025) remain startup and niche.

### Cited Findings
- Databricks announced the Neon acquisition on 14 May 2025, reported at about $1B (price not disclosed by the companies).
  - Databricks cited that over 80% of Neon databases were provisioned by AI agents.
  - Branching ("branch a database just like you branch code") is a key Neon feature.

  — [Yahoo Finance/TechCrunch](https://finance.yahoo.com/news/databricks-buy-open-source-database-120751104.html); [remio.ai](https://www.remio.ai/post/databricks-google-database-rivalry-sharpens-after-neon-acquisition)
- Neon technology became Databricks Lakebase: GA on AWS in early February 2026, and on Azure on 3 March 2026 — [Refonte Learning](https://www.refontelearning.com/blog/databricks-neon-acquisition-lakebase-serverless-postgres) (secondary source)
- **XTDB v2**:
  - The first stable release came in June 2025, with a stable SQL API and storage format. Design partners already run it in production.
  - All tables are bitemporal (system time plus valid time) without triggers or history tables.
  - It follows SQL:2011 bitemporal semantics, offers a Postgres wire-compatible (but not fully compatible) interface, uses Arrow-format columnar storage on object storage, and separates storage from compute.

  — [XTDB launch post](https://www.xtdb.com/blog/launching-xtdb-v2); [XTDB v2 hub](https://www.xtdb.com/v2)
- No named XTDB production customers beyond "design partners" were found — [XTDB launch post](https://www.xtdb.com/blog/launching-xtdb-v2)

### Inferences
- **Adoption status:**
  - Storage-level branching and time travel: mature. Neon/Lakebase, Snowflake zero-copy clone plus Time Travel, Delta/Iceberg snapshots [background, not re-verified for Snowflake/Delta].
  - Bitemporal SQL: startup (XTDB). Datomic is mature in a niche; it became free in 2023 [background, not re-verified].
  - Git-style merge (Dolt, Prolly trees from Noms): startup.
  - Verifiable/Merkle DBs (e.g., Amazon QLDB, LedgerDB): AWS announced the QLDB end-of-life for 2025 [background, not re-verified]. That is negative adoption evidence for ledger DBs.
- **Why row-level merge hasn't spread:**
  1. Merge semantics for relational data (constraint violations, semantic conflicts) have no general solution.
  2. Prolly/Merkle structures cost write amplification and scan speed compared with B-trees and columnar formats.
  3. Most demand (dev/test environments, AI-agent sandboxes) is met by cheap copy-on-write snapshot branches without merge.
  4. The industry used SQL:2011 temporal tables only partially, and bitemporality adds query complexity that most apps avoid.
- The "80% of DBs created by agents" data point suggests agent workloads are the driver for cheap branching. Merge and diff remain unexploited.

### Gaps
- Dolt and DoltgreSQL production status, TerminusDB status, and recent Prolly-tree or verifiable-DB papers (e.g., 2021–2025 VLDB work on verifiable databases, GlassDB) were not retrieved this session.

## 7. Novel data models: GQL / SQL-PGQ (2023), relational–graph unification, array DBs, semantic layer as DB

### Takeaway
SQL/PGQ (SQL:2023) is slow to reach open-source mainstream engines.
- **PostgreSQL:** it was committed for PG19 on 16 March 2026, then reverted from master on 7 September 2026, per a pgsql-hackers message.
- **DuckDB:** support exists as the DuckPGQ community extension, from CWI, demonstrated at VLDB 2023, rather than in core.
- **Kùzu:** the leading embeddable OSS graph engine was archived (see section 2).

Relational–graph unification is still largely research or extension-level in OSS.

### Cited Findings
- A depesz post reports that Peter Eisentraut committed SQL/PGQ (GRAPH_TABLE, CREATE/ALTER/DROP PROPERTY GRAPH) on 16 March 2026, for PostgreSQL 19 — [depesz](https://www.depesz.com/?p=4467)
- A pgsql-hackers message from shihao zhong (10 Sept 2026) states: "SQL/PGQ was reverted from master in b1f106c80cb on 2026-09-07, so GRAPH_TABLE is no longer in the tree". Follow-on commitfest entries (e.g., #7172, multi-pattern matching) went to "Waiting on Author". This rests on that message, and the revert commit itself was not checked — [pgsql-hackers message](https://www.postgresql.org/message-id/CAGRkXqSA0Aos=J0Q==2exRst7bHmsFxOgNR_C7rgzAxH2pLCGw@mail.gmail.com); [CF #7172](https://commitfest.postgresql.org/patch/7172/)
- **DuckPGQ**:
  - Published in PVLDB 16(12): 4034–4037, 2023 (VLDB demo, not CIDR).
  - It implements SQL/PGQ syntax as a DuckDB community extension.
  - It planned factorized and WCOJ algorithms for performance.

  — [DuckDB science page](https://duckdb.org/science/duckpgq); [CWI PDF](https://ir.cwi.nl/pub/33317/33317.pdf)

### Inferences
- **Adoption status:**
  - SQL/PGQ: mature in Oracle 23ai [background, not re-verified]; extension in DuckDB; reverted in PostgreSQL.
  - GQL (ISO 39075:2024): vendor adoption in Neo4j/others is partial [background, not re-verified].
  - Array DBs (SciDB, TileDB, rasdaman): niche/startup [background, not re-verified].
  - Semantic layer as DB (e.g., Snowflake semantic views, which RelationalAI is adopting — [Verdantix](https://atlas.verdantix.com/relationalai/relationalai)): emerging vendor feature.
- **Why SQL/PGQ hasn't landed:**
  1. The specification is large: path quantifiers, path modes, undirected edges.
  2. Efficient execution needs non-relational operators (shortest path, CSR-style adjacency indexes, WCOJ for cyclic patterns), and a naive rewrite to joins and recursive CTEs performs poorly.
  3. The PostgreSQL revert indicates code-quality or planner-integration concerns. The exact reason was not verified.
  4. Demand is lukewarm because most graph-ish queries in SQL shops are shallow and served by joins.

### Gaps
- The reason for the PostgreSQL SQL/PGQ revert was not found.
- Oracle 23ai, SQL Server and other vendor SQL/PGQ support, GQL adoption, array-DB status, and semantic-layer products were not verified with sources this session.
