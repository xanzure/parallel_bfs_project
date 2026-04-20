import os
import math
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CSV = os.path.join(ROOT, "results", "results.csv")
CHART_DIR = os.path.join(ROOT, "results", "charts")

def ensure_dirs():
    os.makedirs(CHART_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv(RESULTS_CSV)

    # keep only successful matching runs
    df = df[df["match"] == True].copy()

    # avoid divide-by-zero / weird rows
    df = df[(df["seq_time"] > 0) & (df["par_time"] > 0)].copy()

    # derived metrics
    df["size"] = df["edges"]  # best single proxy for BFS work
    df["log_edges"] = df["edges"].apply(lambda x: math.log10(x) if x > 0 else 0)
    df["density"] = (2 * df["edges"]) / (df["nodes"] * (df["nodes"] - 1)).replace(0, 1)

    # throughput in million traversed edges per second
    df["seq_mteps"] = (df["edges"] / df["seq_time"]) / 1e6
    df["par_mteps"] = (df["edges"] / df["par_time"]) / 1e6

    return df.sort_values("edges")

def save_runtime_vs_edges(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["edges"], df["seq_time"], marker="o", label="Sequential")
    plt.plot(df["edges"], df["par_time"], marker="o", label="Parallel")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Edges (log scale)")
    plt.ylabel("Runtime in seconds (log scale)")
    plt.title("BFS Runtime vs Graph Size")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "runtime_vs_edges.png"), dpi=200)
    plt.close()

def save_speedup_vs_edges(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["edges"], df["speedup"], marker="o")
    plt.xscale("log")
    plt.xlabel("Edges (log scale)")
    plt.ylabel("Speedup (seq / par)")
    plt.title("Speedup vs Graph Size")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "speedup_vs_edges.png"), dpi=200)
    plt.close()

def save_throughput_vs_edges(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["edges"], df["seq_mteps"], marker="o", label="Sequential")
    plt.plot(df["edges"], df["par_mteps"], marker="o", label="Parallel")
    plt.xscale("log")
    plt.xlabel("Edges (log scale)")
    plt.ylabel("Throughput (MTEPS)")
    plt.title("BFS Throughput vs Graph Size")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "throughput_vs_edges.png"), dpi=200)
    plt.close()

def save_bucketed_speedup(df, buckets=5):
    # bucket by edges so large numbers of test cases stay readable
    bucketed = df.copy()
    bucketed["edge_bucket"] = pd.qcut(bucketed["edges"], q=min(buckets, len(bucketed)), duplicates="drop")

    grouped = bucketed.groupby("edge_bucket", observed=True).agg(
        avg_nodes=("nodes", "mean"),
        avg_edges=("edges", "mean"),
        avg_speedup=("speedup", "mean"),
        avg_seq_time=("seq_time", "mean"),
        avg_par_time=("par_time", "mean"),
        count=("file", "count")
    ).reset_index()

    labels = [
        f"{int(row.avg_edges):,} edges\n(n={row['count']})"
        for _, row in grouped.iterrows()
    ]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, grouped["avg_speedup"])
    plt.ylabel("Average Speedup")
    plt.xlabel("Graph Size Bucket")
    plt.title("Average Speedup by Graph Size Bucket")
    plt.xticks(rotation=20, ha="right")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "bucketed_speedup.png"), dpi=200)
    plt.close()

def save_runtime_scatter(df):
    plt.figure(figsize=(10, 6))
    plt.scatter(df["nodes"], df["par_time"])
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Nodes (log scale)")
    plt.ylabel("Parallel Runtime (log scale)")
    plt.title("Parallel Runtime vs Number of Nodes")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "parallel_runtime_vs_nodes.png"), dpi=200)
    plt.close()

def main():
    ensure_dirs()
    df = load_data()

    if df.empty:
        print("No matching rows found in results.csv")
        return

    save_runtime_vs_edges(df)
    save_speedup_vs_edges(df)
    save_throughput_vs_edges(df)
    save_bucketed_speedup(df)
    save_runtime_scatter(df)

    print(f"Saved charts to: {CHART_DIR}")

if __name__ == "__main__":
    main()