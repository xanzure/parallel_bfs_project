import os
import subprocess
import time
import csv
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "datasets")
BIN_DIR = os.path.join(ROOT, "bin")
RESULTS_DIR = os.path.join(ROOT, "results")
RESULTS_CSV = os.path.join(RESULTS_DIR, "results.csv")

IMPLEMENTATIONS = [
    {
        "name": "seq",
        "source": "bfs_seq.cpp",
        "exe": os.path.join(BIN_DIR, "bfs_seq"),
        "parallel": False,
    },
    {
        "name": "par_shared_lock",
        "source": "bfs_par_shared_lock.cpp",
        "exe": os.path.join(BIN_DIR, "bfs_par_shared_lock"),
        "parallel": True,
    },
    {
        "name": "par_shared_atomic",
        "source": "bfs_par_shared_atomic.cpp",
        "exe": os.path.join(BIN_DIR, "bfs_par_shared_atomic"),
        "parallel": True,
    },
    {
        "name": "par_local_static",
        "source": "bfs_par_local_static.cpp",
        "exe": os.path.join(BIN_DIR, "bfs_par_local_static"),
        "parallel": True,
    },
    {
        "name": "par_local_dynamic",
        "source": "bfs_par_local_dynamic.cpp",
        "exe": os.path.join(BIN_DIR, "bfs_par_local_dynamic"),
        "parallel": True,
    },
]


def compile_programs():
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for impl in IMPLEMENTATIONS:
        cmd = [
            "g++",
            "-std=c++17",
            os.path.join(ROOT, "src", "graph.cpp"),
            os.path.join(ROOT, "src", impl["source"]),
            "-o",
            impl["exe"],
        ]

        if impl["parallel"]:
            cmd.insert(2, "-fopenmp")

        subprocess.run(cmd, check=True)


def read_graph_info(filepath):
    with open(filepath, "r") as f:
        n, m = map(int, f.readline().split())
    return n, m


def run_program(exe, filepath, undirected):
    start = time.perf_counter()
    result = subprocess.run(
        [exe, filepath, str(int(undirected))],
        capture_output=True,
        text=True,
        check=True
    )
    end = time.perf_counter()
    return result.stdout.strip(), end - start


def append_results(rows):
    file_exists = os.path.exists(RESULTS_CSV)

    with open(RESULTS_CSV, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow([
                "trial_id",
                "timestamp",
                "file",
                "graph_type",
                "nodes",
                "edges",
                "implementation",
                "runtime",
                "baseline_seq_time",
                "speedup_vs_seq",
                "checksum",
                "match_seq",
            ])

        writer.writerows(rows)


def main():
    compile_programs()

    trial_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().isoformat(timespec="seconds")

    rows_to_append = []
    speedup_sums = {}
    speedup_counts = {}

    print(
        f"{'Test':<28} {'Impl':<18} {'Type':<12} {'Nodes':>10} {'Edges':>12} "
        f"{'Time':>10} {'Speedup':>10} {'OK':>6}"
    )
    print("-" * 115)

    for subdir in ["undirected", "directed"]:
        dir_path = os.path.join(DATA_DIR, subdir)

        if not os.path.isdir(dir_path):
            continue

        files = sorted(f for f in os.listdir(dir_path) if f.endswith(".txt"))
        undirected_flag = (subdir == "undirected")

        for f in files:
            path = os.path.join(dir_path, f)
            n, m = read_graph_info(path)

            seq_impl = IMPLEMENTATIONS[0]
            seq_out, seq_time = run_program(seq_impl["exe"], path, undirected_flag)

            rows_to_append.append([
                trial_id,
                timestamp,
                f,
                subdir,
                n,
                m,
                seq_impl["name"],
                seq_time,
                seq_time,
                1.0,
                seq_out,
                True,
            ])

            print(
                f"{f:<28} {seq_impl['name']:<18} {subdir:<12} {n:>10} {m:>12} "
                f"{seq_time:>10.6f} {1.00:>10.2f} {str(True):>6}"
            )

            for impl in IMPLEMENTATIONS[1:]:
                out, runtime = run_program(impl["exe"], path, undirected_flag)
                match = (out == seq_out)
                speedup = (seq_time / runtime) if runtime > 0 else float("inf")

                rows_to_append.append([
                    trial_id,
                    timestamp,
                    f,
                    subdir,
                    n,
                    m,
                    impl["name"],
                    runtime,
                    seq_time,
                    speedup,
                    out,
                    match,
                ])

                speedup_sums[impl["name"]] = speedup_sums.get(impl["name"], 0.0) + speedup
                speedup_counts[impl["name"]] = speedup_counts.get(impl["name"], 0) + 1

                print(
                    f"{f:<28} {impl['name']:<18} {subdir:<12} {n:>10} {m:>12} "
                    f"{runtime:>10.6f} {speedup:>10.2f} {str(match):>6}"
                )

    append_results(rows_to_append)

    print("-" * 115)
    print("Average speedup vs sequential:")
    for impl in IMPLEMENTATIONS[1:]:
        name = impl["name"]
        count = speedup_counts.get(name, 0)
        avg = (speedup_sums[name] / count) if count > 0 else 0.0
        print(f"  {name:<18} {avg:>10.2f}x")

    print(f"\nAppended results to: {RESULTS_CSV}")
    print(f"Trial ID: {trial_id}")


if __name__ == "__main__":
    main()