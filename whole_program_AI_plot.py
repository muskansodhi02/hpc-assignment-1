import re
import os
import matplotlib.pyplot as plt


# Hydra Roofline params from Ex 1
HYDRA_BW = 72.99       # GB/s
HYDRA_GFLOPS = 1075.2  # GFLOP/s


RESULT_DIR = "results"


# -----------------------------
# PARSERS (FIXED FOR LIKWID)
# -----------------------------

def extract_flops(file_path):
    with open(file_path, "r") as f:
        text = f.read()

    # LIKWID format:
    # Rate (MFlops/s): XXXX
    match = re.search(r"Rate\s+\(MFlops/s\):\s+([0-9]+\.[0-9]+)", text)

    if match:
        return float(match.group(1)) / 1000.0  # GFLOP/s

    return None


def extract_memory(file_path):
    with open(file_path, "r") as f:
        text = f.read()

    # LIKWID format:
    # Memory bandwidth [MBytes/s] XXXX
    match = re.search(r"Memory bandwidth\s+\[MBytes/s\]\s+([0-9]+\.[0-9]+)", text)

    if match:
        return float(match.group(1)) / 1000.0  # GB/s

    return None


# -----------------------------
# AI COMPUTATION
# -----------------------------

def compute_ai(flops_gflops, mem_gbs):
    if flops_gflops is None or mem_gbs is None:
        return None
    return flops_gflops / mem_gbs


# -----------------------------
# ROOFLINE PLOT
# -----------------------------

def roofline_plot(stencil_type, dimension, data_points):

    plt.figure(figsize=(9, 7))

    ai_range = [0.01, 0.1, 1, 10, 100]

    # memory roof
    mem_roof = [HYDRA_BW * x for x in ai_range]
    plt.loglog(ai_range, mem_roof, label="Memory Bandwidth Roof")

    # compute roof
    plt.loglog(ai_range, [HYDRA_GFLOPS] * len(ai_range),
               label="Compute Roof")

    markers = {2: "o", 16: "s", 32: "^"}
    colors = {2: "blue", 10: "red"}

    for p in data_points:

        if p["ai"] is None:
            continue

        plt.scatter(
            p["ai"],
            p["performance"],
            marker=markers[p["threads"]],
            color=colors[p["iterations"]],
            s=120,
            label=f"t={p['threads']}, it={p['iterations']}"
        )

    # remove duplicate legend entries
    handles, labels = plt.gca().get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    plt.legend(unique.values(), unique.keys())

    plt.xlabel("Arithmetic Intensity (FLOPs/Byte)")
    plt.ylabel("Performance (GFLOP/s)")
    plt.title(f"{stencil_type} stencil - {dimension}")
    plt.grid(True, which="both")

    plt.show()


# -----------------------------
# MAIN LOOP
# -----------------------------

dimensions = [1000, 50000]
stencils = ["star", "compact"]
iterations_list = [2, 10]
threads_list = [2, 16, 32]


for stencil in stencils:
    for dim in dimensions:

        data_points = []

        for it in iterations_list:
            for th in threads_list:

                flops_file = f"{RESULT_DIR}/{stencil}_d{dim}_i{it}_t{th}_flops.txt"
                mem_file = f"{RESULT_DIR}/{stencil}_d{dim}_i{it}_t{th}_mem.txt"

                if not os.path.exists(flops_file) or not os.path.exists(mem_file):
                    continue

                flops = extract_flops(flops_file)
                mem = extract_memory(mem_file)

                ai = compute_ai(flops, mem)

                data_points.append({
                    "ai": ai,
                    "performance": flops,
                    "threads": th,
                    "iterations": it
                })

                print(f"\n{stencil} dim={dim} it={it} t={th}")
                print(f"FLOPs (GFLOP/s): {flops}")
                print(f"Mem  (GB/s):     {mem}")
                print(f"AI:              {ai}")

        roofline_plot(stencil, dim, data_points)