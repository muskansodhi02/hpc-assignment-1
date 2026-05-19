#!/bin/bash

# Whole Program AI Measurement Script (LIKWID + Stencil)

module load likwid
module load gcc

cd ~/Kernels/OPENMP/Stencil

# compile once
make clean
make STAR=1 stencil
make clean
make STAR=0 stencil

# output folder
OUTDIR=Whole_program_AI_LIKWID_results
mkdir -p $OUTDIR

# parameters
ARRAY_SIZES=(1000 50000)
ITERATIONS=(2 10)
THREADS=(2 16 32)

for TYPE in STAR COMPACT
do
    echo "=============================================="
    echo "Running stencil type: $TYPE"
    echo "=============================================="

    # compile correct version
    make clean

    if [ "$TYPE" == "STAR" ]; then
        make STAR=1 stencil
    else
        make STAR=0 stencil
    fi

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
                echo ""
                echo "Running: TYPE=$TYPE N=$N IT=$IT THREADS=$T"

                # Set LIKWID environment variables for thread binding
                export OMP_NUM_THREADS=$T
                export OMP_PROC_BIND=close
                export OMP_PLACES=cores

                echo "-------------------------------------" >> $OUTFILE
                echo "Iterations=$IT Threads=$T" >> $OUTFILE
                echo "-------------------------------------" >> $OUTFILE

                echo "[FLOPS_DP]" >> $OUTFILE
                likwid-perfctr -O -C 0-31 -g FLOPS_DP ./stencil $T $IT $N >> $OUTFILE

                echo "[MEM]" >> $OUTFILE
                likwid-perfctr -O -C 0-31 -g MEM ./stencil $T $IT $N >> $OUTFILE

            done
        done
    done
done

echo "All experiments completed. Results in $OUTDIR"