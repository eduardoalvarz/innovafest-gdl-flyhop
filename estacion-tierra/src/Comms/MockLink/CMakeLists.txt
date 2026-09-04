if(CMAKE_BUILD_TYPE AND NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
    return()
endif()

target_sources(${CMAKE_PROJECT_NAME}
    PRIVATE
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockConfiguration.cc>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockConfiguration.h>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLink.cc>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLink.h>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkFTP.cc>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkFTP.h>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkWorker.cc>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkWorker.h>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkMissionItemHandler.cc>
        $<$<CONFIG:Debug>:${CMAKE_CURRENT_SOURCE_DIR}/MockLinkMissionItemHandler.h>
)

target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
