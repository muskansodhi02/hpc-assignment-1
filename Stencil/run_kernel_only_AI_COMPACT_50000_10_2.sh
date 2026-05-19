#!/bin/bash

# Kernel Only AI Measurement Script (Bottleneck Isolated Run)

module load likwid
module load gcc

# Inject Cluster LIKWID paths into the runtime environment to prevent errors
export PATH=/opt/spack/spack_git_updated/opt/spack/linux-debian11-skylake_avx512/gcc-10.2.1/likwid-5.2.2-eljbkkyevbvcpkln4hn6u2nmsnz76x2y/bin:$PATH
export LD_LIBRARY_PATH=/opt/spack/spack_git_updated/opt/spack/linux-debian11-skylake_avx512/gcc-10.2.1/likwid-5.2.2-eljbkkyevbvcpkln4hn6u2nmsnz76x2y/lib:$LD_LIBRARY_PATH
export LIKWID_FORCE=1

# Memory and Threading environment
export OMP_ALLOC=INTERLEAVED
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

cd ~/Kernels/OPENMP/Stencil

# compile (same as main script)
make clean
make STAR=0 stencil_likwid

# output folder
OUTDIR=Kernel_Only_AI_LIKWID_results
mkdir -p $OUTDIR

# Parameters for the bottleneck run
TYPE="COMPACT"
N=50000
IT=10
T=2

OUTFILE="$OUTDIR/${TYPE}_N${N}_IT${IT}_T${T}.txt"

echo "=============================================="
echo "Running Stencil type: TYPE=$TYPE N=$N IT=$IT THREADS=$T"
echo "=============================================="

# We append to the existing file so it fits right back into the main results
echo "" >> $OUTFILE
echo "-------------------------------------" >> $OUTFILE
echo "Iterations=$IT Threads=$T" >> $OUTFILE
echo "-------------------------------------" >> $OUTFILE

# Set LIKWID environment variables
export OMP_NUM_THREADS=$T
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export LIKWID_THREADS=$T

echo "[FLOPS_DP]" >> $OUTFILE
likwid-perfctr -m -C 0-31 -g FLOPS_DP ./stencil_likwid $T $IT $N >> $OUTFILE

echo "[MEM]" >> $OUTFILE
likwid-perfctr -m -C 0-31 -g MEM ./stencil_likwid $T $IT $N >> $OUTFILE

echo "All experiments completed. Results in $OUTDIR."