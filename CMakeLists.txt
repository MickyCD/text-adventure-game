cmake_minimum_required(VERSION 3.14)
project(TextAdventure)

set(CMAKE_CXX_STANDARD 17)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

find_package(SQLite3 REQUIRED)

include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

add_executable(text_adventure main.cpp)

# Link everything together
target_link_libraries(text_adventure
    PRIVATE
    pybind11::embed      # Links Python embedding
    SQLite::SQLite3      # Links SQL
)

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/game_logic.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
