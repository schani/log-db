# Production Landscape of Cloud-Native Database Architectures (as of Oct 2026)

Source-provenance legend: items marked **[fetched]** were read or summarized from the page during this session. Items marked **[known]** are canonical URLs for well-known papers and announcements, cited from prior knowledge and not re-fetched this session. The report writer should treat [known] details as reliable but unverified this session.

## Q1. Disaggregated compute/storage OLTP: what exactly is pushed to storage?

### Takeaway
"Log is the database" (ship only WAL/redo, with storage materializing pages and serving GetPage@LSN) is fully mainstream. Aurora, Socrates/Hyperscale, Taurus, PolarDB, Neon, AlloyDB and the new Azure HorizonDB all use it. The 2023-2026 frontier is about what else moves below the compute layer:
- predicate/near-data processing (Taurus NDP, PolarDB computational storage)
- shared or disaggregated memory (PolarDB Serverless RDMA, then PolarCXLMem on CXL, which won the SIGMOD 2025 best industrial paper; GaussDB-MP memory nodes)
- columnar replicas built from redo (PolarDB IMCI)
- multi-primary over shared storage. This has mostly failed or been reverted; Aurora Multi-Master was deprecated in 2023.

### Cited Findings
**Amazon Aurora** (SIGMOD 2017, SIGMOD 2018)
- Only redo records cross the network. Storage nodes materialize pages from the log, do MVCC cleanup, checkpoint to S3, validate CRCs, and gossip to fill log gaps.
- 6-way quorum across 3 AZs (write 4/6, read 3/6). A single writer means reads usually need no quorum. Consistency points are tracked via LSN/VCL/VDL/PGCL.
- Read replicas share storage with about 20 ms lag, and recovery runs in parallel across storage nodes.
- Source: [transactional.blog: Notes on Disaggregated OLTP](https://transactional.blog/notes-on/disaggregated-oltp) [fetched]. Paper: [Aurora SIGMOD'17](https://www.amazon.science/publications/amazon-aurora-design-considerations-for-high-throughput-cloud-native-relational-databases) [known].

**Aurora variants**
- Aurora Serverless v2 is described in a VLDB 2024 paper: live migration plus fleet-level placement.
- Aurora Multi-Master resolved conflicts optimistically at the storage layer. It suffered slow commits and high abort rates, was deprecated in 2023, and has no paper.
- Aurora Limitless (2024, closed source) is sharded PostgreSQL. A paper appears in SIGMOD Companion 2026.
- Source: [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched]; [Pavlo 2025 review](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**Microsoft Socrates / Azure SQL Hyperscale** (SIGMOD 2019)
- Separates durability (the log) from availability (page servers).
- The log goes to a Landing Zone (Premium Storage) and to the XLOG service. XLOG disseminates to page servers and archives to XStore (blob).
- Page servers serve GetPage@LSN, checkpoint to XStore, and handle backup/restore by snapshot.
- Compute keeps a local SSD cache (RBPEX).
- Follow-up papers: ICDE 2025 (RBPEX, XLOG) and SIGMOD Companion 2026 (Hyperscale storage tier).
- Source: [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched].

**Huawei Taurus / GaussDB** (SIGMOD 2020)
- Log Stores hold the WAL in 3-replica PLogs. Page Stores (10 GB slices) apply redo, serve any-LSN reads, and gossip.
- Replication is reconfiguration-based rather than quorum-based. Redo runs on storage; undo runs on the frontend.
- Taurus NDP (ICDE 2022) pushes filters, projections and aggregations to Page Stores, with LLVM-JIT predicates returning "NDP pages".
- Taurus MM (VLDB 2023) adds multi-master via hybrid scalar/vector clocks and a global lock manager.
- GaussDB-MP (VLDB 2024) separates three tiers: compute, memory and storage. A stateless memory tier holds the page-owner directory, global locks and warm cache. It includes an MLP query router.
- Source: [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched].

**Alibaba PolarDB family**
- PolarFS (VLDB 2018) is a distributed filesystem, not a page server: ParallelRaft, Optane WAL, SPDK, RDMA.
- Computational storage (FAST 2020) pushes scans to FPGA SmartSSDs.
- PolarDB Serverless (SIGMOD 2021) adds an RDMA remote-memory buffer pool, GetPage@LSN, and page-chunk leaders that materialize pages from redo.
- PolarDB-X (ICDE 2022) adds HLC snapshot isolation, 2PC, and Paxos cross-DC redo.
- IMCI (SIGMOD/PACMMOD 2023) builds in-memory column indexes on read-only nodes from redo.
- SCC (VLDB 2023) gives strongly consistent RO reads via global, table and page LSNs.
- PolarDB-MP (SIGMOD Companion 2024) is multi-primary via an RDMA "transaction/buffer/lock fusion" server.
- Source: [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched].

**PolarDB-CXL ("PolarCXLMem")**
- Paper: "Unlocking the Potential of CXL for Disaggregated Memory in Cloud-Native Databases", SIGMOD 2025 Best Industrial Paper.
- Builds a CXL-switch memory pool for the buffer pool, with up to 2.1x the throughput of RDMA-based pooling.
- PolarRecv uses the persistence of CXL memory for fast crash recovery. A multi-node coherence protocol provides cross-node sharing.
- Single-node memory extends to about 8 TB. The feature is in "gray release".
- Source: [Alibaba Cloud blog](https://www.alibabacloud.com/blog/polardb-brings-alibaba-cloud-another-sigmod-best-paper-award_602713); [Aliyun help: CXL-based disaggregated architecture](https://help.aliyun.com/zh/polardb/polardb-for-mysql/user-guide/cxl-based-disaggregated-architecture-for-polardb) [fetched via search summary].

**Neon**
- Postgres compute is stateless. WAL goes to "safekeepers" (a Paxos-replicated WAL service). Pageservers ingest WAL and serve GetPage@LSN, storing layer files in S3.
- Copy-on-write timelines give instant branching and point-in-time reads, and compute can scale to zero.
- Source: [Neon architecture docs](https://neon.com/docs/introduction/architecture-overview) [known].
- Databricks acquired Neon for about $1B in 2025, and it is now the basis of Databricks Lakebase — [Pavlo 2025 review](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**Google AlloyDB** (2022)
- PostgreSQL with a disaggregated log/storage service built on Colossus. A storage-layer "log processing service" materializes blocks.
- Adds an ultra-fast cache tier and an adaptive in-memory columnar engine.
- Source: [dbdb.io AlloyDB](https://dbdb.io/db/alloydb) (surfaced in search, not fetched); [Google Cloud AlloyDB intro blog](https://cloud.google.com/blog/products/databases/alloydb-for-postgresql-intelligent-scalable-storage) [known].

**New disaggregated Postgres offerings**
- Microsoft announced Azure HorizonDB in 2025: shared, auto-scaling storage up to 128 TB, independent of compute — [Pavlo 2025 review](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched]; the 128 TB figure comes from a [devnewsletter State of Databases 2026](https://devnewsletter.com/p/state-of-databases-2026/) search snippet.
- Earlier cloud Postgres services: Aurora PG (2017), AlloyDB (2022), ServiceNow RaptorDB (2024), IBM Cloud PG (2018), Oracle PG (2023) — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**Ongoing research and failures**
- Research on tail latency in storage-disaggregated DBs continues, e.g. [Purdue SIGMOD'26 "RaaS"](https://cs.purdue.edu/homes/csjgwang/pubs/SIGMOD26_RaaS.pdf) (search result, not fetched).
- MariaDB Xpand did something similar to Taurus MM without publishing it, and was shut down — [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched].

### Inferences
These pushdown layers are heavily exploited:
- (a) redo-only shipping
- (b) page materialization in storage
- (c) storage-side quorum/replication without consensus on the commit path (Aurora)
- (d) PITR, branching and snapshots in storage (Neon, Hyperscale)
- (e) filter/aggregate pushdown to storage (Taurus NDP, PolarDB FPGA)
- (f) columnar replicas from redo (IMCI, AlloyDB columnar)
- (g) remote or shared memory over RDMA and CXL (PolarDB)

Single-writer is the norm. Multi-primary over shared storage exists only in Chinese hyperscalers (PolarDB-MP, Taurus MM, GaussDB-MP). The one Western attempt, Aurora MM, was reverted.

Almost every system pushes redo application to storage. Pushing transaction logic (conflict detection, constraint checks, index maintenance) to storage is rare. The exceptions are Aurora MM, which failed, and DSQL's adjudicators, which are a separate tier rather than storage.

### Gaps
- No fetched primary source on AlloyDB internals or a paper; Google has published no SIGMOD/VLDB paper as far as found.
- The Neon section of transactional.blog was not reached in the fetch, so the Neon details come from known docs.
- HorizonDB architecture details (page-server design? Socrates-derived?) were not verified.

## Q2. Object-storage-native systems and S3 coordination primitives; any OLTP purely on object storage?

### Takeaway
Object storage as primary storage is fully exploited for:
- OLAP: Snowflake, lakehouse table formats, DuckLake/MotherDuck
- streaming logs: WarpStream, and Confluent Freight
- search/vector: turbopuffer, LanceDB
- LSM KV: SlateDB

Since S3 conditional writes arrived (put-if-absent in Aug 2024, If-Match CAS in Nov 2024), systems have dropped ZooKeeper/etcd in favor of single-key CAS on a manifest or pointer. OLTP that sits *directly* on object storage without an intermediate low-latency log tier essentially does not exist in production. Every OLTP-on-object-storage system (Neon/Lakebase, TiDB X, Aurora, Hyperscale) still puts a fast replicated WAL tier in front of S3.

### Cited Findings
**S3 conditional writes as a coordination primitive**
- If-None-Match: * gives put-if-absent. If-Match on an ETag gives true CAS, which enables OCC, leader election and metadata catalogs without a consensus cluster.
- Conditional requests carry no extra charge. Sources disagree on the race outcome: one says 409 ConditionalRequestConflict, another says 412 for the loser.
- Source: [mohakchugh blog](https://mohakchugh.is-a.dev/blog/s3-conditional-writes-distributed-coordination); [braindetox 2026](https://braindetox.kr/en/posts/s3_does_not_replace_consensus_conditional_writes_2026.html); [Tigris blog](https://tigrisdata.com/blog/s3-conditional-writes) (search summaries).
- AWS announcements: [S3 conditional writes, Aug 2024](https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes/) [known]; [S3 If-Match conditional writes, Nov 2024](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-functionality-conditional-writes/) [known].
- Apache Ozone added S3 conditional requests in July 2026 — [Ozone blog](https://ozone.apache.org/blog/2026/07/08/ozone-s3-conditional-request) (search result).

**SlateDB**
- An embedded LSM KV store on object storage. WAL SSTs, compacted SSTs and manifests all live in S3.
- Writers fence by creating the next manifest or WAL object with If-None-Match.
- Source: [mohakchugh blog](https://mohakchugh.is-a.dev/blog/s3-conditional-writes-distributed-coordination) (search summary); [slatedb.io](https://slatedb.io) [known].

**WarpStream**
- Kafka-compatible with diskless, stateless agents that write directly to S3, plus a separate metadata service.
- Confluent acquired it in Sep 2024 — [Confluent blog](https://www.confluent.io/blog/confluent-acquires-warpstream/) [known].
- Confluent itself was reported near an approximately $11B acquisition by IBM in Dec 2025 — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**turbopuffer**
- Search/vector engine whose writes reduce to appending WAL files to S3 with group commit, with NVMe/RAM caches in front.
- Funding undisclosed in 2025 — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched]. Architecture: [turbopuffer architecture docs](https://turbopuffer.com/docs/architecture) [known].

**Snowflake** (SIGMOD 2016)
- Immutable micro-partitions on S3, with a FoundationDB-backed metadata/catalog service and ephemeral virtual warehouses.
- Source: [Snowflake Elastic Data Warehouse, SIGMOD'16](https://dl.acm.org/doi/10.1145/2882903.2903741) [known].

**Lakehouse table formats (Delta Lake, Iceberg, Hudi)**
- Commit protocols are optimistic, swapping a log or metadata pointer.
- Delta Lake (VLDB 2020) — [paper](https://www.vldb.org/pvldb/vol13/p3411-armbrust.pdf) [known].

**DuckLake**
- Puts table-format metadata (schema, snapshots, file lists, stats) as rows in a SQL DB (DuckDB, Postgres, SQLite) instead of JSON/Avro files. It is MIT-licensed.
- From DuckLake 0.4, small inserts (≤10 rows by default) are "inlined" into the catalog DB rather than written as Parquet.
- MotherDuck offers managed DuckLakes (preview).
- Source: [MotherDuck DuckLake glossary/docs](https://motherduck.com/glossary/ducklake.md); [MotherDuck managed DuckLake preview](https://motherduck.com/blog/announcing-ducklake-support-motherduck-preview/) (search summaries). The original launch was May 2025: [duckdb.org DuckLake announcement](https://duckdb.org/2025/05/27/ducklake.html) [known].

**File-format proliferation**
- 2024: Meta Nimble, Lance, TsFile.
- 2025: FastLanes, F3 (CMU/Tsinghua), Vortex (donated to the Linux Foundation), AnyBlox (VLDB 2025 best paper), Microsoft Amudai (apparently discontinued end of 2025).
- 94% of Parquet files in the wild use only v1 features.
- LanceDB raised a $30M Series A.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**TiDB X** (announced Oct 8, 2025)
- Moves TiDB from shared-nothing to shared storage on object storage. Raft is retained; local state is a cache over durable object storage.
- Compaction and other background work is isolated from OLTP, with claimed up to 10x faster scaling.
- GA in TiDB Cloud Starter/Essential/Premium.
- Source: [TiDB X architecture docs](https://docs.pingcap.com/tidbcloud/tidb-x-architecture/); [PingCAP blog](https://www.pingcap.com/blog/introducing-tidb-x-a-new-foundation-distributed-sql-ai-era/) (search summary).

**Databricks Lakebase and LTAP**
- Lakebase is "serverless Postgres on object storage", Neon-derived.
- LTAP ("Lake Transactional/Analytical Processing") was announced June 16, 2026 and is "coming soon as part of Lakebase". It claims OLTP and OLAP on one copy of data in Delta/Iceberg on object storage, with no ETL. The write path is not disclosed.
- Vendor claims: thousands of customers, 12M database launches/day, plus branching, snapshots and DR.
- Source: [Databricks LTAP press release](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-ltap-first-lake-transactionalanalytical) [fetched]; [Databricks "What is a Lakebase"](https://www.databricks.com/blog/what-is-a-lakebase) (search result).

**Research view on OLTP directly on object storage**
- A VLDB 2026 paper (Terark-DS) notes object storage is "impractical for OLTP due to high latency and per-append cost".
- Source: [VLDB 2026 program](https://vldb.org/2026/program.html) (search summary).

**S3 Express One Zone** (Nov 2023)
- Single-digit-ms single-AZ object storage. WarpStream and others offer it as a lower-latency write tier.
- Source: [AWS announcement](https://aws.amazon.com/about-aws/whats-new/2023/11/amazon-s3-express-one-zone-storage-class/) [known].

### Inferences
Two layers are well trodden: "S3 + manifest CAS" for single-writer or append-mostly systems, and "fast WAL tier + S3 for pages" for OLTP.

The open ground is genuine multi-writer, high-contention OLTP whose *commit path* is object-storage-native, e.g. built on conditional writes or S3 Express append. Today the single-key CAS limit pushes everyone to one manifest pointer, which serializes all commits.

LTAP shows the industry converging on "OLTP rows to open lake formats". Databricks has not disclosed how row-level OLTP writes become Delta/Iceberg files, so the mechanism (CDC-to-lake, or a pageserver emitting Parquet?) is unknown.

### Gaps
- No production OLTP found that commits directly via S3 conditional writes without an intermediate log service.
- Turbopuffer, LanceDB and Iceberg architecture pages were not fetched.
- The exact S3 conflict status code is disputed between sources.
- S3 Express append support (2024) and its use by databases were not verified.

## Q3. Distributed SQL / NewSQL: concurrency and replication choices

### Takeaway
Production distributed SQL clusters into these camps:
- pessimistic 2PL/MVCC + Paxos/Raft per shard + clock-bounded timestamps (Spanner TrueTime; CockroachDB HLC; YugabyteDB HLC)
- Percolator-style OCC/pessimistic with a central timestamp oracle (TiDB)
- a centralized sequencer/resolver with OCC (FoundationDB)
- the newer OCC with precise clocks and a separate log/adjudicator tier (Aurora DSQL, GA May 2025, paper July 2026)

Deterministic/Calvin-style execution lost its flagship production system when Fauna shut down in May 2025.

### Cited Findings
**Aurora DSQL** (preview Dec 2024, GA May 2025)
- Paper: arXiv 2607.13276 (Jul 16 2026; Brooker, Bowes, Hershey, van der Merwe, Morle, Strydom).
- Components:
  - Stateless PostgreSQL-compatible Query Processors in Firecracker microVMs, which buffer writes locally until commit.
  - Adjudicators sharded by key range, doing conflict detection and ordering.
  - A durable Journal of committed post-images; a commit is durable at the Journal.
  - Crossbars merge-sort journal streams to MVCC storage nodes, which do not handle durability.
- Isolation and commit: OCC with strong snapshot isolation. Coordination happens once per transaction, at commit, rather than per statement.
- Clocks and multi-region: microsecond-precision AWS time sync. Multi-region uses a 2-of-3 regional journal quorum with erasure coding.
- Numbers: PK lookup about 1.4–2 ms; East/West US multi-region commit about 30 ms p99; claimed "seven nines" availability; limits of 3,000 rows or 10 MiB per transaction.
- Source: [arXiv/alphaxiv 2607.13276](https://www.alphaxiv.org/abs/2607.13276) [fetched]; [Marc Brooker, "DSQL Vignette: Transactions and Durability" (Dec 2024)](https://brooker.co.za/blog/2024/12/05/inside-dsql-writes/) (search result); [DeNA engineering analysis series 2025](https://engineering.dena.com/blog/2025/08/aurora-dsql_02_spanner_en/) (search result). GA date: [AWS What's New May 2025](https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-aurora-dsql-generally-available/) [known].

**Spanner**
- Paxos per split, 2PL plus wound-wait, and TrueTime commit-wait for external consistency (OSDI 2012).
- Later additions: Spanner SQL (SIGMOD 2017) and Spanner "columnar"/Data Boost.
- Source: [Spanner OSDI'12](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) [known].

**CockroachDB** (SIGMOD 2020)
- Raft per range, MVCC with HLC-based serializable isolation, parallel commits, and a write-intent/txn-record protocol.
- Source: [CockroachDB SIGMOD'20](https://dl.acm.org/doi/10.1145/3318464.3386134) [known].

**TiDB** (VLDB 2020)
- Raft-based HTAP: TiKV is row-oriented, and TiFlash is a columnar Raft learner.
- Percolator 2PC with a PD timestamp oracle.
- Shifted to the object-storage-backed TiDB X in 2025 (see Q2).
- Source: [TiDB VLDB'20](https://www.vldb.org/pvldb/vol13/p3072-huang.pdf) [known].

**YugabyteDB**
- A hard fork of the Postgres query layer (PG15-compatible) over DocDB (a Raft-replicated RocksDB), with HLC.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched], for the fork and PG15 compatibility.

**FoundationDB** (SIGMOD 2021)
- Unbundled design: a sequencer, resolvers doing OCC conflict checks, log servers and storage servers.
- Strict serializability with a 5-second transaction limit. Deterministic simulation testing.
- Snowflake and Apple use it as a metadata store.
- Source: [FoundationDB SIGMOD'21](https://www.foundationdb.org/files/fdb-paper.pdf) [known].

**FaunaDB** (Calvin-derived)
- Fauna shut down the FaunaDB service in May 2025.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched]. Calvin paper: [SIGMOD 2012](http://cs.yale.edu/homes/thomson/publications/calvin-sigmod12.pdf) [known].

**Sharded Postgres middleware renaissance (2025)**
- Supabase Multigres is led by Sugu (Vitess co-creator), who was hired in June 2025.
- PlanetScale Neki is "Vitess for Postgres". PlanetScale's Postgres DBaaS launched March 2025.
- PgDog is open source.
- Earlier attempts: Citus (Microsoft, 2019), Postgres-XC/XL.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**RegattaDB** (GA July 2026)
- A distributed SQL DB covering OLTP, OLAP and vector workloads. It is Postgres drop-in and claims tens of thousands of nodes.
- The storage architecture is not confirmed.
- Source: [Blocks & Files, Jul 15 2026](https://www.blocksandfiles.com/data-management/2026/07/15/regatta-launches-its-unified-oltp-olap-and-vector-database/5271769) (search summary).

### Inferences
Well exploited:
- consensus per shard plus MVCC
- HLC/TrueTime timestamps
- a centralized sequencer (FDB)
- OCC with disaggregated adjudication (DSQL)

The disaggregated "unbundled transaction tier" idea (FDB resolvers, then DSQL adjudicators) is now proven at hyperscale.

Deterministic/Calvin execution has no surviving major production DBaaS after Fauna. That is a signal of commercial failure, not necessarily of technical exhaustion.

DSQL's OCC with hard per-transaction limits leaves high-contention and long transactions under-served in serverless distributed SQL.

### Gaps
- No fetched sources for CockroachDB, YugabyteDB or Spanner 2025-2026 architectural changes.
- Whether DSQL's paper was accepted at a venue is unconfirmed; the page only showed an arXiv preprint.

## Q4. Serverless databases: scale-to-zero and edge/embedded replication

### Takeaway
Scale-to-zero is well exploited in two ways:
- Stateless compute over disaggregated storage: Neon, Aurora Serverless v2 (min 0 ACU added 2024), Aurora DSQL, TiDB Starter.
- Tiny per-tenant SQLite databases: Turso/libSQL, Cloudflare D1 and Durable Objects SQLite storage.

Agent-driven database creation is now the dominant use case cited by vendors. Postgres-as-a-service is the hottest M&A area.

### Cited Findings
**Neon and Lakebase**
- Neon reported in July 2025 that agents create 80% of its databases. It was acquired by Databricks for about $1B — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].
- Lakebase claims 12M database launches/day — [Databricks LTAP PR](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-ltap-first-lake-transactionalanalytical) [fetched].

**Aurora Serverless v2**
- Scales in place with live migration across hosts (VLDB 2024 paper) — [transactional.blog](https://transactional.blog/notes-on/disaggregated-oltp) [fetched].
- Scale-to-0 ACU added Nov 2024 — [AWS What's New](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-aurora-serverless-v2-scaling-zero-capacity/) [known].

**Aurora DSQL**
- Firecracker microVM query processors, scaling "from zero to millions of transactions per second" — [DSQL paper](https://www.alphaxiv.org/abs/2607.13276) [fetched].

**Postgres DBaaS market**
- Snowflake bought Crunchy Data for $250M; Snowflake Postgres went to public preview in Dec 2025.
- Supabase raised a $200M Series D and a $100M Series E in 2025.
- PlanetScale Postgres launched March 2025.
- Xata moved off Aurora to its own infrastructure. Tembo dropped hosted Postgres.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**Turso and libSQL**
- libSQL (a C SQLite fork) is the production layer. The Turso Database rewrite of SQLite in Rust (formerly "Limbo") is in beta.
- It adds MVCC `BEGIN CONCURRENT`, with row-level conflict detection at commit. A concurrent-writes early preview on Turso Cloud is dated Aug 3, 2026 in one summary.
- Source: [Turso blog: concurrent writes](https://turso.tech/blog/concurrent-writes-on-turso-cloud); [Turso: next evolution of SQLite](https://turso.tech/blog/turso-the-next-evolution-of-sqlite) (search summaries).
- A Turso blog URL titled "a-new-modern-version-of-postgres-in-rust" also surfaced but was not verified: [link](https://turso.tech/blog/a-new-modern-version-of-postgres-in-rust).

**Cloudflare D1 and Durable Objects**
- D1 is SQLite-based, with per-database size limits and read replication (2025).
- Durable Objects provide single-threaded actors with co-located SQLite storage (2024). Durability comes from shipping WAL to followers and object storage via the "Storage Relay Service".
- Source: [Cloudflare blog "Zero-latency SQLite storage in every Durable Object" (Sep 2024)](https://blog.cloudflare.com/sqlite-in-durable-objects/) [known].

**Cloudflare data stack**
- Cloudflare acquired Arroyo (stream processing) on Apr 10, 2025 to power Pipelines, which ingests to R2/Iceberg.
- Source: [Cloudflare blog](https://blog.cloudflare.com/cloudflare-acquires-arroyo-pipelines-streaming-ingestion-beta) (search summary).

**Other serverless and edge**
- Vercel acquired Gel (EdgeDB) in Dec 2025, and Convex raised a $24M Series B — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].
- PlanetScale (Vitess) deprecated its free Hobby tier in 2024 — [PlanetScale blog](https://planetscale.com/blog/planetscale-forever) [known].

### Inferences
"Database per tenant/agent", branching and scale-to-zero are now commodity features: Neon, Lakebase, TiDB ("millions of agent branches" in its 2026 marketing), Turso, D1.

Edge replication is almost entirely single-primary SQLite with read replicas or actor-pinned writes. Multi-writer edge OLTP with strong guarantees is not in production.

Caution: scale-to-zero for *distributed* write paths exists only in DSQL, and only under strict per-transaction limits.

### Gaps
- Cloudflare D1/DO internals were not fetched this session; the search returned nothing on them.
- Supabase's own storage architecture work (e.g. OrioleDB) and its 2026 status were not verified.
- Aurora Serverless v2 scale-to-zero details were not re-fetched.

## Q5. Streaming / incremental view maintenance in production

### Takeaway
Production incremental-view maintenance (IVM) and streaming SQL is a crowded but small market:
- Materialize: Differential/Timely Dataflow; self-managed with a license key from v26, Nov 2025.
- RisingWave: state in S3 via the Hummock LSM, 1 s checkpoints, Apache 2.0.
- Feldera: DBSP, VLDB 2023 best paper.
- Arroyo: Rust, acquired by Cloudflare in Apr 2025.
- ksqlDB: Confluent, legacy since the Flink pivot.

The common architecture is "object storage holds state + periodic checkpoints". IVM *inside* OLTP databases is still largely absent from production.

### Cited Findings
**RisingWave**
- Decouples compute and storage, with state on S3 (Hummock), a default 1-second checkpoint interval, native CDC and Iceberg sinks, and an Apache 2.0 license.
- Source: [RisingWave vs Materialize docs](https://docs.risingwave.com/reference/risingwave-materialize-comparison); [RisingWave blog 2026](https://risingwave.com/blog/risingwave-vs-materialize-comparison/) (vendor-authored; search summary).

**Materialize**
- Self-Managed reached early access in 2025. From v26.0.0 (Nov 18, 2025), a license key is required.
- RisingWave claims the free tier is capped at 24 GiB memory / 48 GiB disk; this is unverified.
- Source: [Materialize changelog v26](https://materialize.com/changelog/2025-11-18-v26-release/); [Self-managed EA](https://materialize.com/blog/self-managed-materialize-early-access/) (search summaries).
- Underlying papers: Differential Dataflow (CIDR 2013) and Naiad (SOSP 2013) — [Naiad](https://dl.acm.org/doi/10.1145/2517349.2522738) [known].

**Feldera**
- Built on DBSP: incremental computation for any SQL via Z-sets. VLDB 2023 best paper (Budiu et al.).
- Source: [DBSP paper](https://www.vldb.org/pvldb/vol16/p1601-budiu.pdf) [known].

**Arroyo**
- Acquired by Cloudflare on Apr 10, 2025. It powers Cloudflare Pipelines and remains open source.
- Source: [Cloudflare blog](https://blog.cloudflare.com/cloudflare-acquires-arroyo-pipelines-streaming-ingestion-beta); [Dealroom](https://ai-startups.dealroom.co/news/feed/arroyo-acquired-by-cloudflare-for-sql-processing) (search summaries).

**Other streaming moves**
- Redpanda acquired Oxla, an OLAP engine, in Oct 2025.
- Confluent was reported near a ~$11B IBM acquisition in Dec 2025.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

**Databricks LTAP**
- Claims streaming, transactions and analytics on one copy of lake data (June 2026) — [Databricks PR](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-ltap-first-lake-transactionalanalytical) [fetched].

### Inferences
The IVM *engines* are well exploited, but they are almost always deployed as a separate system fed by CDC/Kafka. "IVM as a first-class feature inside a disaggregated OLTP storage layer" (e.g. pageservers or log consumers maintaining views) has no production example found.

Streaming state-on-S3 (RisingWave Hummock) is the same object-storage-LSM pattern as SlateDB and TiDB X.

### Gaps
- No fetched source on Feldera's 2025-2026 commercial status, or on ksqlDB deprecation.
- RisingWave's Hummock paper/venue was not verified.

## Q6. Notable 2024-2026 launches and shutdowns: direction of travel

### Takeaway
2024-2026 points to six directions:
- Postgres everywhere: M&A of Neon, Crunchy, plus HorizonDB, Lakebase, Snowflake Postgres, and sharded-Postgres middleware.
- Lake-OLTP convergence: Lakebase, LTAP (June 2026), TiDB X on S3.
- Object-storage + CAS coordination as the default for new infrastructure.
- Agent-driven database creation and branching, plus MCP everywhere.
- OCC-based serverless distributed SQL: DSQL.
- Consolidation and shutdowns: Fauna, Hydra, PostgresML, MyScale, Voltron Data.

### Cited Findings
Timeline (launches, acquisitions, shutdowns):
- **Aug & Nov 2024:** S3 conditional writes, then If-Match — [AWS Aug 2024](https://aws.amazon.com/about-aws/whats-new/2024/08/amazon-s3-conditional-writes/) [known].
- **Sep 2024:** Confluent acquires WarpStream — [Confluent](https://www.confluent.io/blog/confluent-acquires-warpstream/) [known].
- **Dec 2024:** Aurora DSQL preview at re:Invent; Aurora Limitless GA (2024) — [Brooker blog](https://brooker.co.za/blog/2024/12/05/inside-dsql-writes/); [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html).
- **Mar 2025:**
  - PlanetScale Postgres launched.
  - MCP adoption accelerated after OpenAI's support; nearly every DBMS vendor shipped an MCP server.
  - Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].
- **Apr 2025:** Cloudflare acquires Arroyo — [Cloudflare](https://blog.cloudflare.com/cloudflare-acquires-arroyo-pipelines-streaming-ingestion-beta).
- **May 2025:**
  - Fauna shut down FaunaDB. MyScaleDB closed. Databricks bought Neon (about $1B).
  - DuckLake launched — [duckdb.org](https://duckdb.org/2025/05/27/ducklake.html) [known].
  - DSQL went GA [known].
  - Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched], except where marked.
- **Jun 2025:** Snowflake buys Crunchy Data ($250M). Supabase hires Sugu for Multigres — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html).
- **2025 (other):**
  - SIGMOD 2025 Best Industrial Paper went to PolarCXLMem — [Alibaba](https://www.alibabacloud.com/blog/polardb-brings-alibaba-cloud-another-sigmod-best-paper-award_602713).
  - Voltron Data (GPU DB, about $110M raised) failed. Hydra and PostgresML died.
  - Amudai was apparently discontinued, and Apache Derby went read-only (Oct 2025).
  - Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html).
- **Oct 2025:** TiDB X on object storage (Oct 8) — [PingCAP](https://www.pingcap.com/blog/introducing-tidb-x-a-new-foundation-distributed-sql-ai-era/). Redpanda acquired Oxla.
- **Nov 2025:**
  - PostgreSQL 18 shipped with async I/O, skip scan and self-join removal.
  - Microsoft HorizonDB was announced (2025).
  - Materialize v26 made the self-managed edition license-keyed.
  - Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html); [Materialize changelog](https://materialize.com/changelog/2025-11-18-v26-release/).
- **Dec 2025:**
  - Snowflake Postgres public preview. IBM–Confluent deal reported (~$11B). Vercel acquires Gel.
  - Funding highlights for 2025: Databricks $4B Series L, ClickHouse $350M Series C, TigerData $110M, LanceDB $30M, SpiralDB $22M.
  - Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html).
- **Jun 16, 2026:** Databricks LTAP (coming soon in Lakebase) — [Databricks PR](https://www.databricks.com/company/newsroom/press-releases/databricks-launches-ltap-first-lake-transactionalanalytical).
- **Jul 2026:**
  - RegattaDB GA — [Blocks & Files](https://www.blocksandfiles.com/data-management/2026/07/15/regatta-launches-its-unified-oltp-olap-and-vector-database/5271769).
  - Aurora DSQL paper on arXiv (Jul 16) — [arXiv 2607.13276](https://www.alphaxiv.org/abs/2607.13276).
  - Apache Ozone added S3 conditional requests — [Ozone](https://ozone.apache.org/blog/2026/07/08/ozone-s3-conditional-request).
- **Aug 2026:** Turso Cloud concurrent writes (MVCC) early preview — [Turso](https://turso.tech/blog/concurrent-writes-on-turso-cloud).

Pavlo's commentary:
- OLAP engines are commoditizing, so differentiation comes down to UX and optimizer quality.
- PostgreSQL is the only major DBMS still relying on the OS page cache.
- MCP servers are mostly thin proxies with little query introspection. Each MCP request targets a single DB, so applications must do cross-source joins.
- Source: [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html) [fetched].

### Inferences
**Taxonomy of WELL-EXPLOITED patterns (production, 2026):**
1. **Log-is-the-database / page-server disaggregation, single writer.** Aurora, Socrates/Hyperscale, Taurus, PolarDB, Neon, AlloyDB, HorizonDB.
2. **Storage-side extras:**
   - near-data processing: Taurus NDP, PolarDB SmartSSD
   - columnar replicas from redo: IMCI, AlloyDB
   - branching/PITR via COW: Neon, Lakebase, TiDB
3. **Memory disaggregation:** RDMA (PolarDB Serverless/MP), CXL (PolarCXLMem), memory tier (GaussDB-MP).
4. **Shared-nothing distributed SQL with consensus per shard:**
   - Spanner, CockroachDB and YugabyteDB with HLC/TrueTime
   - TiDB with Percolator + TSO
   - re-platformed onto object storage (TiDB X)
5. **Unbundled transaction tier with OCC:** FoundationDB (resolvers), Aurora DSQL (adjudicators + journal + precise clocks).
6. **Object-storage-native immutable data + catalog/manifest CAS:** Snowflake, Delta, Iceberg, Hudi, DuckLake, SlateDB, WarpStream, turbopuffer, LanceDB, RisingWave Hummock.
7. **Serverless scale-to-zero:** stateless compute (Neon, Aurora SLv2, DSQL), or per-tenant SQLite (Turso, D1, Durable Objects).
8. **Sharding middleware:** Vitess, Citus, Multigres, Neki, PgDog, Aurora Limitless.
9. **Separate IVM/streaming engines:** Materialize, Feldera, RisingWave, Arroyo, Flink/ksqlDB.

**Thin or empty areas (candidates for "not exploited"):**
- OLTP that commits directly through object-storage CAS at high concurrency.
- Multi-writer serverless OLTP without hard transaction limits.
- Deterministic/Calvin execution after Fauna.
- IVM integrated into the disaggregated OLTP storage layer.
- Multi-primary shared-storage OLTP outside China.
- Multi-writer edge replication with strong guarantees.
- CXL memory pooling outside Alibaba.
- Transaction logic (not just redo) pushed into storage.

### Gaps
- Pavlo's 2023 and 2024 reviews were not fetched this session; the 2025 one was.
- No 2026 Pavlo review exists yet as of Oct 2026.
- Several dates marked [known] (DSQL GA May 2025, S3 conditional writes Aug/Nov 2024, DuckLake May 27 2025, Aurora SLv2 scale-to-zero Nov 2024) were not re-verified this session.
- HorizonDB and RegattaDB architectures are unverified.
