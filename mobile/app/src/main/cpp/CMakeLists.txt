cmake_minimum_required(VERSION 3.22.1)

project("sieve")

# OpenCV and FFT stubs are defined here for the Orchestration Sieve
add_library(sieve SHARED
            sieve-native.cpp)

find_library(log-lib log)

target_link_libraries(sieve
                      ${log-lib})
