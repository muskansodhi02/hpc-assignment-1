import os
import statistics
import matplotlib.pyplot as plt

DATA_BCAST = r"data/data_bcast"
DATA_CHAIN = r"data/data_chain_study"
OUTDIR = r"plots"

os.makedirs(OUTDIR, exist_ok=True)


def parse_reprompi_file(path):
    """
    Returns:
        dict: message_size -> list of runtime values in microseconds
    """
    results = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "MPI_Bcast" not in line:
                continue

            parts = line.split()

            # Expected format:
            # test nrep count runtime_sec
            # MPI_Bcast 0 1000 0.0000355790
            try:
                size = int(parts[2])
                runtime_us = float(parts[3]) * 1_000_000
            except (IndexError, ValueError):
                continue

            results.setdefault(size, []).append(runtime_us)

    return results


def median_results(path):
    raw = parse_reprompi_file(path)
    return {size: statistics.median(times) for size, times in raw.items()}


def plot_exercise_5_1():
    layouts = ["1x32", "16x1", "16x2", "16x32"]

    for layout in layouts:
        files = {
            "MPI": os.path.join(DATA_BCAST, f"default_{layout}.txt"),
            "Knomial": os.path.join(DATA_BCAST, f"knomial_{layout}.txt"),
            "Chain": os.path.join(DATA_BCAST, f"chain_{layout}.txt"),
        }

        plt.figure(figsize=(8, 5))

        for label, path in files.items():
            data = median_results(path)
            sizes = sorted(data.keys())
            times = [data[s] for s in sizes]

            plt.plot(sizes, times, marker="o", label=label)

        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("Message size (bytes)")
        plt.ylabel("Median runtime (µs)")
        plt.title(f"MPI_Bcast Performance Comparison ({layout})")
        plt.legend()
        plt.grid(True, which="both")
        plt.tight_layout()

        out = os.path.join(OUTDIR, f"exercise_5_1_{layout}.png")
        plt.savefig(out, dpi=300)
        plt.close()

        print(f"Saved {out}")


def plot_exercise_5_2():
    message_sizes = {
        1048576: "1 MB",
        10485760: "10 MB",
    }

    chains = [1, 2, 4, 8]
    segments = [1024, 5120]

    default_data = median_results(os.path.join(DATA_CHAIN, "default_mpi.txt"))

    for size, size_label in message_sizes.items():
        labels = []
        values = []

        for chain in chains:
            for seg in segments:
                path = os.path.join(DATA_CHAIN, f"chain_{chain}_{seg}.txt")
                data = median_results(path)

                labels.append(f"{chain} chains\n{seg} B")
                values.append(data[size])

        labels.append("Default\nMPI_Bcast")
        values.append(default_data[size])

        plt.figure(figsize=(10, 5))
        plt.bar(labels, values)

        plt.xlabel("Chain configuration")
        plt.ylabel("Median runtime (µs)")
        plt.title(f"Chain Parameter Study for {size_label}")
        plt.grid(True, axis="y")
        plt.tight_layout()

        out = os.path.join(OUTDIR, f"exercise_5_2_chain_{size}.png")
        plt.savefig(out, dpi=300)
        plt.close()

        print(f"Saved {out}")


if __name__ == "__main__":
    plot_exercise_5_1()
    plot_exercise_5_2()
    print("All required plots generated.")