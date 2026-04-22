import os
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CSV = os.path.join(ROOT, "results", "results.csv")
CHART_DIR = os.path.join(ROOT, "results", "charts")

IMPLEMENTATION_ORDER = [
    "seq",
    "par_shared_lock",
    "par_shared_atomic",
    "par_local_static",
    "par_local_dynamic",
]

IMPLEMENTATION_LABELS = {
    "seq": "Seq",
    "par_shared_lock": "Shared Lock",
    "par_shared_atomic": "Shared Atomic",
    "par_local_static": "Local Static",
    "par_local_dynamic": "Local Dynamic",
}


def ensure_dirs():
    os.makedirs(CHART_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(RESULTS_CSV)

    df = df[df["match_seq"] == True].copy()
    df = df[df["runtime"] > 0].copy()
    df = df[df["baseline_seq_time"] > 0].copy()

    df["implementation"] = pd.Categorical(
        df["implementation"],
        categories=IMPLEMENTATION_ORDER,
        ordered=True
    )

    df["label"] = df["implementation"].map(IMPLEMENTATION_LABELS)
    df["mteps"] = (df["edges"] / df["runtime"]) / 1e6

    return df.sort_values(["file", "implementation"])


def aggregate_runs(df):
    grouped = (
        df.groupby(
            ["file", "graph_type", "nodes", "edges", "implementation", "label"],
            observed=True
        )
        .agg(
            avg_runtime=("runtime", "mean"),
            avg_speedup=("speedup_vs_seq", "mean"),
            avg_baseline_seq_time=("baseline_seq_time", "mean"),
            avg_mteps=("mteps", "mean"),
            trials=("trial_id", "nunique"),
        )
        .reset_index()
    )

    grouped["implementation"] = pd.Categorical(
        grouped["implementation"],
        categories=IMPLEMENTATION_ORDER,
        ordered=True
    )

    return grouped.sort_values(["file", "implementation"])


def save_avg_speedup_by_implementation(agg):
    df = agg[agg["implementation"] != "seq"].copy()

    summary = (
        df.groupby(["implementation", "label"], observed=True)
        .agg(avg_speedup=("avg_speedup", "mean"))
        .reset_index()
        .sort_values("implementation")
    )

    plt.figure(figsize=(10, 6))
    plt.bar(summary["label"], summary["avg_speedup"])
    plt.ylabel("Average Speedup vs Sequential")
    plt.xlabel("Implementation")
    plt.title("Average Speedup by Implementation")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "avg_speedup_by_implementation.png"), dpi=200)
    plt.close()


def save_speedup_by_dataset_and_implementation(agg):
    df = agg[agg["implementation"] != "seq"].copy()

    pivot = (
        df.pivot(index="file", columns="label", values="avg_speedup")
        .reindex(columns=[
            IMPLEMENTATION_LABELS["par_shared_lock"],
            IMPLEMENTATION_LABELS["par_shared_atomic"],
            IMPLEMENTATION_LABELS["par_local_static"],
            IMPLEMENTATION_LABELS["par_local_dynamic"],
        ])
    )

    plt.figure(figsize=(12, 7))
    pivot.plot(kind="bar", ax=plt.gca())
    plt.ylabel("Average Speedup vs Sequential")
    plt.xlabel("Dataset")
    plt.title("Speedup by Dataset and Implementation")
    plt.xticks(rotation=20, ha="right")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Implementation")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "speedup_by_dataset_and_implementation.png"), dpi=200)
    plt.close()


def save_avg_runtime_by_implementation(agg):
    summary = (
        agg.groupby(["implementation", "label"], observed=True)
        .agg(avg_runtime=("avg_runtime", "mean"))
        .reset_index()
        .sort_values("implementation")
    )

    plt.figure(figsize=(10, 6))
    plt.bar(summary["label"], summary["avg_runtime"])
    plt.ylabel("Average Runtime (seconds)")
    plt.xlabel("Implementation")
    plt.title("Average Runtime by Implementation")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "avg_runtime_by_implementation.png"), dpi=200)
    plt.close()


def save_runtime_vs_edges_best_impls(agg):
    keep = ["seq", "par_local_static", "par_local_dynamic"]
    df = agg[agg["implementation"].isin(keep)].copy()

    plt.figure(figsize=(10, 6))

    for impl in keep:
        subset = df[df["implementation"] == impl].sort_values("edges")
        plt.plot(
            subset["edges"],
            subset["avg_runtime"],
            marker="o",
            label=IMPLEMENTATION_LABELS[impl]
        )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Edges (log scale)")
    plt.ylabel("Average Runtime (seconds, log scale)")
    plt.title("Runtime vs Graph Size for Best Implementations")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "runtime_vs_edges_best_impls.png"), dpi=200)
    plt.close()


def save_avg_throughput_by_implementation(agg):
    summary = (
        agg.groupby(["implementation", "label"], observed=True)
        .agg(avg_mteps=("avg_mteps", "mean"))
        .reset_index()
        .sort_values("implementation")
    )

    plt.figure(figsize=(10, 6))
    plt.bar(summary["label"], summary["avg_mteps"])
    plt.ylabel("Average Throughput (MTEPS)")
    plt.xlabel("Implementation")
    plt.title("Average Throughput by Implementation")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "avg_throughput_by_implementation.png"), dpi=200)
    plt.close()

def save_speedup_vs_edges_by_implementation(agg):
    plt.figure(figsize=(10, 6))

    # Plot parallel implementations
    for impl in IMPLEMENTATION_ORDER:
        subset = agg[agg["implementation"] == impl].sort_values("edges")

        if subset.empty:
            continue

        if impl == "seq":
            # plot constant line at 1
            plt.plot(
                subset["edges"],
                [1.0] * len(subset),
                linestyle="--",
                label="Seq (baseline)"
            )
        else:
            plt.plot(
                subset["edges"],
                subset["avg_speedup"],
                marker="o",
                label=IMPLEMENTATION_LABELS[impl]
            )

    plt.xscale("log")
    plt.xlabel("Edges (log scale)")
    plt.ylabel("Speedup vs Sequential")
    plt.title("Speedup vs Graph Size by Implementation")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, "speedup_vs_edges_by_implementation.png"), dpi=200)
    plt.close()

def main():
    ensure_dirs()
    df = load_data()

    if df.empty:
        print("No matching rows found in results.csv")
        return

    agg = aggregate_runs(df)

    if agg.empty:
        print("No aggregated rows available for charting")
        return

    save_avg_speedup_by_implementation(agg)
    save_speedup_by_dataset_and_implementation(agg)
    save_avg_runtime_by_implementation(agg)
    save_runtime_vs_edges_best_impls(agg)
    save_avg_throughput_by_implementation(agg)
    save_speedup_vs_edges_by_implementation(agg)

    print(f"Saved charts to: {CHART_DIR}")


if __name__ == "__main__":
    main()