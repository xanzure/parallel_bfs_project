import os
import subprocess
import time
import csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
BIN_DIR = os.path.join(ROOT, "bin")
RESULTS_DIR = os.path.join(ROOT, "results")

SEQ_EXE = os.path.join(BIN_DIR, "bfs_seq")
PAR_EXE = os.path.join(BIN_DIR, "bfs_parallel")

def compile_programs():
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    subprocess.run(
        ["g++", "-std=c++17",
         os.path.join(ROOT, "src", "graph.cpp"),
         os.path.join(ROOT, "src", "bfs_seq.cpp"),
         "-o", SEQ_EXE],
        check=True
    )

    subprocess.run(
        ["g++", "-std=c++17", "-fopenmp",
         os.path.join(ROOT, "src", "graph.cpp"),
         os.path.join(ROOT, "src", "bfs_parallel.cpp"),
         "-o", PAR_EXE],
        check=True
    )

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

def main():
    compile_programs()
    results = []

    print(f"{'Test':<20} {'Type':<12} {'Nodes':>8} {'Edges':>8} {'Seq':>10} {'Par':>10} {'Speedup':>10} {'OK':>6}")
    print("-" * 95)

    for subdir in ["undirected", "directed"]:
        dir_path = os.path.join(DATA_DIR, subdir)

        if not os.path.isdir(dir_path):
            continue

        files = sorted(f for f in os.listdir(dir_path) if f.endswith(".txt"))
        undirected_flag = (subdir == "undirected")

        for f in files:
            path = os.path.join(dir_path, f)
            n, m = read_graph_info(path)

            seq_out, t_seq = run_program(SEQ_EXE, path, undirected_flag)
            par_out, t_par = run_program(PAR_EXE, path, undirected_flag)

            ok = (seq_out == par_out)
            speedup = (t_seq / t_par) if t_par > 0 else float("inf")

            results.append([f, subdir, n, m, t_seq, t_par, speedup, ok])

            print(f"{f:<20} {subdir:<12} {n:>8} {m:>8} {t_seq:>10.6f} {t_par:>10.6f} {speedup:>10.2f} {str(ok):>6}")

    output_file = os.path.join(RESULTS_DIR, "results.csv")
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file", "graph_type", "nodes", "edges", "seq_time", "par_time", "speedup", "match"])
        writer.writerows(results)

    avg_speedup = sum(r[6] for r in results) / len(results) if results else 0

    print("-" * 95)
    print(f"{'Average Speedup':<71} {avg_speedup:>10.2f}x")
    print(f"\nSaved results to: {output_file}")

if __name__ == "__main__":
    main()