import os
import re
import numpy as np
import matplotlib.pyplot as plt


# Configuration & Infrastructure Parameters (From Exercise 1)

RESULT_DIR = "Whole_program_AI_LIKWID_results"

# Hydra Cluster Node Specifications
HYDRA_MEM_BANDWIDTH = 95.15   # GB/s
HYDRA_COMPUTE_ROOF  = 2150.40  # GFLOP/s

# Marker mapping per task specifications: different symbols for different (Iterations, Threads)
MARKER_MAP = {
    (2, 2):   {'marker': 'o', 'color': '#1f77b4', 'size': 13}, # Large Circle Blue
    (2, 16):  {'marker': 's', 'color': '#ff7f0e', 'size': 11}, # Med Square Orange
    (2, 32):  {'marker': '^', 'color': '#2ca02c', 'size': 9},  # Small Triangle Green
    (10, 2):  {'marker': 'v', 'color': '#d62728', 'size': 13}, # Large Inv-Triangle Red
    (10, 16): {'marker': 'D', 'color': '#9467bd', 'size': 11}, # Med Diamond Purple
    (10, 32): {'marker': 'X', 'color': '#8c564b', 'size': 9}   # Small Thick X Brown
}

# Target file list
target_files = [
    "STAR_N50000.txt",
    "STAR_N1000.txt",
    "COMPACT_N50000.txt",
    "COMPACT_N1000.txt"
]


# LIKWID parsing function to extract FLOPs, Memory Volume, and Runtime for each configuration block

