import os
import re
import numpy as np
import matplotlib.pyplot as plt

# Configuration & Infrastructure Parameters
RESULT_DIR = "Kernel_only_AI_LIKWID_results"
PLOT_OUTPUT_DIR = "Kernel_Only_AI_plots"

# Ensure the output directory for plots exists before execution
if not os.path.exists(PLOT_OUTPUT_DIR):
    os.makedirs(PLOT_OUTPUT_DIR)

# Hydra Cluster Node Specifications
HYDRA_MEM_BANDWIDTH = 95.15   # GB/s
HYDRA_COMPUTE_ROOF  = 2150.40  # GFLOP/s

# Marker mapping per task specifications
MARKER_MAP = {
    (2, 2):   {'marker': 'o', 'color': '#1f77b4', 'size': 13}, # Large Circle Blue
    (2, 16):  {'marker': 's', 'color': '#ff7f0e', 'size': 11}, # Med Square Orange
    (2, 32):  {'marker': '^', 'color': '#2ca02c', 'size': 9},  # Small Triangle Green
    (10, 2):  {'marker': 'v', 'color': '#d62728', 'size': 13}, # Large Inv-Triangle Red
    (10, 16): {'marker': 'D', 'color': '#9467bd', 'size': 11}, # Med Diamond Purple
    (10, 32): {'marker': 'X', 'color': '#8c564b', 'size': 9}   # Small Thick X Brown
}

# Explicit mapping to direct standalone custom files to their base logical group
# This ensures COMPACT_N50000_IT10_T2.txt is plotted inside the COMPACT_N50000 roofline chart!
CUSTOM_FILE_MAPPING = {
    "COMPACT_N50000_IT10_T2.txt": "COMPACT_N50000.txt"
}

# Baseline Target file list
target_files = [
    "STAR_N50000.txt",
    "STAR_N1000.txt",
    "COMPACT_N50000.txt",
    "COMPACT_N1000.txt",
    "COMPACT_N50000_IT10_T2.txt" # Added your standalone custom run file
]

def parse_likwid_file(filepath, filename):
    """
    Parses LIKWID log files. Handles standard combined block logs and standalone
    custom files missing internal iteration/thread block headers.
    """
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found. Skipping...")
        return {}

    with open(filepath, 'r') as f:
        content = f.read()

    results = {}
    
    # Check if the file contains the standard block separator header
    block_splits = re.split(r'-+\s*Iterations=(\d+)\s+Threads=(\d+)\s*-+', content)
    
    if len(block_splits) > 1:
        # Standard combined log file parsing logic
        data_blocks = block_splits[1:]
        for i in range(0, len(data_blocks), 3):
            iters = int(data_blocks[i])
            threads = int(data_blocks[i+1])
            block_text = data_blocks[i+2]
            metrics = parse_raw_block_text(block_text)
            if metrics:
                results[(iters, threads)] = metrics
    else:
        # Standalone custom run file handling logic (e.g., COMPACT_N50000_IT10_T2.txt)
        # Parse iters and threads directly out of the filename string using regex
        fn_match = re.search(r'_IT(\d+)_T(\d+)', filename)
        if fn_match:
            iters = int(fn_match.group(1))
            threads = int(fn_match.group(2))
            metrics = parse_raw_block_text(content)
            if metrics:
                results[(iters, threads)] = metrics
        else:
            print(f"Warning: Could not extract configurations from custom filename: {filename}")
            
    return results

