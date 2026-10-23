# Storage, Hardware, and Disaggregation Research (2019-2026) and Its Production Adoption

Scope note: 15 web searches were run. Vendor performance claims are self-reported unless noted. Where I relied on prior knowledge without verifying it in this session, the item is in Gaps, not Findings.

## 1. Memory disaggregation, CXL, and RDMA-based OLTP: what is in production?

### Takeaway
CXL memory pooling has one production cloud-DB deployment (Alibaba PolarDB, in gray-scale rollout, not GA). Academic RDMA/disaggregated-memory indexes and transaction systems (Sherman, ROLEX, dLSM, FORD, Motor) remain research prototypes with no adoption found. The bottleneck these papers keep reporting is the memory-node RNIC and the cost of RDMA atomics.

### Cited Findings
**PolarDB-CXL ("Unlocking the Potential of CXL for Disaggregated Memory in Cloud-Native Databases", SIGMOD 2025 industry track, Best Industrial Paper, DOI 10.1145/3722212.3724460)**
- Idea: a distributed memory pool on a CXL switch (PolarCXLMem) replaces RDMA-based remote buffer pools. PolarRecv uses CXL memory's persistence across host crashes for fast recovery — [Alibaba Cloud blog](https://www.alibabacloud.com/blog/polardb-brings-alibaba-cloud-another-sigmod-best-paper-award_602713); [rmarcus.info paper entry](https://rmarcus.info/dbscholar/papers/hc634484319399e4a)
- Claimed results: up to 2.1x over RDMA-based memory pooling; >100% gain on sysbench IO-bound workloads; >40x faster crash recovery; single-node memory expandable to ~8 TB — [Alibaba Cloud blog](https://www.alibabacloud.com/blog/polardb-brings-alibaba-cloud-another-sigmod-best-paper-award_602713); [Aliyun help page](https://help.aliyun.com/zh/polardb/polardb-for-mysql/user-guide/cxl-based-disaggregated-architecture-for-polardb)
- Adoption: shipped as PolarDB's "DMP" feature, but the help page says it is in gray-scale (limited) rollout, not generally available — [Aliyun help page](https://help.aliyun.com/zh/polardb/polardb-for-mysql/user-guide/cxl-based-disaggregated-architecture-for-polardb)

**CXL evaluations for DBMSs**
- Ahn et al., PVLDB 17 (2024), SAP HANA Cloud on CXL: negligible OLTP degradation, wide OLAP degradation; CXL shared memory cut failover restart time 40% at TPC-H SF10, estimated 84% at SF100 — [PVLDB 17 p3827](https://vldb.org/pvldb/vol17/p3827-ahn.pdf)
- Weisgut et al., PVLDB 18 (2025), "CXL Memory Performance for In-Memory Data Processing": tested four real CXL devices. Access-frequency-aware column placement put >80% of TPC-H data in CXL memory at 85% of local-DRAM performance. Conclusion: CXL need not slow queries, but only with workload-aware data placement — [PVLDB 18 p3119](https://www.vldb.org/pvldb/vol18/p3119-weisgut.pdf); [HPI PDF](https://hpi.de/oldsite/fileadmin/user_upload/fachgebiete/rabl/publications/2025/vldb25-cxl-performance.pdf)
- Huang et al., ADMS@VLDB 2024: interleaving CXL with host memory gave up to 1.61x for in-memory analytics — [ADMS24_01](https://vldb.org/workshops/2024/proceedings/ADMS/ADMS24_01.pdf)
- CXL-Bench (Weisgut et al., ADMS@VLDB 2025) benchmarks shared CXL memory access — [ADMS25-07](https://www.vldb.org/2025/Workshops/VLDB-Workshops-2025/ADMS/ADMS25-07.pdf)

**Disaggregated-memory indexes and transactions (RDMA)**
- Sherman (SIGMOD 2022): write-optimized B+-tree on disaggregated memory using commodity RDMA NICs. It uses hierarchical locks, fewer round trips, and a node layout that reduces write-back amplification. Claims roughly 10x on write-heavy workloads but only slightly higher throughput on 95%-read workloads, with 25% lower p99 — [DeepAI summary](https://deepai.org/publication/sherman-a-write-optimized-distributed-b-tree-index-on-disaggregated-memory); [CACM Research Highlight](https://cacm.acm.org/research-highlights/designing-an-efficient-tree-index-on-disaggregated-memory)
- ROLEX (FAST 2023 Best Paper): learned KV store on disaggregated memory. Compute nodes modify data through one-sided RDMA, and models retrain asynchronously on memory nodes, which assumes memory nodes have some compute — [USENIX FAST'23](https://usenix.org/conference/fast23/presentation/li-pengfei)
- dLSM (ICDE 2023; VLDBJ 2024): LSM-tree on disaggregated memory that offloads compaction to memory nodes. Claims 2.3-11.6x write throughput over an optimized B-tree and adapted LSMs. Open source — [ICDE23 PDF](https://www.cs.purdue.edu/homes/csjgwang/pubs/ICDE23_dLSM.pdf); [VLDBJ24 PDF](https://cs.purdue.edu/homes/csjgwang/pubs/VLDBJ24_dLSM.pdf)
- FORD (single-version) and Motor (MVCC): transactions on disaggregated memory using one-sided RDMA from compute nodes. The 2025 Lotus paper says these systems hit a bottleneck at memory-node RNICs, and the CAS/FAA atomics used for locking cost more than plain reads and writes — [Lotus arXiv 2512.16136](https://arxiv.org/html/2512.16136v1)
- Industry interest appears only as "companies, e.g., Microsoft, Alibaba, and IBM, experiment with memory disaggregation". No production use of these research systems was found — [NSF PAR paper](https://par.nsf.gov/servlets/purl/10467780)

### Inferences
- Productionized disaggregation in cloud DBs means coarse-grained remote buffer pools or memory expansion owned by the vendor (PolarDB). Fine-grained one-sided RDMA data structures and transactions have not been adopted. Likely reasons: they need RDMA fabrics that public-cloud tenants usually lack, RNIC atomics bottleneck, and memory-node failures are hard to handle. The Lotus finding supports the second reason directly.
- CXL looks more deployable than RDMA because it is load/store and needs no custom data structures. But the evaluations show gains depend on DBMS-aware tiering and placement, which mainstream engines (PostgreSQL, MySQL) don't do. That makes "CXL-aware buffer/tier placement" an open opportunity.
- PolarRecv (fast recovery via CXL memory that survives host failure) and HANA's 40-84% failover reduction suggest that shared CXL memory for fast failover may matter more than capacity expansion. Outside Alibaba, I found no deployment.

### Gaps
- FaRM (SOSP 2015 / A1 graph DB at Microsoft) and NAM-DB (VLDB 2017) were not checked. My recollection is that FaRM backed Microsoft's internal A1 graph store, but this was not verified, and both predate 2019.
- No public data on whether AWS, Azure, or GCP offer CXL-pooled memory to database services.
- I did not find a paper with the exact title "Is CXL ready for DBs". The closest matches are the Weisgut and Ahn papers above.

## 2. Object-storage-native OLTP, S3 conditional writes, and cloud-native storage engines

### Takeaway
S3 gained put-if-absent (Aug 2024) and If-Match/ETag CAS (Nov 2024). That enabled a wave of startup and OSS systems (SlateDB, Lakebase-style Postgres on object storage) more than academic OLTP papers. Academic work on OLTP directly on object storage is thin: the clearest example is Milliscale (arXiv, March 2026) on S3 Express One Zone. TUM's Colibri, AnyBlob, and vmcache line flows into the startup CedarDB, not into mature systems.

### Cited Findings
- S3 conditional writes: If-None-Match (put-if-absent) in Aug 2024, then ETag-based If-Match on PutObject and CompleteMultipartUpload in Nov 2024 — [AWS What's New, Nov 2024](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-s3-functionality-conditional-writes); [Simon Willison](https://simonwillison.net/2024/Nov/26/s3-conditional-writes)
- Limitation: S3 compares only existence or ETag, not arbitrary values, so it is not general CAS. Writers need retry loops on 412 — [Tigris blog](https://www.tigrisdata.com/blog/s3-conditional-writes/)
- SlateDB uses If-None-Match on new manifest and WAL object names as fencing points against zombie writers — [blog on S3 CAS coordination](https://mohakchugh.is-a.dev/blog/s3-conditional-writes-distributed-coordination). Apache Ozone added S3 conditional requests in 2026 for similar patterns — [Ozone blog 2026-07-08](https://ozone.apache.org/blog/2026/07/08/ozone-s3-conditional-request)
- Milliscale (Zhou, Huang, Wang; arXiv 2603.02108, March 2026): memory-optimized OLTP engine targeting commit latency on S3 Express One Zone. It argues naive designs still have high commit latency because of S3 Express quirks and decentralized logging, and that S3 Standard is cheap but has very high latency. Prototype only — [arXiv 2603.02108](https://arxiv.org/abs/2603.02108)
- Databricks Lakebase markets Postgres running "natively on object storage" with decoupled compute and storage. This is a commercial (Neon-derived) system, not an academic artifact — [Databricks DAIS session](https://www.databricks.com/dataaisummit/session/oltp-object-store-reimagining-postgres-lakebase-architecture)
- Colibri ("Two Birds With One Stone: Designing a Hybrid Cloud Storage Engine for HTAP", Schmidt, Durner, Leis, Neumann, PVLDB 17(11) 2024): hybrid column-row store with hot/cold separation across memory, SSD, and object storage. It has log servers and page servers, bypasses the WAL for cold data, and uses lightweight MVCC. Claims up to 10x over ETL-based setups — [PDF](https://db.in.tum.de/~schmidt/papers/colibri.pdf); [poster](https://www.db.in.tum.de/~schmidt/papers/colibri-poster.pdf)
- Adoption of Colibri: CedarDB (TUM spin-off startup, Umbra-based) blogged that the hybrid storage engine was developed with TUM. Status: startup, not mature — [CedarDB blog, Aug 2024](https://cedardb.com/blog/colibri/)
- AnyBlob (Durner, Leis, Neumann, PVLDB 16(11) 2023, "Exploiting Cloud Object Storage for High-Performance Analytics"): io_uring-based object-store download manager. With no SSD cache, Umbra+AnyBlob matched cloud warehouses that cache on local SSDs, with better elasticity and less CPU than vendor SDKs — [PVLDB p2769](https://vldb.org/pvldb/vol16/p2769-durner.pdf); [GitHub](https://github.com/durner/AnyBlob)
- AnyBlob adoption: no third-party adoption found. GreptimeDB said the paper's findings guide its engineering, which is not the same as using the code — [Greptime blog](https://greptime.com/blogs/2024-01-31-paper-sharing)
- "Cloud-Native Database Systems and Unikernels: Reimagining OS Abstractions for Modern Hardware" (VLDB 2024 vision paper, presented by Christian Dietrich, TU Braunschweig): argues unikernels with direct hardware access can improve DBMS performance — [TU Braunschweig IBR](https://admin@ibr.cs.tu-bs.de)

### Inferences
- The S3 CAS primitives are recent (late 2024). Academia has published little on OLTP commit protocols over them, while industry (SlateDB, WarpStream-style systems, Lakebase/Neon) moved first. A rigorous treatment of latency and cost tradeoffs for OLTP commit on S3/S3 Express, such as group commit, fencing, and multi-writer, looks under-explored. Milliscale is the first clear academic entry found.
- The ETag-only CAS limitation means multi-object atomic commit must go through a single manifest or log object. That serializes commits through one object and caps throughput per database. This is an inference; no source quantified it.

### Gaps
- Not verified this session: Delta Lake (VLDB 2020) and Iceberg use put-if-absent/rename for commits. Neon's and Aurora's page-server/log-store designs were not re-checked.
- No academic benchmark found of S3 conditional-write throughput or latency limits per key.
- Authorship of the unikernel paper beyond Dietrich (I believe Leis co-authored it) was not confirmed by search.

## 3. Learned indexes (RMI, ALEX, PGM, LIPP): adoption status in 2026

### Takeaway
Still essentially unadopted in mature general-purpose DBMSs. The one published production-scale integration is Google's Bigtable learned index paper (2020). Its production status after publication is not documented. Recent academic work itself says adoption is limited because concurrency and persistence support does not match B+-trees.

### Cited Findings
- "Learned Indexes for a Google-scale Disk-based Database" (Abu-Libdeh et al., arXiv Dec 2020; ML for Systems workshop): integrates a learned index into Bigtable's disk-based SSTable lookup and reports significant end-to-end read latency and throughput gains. Written in response to critiques that learned indexes lacked inserts and disk support and gave negligible end-to-end benefit — [arXiv 2012.12501](https://arxiv.org/pdf/2012.12501); [Google Research](https://research.google/pubs/learned-indexes-for-a-google-scale-disk-based-database/)
- A 2026 arXiv RocksDB case study says production adoption "remains limited", partly because learned indexes lack B+-tree-grade concurrency and persistence (from search snippet; exact paper URL not retrieved) — see the learned-index search results, e.g. [arXiv 2506.08671](https://arxiv.org/abs/2506.08671v1) (LSM learned-index benchmark, June 2025)
- PVLDB 16 "Learned Index: A Comprehensive Experimental Evaluation" benchmarks the space — [VLDB page](https://mail.vldb.org/pvldb/volumes/16/paper/Learned%20Index%3A%20A%20Comprehensive%20Experimental%20Evaluation)
- The VLDB Journal (2025) multi-dimensional learned index survey cites the lack of standardized benchmarks as a barrier — [BUAA record](https://research.buaa.edu.cn/en/publications/how-good-are-multi-dimensional-learned-indexes-an-experimental-su/)
- ROLEX (FAST 2023) applies learned indexing to disaggregated memory. It is a prototype — [USENIX](https://usenix.org/conference/fast23/presentation/li-pengfei)

### Inferences
- Learned indexes best fit immutable sorted runs: SSTable fence and block indexes, Parquet/columnar zone maps, and static lookup tables. They fit poorly with mutable concurrent B-trees. The Bigtable result is consistent with this. The practical niche is "learned index per immutable file", and mature LSM engines such as RocksDB have not shipped it.
- Reasons cited for non-adoption: concurrency, persistence, and update support; small end-to-end gains when I/O dominates; and a lack of standardized benchmarks.

### Gaps
- Could not confirm whether Bigtable's learned index remained in production after 2020.
- Not verified: claims that any commercial system (e.g., SingleStore or Redshift) ships learned indexes. I found no source.

## 4. Computational storage, SmartNIC/DPU offload, FPGA acceleration, ZNS, and FDP

### Takeaway
FDP (NVMe TP4146) is getting industrial traction: Meta's CacheLib paper at EuroSys 2025, plus Samsung-led RocksDB and CacheLib integrations. ZNS appears to have stalled outside niche deployments, though I found no source that states this. DPU offload for databases is at the Microsoft Research prototype stage (DDS on Azure SQL Hyperscale page servers), with no confirmed production rollout.

### Cited Findings
- FDP in CacheLib ("Towards Efficient Flash Caches with Emerging NVMe Flexible Data Placement SSDs", EuroSys 2025, Meta/Samsung): segregating data with FDP placement handles brought device write amplification close to 1 on Meta and Twitter production traces, reducing embodied carbon and power — [arXiv 2503.11665](https://arxiv.org/abs/2503.11665)
- FDP is ratified NVMe TP4146. One industry comparison says ZNS suits fully sequential-write software, while FDP fits incremental adoption — [Blocks and Files](https://blocksandfiles.com/?p=54224)
- SNIA SDC 2025 session (Samsung, Manzanares): FDP stack implementations in CacheLib and RocksDB, covering write amplification and the engineering effort to adopt — [SNIA SDC25 session 18579](https://www.snia.org/sniadeveloper/session/18579)
- ZNS: the HotOS 2021 paper "Don't Be a Blockhead" argued industry was standardizing on ZNS and research should follow — [Microsoft Research](https://www.microsoft.com/en-us/research/?p=831997). SNIA 2023 described ZNS as "increasingly popular" for large deployments, which is advocacy framing — [SNIA 2023](https://www.snia.org/educational-library/towards-large-scale-deployments-zoned-namespace-ssds-2023). Characterization study — [arXiv 2206.01547](https://arxiv.org/pdf/2206.01547)
- DPU offload, Microsoft Research DDS (Phil Bernstein et al.): runs GetPage@LSN on the DPU of an Azure SQL Hyperscale page server. Claims up to 17 host cores saved, 70% lower latency, and 75% higher throughput. Research claim, not a production announcement — [UWaterloo seminar](https://cs.uwaterloo.ca/events/data-systems-seminar-series-dds-dpu-optimized-disaggregated-storage); [Berkeley Sky seminar](https://sky.cs.berkeley.edu/?p=2678)
- DPU storage offload generally (NVIDIA SNAP NVMe emulation on BlueField) is infrastructure-level, not DBMS-level — [FlexBSO arXiv 2409.02381](https://arxiv.org/pdf/2409.02381)

### Inferences
- The pattern: hardware features that need application rewrites (ZNS, which requires sequential zone management) lose to features that are optional hints (FDP placement IDs on a conventional block interface). The same pattern applies to RDMA-native versus CXL load/store designs.
- DPU/SmartNIC offload in DBs only shows up where one vendor owns the whole stack (cloud page servers). DBMS vendors that run on tenant VMs can't assume DPUs.

### Gaps
- Did not verify status of AWS Redshift AQUA (FPGA/Nitro-based query acceleration, announced 2019-2021). My recollection is that it was folded into RA3 and stopped being marketed separately, but no source was retrieved.
- No data found on ScaleFlux or Samsung SmartSSD computational storage use in production DBMSs, or on FPGA query acceleration in mature DBs post-2019.
- No source confirms ZNS deployment counts or ZenFS's maintenance status in 2025-2026.

## 5. Persistent memory research after Optane: what survives?

### Takeaway
The hardware is gone (Intel wound down Optane in 2022). The consensus is that crash-consistency, programming-model, and tiering techniques transfer to CXL-attached memory. Memory-speed byte-addressable persistence has no successor, and CXL may make crash consistency a multi-host problem even with volatile memory.

### Cited Findings
- Intel framed winding down Optane "as we embrace CXL" — [Blocks and Files, July 2022](https://www.blocksandfiles.com/scm/2022/07/29/intel-at-3d-exit-point-alas-poor-optane-i-knew-it-well/1600509)
- Benson, Weisgut, Rabl (BTW 2023), "What We Can Learn from Persistent Memory for CXL": PMem insights on limited hardware availability, CPU components untuned for these access patterns, and multi-tier price-performance should apply to CXL memory — [GI DL](https://dl.gi.de/items/ba3b1c7a-a5bc-4424-89fd-d4b8caa278a8/full)
- Desnoyers et al. (2023), "Persistent Memory Research in the Post-Optane Era": most PMem research actually addressed in-memory crash consistency, not persistence, so it transfers. CXL pooling puts hosts sharing memory in different failure domains, which creates crash-consistency issues even with volatile memory. Memory-speed persistence technologies "seem years off" — [Stony Brook record](https://researchconnect.stonybrook.edu/en/publications/persistent-memory-research-in-the-post-optane-era/)
- Concrete survivor in production: PolarDB's PolarRecv uses CXL memory persistence across host crashes for >40x faster recovery (gray-scale rollout) — [Aliyun help page](https://help.aliyun.com/zh/polardb/polardb-for-mysql/user-guide/cxl-based-disaggregated-architecture-for-polardb)
- SAP HANA Cloud evaluated CXL shared memory for faster failover — [PVLDB 17 p3827](https://vldb.org/pvldb/vol17/p3827-ahn.pdf)

### Inferences
- The surviving PMem idea in DBs is "memory that outlives the process or host", used for instant restart and failover, now delivered by CXL-attached DRAM in a separate failure domain. Persistent data structures for durability are not what survived.

### Gaps
- Not checked: whether SAP HANA's earlier Optane persistent-memory support has been officially deprecated.

## 6. Unikernel/OS-bypass DBs, DB-as-OS (DBOS), io_uring engines, and vmcache

### Takeaway
vmcache/exmap (SIGMOD 2023) is the most cited idea here but has no confirmed mature-system adoption. exmap is an out-of-tree Linux kernel module, which is a likely barrier. DBOS evolved from a "database-oriented OS" research project into a commercial durable-workflow library on Postgres, a big narrowing of the original vision. Unikernel DBMSs remain at the vision-paper stage.

### Cited Findings
- vmcache (Leis, Alhomssi, Ziegler, Loeck, Dietrich; SIGMOD 2023 / PACMMOD, DOI 10.1145/3588687): uses hardware virtual memory to translate page IDs to addresses instead of hash tables or pointer swizzling. Unlike mmap, the DBMS keeps control of faulting and eviction. exmap is a Linux kernel extension for scalable page-table manipulation, because OS primitives bottleneck with fast SSDs — [TUM PDF](https://www.cs.cit.tum.de/fileadmin/w00cfj/dis/_my_direct_uploads/vmcache.pdf)
- Follow-up vmcache_n (arXiv 2603.03271, 2026): multi-tier extension where each page's virtual address stays fixed while its physical frame moves between tiers. Claims up to 4x TPC-C throughput over vmcache — [arXiv 2603.03271](https://arxiv.org/html/2603.03271v1)
- DBOS: began as a Stanford/MIT joint research project. It is now a lightweight durable-workflow library on Postgres, integrated with Supabase and CockroachDB — [Supabase blog](https://supabase.com/blog/durable-workflows-in-postgres-dbos); [DBOS architecture docs](https://docs.dbos.dev/architecture); [CockroachDB blog](https://cockroachlabs.com/blog/embedded-durable-execution-dbos-cockroachdb). 2026 marketing emphasizes durable AI agents, and DBOS claims Postgres queues reach ~30k workflows/s — [RuntimeWire](https://runtimewire.com/article/dbos-postgres-queues-30600-workflows-per-second)
- Unikernel DBMS: vision paper at VLDB 2024 — [TU Braunschweig IBR](https://admin@ibr.cs.tu-bs.de)
- io_uring in research engines: AnyBlob is io_uring-based for object-store I/O — [GitHub](https://github.com/durner/AnyBlob)

### Inferences
- The original DBOS idea (OS state in a DBMS, scheduler as queries) was not adopted. The commercial residue is "workflow state in Postgres". Research to industry here meant drastic scope reduction.
- vmcache needs either exmap (custom kernel module) or tolerating Linux page-table scalability limits. Most cloud DBaaS vendors control their kernels, so this is technically adoptable, but I found no evidence that any did. vmcache_n suggests the line continues toward CXL tiering.

### Gaps
- Could not confirm whether CedarDB or LeanStore use vmcache/exmap in their current code.
- No data on io_uring adoption in mature engines (e.g., PostgreSQL 18's AIO/io_uring support) was retrieved this session.

## 7. Multi-tier caching across RAM, SSD, and object store

### Takeaway
Research shows that object-store bandwidth can match SSD-cached warehouses for analytics (AnyBlob) and that one engine can tier hot/cold data across RAM, SSD, and S3 for HTAP (Colibri). Commercial cloud warehouses still lean on local SSD caches. Multi-tier virtual-memory buffer management (vmcache_n) is 2026 research.

### Cited Findings
- AnyBlob: without caching, Umbra matched SSD-caching cloud warehouses while improving elasticity. The network-to-NVMe bandwidth gap is closing — [PVLDB 16 p2769](https://vldb.org/pvldb/vol16/p2769-durner.pdf)
- Colibri: hot/cold separation across memory, SSD, and object storage for HTAP; up to 10x over ETL — [Colibri PDF](https://db.in.tum.de/~schmidt/papers/colibri.pdf)
- vmcache_n: fixed virtual addresses with physical frames moving among tiers; up to 4x on TPC-C vs vmcache — [arXiv 2603.03271](https://arxiv.org/html/2603.03271v1)
- Weisgut et al.: access-frequency column placement between DRAM and CXL — [PVLDB 18 p3119](https://www.vldb.org/pvldb/vol18/p3119-weisgut.pdf)
- FDP-aware flash caching (CacheLib) — [arXiv 2503.11665](https://arxiv.org/abs/2503.11665)

### Inferences
- A unified buffer manager spanning DRAM, CXL, local NVMe, and object store, with one page-addressing scheme, is assembled from published pieces (vmcache_n, Colibri, AnyBlob, CXL placement studies). No mature system ships it.

### Gaps
- Did not retrieve sources on caching designs in Snowflake, Neon, Aurora, or Databricks for comparison.
- Not found: an academic paper systematically comparing cost models across RAM, SSD, S3 Express, and S3 Standard tiers for OLTP.
