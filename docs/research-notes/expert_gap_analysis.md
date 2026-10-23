# Expert Gap Analysis: Open, Under-Exploited Architectural Directions for Cloud Databases (2020-2026)

Method note: primary PDFs (Stonebraker & Pavlo 2024; Leis & Dietrich 2024; Leis & Kuschewski 2021) were downloaded and text-extracted locally, so quotes from them are verbatim (minor hyphenation artifacts removed). Blog quotes come from WebFetch extractions of the original pages. The Seattle Report PDF returned HTTP 500 and was not read.

## 1. What do vision/position papers say?

### Takeaway
The vision papers converge on two claims: (a) shared-disk/disaggregated storage over object stores is now the settled cloud architecture, and (b) the big remaining opportunities lie *below* and *around* the DBMS: OS abstractions co-designed with the DBMS (unikernels), cost (not runtime) as the optimization target, and reusable/standardized DBMS components. All three are framed as largely unrealized.

### Cited Findings

**Stonebraker & Pavlo, "What Goes Around Comes Around... And Around..." (SIGMOD Record, June 2024)** — [PDF](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Cloud architecture is settled: "Since enterprises are moving everything possible to the cloud, we expect this shared-disk to dominate DBMS architectures. Hence, we do not foresee shared-nothing architectures resurfacing in the future." They frame this as recurrence: "Multi-node shared-disk DBMSs are an old idea that historically tended not to work out well. However, it is back in vogue with technology change (faster networking)." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Rationale: "over the last 20 years, networking bandwidth has increased much faster than disk bandwidth, making network attached storage (NAS) attractive"; benefits listed are per-query elasticity without reshuffling data, reassigning idle compute, and pushing computation to storage nodes. They note "Effective utilization of this model requires a hosted multi-node environment in which multiple DBMS customers are grouped onto the same node(s) with a multi-tenant execution scheme." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Cloud as "once-in-a-lifetime opportunity for enterprises to refactor codebases and remove bad historical technology decisions." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Explicit gap / call to action: "Another concern is the wasted effort of new projects reimplementing the same components that are not novel but necessary to have a production-ready DBMS (e.g., config handlers, parsers, buffer pools)... the community should foster the development of open-source reusable components and services... We contend that the database community should strive for a POSIX-like standard of DBMS internals to accelerate interoperability." Existing partial efforts named: file formats, Calcite/Orca, DataFusion/Velox. — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Explicit gap: "There is a crucial need for what one of us calls 'self-driving' DBMSs" (physical design, knob tuning, schema design, query tuning). — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Explicit gap: "Every DBMS should, therefore, make it easy to perform in situ processing of local and cloud storage files. DuckDB's rising popularity is partly due to its ability to do this well." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- On ML-for-DB (learned optimizers, tuners, learned access methods): "Although such ML-assisted optimizations are powerful tools to improve the performance of DBMSs, it does not obviate the need for high-quality systems engineering." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Data lakes: "At first glance, a data lake seems like a terrible idea... a recipe for integrity, discovery, and versioning problems"; lakehouses help mitigate metadata, caching, and indexing problems. — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)

