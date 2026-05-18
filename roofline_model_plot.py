import re
import matplotlib.pyplot as plt


# Parse lscpu and extract values:

def parse_lscpu(file):
    with open(file) as f:
        text = f.read()


    # physical cores  = sockets × cores per socket   
    sockets = int(re.search(r"Socket\(s\):\s+(\d+)", text).group(1))
    cores_per_socket = int(re.search(r"Core\(s\) per socket:\s+(\d+)", text).group(1))

    physical_cores = sockets * cores_per_socket

    # detect AVX level and compute FLOPs/cycle
    # NOTE: derived from SIMD width + FMA units
    flags = text.lower()

    if "avx512" in flags:
        # 512-bit SIMD = 8 doubles per vector
        # 2 FLOPs per FMA × 2 FMA units (Skylake-SP model)
        flops_per_cycle = 32
        instruction_set = "AVX-512 (8 doubles × 2 FLOPs × 2 FMA units)"

    elif "avx2" in flags:
        # 256-bit SIMD = 4 doubles per vector
        # 2 FLOPs per FMA × 2 FMA units
        flops_per_cycle = 16
        instruction_set = "AVX2 (4 doubles × 2 FLOPs × 2 FMA units)"

    else:
        flops_per_cycle = 8
        instruction_set = "SSE/Other (fallback model)"

    return physical_cores, flops_per_cycle, instruction_set


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
    "Laptop": 2300,   # 2.30 GHz sustained turbo frequency (from lscpu)
    "Hydra": 2100     # 2.10 GHz base all-core frequency (from lscpu)
}


# Compute theoretical peak GFLOP/s

def compute_peak_gflops(cores, freq_mhz, flops_per_cycle):

    # convert MHz → GHz
    freq_ghz = freq_mhz / 1000.0

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
    bw = parse_babel(babel_file) / 1e3

    # theoretical compute roof
    gflops = compute_peak_gflops(cores, FREQS[name], flops)

    results[name] = (bw, gflops)

    print(f"{name} Roofline Parameters===============================")

    print(f"Physical cores      : {cores}")
    print(f"Frequency (MHz)     : {FREQS[name]}")
    print(f"Instruction set     : {instruction_set}")
    print(f"FLOPs/cycle model   : {flops}")

    print("\nTheoretical Peak GFLOP/s Calculation:")
    print(f"GFLOP/s = {cores} × ({FREQS[name]}/1e3) × {flops}")

    print(f"Peak Compute Roof   : {gflops:.2f} GFLOP/s")
    print(f"Memory Bandwidth    : {bw:.2f} GB/s")


# Roofline plot for each machine:

def plot(name, bw, gflops):

    ai = [0.01, 0.1, 1, 10, 100]

    memory_perf = [bw * x for x in ai]

    plt.figure(figsize=(8, 6))

    # memory roof
    plt.loglog(ai, memory_perf, color="blue", label="Memory Bandwidth Roof")

    # compute roof 
    plt.loglog(ai, [gflops] * len(ai), color="red", label="Compute Roof")

    # ridge point
    ridge_ai = gflops / bw if bw > 0 else 0

    plt.scatter([ridge_ai], [gflops], color="black", s=100, label="Ridge Point")

    plt.title(f"Roofline Model - {name}")
    plt.xlabel("Arithmetic Intensity (FLOPs/Byte)")
    plt.ylabel("Performance (GFLOP/s)")

    plt.grid(True, which="both")
    plt.legend()

    plt.show()


for name in results:
    plot(name, *results[name])


# Comparison plot:

machine_names = list(results.keys())

bandwidths = [results[m][0] for m in machine_names]
gflops_values = [results[m][1] for m in machine_names]

x = range(len(machine_names))

plt.figure(figsize=(8, 6))

plt.bar([i - 0.2 for i in x], bandwidths, width=0.4, color="green", label="Memory Bandwidth (GB/s)")
plt.bar([i + 0.2 for i in x], gflops_values, width=0.4, color="red", label="Peak GFLOP/s")

plt.xticks(x, machine_names)
plt.ylabel("Performance")
plt.title("Comparison of Laptop and Hydra")

plt.legend()
plt.grid(True)

plt.show()