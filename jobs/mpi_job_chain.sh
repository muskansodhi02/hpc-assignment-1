#! /bin/bash
#SBATCH -N 16
#SBATCH --ntasks-per-node=32
#SBATCH -t 5
#SBATCH -p q_student


spack load openmpi@4.1.6

# change this to your home directory, e.g., /home/student/hpc26sXX
HOMEDIR=/home/student/stester

REPROMPI_BIN=$HOMEDIR/bcast/reprompi-dev/build/bin
BCAST_LIB=$HOMEDIR/bcast/build

# don't modify these variables, they are used in the output file names
N=$SLURM_NNODES
n=$SLURM_NTASKS_PER_NODE

MSIZES="1048576,10485760"

srun $REPROMPI_BIN/mpibenchmark --msizes-list=$MSIZES --calls-list=MPI_Bcast --nrep=2000 --rt-bench-time-ms=2000 --proc-sync=roundtime > job_${N}_${n}_chain_test_default_${SLURM_JOB_ID}.dat

for c in 1 2 4 8; do
    for s in 1024 5120; do
    HPC_BCAST_CHAIN_NUM=$c HPC_BCAST_CHAIN_SEG=$s LD_PRELOAD=$BCAST_LIB/libbcast_chain.so \
    srun $REPROMPI_BIN/mpibenchmark --msizes-list=$MSIZES --calls-list=MPI_Bcast --nrep=2000 --rt-bench-time-ms=2000 --proc-sync=roundtime > job_${N}_${n}_chain_test_chain_${c}_${s}_${SLURM_JOB_ID}.dat
    done
done