def parse_raw_block_text(block_text):
    """
    Helper function extracting FLOPs, Memory Volume, and Runtime metrics out of raw LIKWID text blocks.
    """
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

    # Parse FLOPs counters from LIKWID STAT lines
    p128 = re.search(r'FP_ARITH_INST_RETIRED_128B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
    p256 = re.search(r'FP_ARITH_INST_RETIRED_256B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
    p512 = re.search(r'FP_ARITH_INST_RETIRED_512B_PACKED_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
    scalar = re.search(r'FP_ARITH_INST_RETIRED_SCALAR_DOUBLE STAT\s*\|\s*PMC\d\s*\|\s*(\d+)', flops_section)
    
    inst_128 = int(p128.group(1)) if p128 else 0
    inst_256 = int(p256.group(1)) if p256 else 0
    inst_512 = int(p512.group(1)) if p512 else 0
    inst_scalar = int(scalar.group(1)) if scalar else 0
    
    total_flops = (inst_128 * 2) + (inst_256 * 4) + (inst_512 * 8) + inst_scalar

    # Adaptive memory parser supporting both GBytes and MBytes metrics units scaling
    vol_match = re.search(r'Memory data volume \[GBytes\] STAT\s*\|\s*([\d\.]+)', mem_section)
    is_mbytes = False
    if not vol_match:
        vol_match = re.search(r'Memory data volume \[MBytes\] STAT\s*\|\s*([\d\.]+)', mem_section)
        if vol_match:
            is_mbytes = True

    time_match = re.search(r'Runtime \(RDTSC\) \[s\] STAT\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*([\d\.]+)', mem_section)
    
    mem_value = float(vol_match.group(1)) if vol_match else None
    runtime_sec = float(time_match.group(1)) if time_match else None
    
    if total_flops > 0 and mem_value and runtime_sec:
        total_bytes = mem_value * 1e6 if is_mbytes else mem_value * 1e9
        ai = total_flops / total_bytes
        gflops = (total_flops / 1e9) / runtime_sec
        
        return {
            'flops': total_flops,
            'bytes': total_bytes,
            'ai': ai,
            'gflops': gflops,
            'runtime': runtime_sec,
            'raw_flops_g': total_flops / 1e9,      
            'raw_mem_gb': total_bytes / 1e9              
        }
    return None


# Global Data Aggregator Setup
all_data = {}

print("="*125)
print(f"{'KERNEL-ONLY STENCIL METRICS SUMMARY TABLE (EXCLUDING SYSTEM INITIALIZATION TRAFFIC)':^125}")
print("="*125)
print(f"{'Stencil Type':<13} | {'Grid Size':<9} | {'Iters':<5} | {'Threads':<7} | {'Runtime (s)':<12} | {'[FLOPS_DP] GFLOPs':<17} | {'[MEM] Volume (GB)':<17} | {'AI (FLOP/B)':<11} | {'Perf (GFLOP/s)':<14}")
print("-"*125)

for filename in target_files:
    filepath = os.path.join(RESULT_DIR, filename)
    parsed_meta = parse_likwid_file(filepath, filename)
    
    if not parsed_meta:
        continue
    
    # Determine the structural plotting bucket target
    plot_bucket = CUSTOM_FILE_MAPPING.get(filename, filename)
    
    if plot_bucket not in all_data:
        all_data[plot_bucket] = {}
        
    # Merge configurations cleanly into the plotting target bucket
    all_data[plot_bucket].update(parsed_meta)
    
    # Visual stdout layout table generation strings
    file_parts = plot_bucket.replace(".txt", "").split("_N")
    stencil_type = file_parts[0]
    grid_size = f"N={file_parts[1]}"
    
    for (iters, threads), metrics in sorted(parsed_meta.items()):
        print(f"{stencil_type:<13} | {grid_size:<9} | {iters:<5} | {threads:<7} | {metrics['runtime']:<12.4f} | {metrics['raw_flops_g']:<17.3f} | {metrics['raw_mem_gb']:<17.6f} | {metrics['ai']:<11.4f} | {metrics['gflops']:<14.2f}")

print("="*125)


# Roofline Plot Processing
ai_axis = np.logspace(-2, 5, 5000)

for filename, configurations in all_data.items():
    file_parts = filename.replace(".txt", "").split("_N")
    title_clean = filename.replace(".txt", "").replace("_", " - ")
    
    plt.figure(figsize=(10, 7))
    
    # Draw Background Roof Infrastructure Lines
    plt.loglog(ai_axis, ai_axis * HYDRA_MEM_BANDWIDTH, 
                color='#1f77b4', linestyle='--', linewidth=1.2, alpha=0.6,
                label=f'Memory Roof ({HYDRA_MEM_BANDWIDTH} GB/s)')
    
    plt.axhline(y=HYDRA_COMPUTE_ROOF, 
                color='#d62728', linestyle='--', linewidth=1.2, alpha=0.6,
                label=f'Compute Roof ({HYDRA_COMPUTE_ROOF} GFLOP/s)')
    
    roofline_boundary = np.minimum(HYDRA_COMPUTE_ROOF, ai_axis * HYDRA_MEM_BANDWIDTH)
    plt.loglog(ai_axis, roofline_boundary, color='black', linewidth=2.5, label='Attainable Performance Bound')

    # Hardware Ridge Point Mapping
    ridge_point = HYDRA_COMPUTE_ROOF / HYDRA_MEM_BANDWIDTH
    plt.axvline(x=ridge_point, color='purple', linestyle=':', linewidth=2, alpha=0.7)
    plt.plot(ridge_point, HYDRA_COMPUTE_ROOF, marker='X', color='purple', markersize=12, 
             label=f'Hardware Ridge Point ({ridge_point:.2f} FLOP/B)')

    plt.text(ridge_point * 1.1, 0.1, f'Ridge Point = {ridge_point:.2f} FLOP/B', 
             color='purple', rotation=90, verticalalignment='bottom', fontsize=9, fontweight='bold')

    # Scatter Plotting Operational Profiles
    for (iters, threads), data in sorted(configurations.items()):
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
                alpha=0.85,
                linestyle='', 
                label=f"Iters={iters}, Threads={threads} ({data['gflops']:.1f} GFLOP/s)"
            )

    plt.title(f"Hydra Node Kernel-Only Roofline Analysis\nKernel: {title_clean}", fontsize=12, fontweight='bold')
    plt.xlabel('Arithmetic Intensity (FLOP/Byte)', fontsize=11)
    plt.ylabel('Performance (GFLOP/s)', fontsize=11)
    
    plt.xlim(0.01, 10000)
    plt.ylim(0.05, 5000)
    
    plt.grid(True, which="both", ls="-", color='lightgray', alpha=0.5)
    plt.legend(loc='upper left', fontsize=9, framealpha=0.9, facecolor='white', edgecolor='gray')
    
    # Save the output chart files inside the designated directory
    out_img_name = os.path.join(PLOT_OUTPUT_DIR, f"kernel_only_AI_{filename.replace('.txt', '')}.png")
    plt.tight_layout()
    plt.savefig(out_img_name, dpi=150)
    print(f"Generated Plot Asset successfully saved as: [ {out_img_name} ]")
    plt.show()
    plt.close()

print("\nAll tasks completed successfully!")