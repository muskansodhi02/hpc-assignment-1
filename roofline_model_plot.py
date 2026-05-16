import re
import matplotlib.pyplot as plt


# Paring the output of lscpu and babel to extract the necessary information for the roofline model:

def parse_lscpu(file):
    with open(file) as f:
        text = f.read()

    cores = int(re.search(r"CPU\(s\):\s+(\d+)", text).group(1))

    # frequency (fallback-safe)
    freq = re.search(r"CPU MHz:\s+([\d\.]+)", text)
    freq = float(freq.group(1)) if freq else None

    # detect AVX level
    if "avx512" in text.lower():
        flops_per_cycle = 32
    elif "avx2" in text.lower():
        flops_per_cycle = 16
    else:
        flops_per_cycle = 8  # conservative fallback

    return cores, freq, flops_per_cycle


def parse_babel(file):
    with open(file) as f:
        text = f.read()

    triad = float(re.search(r"Triad\s+([\d\.]+)", text).group(1))
    return triad  # MB/s


# to compute the peak GFLOP/s based on cores, frequency, and flops per cycle:

def compute_peak_gflops(cores, freq_mhz, flops_per_cycle):
    if freq_mhz is None:
        freq_mhz = 2000  # safe fallback

    # make sure frequency scaling is stable and realistic
    freq_ghz = freq_mhz / 1000

    return cores * freq_ghz * flops_per_cycle


# to load data for both machines and compute the necessary values for plotting:


laptop_lscpu = "lscpu_laptop.txt"
hydra_lscpu = "lscpu_hydra.txt"

laptop_babel = "babel_laptop.txt"
hydra_babel = "babel_hydra.txt"

machines = {
    "Laptop": (laptop_lscpu, laptop_babel),
    "Hydra": (hydra_lscpu, hydra_babel)
}

results = {}

for name, (cpu_file, babel_file) in machines.items():
    cores, freq, flops = parse_lscpu(cpu_file)
    bw = parse_babel(babel_file) / 1000  # MB/s → GB/s
    gflops = compute_peak_gflops(cores, freq, flops)

    results[name] = (bw, gflops)


# Plotting the roofline model for both machines using matplotlib:


def plot(name, bw, gflops):
    ai = [0.01, 10]

    plt.figure()
    plt.loglog(ai, [bw*x for x in ai], color="blue", label="Memory Bandwidth Roof")

    
    plt.hlines(
        gflops,
        xmin=min(ai),
        xmax=max(ai),
        color="red",
        linewidth=2,
        label="Compute Roof"
    )

    plt.scatter([1], [min(bw, gflops)], color="green", label="Measured Peak")

    plt.title(f"Roofline Model - {name}")
    plt.xlabel("Arithmetic Intensity (FLOPs/Byte)")
    plt.ylabel("Performance (GFLOP/s)")
    plt.legend()
    plt.grid(True, which="both")
    plt.show()


for name in results:
    plot(name, *results[name])