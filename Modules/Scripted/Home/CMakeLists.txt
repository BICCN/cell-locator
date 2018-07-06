#-----------------------------------------------------------------------------
set(MODULE_NAME Home)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/annotation_25.png
  Resources/Icons/annotation_50.png
  Resources/UI/${MODULE_NAME}.ui
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
# Download and package the data

set(CellLocator_DOWNLOAD_DIR ${CMAKE_BINARY_DIR}/CellLocatorData)
set(CellLocator_DATA_URLS
  "download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_25.nrrd"
  "download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_50.nrrd"
  )

foreach(data_url ${CellLocator_DATA_URLS})

  set(last_slash_pos)
  string(FIND ${data_url} "/" last_slash_pos REVERSE)
  math(EXPR last_slash_pos "${last_slash_pos}+1")
  string(SUBSTRING ${data_url} ${last_slash_pos} -1 filename)

  string(CONCAT src_path ${CellLocator_DOWNLOAD_DIR} "/" ${filename})

  # Check if we need to download it again
  if (NOT EXISTS ${src_path})
    message(STATUS "Downloading ${filename}")
    file(DOWNLOAD ${data_url} ${src_path} SHOW_PROGRESS)
    message(STATUS "Downloading ${filename} - DONE")
  endif()

  set(tgt_path
    ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}/CellLocatorData/${filename})
  add_custom_command(
    DEPENDS ${src_path}
    COMMAND ${CMAKE_COMMAND} -E copy ${src_path} ${tgt_path}
    OUTPUT ${tgt_path}
    COMMENT "Copying python ${filename}: ${tgt_path}"
    )
  list(APPEND copied_files ${tgt_path})
endforeach()

add_custom_target(CopySlicerPythonResourceFiles ALL DEPENDS ${copied_files})

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
