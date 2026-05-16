#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

const char *ENV_SEG    = "HPC_BCAST_CHAIN_SEG";
const char *ENV_NCHAINS = "HPC_BCAST_CHAIN_NUM";

static int SEG     = 1;
static int NCHAINS = 1;

int MPI_Bcast(void *buffer, int count, MPI_Datatype datatype,
              int root, MPI_Comm comm)
{
    // implement yourself
    return PMPI_Bcast(buffer, count, datatype, root, comm);    
}


int MPI_Init(int *argc, char ***argv)
{
    int rc = PMPI_Init(argc, argv);

    int rank, size;
    PMPI_Comm_rank(MPI_COMM_WORLD, &rank);
    PMPI_Comm_size(MPI_COMM_WORLD, &size);

    char *env_seg = getenv(ENV_SEG);
    char *end_seg;
    SEG = (env_seg && *(env_seg)) ? (int)strtol(env_seg, &end_seg, 10) : 0;
    if (SEG <= 0) SEG = 1;

    char *env_nc = getenv(ENV_NCHAINS);
    char *end_nc;
    int nchains = (env_nc && *(env_nc)) ? (int)strtol(env_nc, &end_nc, 10) : 0;
    if (nchains <= 0) nchains = 1;
    NCHAINS = nchains; 
    if(NCHAINS > size - 1) NCHAINS = size - 1;

    if (rank == 0) {
        fprintf(stderr, "#@HPC_BCAST_CHAIN_SEG=%d\n", SEG);
        fprintf(stderr, "#@HPC_BCAST_CHAIN_NUM=%d\n", NCHAINS);
    }

    return rc;
}

int MPI_Finalize()
{
    return PMPI_Finalize();
}