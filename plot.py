import matplotlib.pyplot as plt
import re
import os

def parse_file(path):
    sizes = []
    times = []
    with open(path) as f:
        for line in f:
            if "MPI_Bcast" in line and not line.startswith("#"):
                parts = line.split()
                sizes.append(int(parts[2]))
                times.append(float(parts[3]))
    return sizes, times

def plot_layout(layout):
    base = "data/data_bcast"
    files = {
        "MPI": f"{base}/default_{layout}.txt",
        "Knomial": f"{base}/knomial_{layout}.txt",
        "Chain": f"{base}/chain_{layout}.txt"
    }

    plt.figure()
    for label, file in files.items():
        sizes, times = parse_file(file)
        plt.plot(sizes, times, marker='o', label=label)

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Message size (bytes)")
    plt.ylabel("Runtime (s)")
    plt.title(f"Broadcast Performance ({layout})")
    plt.legend()
    plt.grid()
    plt.savefig(f"plot_{layout}.png")
    plt.close()

layouts = ["1x32", "16x1", "16x2", "16x32"]

for l in layouts:
    plot_layout(l)

print("Plots generated.")
