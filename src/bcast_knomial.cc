#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int K_PARAM = 2;

int MPI_Bcast(void *buffer, int count, MPI_Datatype datatype, int root, MPI_Comm comm) {
    int rank, size;
    PMPI_Comm_rank(comm, &rank);
    PMPI_Comm_size(comm, &size);

    if (size <= 1 || count == 0) return MPI_SUCCESS;

    int rel = (rank - root + size) % size;

    for (int step = 1; step < size; step *= K_PARAM) {

        if (rel < step) {
            for (int i = 1; i < K_PARAM; i++) {
                int child_rel = rel + i * step;

                if (child_rel < size) {
                    int child = (child_rel + root) % size;
                    PMPI_Send(buffer, count, datatype, child, 0, comm);
                }
            }
        }
        else if (rel < step * K_PARAM) {
            int parent_rel = rel % step;
            int parent = (parent_rel + root) % size;

            PMPI_Recv(buffer, count, datatype, parent, 0, comm, MPI_STATUS_IGNORE);
        }
    }

    return MPI_SUCCESS;
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
