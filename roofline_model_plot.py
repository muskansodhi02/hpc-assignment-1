import re
import matplotlib.pyplot as plt


# Parse lscpu and extract values:

def parse_lscpu(file):
    with open(file) as f:
        text = f.read()

    # logical cores (used for peak performance)
    cores = int(re.search(r"CPU\(s\):\s+(\d+)", text).group(1))

    # physical cores 
    physical_cores_match = re.search(r"Core\(s\) per socket:\s+(\d+)", text)

    if physical_cores_match:
        physical_cores = int(physical_cores_match.group(1))
    else:
        physical_cores = cores

    # detect AVX level and compute FLOPs/cycle
    flags = text.lower()

    if "avx512" in flags:
        flops_per_cycle = 32
        instruction_set = "AVX-512"

    elif "avx2" in flags:
        flops_per_cycle = 16
        instruction_set = "AVX2"

    else:
        flops_per_cycle = 8
        instruction_set = "SSE/Other"

    return cores, flops_per_cycle, instruction_set


# Parse BabelStream output 

def parse_babel(file):
    with open(file) as f:
        text = f.read()

    match = re.search(r"Triad\s+([\d\.]+)", text)
    if not match:
        raise ValueError("Triad not found in BabelStream output")

    triad = float(match.group(1))
    return triad  # MB/s


# Frequency values for each machine (in MHz)
FREQS = {
    "Laptop": 2300,   # MHz (base frequency)
    "Hydra": 2100     # MHz (Xeon base frequency)
}


# Compute theoretical peak GFLOP/s

def compute_peak_gflops(cores, freq_mhz, flops_per_cycle):

    # convert MHz → GHz
    freq_ghz = freq_mhz / 1000.0

    # Roofline peak performance model
    return cores * freq_ghz * flops_per_cycle


# Input files

laptop_lscpu = "lscpu_laptop.txt"
hydra_lscpu = "lscpu_hydra.txt"

laptop_babel = "babel_laptop.txt"
hydra_babel = "babel_hydra.txt"

machines = {
    "Laptop": (laptop_lscpu, laptop_babel),
    "Hydra": (hydra_lscpu, hydra_babel)
}

results = {}


# Data processing:

for name, (cpu_file, babel_file) in machines.items():

    cores, flops, instruction_set = parse_lscpu(cpu_file)

    # Convert MB/s → GB/s
    bw = parse_babel(babel_file) / 1000.0

    # theoretical compute roof
    gflops = compute_peak_gflops(cores, FREQS[name], flops)

    results[name] = (bw, gflops)

    
    print(f"{name} Roofline Parameters:")
  

    print(f"Logical cores       : {cores}")
    print(f"Frequency (MHz)     : {FREQS[name]}")
    print(f"Instruction set     : {instruction_set}")
    print(f"FLOPs/cycle         : {flops}")

    print("\nTheoretical Peak GFLOP/s Calculation:")
    print(f"GFLOP/s = {cores} × ({FREQS[name]}/1000) × {flops}")

    print(f"Peak Compute Roof   : {gflops:.2f} GFLOP/s")
    print(f"Memory Bandwidth    : {bw:.2f} GB/s")


# Roofline plot for each machine:

def plot(name, bw, gflops):

    ai = [0.01, 0.1, 1, 10, 100]

    memory_perf = [bw * x for x in ai]

    plt.figure(figsize=(8, 6))

    # memory roof
    plt.loglog(ai, memory_perf, label="Memory Bandwidth Roof", color="blue")

    # compute roof 
    plt.loglog(ai, [gflops] * len(ai), label="Compute Roof", color="red")

    # ridge point (where memory and compute roofs intersect)
    ridge_ai = gflops / bw if bw > 0 else 0

    plt.scatter([ridge_ai], [gflops], color="green", label="Ridge Point")

    plt.title(f"Roofline Model - {name}")
    plt.xlabel("Arithmetic Intensity (FLOPs/Byte)")
    plt.ylabel("Performance (GFLOP/s)")

    plt.grid(True, which="both")
    plt.legend()

    plt.show()


for name in results:
    plot(name, *results[name])


# Comparison plot of two machines:

machine_names = list(results.keys())

bandwidths = [results[m][0] for m in machine_names]
gflops_values = [results[m][1] for m in machine_names]

x = range(len(machine_names))

plt.figure(figsize=(8, 6))

plt.bar([i - 0.2 for i in x], bandwidths, width=0.4, label="Memory Bandwidth (GB/s)")
plt.bar([i + 0.2 for i in x], gflops_values, width=0.4, label="Peak GFLOP/s")

plt.xticks(x, machine_names)
plt.ylabel("Performance")
plt.title("Comparison of Laptop and Hydra")

plt.legend()
plt.grid(True)
plt.show()