cmake_minimum_required(VERSION 3.10.0)
set(TARGET "MameVfxFrontPanel")
project(${TARGET} VERSION 0.1.0 LANGUAGES C CXX)

add_executable(${TARGET})

target_compile_features(${TARGET} PUBLIC
  cxx_std_26
)

target_compile_features(${TARGET} PUBLIC
  c_std_23
)

target_compile_options(${TARGET} PUBLIC
  -Wno-c23-extensions
  -g
)

target_include_directories(${TARGET} PRIVATE
  civetweb/include
)

target_compile_definitions(${TARGET} PRIVATE
  "NO_SSL"
  "NO_CGI"
  "NO_FILESYSTEM"
  "USE_WEBSOCKET"
)

target_sources(${TARGET} PRIVATE 
  main.cpp
  civetweb/src/civetweb.c
)

