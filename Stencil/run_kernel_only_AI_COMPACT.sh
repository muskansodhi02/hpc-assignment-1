#!/bin/bash

# Kernel Only AI Measurement Script (LIKWID + Stencil)

module load likwid
module load gcc

# Inject Cluster LIKWID paths into the runtime environment to prevent errors
export PATH=/opt/spack/spack_git_updated/opt/spack/linux-debian11-skylake_avx512/gcc-10.2.1/likwid-5.2.2-eljbkkyevbvcpkln4hn6u2nmsnz76x2y/bin:$PATH
export LD_LIBRARY_PATH=/opt/spack/spack_git_updated/opt/spack/linux-debian11-skylake_avx512/gcc-10.2.1/likwid-5.2.2-eljbkkyevbvcpkln4hn6u2nmsnz76x2y/lib:$LD_LIBRARY_PATH
export LIKWID_FORCE=1

export OMP_ALLOC=INTERLEAVED
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

cd ~/Kernels/OPENMP/Stencil

# compile once
make clean
make STAR=0 stencil_likwid

# output folder
OUTDIR=Kernel_Only_AI_LIKWID_results
mkdir -p $OUTDIR

# parameters
TYPE="COMPACT"
ARRAY_SIZES=(1000 50000)
ITERATIONS=(2 10)
THREADS=(2 16 32)

echo "=============================================="
echo "Running stencil type: $TYPE"
echo "=============================================="

for N in "${ARRAY_SIZES[@]}"
do
    OUTFILE="$OUTDIR/${TYPE}_N${N}.txt"
    > $OUTFILE

    echo "Stencil Type: $TYPE" >> $OUTFILE
    echo "Array Size  : $N" >> $OUTFILE
    echo "=====================================" >> $OUTFILE

    for IT in "${ITERATIONS[@]}"
    do
        for T in "${THREADS[@]}"
        do
            # Skip the specific bottleneck combination
            if [ $N -eq 50000 ] && [ $IT -eq 10 ] && [ $T -eq 2 ]; then
                echo "Skipping bottleneck combo: N=$N IT=$IT THREADS=$T"
                continue
            fi

            echo ""
            echo "Running: TYPE=$TYPE N=$N IT=$IT THREADS=$T"

            # Set LIKWID environment variables for thread binding
            export OMP_NUM_THREADS=$T
            export OMP_PROC_BIND=close
            export OMP_PLACES=cores

            # Tells the LIKWID wrapper exactly how many threads to expect inside its 
            # monitored zones. 
            export LIKWID_THREADS=$T

            echo "-------------------------------------" >> $OUTFILE
            echo "Iterations=$IT Threads=$T" >> $OUTFILE
            echo "-------------------------------------" >> $OUTFILE

            echo "[FLOPS_DP]" >> $OUTFILE
            likwid-perfctr -m -C 0-31 -g FLOPS_DP ./stencil_likwid $T $IT $N >> $OUTFILE

            echo "[MEM]" >> $OUTFILE
            likwid-perfctr -m -C 0-31 -g MEM ./stencil_likwid $T $IT $N >> $OUTFILE

        done
    done
done

echo "All experiments completed. Results in $OUTDIR"