cmake_minimum_required(VERSION 3.10.0)
set(TARGET "MameVfxFrontPanel")
project(${TARGET} VERSION 0.1.0 LANGUAGES C CXX)

set(USE_SSL FALSE)

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
  "NO_CGI"
  "NO_FILESYSTEM"
  "USE_WEBSOCKET"
)

if(USE_SSL)
  set(OPENSSL_USE_STATIC_LIBS TRUE)
  find_package(OpenSSL COMPONENTS SSL)
  add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/cert.der ${CMAKE_CURRENT_BINARY_DIR}/key.der
    COMMAND openssl req -x509 -newkey rsa:4096 -keyout ${CMAKE_CURRENT_BINARY_DIR}/key.pem -outform der -out ${CMAKE_CURRENT_BINARY_DIR}/cert.der -sha256 -days 3650 -nodes -subj "/C=XX/L=NA/O=NA/OU=NA/CN=localhost"
    COMMAND openssl rsa -in ${CMAKE_CURRENT_BINARY_DIR}/key.pem -outform der -out ${CMAKE_CURRENT_BINARY_DIR}/key.der
    COMMAND rm ${CMAKE_CURRENT_BINARY_DIR}/key.pem
    VERBATIM
  )
  add_custom_target(build_keys DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/cert.der ${CMAKE_CURRENT_BINARY_DIR}/key.der)
  add_dependencies(${TARGET} build_keys)
  target_link_libraries(${TARGET} PRIVATE OpenSSL::SSL)
  target_compile_definitions(${TARGET} PRIVATE 
    "OPENSSL_API_3_0"
    "SSL_CERT=\"${CMAKE_CURRENT_BINARY_DIR}/cert.der\""
    "SSL_KEY=\"${CMAKE_CURRENT_BINARY_DIR}/key.der\""
    "USE_SSL=1"
  )
else()
  target_compile_definitions(${TARGET} PRIVATE 
    "NO_SSL"
    "USE_SSL=0"
  )
endif()

target_sources(${TARGET} PRIVATE 
  main.cpp
  civetweb/src/civetweb.c
)