def parse_likwid_file(filepath):
    """
    Parses a combined LIKWID log file and extracts metrics for each configuration blocks.
    """
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found. Skipping...")
        return {}

    with open(filepath, 'r') as f:
        content = f.read()

    # Split the file into configuration blocks: e.g., "Iterations=2 Threads=2"
    block_splits = re.split(r'-+\s*Iterations=(\d+)\s+Threads=(\d+)\s*-+', content)
    
    # The first element is header garbage before any block definition
    header = block_splits[0]
    data_blocks = block_splits[1:]
    
    results = {}
    
    # Iterate through extracted text blocks (3 items per iteration: iters, threads, text_body)
    for i in range(0, len(data_blocks), 3):
        iters = int(data_blocks[i])
        threads = int(data_blocks[i+1])
        block_text = data_blocks[i+2]
        
        # Isolation step: Extract FLOPS_DP and MEM sub-groups within this specific block
        flops_section = ""
        mem_section = ""
        
        sections = re.split(r'\[(FLOPS_DP|MEM)\]', block_text)
        for j in range(1, len(sections), 2):
            sec_name = sections[j]
            sec_body = sections[j+1]
            if sec_name == "FLOPS_DP":
                flops_section = sec_body
            elif sec_name == "MEM":
                mem_section = sec_body

        # Parse FLOPs counters
        # Extract the sum value for 128B (vectorized double) and scalar double instructions
        p128 = re.search(r'FP_ARITH_INST_RETIRED_128B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
        p256 = re.search(r'FP_ARITH_INST_RETIRED_256B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
        p512 = re.search(r'FP_ARITH_INST_RETIRED_512B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
        scalar = re.search(r'FP_ARITH_INST_RETIRED_SCALAR_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
        
        inst_128 = int(p128.group(1)) if p128 else 0
        inst_256 = int(p256.group(1)) if p256 else 0
        inst_512 = int(p512.group(1)) if p512 else 0
        inst_scalar = int(scalar.group(1)) if scalar else 0
        
        # Calculate overall exact Double-Precision FLOPs based on vector widths
        total_flops = (inst_128 * 2) + (inst_256 * 4) + (inst_512 * 8) + inst_scalar

        # Parse Memory Volume & Execution Times
        # Extract the aggregated Memory data volume string
        vol_match = re.search(r'Memory data volume \[GBytes\] STAT\s*\|\s*([\d\.]+)', mem_section)
        # Extract execution runtime to compute real GFLOP/s performance
        time_match = re.search(r'Runtime \(RDTSC\) \[s\] STAT\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*([\d\.]+)', mem_section)
        
        mem_gbytes = float(vol_match.group(1)) if vol_match else None
        runtime_sec = float(time_match.group(1)) if time_match else None
        
        if total_flops > 0 and mem_gbytes and runtime_sec:
            total_bytes = mem_gbytes * 1e9
            ai = total_flops / total_bytes
            gflops = (total_flops / 1e9) / runtime_sec
            
            results[(iters, threads)] = {
                'flops': total_flops,
                'bytes': total_bytes,
                'ai': ai,
                'gflops': gflops,
                'runtime': runtime_sec,
                'raw_flops_g': total_flops / 1e9,      
                'raw_mem_gb': mem_gbytes               
            }
            
    return results

# Pipeline to process all target files, extract metrics, and print a summary table

all_data = {}

print("="*125)
print(f"{'STENCIL EXECUTION METRICS SUMMARY TABLE (FROM LIKWID FLOPS_DP & MEM GROUPS)':^125}")
print("="*125)
print(f"{'Stencil Type':<13} | {'Grid Size':<9} | {'Iters':<5} | {'Threads':<7} | {'Runtime (s)':<12} | {'[FLOPS_DP] GFLOPs':<17} | {'[MEM] Volume (GB)':<17} | {'AI (FLOP/B)':<11} | {'Perf (GFLOP/s)':<14}")
print("-"*125)

for filename in target_files:
    filepath = os.path.join(RESULT_DIR, filename)
    parsed_meta = parse_likwid_file(filepath)
    
    if not parsed_meta:
        continue
        
    all_data[filename] = parsed_meta
    
    # Destructure the raw file string to map structural size and layout types independently
    file_parts = filename.replace(".txt", "").split("_N")
    stencil_type = file_parts[0]
    grid_size = f"N={file_parts[1]}"
    
    for (iters, threads), metrics in sorted(parsed_meta.items()):
        print(f"{stencil_type:<13} | {grid_size:<9} | {iters:<5} | {threads:<7} | {metrics['runtime']:<12.4f} | {metrics['raw_flops_g']:<17.3f} | {metrics['raw_mem_gb']:<17.3f} | {metrics['ai']:<11.4f} | {metrics['gflops']:<14.2f}")

print("="*125)

# Roofline Plotting for each configuration file with enhanced visualization features

# Generate a wide range for Arithmetic Intensity to draw extended roofs
ai_axis = np.logspace(-2, 4, 4000)

for filename, configurations in all_data.items():
    file_parts = filename.replace(".txt", "").split("_N")
    stencil_type = file_parts[0]
    grid_size = f"N={file_parts[1]}"
    title_clean = filename.replace(".txt", "").replace("_", " - ")
    
    plt.figure(figsize=(10, 7))
    
    # 1. Draw independent boundary cielings for Memory and Compute
    # Slanted Theoretical Memory Boundary (Memory Roof)
    plt.loglog(ai_axis, ai_axis * HYDRA_MEM_BANDWIDTH, 
               color='#1f77b4', linestyle='--', linewidth=1.2, alpha=0.6,
               label=f'Memory Roof ({HYDRA_MEM_BANDWIDTH} GB/s)')
    
    # Horizontal Theoretical Compute Boundary (Compute Roof)
    plt.axhline(y=HYDRA_COMPUTE_ROOF, 
                color='#d62728', linestyle='--', linewidth=1.2, alpha=0.6,
                label=f'Compute Roof ({HYDRA_COMPUTE_ROOF} GFLOP/s)')
    
    # The combined active boundary (The "Roofline" itself)
    roofline_boundary = np.minimum(HYDRA_COMPUTE_ROOF, ai_axis * HYDRA_MEM_BANDWIDTH)
    plt.loglog(ai_axis, roofline_boundary, color='black', linewidth=2.5, 
               label='Attainable Performance Bound')

    # 2. Mark the Ridge Point where the Memory Roof and Compute Roof intersect
    ridge_point = HYDRA_COMPUTE_ROOF / HYDRA_MEM_BANDWIDTH  # ~22.60 FLOP/Byte
    
    # Draw a vertical indicator line down to the X-axis
    plt.axvline(x=ridge_point, color='purple', linestyle=':', linewidth=2, alpha=0.7)
    
    # Place a visible marker point exactly at the intersection point
    plt.plot(ridge_point, HYDRA_COMPUTE_ROOF, marker='X', color='purple', markersize=12, 
             label=f'Hardware Ridge Point ({ridge_point:.2f} FLOP/B)')

    # Draw and write the ridge point value directly text-aligned along the vertical tracking line
    plt.text(ridge_point * 1.1, 1.2, f'Ridge Point = {ridge_point:.2f} FLOP/B', 
             color='purple', rotation=90, verticalalignment='bottom', fontsize=9, fontweight='bold')

    # 3. Overlay the actual performance data points for each configuration with distinct markers and colors
    for (iters, threads), data in configurations.items():
        cfg_key = (iters, threads)
        if cfg_key in MARKER_MAP:
            marker_style = MARKER_MAP[cfg_key]['marker']
            color_style  = MARKER_MAP[cfg_key]['color']
            marker_size  = MARKER_MAP[cfg_key]['size']
            
            plt.plot(
                data['ai'], data['gflops'],
                marker=marker_style, 
                color=color_style,
                markersize=marker_size, 
                markeredgecolor='black',
                markeredgewidth=1.2,
                alpha=0.85, # Adds light transparency so stacked boundaries are exposed
                linestyle='', 
                label=f"Iters={iters}, Threads={threads} ({data['gflops']:.1f} GFLOP/s)"
            )

    # Graphical layout adjustments
    plt.title(f"Hydra Node Roofline Analysis\nKernel: {title_clean}", fontsize=12, fontweight='bold')
    plt.xlabel('Arithmetic Intensity (FLOP/Byte)', fontsize=11)
    plt.ylabel('Performance (GFLOP/s)', fontsize=11)
    
    # Expanded boundaries to prevent points with low memory footprints from being cropped off in plots
    plt.xlim(0.01, 2000)
    plt.ylim(0.05, 5000)
    
    plt.grid(True, which="both", ls="-", color='lightgray', alpha=0.5)
    
    # Placing legend with high contrast outline
    plt.legend(loc='upper left', fontsize=9, framealpha=0.9, facecolor='white', edgecolor='gray')
    
    # Save the output chart files
    out_img_name = f"roofline_{filename.replace('.txt', '')}.png"
    plt.tight_layout()
    plt.savefig(out_img_name, dpi=150)
    print(f"Generated Plot Asset successfully saved as: [ {out_img_name} ]")
    plt.show()
    plt.close()

print("\nAll tasks completed successfully!")