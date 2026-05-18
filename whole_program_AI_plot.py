import os
import re
import matplotlib.pyplot as plt

# -------------------------------
# Roofline parameters (Ex 1)
# -------------------------------
PEAK_GFLOPS = 2150.40   # Hydra compute peak
MEM_BW = 95.15          # GB/s

RESULT_DIR = "Whole_program_AI_LIKWID_results"

# -------------------------------
# Extract FLOPS + MEM + AI + PERF
# -------------------------------
def parse_file(filepath):
    results = []

    with open(filepath, "r") as f:
        content = f.read()

    # Split runs
    blocks = content.split("Iterations=")

    for b in blocks[1:]:
        try:
            it_match = re.search(r"Iterations=(\d+)", "Iterations=" + b)
            th_match = re.search(r"Threads=(\d+)", b)

            # LIKWID values
            flops_match = re.search(r"DP \[MFLOP/s\][^\n]*([\d\.]+)", b)
            mem_match = re.search(r"Memory bandwidth[^\n]*([\d\.]+)", b)

            if not (it_match and th_match and flops_match and mem_match):
                continue

            it = int(it_match.group(1))
            th = int(th_match.group(1))

            flops = float(flops_match.group(1))   # MFLOP/s
            mem = float(mem_match.group(1))       # GB/s

            # Convert units
            flops_g = flops / 1000.0  # GFLOP/s

            # -------------------------------
            # Roofline values
            # -------------------------------
            ai = flops_g / mem if mem > 0 else 0.0   # FLOP/byte
            perf = flops_g                           # GFLOP/s

            results.append((it, th, ai, perf))

        except:
            continue

    return results


# -------------------------------
# Roofline curve
# -------------------------------
def plot_roofline(ax, title):
    import numpy as np

    x = np.logspace(-3, 2, 200)
    y = np.minimum(PEAK_GFLOPS, MEM_BW * x)

    ax.loglog(x, y, label="Roofline", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Arithmetic Intensity (FLOP/Byte)")
    ax.set_ylabel("Performance (GFLOP/s)")
    ax.grid(True, which="both")


# -------------------------------
# Load files
# -------------------------------
files = [f for f in os.listdir(RESULT_DIR) if f.endswith(".txt")]

data_map = {
    "STAR_N1000": [],
    "STAR_N50000": [],
    "COMPACT_N1000": [],
    "COMPACT_N50000": []
}

for f in files:
    path = os.path.join(RESULT_DIR, f)
    data = parse_file(path)

    if "STAR_N1000" in f:
        data_map["STAR_N1000"] = data
    elif "STAR_N50000" in f:
        data_map["STAR_N50000"] = data
    elif "COMPACT_N1000" in f:
        data_map["COMPACT_N1000"] = data
    elif "COMPACT_N50000" in f:
        data_map["COMPACT_N50000"] = data


# -------------------------------
# Plot setup
# -------------------------------
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

plots = {
    (0,0): "STAR_N1000",
    (0,1): "STAR_N50000",
    (1,0): "COMPACT_N1000",
    (1,1): "COMPACT_N50000"
}

colors = {2: "red", 16: "green", 32: "blue"}

# -------------------------------
# Draw plots
# -------------------------------
for (i, j), key in plots.items():

    ax = axs[i, j]
    plot_roofline(ax, key)

    for it, th, ai, perf in data_map[key]:
        ax.scatter(
            ai,
            perf,
            color=colors.get(th, "black"),
            label=f"it={it}, t={th}"
        )

    # remove duplicate legend entries
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=8)


plt.tight_layout()
plt.show()