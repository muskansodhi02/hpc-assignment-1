#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int msg_size     = 1024;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0 && i + 1 < argc)
            msg_size = atoi(argv[++i]);
    }
    if (msg_size <= 0) msg_size = 1;

    char *buf_ref    = (char *)malloc(msg_size);
    char *buf_custom = (char *)malloc(msg_size);

    /* root fills both buffers with the same known pattern */
    if (rank == 0) {
        for (int i = 0; i < msg_size; i++)
            buf_ref[i] = buf_custom[i] = (char)(i & 0xFF);
    } else {
        memset(buf_ref,    0, msg_size);
        memset(buf_custom, 0, msg_size);
    }

    /* reference: bypasses any LD_PRELOAD override */
    PMPI_Bcast(buf_ref,    msg_size, MPI_BYTE, 0, MPI_COMM_WORLD);
    /* custom:   intercepted via LD_PRELOAD        */
    MPI_Bcast (buf_custom, msg_size, MPI_BYTE, 0, MPI_COMM_WORLD);

    int local_ok  = (memcmp(buf_ref, buf_custom, msg_size) == 0);
    int global_ok = 0;
    MPI_Reduce(&local_ok, &global_ok, 1, MPI_INT, MPI_MIN, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("%s  size=%d bytes  np=%d\n",
               global_ok ? "PASS" : "FAIL", msg_size, size);
    }

    free(buf_ref);
    free(buf_custom);

    MPI_Finalize();
    return 0;
}
