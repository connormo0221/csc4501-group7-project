cmake_minimum_required(VERSION 3.19)

project(csc4501-group7-project)

set(CMAKE_CXX_STANDARD 20)

add_executable(project src/main.cpp)

if(WIN32)
  target_link_libraries(project wsock32 ws2_32)
endif()