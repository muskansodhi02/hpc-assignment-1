import matplotlib.pyplot as plt
import os

def parse_file(path):
    data = {}
    with open(path) as f:
        for line in f:
            if "MPI_Bcast" in line and not line.startswith("#"):
                parts = line.split()
                size = int(parts[2])
                time = float(parts[3])
                data[size] = time
    return data

base = "data/data_chain_study"

# Load default
default = parse_file(f"{base}/default_mpi.txt")

chains = [1,2,4,8]
segs = [1024,5120]

for size in [1048576, 10485760]:
    labels = []
    values = []

    for c in chains:
        for s in segs:
            file = f"{base}/chain_{c}_{s}.txt"
            data = parse_file(file)
            labels.append(f"{c},{s}")
            values.append(data[size])

    # add default
    labels.append("MPI")
    values.append(default[size])

    plt.figure(figsize=(10,5))
    plt.bar(labels, values)
    plt.xticks(rotation=45)
    plt.ylabel("Runtime (s)")
    plt.title(f"Chain Parameter Study ({size} bytes)")
    plt.tight_layout()
    plt.savefig(f"chain_plot_{size}.png")
    plt.close()

print("Chain plots done")
