#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int K_PARAM = 2;

int MPI_Bcast(void *buffer, int count, MPI_Datatype datatype, int root, MPI_Comm comm) {
    // implement yourself
    return PMPI_Bcast(buffer, count, datatype, root, comm);
}

int MPI_Init(int *argc, char ***argv) {
    int rc = PMPI_Init(argc, argv);
    int rank = -1;
    PMPI_Comm_rank(MPI_COMM_WORLD, &rank);
    const char *s = getenv("HPC_BCAST_KNOMIAL_K");
    if(!s) s = "2";
    char *end = NULL;
    K_PARAM = (int)strtol(s, &end, 10);
    if (end == s || K_PARAM < 2) {
        K_PARAM = 2;
    }
    if(rank == 0) {
        fprintf(stderr, "#@HPC_BCAST_KNOMIAL_K=%d\n", K_PARAM);
    }
    return rc;
}

int MPI_Finalize() {
    int rc = PMPI_Finalize();
    return rc;
}
