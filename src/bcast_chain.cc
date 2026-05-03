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
    int rank, size;
    PMPI_Comm_rank(comm, &rank);
    PMPI_Comm_size(comm, &size);

    if (size <= 1 || count == 0) return MPI_SUCCESS;

    int type_size;
    PMPI_Type_size(datatype, &type_size);

    int total_bytes = count * type_size;
    char *buf = (char *)buffer;

    int rel = (rank - root + size) % size;

    if (NCHAINS < 1) NCHAINS = 1;
    if (NCHAINS > size - 1) NCHAINS = size - 1;

    int chunk_size = SEG;
    if (chunk_size < 1) chunk_size = total_bytes;

    for (int offset = 0; offset < total_bytes; offset += chunk_size) {
        int this_chunk = chunk_size;
        if (offset + this_chunk > total_bytes)
            this_chunk = total_bytes - offset;

        if (rel == 0) {
            for (int c = 0; c < NCHAINS; c++) {
                int child_rel = 1 + c;
                if (child_rel < size) {
                    int child = (root + child_rel) % size;
                    PMPI_Send(buf + offset, this_chunk, MPI_BYTE, child, 0, comm);
                }
            }
        } else {
            int prev_rel = rel - NCHAINS;
            int prev;

            if (prev_rel <= 0)
                prev = root;
            else
                prev = (root + prev_rel) % size;

            PMPI_Recv(buf + offset, this_chunk, MPI_BYTE, prev, 0, comm, MPI_STATUS_IGNORE);

            int next_rel = rel + NCHAINS;
            if (next_rel < size) {
                int next = (root + next_rel) % size;
                PMPI_Send(buf + offset, this_chunk, MPI_BYTE, next, 0, comm);
            }
        }
    }

    return MPI_SUCCESS;
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