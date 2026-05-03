cmake_minimum_required(VERSION 3.22)

project(bcast_solution
        VERSION 1.0.0
        LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

# Find MPI
find_package(MPI REQUIRED)

# Add library for chain broadcast
add_library(bcast_chain SHARED src/bcast_chain.cc)
target_link_libraries(bcast_chain PRIVATE MPI::MPI_CXX)

# Add library for knomial broadcast
add_library(bcast_knomial SHARED src/bcast_knomial.cc)
target_link_libraries(bcast_knomial PRIVATE MPI::MPI_CXX)

# Test binary
add_executable(bcast_test src/bcast_test.cc)
target_link_libraries(bcast_test PRIVATE MPI::MPI_CXX)

# Pack sources into a zip
add_custom_target(pack
    COMMAND zip -r "${CMAKE_BINARY_DIR}/bcast.zip"
            bcast/CMakeLists.txt bcast/src/bcast_chain.cc bcast/src/bcast_knomial.cc bcast/src/bcast_test.cc
            bcast/jobs
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/.."
    COMMENT "Packing sources into ${CMAKE_BINARY_DIR}/bcast.zip"
)
