#! /bin/bash
#SBATCH -N 1
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

MSIZES="1,10,100,1000,10000,100000,1000000,10000000,100000000"

srun $REPROMPI_BIN/mpibenchmark --msizes-list=$MSIZES --calls-list=MPI_Bcast --nrep=2000 --rt-bench-time-ms=2000 --proc-sync=roundtime > job_${N}_${n}_default_${SLURM_JOB_ID}.dat

HPC_BCAST_CHAIN_NUM=2 HPC_BCAST_CHAIN_SEG=1024 LD_PRELOAD=$BCAST_LIB/libbcast_chain.so \
srun $REPROMPI_BIN/mpibenchmark --msizes-list=$MSIZES --calls-list=MPI_Bcast --nrep=2000 --rt-bench-time-ms=2000 --proc-sync=roundtime > job_${N}_${n}_chain_${SLURM_JOB_ID}.dat

HPC_BCAST_KNOMIAL_K=2 LD_PRELOAD=$BCAST_LIB/libbcast_knomial.so \
srun $REPROMPI_BIN/mpibenchmark --msizes-list=$MSIZES --calls-list=MPI_Bcast --nrep=2000 --rt-bench-time-ms=2000 --proc-sync=roundtime > job_${N}_${n}_knomial_${SLURM_JOB_ID}.dat