**Leis & Dietrich, "Cloud-Native Database Systems and Unikernels: Reimagining OS Abstractions for Modern Hardware" (PVLDB 17(8), 2024, vision paper)** — [PDF](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Core claim: "Although the idea of custom, DBMS-optimized OS kernels is old, it is largely unrealized due to the demands of hardware compatibility and the reluctance of users to install specialized operating systems. However, the cloud and the database-as-a-service model make custom OS kernels realistic for the first time." — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Why it failed before: "few users would buy a DBMS that requires installing a custom OS as a prerequisite"; and a custom OS "would have to implement and maintain drivers for a myriad of devices." — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Why now: a DBMS on any recent EC2 instance "only needs to implement two drivers: an AWS-specific EFA driver for networking and a generic NVMe driver for storage." — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Diagnosis of current state: "database systems effectively already perform the traditional hardware management job of operating systems — but without having the low-level tools an OS has." OSv's whole VM subsystem is ~2,100 lines vs. >110,000 lines in Linux mm/. — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Under-exploited hardware primitives they list: CPU preemption and sleep/power states; page table and TLB manipulation; hypervisor memory ballooning and CPU hot-plugging; direct access to I/O submission/completion queues and interrupt control. — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Cost link: scope limited to the elastic data plane (not the control plane); sub-second unikernel boot is "highly useful," and "An integrated scheduling approach also allows for balancing the current resource demand with the cloud provider's pricing model." — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Counter-argument they address (security): unikernels "may lack standard security measures (e.g., address and privilege isolation)"; they argue this is acceptable for single-tenant hosting because "the big prize for an attacker is obtaining illegal access to the database," and note Google disabled io_uring on ChromeOS, Android and production servers after recurring exploits. — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)

**Leis & Kuschewski, "Towards Cost-Optimal Query Processing in the Cloud" (PVLDB 14, VLDB 2021)** — [PDF](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Thesis: research implicitly assumes fixed hardware ("a traditional procurement process"), but in the cloud "the goal must be to minimize workload cost rather than runtime." — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Spread across EC2 instance types (at time of writing): CPU cores/$ 4.9x (c5 vs x1e), DRAM 3.5x, network bandwidth 28.5x (c5n vs x1e). — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Explicit gap claim: "Current cloud systems are still far away from cost optimality." Worked example: scanning 1 TB from S3 on a c5n.18xlarge at ~80 Gbit/s takes ~100 s and costs ~$0.11 with per-second billing, vs. $5 on Athena ("almost 50x more expensive"); "The use of spot or reserved rather than on demand instances would increase the gap further to 100-200x." — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Their vision is a model of a "hypothetical, idealized system that is capable of exploiting all hardware resources" (100 Gbit networks, NVMe arrays) as a lower bound to steer cloud-native DBMS design; spot instances and serverless are explicitly left out of scope. — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)

**Disaggregation surveys/panels**
- Xiangyao Yu's PVLDB 2025 perspective paper "Disaggregation: A New Architecture for Cloud Databases" describes disaggregation as foundational for cloud-native DBs. — [PVLDB vol 18](https://vldb.org/pvldb/vol18/p5527-xiangyao.pdf) (via search summary; not read in full)
- Ghandeharizadeh et al., "Disaggregated Database Management Systems" (arXiv Nov 2024) summarizes a panel on "capability, challenges, and opportunities" of disaggregated DBMSs and hardware. — [arXiv 2411.01269](https://arxiv.org/abs/2411.01269v1) (via search summary; not read in full)

### Inferences
- The papers agree the storage architecture question is closed (shared-disk over object storage), which pushes remaining novelty to: OS/hypervisor co-design, cost-as-objective, multi-tenant execution, and componentization. Each is labelled "largely unrealized" or "far away" by its own proponents.
- Stonebraker & Pavlo note serverless efficiency "requires" multi-tenant execution on shared nodes, but do not elaborate how; this is a stated dependency without a stated solution.

### Gaps
- Seattle Report on Database Research (SIGMOD Record 2022) not read (server returned HTTP 500 at https://sigmodrecord.org/publications/sigmodRecord/2203/pdfs/08_The_seattle-report.pdf).
- Not covered due to tool budget: "Cloud-Native Database Systems at Alibaba" (VLDB 2019), DBOS papers (CIDR 2022, VLDB 2022), CIDR 2023-2026 vision papers, Yu's 2025 paper in full.
- Could not confirm a paper titled "Is the Cloud the Future of DBMSs?".

## 2. What does Andy Pavlo's yearly review identify as missing?

### Takeaway
Pavlo's reviews flag concrete, practical gaps rather than grand visions: Postgres's storage layer and lack of scale-out, unsafe/unfederated LLM-to-DB access via MCP, file-format stagnation (Parquet v1), the fragility of cloud-only DBaaS when vendors fail, and dismissal of GPUs, blockchain and standalone vector DBs.

### Cited Findings
- 2025 review: "PostgreSQL is the only major DBMS still relying on the OS page cache" (v18 async I/O a step away). — [Pavlo, 2025 retrospective](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- 2025: Postgres services are "single-primary node architectures"; Citus/Greenplum/Postgres-XL have limits; YugabyteDB "is a hard fork, so it is only compatible with PostgreSQL v15." (Scale-out Postgres remains unsolved.) — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- 2025, MCP/agents: "each request in these MCP servers targets only a single database at a time, so the application is responsible for performing joins across sources"; "There is no deep introspection to understand what the request aims to do and whether it is appropriate"; "nobody should trust an application with unfettered database access." — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- 2025, file formats: of Parquet files examined, "94% of them use only v1 features from 2013, even though their creation timestamps are after 2020." Microsoft's Amudai format was "quietly killed off." — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- 2025, failures: cites "the inviability of GPU-accelerated databases"; Voltron Data "failed to launch [Theseus] in a timely manner"; "The buzz around vector databases has muted." — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- 2024 review: Postgres has "a great front-end but an outdated storage architecture"; columnar add-ons "only solved part of the problem" because a DBMS "cannot fully exploit those formats if it still uses a row-oriented query processing model"; Postgres extensions' "lack of guard rails means that extensions can interfere with each other." — [Pavlo, 2024 retrospective](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- 2024: "Vectorized execution engines for analytical queries are a commodity now"; a single DuckDB instance suffices for most analytics given a median scan of ~100 MB (citing Fivetran data). — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- 2024: QLDB shutdown: "If Amazon can't figure out how to make money on a blockchain database, then nobody can." Rockset criticized for storing "three copies of your data in its indexes." — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- 2024: the "overarching issue" is "the long-term viability of open-source independent software vendors" because cloud vendors can host their projects. — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- 2023 review: "Cloud-only DBaaS makes this issue even more pernicious" (vendor failure ends hosting); Xeround gave customers two weeks, InfluxDB six months before deleting regions. — [Pavlo, 2023 retrospective](https://www.cs.cmu.edu/~pavlo/blog/2024/01/2023-databases-retrospective.html)
- 2023: worst-case optimal joins/factorization absent in Neo4j, TigerGraph and "most relational DBMSs"; vector DBMS "is just a document database with a specialized index data structure" and vendors "do not have a large enough moat." — [Pavlo 2023](https://www.cs.cmu.edu/~pavlo/blog/2024/01/2023-databases-retrospective.html)

### Inferences
- Pavlo's "missing" items cluster in the Postgres ecosystem (storage engine, scale-out, extension isolation) and in AI-facing interfaces (federation, safety), not in storage disaggregation, which he treats as solved.
- The DuckDB/100 MB median observation implies scale-out analytics is over-provisioned for most workloads, a cost argument consistent with Leis & Kuschewski.

### Gaps
- 2022 review and CMU DB talk series not reviewed.

## 3. Practitioner perspectives (Brooker, Vanlightly, Riccomini, Demirbas, Eaton, Jepsen)

### Takeaway
Practitioners treat object storage and disaggregation as the default, and point to the unsolved parts: low-latency hot tiers over S3, cross-AZ replication cost, unified hot/cold storage semantics, indexes on open table formats, and operational simplicity (online DDL, tail latency, avoiding big caches). Brooker argues strong consistency and OCC-based disaggregation are underrated defaults.

### Cited Findings
**Marc Brooker (AWS, Aurora DSQL)**
- DSQL design lessons from Aurora/DynamoDB: "avoiding large caches (they make failovers and read scale tricky)", "offering strongly consistent scalable reads", "pushing expensive operations like scans down to storage"; DSQL goes further by "completely disaggregating replication from transaction isolation and storage." — [Brooker, DSQL paper post, Jul 2026](https://www.brooker.co.za/blog/2026/07/19/dsql-paper.html)
- OCC: "Another practical advantage of OCC is preventing clients from ever being able to block other clients," tied to avoiding metastable failures. — [Brooker 2026](https://www.brooker.co.za/blog/2026/07/19/dsql-paper.html)
- "Strong consistency is the right default, and the right choice for nearly all applications." — [Brooker 2026](https://www.brooker.co.za/blog/2026/07/19/dsql-paper.html)
- Open-ended: agents are "great at building, but not (yet?) so great at long-horizon tasks like database operations." — [Brooker 2026](https://www.brooker.co.za/blog/2026/07/19/dsql-paper.html)
- Hard operational problems: "Tail latency is one of the hardest things to debug"; teams "spend months building tooling and processes for zero-impact DDL operations"; relational DBs are "head-of-line blocking" machines for large commits; reject "the mid-2000s idea that you need to put up with eventual consistency." DSQL's five-minute transaction limit avoids Postgres-style VACUUM accounting. Trade-off acknowledged: active-active multi-region pushes conflict detection to commit time. — [Brooker, "DSQL: Simplifying Architectures", Nov 2025](https://brooker.co.za/blog/2025/11/02/thinking-dsql.html)
- Aurora DSQL paper ("Aurora DSQL: Scalable, Multi-Region OLTP") is on arXiv as of Jul 2026. — [Brooker 2026](https://www.brooker.co.za/blog/2026/07/19/dsql-paper.html)

**Jack Vanlightly**
- "Object storage is taking over more of the data stack, but low-latency systems still need separate hot-data storage." Shared tiering into a lakehouse has "a large conversion cost when serving lagging or catch-up consumers," and lakehouse layout optimizations can make primary reads "fantastically inefficient compared to internal tiering." Verdict: "I am sure that shared tiering can be made to work, but with great care." Open governance question: "Who controls the retention policy of the Kafka topic?" — [Vanlightly, "A Conceptual Model for Storage Unification", Aug 2025](https://jack-vanlightly.com/blog/2025/8/21/a-conceptual-model-for-storage-unification)
- Kafka "diskless" KIPs (KIP-1150, 1176, 1183) motivated by cross-AZ replication costs; which design to adopt remains open. — [Vanlightly, "A Fork in the Road", Oct 2025](https://jack-vanlightly.com/blog/2025/10/22/a-fork-in-the-road-deciding-kafkas-diskless-future) (via blog index summary)
- Open table formats (Iceberg/Delta/Hudi) lack secondary indexes and rely on column stats/Bloom filters; whether they can get them: "no and it's complicated." — [Vanlightly, "Beyond Indexes", Oct 2025](https://jack-vanlightly.com/blog/2025/10/8/beyond-indexes-how-open-table-formats-optimize-query-performance) (via blog index summary)
- Argues against zero-copy Kafka-to-Iceberg ("topic as table"). — [Vanlightly, Oct 2025](https://jack-vanlightly.com/blog/2025/10/15/why-im-not-a-fan-of-zero-copy-apache-kafka-apache-iceberg) (title/teaser only)

**Chris Riccomini (materializedview.io)**
- "S3 Is the New SFTP": SaaS vendors can publish Parquet to a shared bucket under an Iceberg catalog; missing pieces: batch-only delivery, vendors still "roll their own visualization," and "Schema evolution challenges still remain." Prediction: "Customer data lakes might actually end up being a driving force for lakehouse adoption." — [Riccomini, Dec 2024](https://materializedview.io/p/s3-is-the-new-sftp)
- Related posts on IVM and a distributed POSIX filesystem exist but were not read: [IVM explainer](https://materializedview.io/p/everything-to-know-incremental-view-maintenance), [Distributed POSIX FS](https://materializedview.io/p/the-quest-for-a-distributed-posix-fs).

**Murat Demirbas**
- Nov 2025 post reviews the disaggregated-DBMS panel paper, focusing on AlloyDB, Rockset, Nova-LSM; QCon SF 2025 talk "Parting the Clouds" frames the shift as "driven primarily by cloud economics." — [Demirbas blog (via aggregator)](https://scour.ing/p/http://muratbuffalo.blogspot.com/2025/11/disaggregated-database-management.html); [InfoQ coverage](https://www.infoq.com/news/2025/11/disaggregated-systems-qcon/) (summaries only)

### Inferences
- The hot-tier-over-object-storage problem (Vanlightly) and the "avoid large caches" stance (Brooker) are in tension: one says low latency needs a separate hot tier; the other says big caches hurt failover. How to get low latency over S3 without large stateful caches is an open design space.
- Cross-AZ transfer pricing, not hardware, is the stated driver for streaming systems moving to object storage.

### Gaps
- Phil Eaton and Jepsen (Kyle Kingsbury) not reviewed within budget.
- Vanlightly's 2023-2024 posts (e.g., on S3 Express, table format internals) not reached; only 2025-2026 index was visible.
- No full text of Demirbas's post.

## 4. Cost/economics-driven architecture: which ideas remain unbuilt?

### Takeaway
Experts state that cloud DBMSs are far from cost-optimal and that pricing (cross-AZ transfer, per-second billing, spot) should drive architecture, but the concrete systems that do this (cost-optimal OLAP, pricing-aware scheduling, spot-native engines) remain mostly proposals.

### Cited Findings
- "Current cloud systems are still far away from cost optimality"; Athena ~50x costlier than a hand-sized EC2 scan, 100-200x with spot/reserved. — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Leis & Kuschewski call cost minimization "neither original nor, we believe, controversial," yet frame the cost-optimal system as a "long-term vision." — [Leis & Kuschewski 2021](https://www.cs6.tf.fau.de/files/2021/04/costoptimal.pdf)
- Unikernel data planes could balance demand "with the cloud provider's pricing model" via integrated scheduling. — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Cross-AZ replication cost drives Kafka diskless designs. — [Vanlightly blog index](https://jack-vanlightly.com/blog)
- Demirbas: the disaggregation shift is "driven primarily by cloud economics." — [InfoQ, Nov 2025](https://www.infoq.com/news/2025/11/disaggregated-systems-qcon/)
- Median analytical scan ~100 MB means a single DuckDB node is enough for most queries. — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)

### Inferences
- Spot instances, egress-aware placement, and multi-region cost models are named as levers (Leis & Kuschewski mention spot; Vanlightly cross-AZ) but no source reviewed describes a production DBMS that optimizes for them end-to-end.

### Gaps
- No source found quantifying S3 request-cost-driven design or multi-region egress cost models for OLTP.
- Leis group's follow-ups (e.g., NVMe-array and cloud network papers, 2023-2025) not reviewed.

## 5. "Obvious" ideas tried and failed (or stalled) in production, and why

### Takeaway
Repeated failure modes: specialized hardware (FPGA/GPU/custom) not cost-effective unless built by the cloud vendor; NVM lost its hardware (Optane cancelled); blockchain DBs too slow for trusted parties; NewSQL adoption limited by migration risk; vendor-run cloud-only databases die with their company (Fauna). Learned indexes have one notable production-scale result (Bigtable), with gains from side effects, not faster lookups.

### Cited Findings
- Hardware accelerators: "All other custom hardware DBMS acceleration during the 1980s failed"; Swarm64 dropped its FPGA; for GPUs, "If data does not fit in GPU memory, then query execution is bottlenecked on loading data into the device"; "special purpose hardware is not likely to find acceptance unless it is built by the cloud vendor." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Pavlo 2025 reiterates "the inviability of GPU-accelerated databases." — [Pavlo 2025](https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html)
- Blockchain DBs: "Legitimate businesses are unwilling to pay the performance price (about five orders of magnitude)." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf); QLDB shutdown — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- NewSQL: "There has yet to be a dramatic uptake in NewSQL DBMS adoption... existing DBMSs were good enough... Companies are more risk averse with changing OLTP DBMSs than with OLAP." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- MapReduce/Hadoop: "Hadoop died about a decade ago"; "HDFS has lost its luster." — [Stonebraker & Pavlo 2024](https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf)
- Custom DB-OS kernels: never adopted because users won't install a custom OS and drivers are unmaintainable; cloud removes both blockers. — [Leis & Dietrich 2024](https://vldb.org/pvldb/vol17/p2115-leis.pdf)
- Persistent memory: Intel wound down Optane in July 2022, final DIMM shipments extended to Dec 29, 2023; researchers argue PMem insights carry over to CXL-attached memory. — [BTW 2023 paper](https://dl.gi.de/bitstream/handle/20.500.12116/40355/C1-5.pdf); [Northeastern, "Persistent Memory Research in the Post-Optane Era"](https://news.northeastern.edu/?p=204934); counter-view that most of what DB developers wanted was already available via mmap — [specbranch, "Rest in Peace, Optane"](https://specbranch.com/posts/rip-optane/) (via search summaries)
- Learned indexes: Google integrated a learned index into Bigtable and improved end-to-end read latency/throughput, but gains came mainly from "a smaller index, fewer index seeks, fewer index blocks read, and simpler data block prefetching" rather than faster lookups; published only as a 4-page NeurIPS 2020 ML-for-Systems workshop paper. — [Abu-Libdeh et al., arXiv 2012.12501](https://arxiv.org/abs/2012.12501v1)
- Fauna (Calvin-derived): service ended May 30, 2025; Fauna said it was "not possible to raise the capital needed" independently and announced an open-source release. — [Fauna EOL FAQ](https://docs.fauna.com/fauna/current/eol-faq)
- Rockset: DBaaS shut down Sept 2024 (acquired by OpenAI); Pavlo criticized its design storing "three copies of your data in its indexes." — [Pavlo 2024](https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html)
- Cloud-only DBaaS vendor failure strands customers (Xeround two weeks, InfluxDB six months). — [Pavlo 2023](https://www.cs.cmu.edu/~pavlo/blog/2024/01/2023-databases-retrospective.html)

### Inferences
- Fauna's shutdown is attributed by Fauna to funding, not to the Calvin deterministic-transaction design; no source reviewed links its failure to Calvin's technical limits.
- Leis & Dietrich's argument is structurally the same as Stonebraker & Pavlo's hardware conclusion: specialization becomes viable when the vendor controls the full stack (cloud), which is the common thread for "failed before, maybe viable now."

### Gaps
- No primary source found analyzing Calvin/deterministic databases' production limitations (e.g., Abadi's own retrospectives).
- No source found on learned query optimizers' production adoption (e.g., Bao, Neo) beyond Stonebraker & Pavlo's general caveat.
- Hacker News practitioner skepticism threads not reviewed.
