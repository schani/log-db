mod bench;
mod log;
mod node;
mod s2;
mod server;
mod state;

use std::sync::Arc;
use std::time::Duration;

use anyhow::Context;
use clap::{Args, Parser, Subcommand, ValueEnum};

use crate::log::{Log, MemLog};
use crate::node::{Node, NodeConfig};

#[derive(Parser)]
#[command(about = "A deterministic database whose only durable state is a shared log")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Run a node with an HTTP API. Any number of nodes may serve the same stream.
    Serve {
        #[command(flatten)]
        log: LogArgs,
        #[command(flatten)]
        node: NodeArgs,
        #[arg(long, default_value = "127.0.0.1:7000")]
        listen: String,
    },
    /// In-process benchmark: bank transfers through writer nodes, verified on replicas.
    Bench {
        #[command(flatten)]
        log: LogArgs,
        #[command(flatten)]
        node: NodeArgs,
        #[arg(long, default_value_t = 1)]
        writers: usize,
        #[arg(long, default_value_t = 1)]
        replicas: usize,
        #[arg(long, default_value_t = 1000)]
        clients: usize,
        #[arg(long, default_value_t = 10_000)]
        accounts: usize,
        #[arg(long, default_value_t = 20)]
        seconds: u64,
    },
}

#[derive(Clone, Copy, ValueEnum)]
enum LogKind {
    Mem,
    S2,
}

#[derive(Args)]
struct LogArgs {
    #[arg(long, value_enum, default_value = "mem")]
    log: LogKind,
    /// S2 stream; defaults to a fresh one.
    #[arg(long)]
    stream: Option<String>,
    #[arg(long, env = "S2_BASIN")]
    basin: Option<String>,
    #[arg(long, env = "S2_API_KEY", hide_env_values = true)]
    s2_key: Option<String>,
    /// Simulated round trip of the in-memory log.
    #[arg(long, default_value_t = 30)]
    mem_latency_ms: u64,
}

#[derive(Args)]
struct NodeArgs {
    /// How long an epoch collects transactions after its first one.
    #[arg(long, default_value_t = 5)]
    epoch_ms: u64,
}

impl NodeArgs {
    fn config(&self) -> NodeConfig {
        NodeConfig { epoch: Duration::from_millis(self.epoch_ms), ..NodeConfig::default() }
    }
}

impl LogArgs {
    fn stream_name(&self) -> String {
        self.stream.clone().unwrap_or_else(|| {
            let ts = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
            format!("logdb-{ts}")
        })
    }

    /// Returns a factory producing one log client per node, all on the same log.
    fn factory(&self) -> impl AsyncFn() -> anyhow::Result<Arc<dyn Log>> {
        let kind = self.log;
        let mem: Arc<dyn Log> = Arc::new(MemLog::new(Duration::from_millis(self.mem_latency_ms)));
        let stream = self.stream_name();
        let basin = self.basin.clone();
        let key = self.s2_key.clone();
        if matches!(kind, LogKind::S2) {
            println!("log: s2 basin {} stream {stream}", basin.as_deref().unwrap_or("?"));
        }
        async move || -> anyhow::Result<Arc<dyn Log>> {
            Ok(match kind {
                LogKind::Mem => mem.clone(),
                LogKind::S2 => {
                    let basin = basin.as_deref().context("--basin or S2_BASIN required")?;
                    let key = key.as_deref().context("S2_API_KEY required")?;
                    Arc::new(s2::S2Log::connect(basin, &stream, key).await?)
                }
            })
        }
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let _ = dotenvy::dotenv();
    tracing_subscriber::fmt().with_env_filter(tracing_subscriber::EnvFilter::from_default_env()).init();
    match Cli::parse().cmd {
        Cmd::Serve { log, node, listen } => {
            let node = Node::start(log.factory()().await?, node.config());
            let listener = tokio::net::TcpListener::bind(&listen).await?;
            println!("node {:016x} listening on {listen}", node.id);
            axum::serve(listener, server::router(node)).await?;
        }
        Cmd::Bench { log, node, writers, replicas, clients, accounts, seconds } => {
            let cfg = bench::BenchConfig {
                writers,
                replicas,
                clients,
                accounts,
                duration: Duration::from_secs(seconds),
                node: node.config(),
            };
            if !bench::run(log.factory(), cfg).await? {
                std::process::exit(1);
            }
        }
    }
    Ok(())
}
