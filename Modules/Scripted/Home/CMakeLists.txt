#-----------------------------------------------------------------------------
set(MODULE_NAME Home)

#-----------------------------------------------------------------------------
set(annotation_resolution 25) # Possible values are 25 or 50
configure_file(
  ${MODULE_NAME}Lib/CellLocatorConfig.py.in
  ${CMAKE_CURRENT_BINARY_DIR}/${MODULE_NAME}Lib/CellLocatorConfig.py
  @ONLY
  )

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Lib/__init__.py
  ${CMAKE_CURRENT_BINARY_DIR}/${MODULE_NAME}Lib/CellLocatorConfig.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  )

slicerFunctionAddPythonQtResources(MODULE_PYTHON_QRC_RESOURCES
  ${MODULE_NAME}Lib/${MODULE_NAME}.qrc
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS} ${MODULE_PYTHON_QRC_RESOURCES}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
# Convenience function for downloading and installing data files

function(CellLocator_download_datafile dest_file url expected_sha256)
  get_filename_component(filename ${dest_file} NAME)
  message(STATUS "Checking ${filename}")
  if(NOT EXISTS ${dest_file})
    message(STATUS "Checking ${filename} - nonexistent")
    message(STATUS "Downloading ${filename}")
    file(DOWNLOAD ${url} ${dest_file} EXPECTED_HASH SHA256=${expected_sha256})
    message(STATUS "Downloading ${filename} - done")
  else()
    file(SHA256 ${dest_file} current_hash)
    if(NOT ${current_hash} STREQUAL ${expected_sha256})
      message(STATUS "Checking ${filename} - expired")
      message(STATUS "Downloading ${filename}")
      file(DOWNLOAD ${url} ${dest_file} EXPECTED_HASH SHA256=${expected_sha256})
      message(STATUS "Downloading ${filename} - done")
    else()
      message(STATUS "Checking ${filename} - up-to-date")
    endif()
  endif()
endfunction()

function(CellLocator_install_datafiles datafile)
  install(
    FILES ${datafile} ${ARGN}
    DESTINATION "${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}/"
    COMPONENT RuntimeLibraries
    )
endfunction()

#-----------------------------------------------------------------------------
# Download and package the data

set(CellLocator_DOWNLOAD_DIR ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}/CellLocatorData)

set(average_template_file "${CellLocator_DOWNLOAD_DIR}/average_template_${annotation_resolution}.nrrd")
set(annotation_file "${CellLocator_DOWNLOAD_DIR}/annotation_${annotation_resolution}.nrrd")

if(annotation_resolution STREQUAL "50")
  CellLocator_download_datafile(${average_template_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/average_template_50.nrrd"
    "6114c341d526f9782ca93b314b3244bb0c4c6cea17045f432d4cda63339915aa"
    )
  CellLocator_download_datafile(${annotation_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_50.nrrd"
    "84e7cecea1b03af16e923c3639602b8324929f833425ba03582bf56f962ea0d4"
    )
elseif(annotation_resolution STREQUAL "25")
  CellLocator_download_datafile(${average_template_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/average_template_25.nrrd"
    "e4a2b483e842b4c8c1b5452d940ea59e14bc1ebaa38fe6a9c3bacac6db2a8f4b"
    )
  CellLocator_download_datafile(${annotation_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_25.nrrd"
    "c620cbcc562183e4dcd40250d440130501781f74b41de35b1c1bdabace290c42"
    )
else()
  message(FATAL_ERROR "Unkown annotation resolution: ${annotation_resolution}")
endif()

#-----------------------------------------------------------------------------
# Download Ontology

set(script "${CMAKE_BINARY_DIR}/ontology_download.cmake")
set(ontology_download_url "http://api.brain-map.org/api/v2/data/Structure/query.json?criteria=%5Bgraph_id$eq1%5D&num_rows=2000")
set(ontology_original_file "${CellLocator_DOWNLOAD_DIR}/ontology-original.json")

file(WRITE ${script} "
set(url \"${ontology_download_url}\")
set(dest_file \"${ontology_original_file}\")
get_filename_component(filename \${dest_file} NAME)
message(STATUS \"Downloading \${filename}\")
file(DOWNLOAD \${url} \${dest_file})
message(STATUS \"Downloading \${filename} - done\")
")

add_custom_command(
  OUTPUT
    ${ontology_original_file}
  COMMAND ${CMAKE_COMMAND} -P ${script}
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMENT "Downloading ontology"
  )

#-----------------------------------------------------------------------------
# Format ontology file (filename hardcoded in Home.py)
set(ontology_file "${CellLocator_DOWNLOAD_DIR}/ontology-formatted.json")

add_custom_command(
  OUTPUT
    ${ontology_file}
  DEPENDS
    ${ontology_original_file}
  COMMAND ${PYTHON_EXECUTABLE} -m json.tool ${ontology_original_file} ${ontology_file}
  WORKING_DIRECTORY ${CellLocator_BINARY_DIR}
  COMMENT "Prettifying ontology file"
  )

#-----------------------------------------------------------------------------
# Generate contiguous annotation and color table
set(script ${CellLocator_SOURCE_DIR}/Scripts/GenerateContiguousAnnotation.py)

# Outputs: These filenames are hardcoded in Home.py
set(annotation_contiguous_file "${CellLocator_DOWNLOAD_DIR}/annotation_${annotation_resolution}_contiguous.nrrd")
set(color_table "${CellLocator_DOWNLOAD_DIR}/annotation_color_table.txt")
set(annotation_color_allen2slicer_mapping_file "${CellLocator_DOWNLOAD_DIR}/annotation_color_allen2slicer_mapping.json")
set(annotation_color_slicer2allen_mapping_file "${CellLocator_DOWNLOAD_DIR}/annotation_color_slicer2allen_mapping.json")

get_property(module_targets GLOBAL PROPERTY SLICER_MODULE_TARGETS)

add_custom_command(
  DEPENDS
    ${annotation_file}
    ${ontology_file}
    ${script}
    CellLocatorConfigureLauncher
    ${module_targets}
  OUTPUT
    ${annotation_contiguous_file}
    ${color_table}
    ${annotation_color_allen2slicer_mapping_file}
    ${annotation_color_slicer2allen_mapping_file}
  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:CellLocatorApp>
    --python-script ${script}
    --annotation-input ${annotation_file}
    --ontology-input ${ontology_file}
    --annotation-output ${annotation_contiguous_file}
    --colortable-output ${color_table}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Pre-processing structure ontology and annotation volume"
  )

add_custom_target(CellLocatorGenerateContiguousAnnotation ALL
  DEPENDS
    ${annotation_contiguous_file}
    ${color_table}
    ${annotation_color_allen2slicer_mapping_file}
    ${annotation_color_slicer2allen_mapping_file}
  )

CellLocator_install_datafiles(
  ${average_template_file}
  ${annotation_contiguous_file}
  ${color_table}
  ${annotation_color_allen2slicer_mapping_file}
  ${annotation_color_slicer2allen_mapping_file}
  ${ontology_file}
  )

#-----------------------------------------------------------------------------
# Prepare layer ontology file

set(layer_ontology_file "${CellLocator_DOWNLOAD_DIR}/layer-ontology-formatted.json")

configure_file(
  ${CellLocator_SOURCE_DIR}/Scripts/data/layer-ontology-formatted.json
  ${layer_ontology_file}
  COPYONLY
  )

#-----------------------------------------------------------------------------
# Generate layer color table
set(script ${CellLocator_SOURCE_DIR}/Scripts/CreateColorTable.py)

# Outputs: These filenames are hardcoded in Home.py
set(layer_color_table "${CellLocator_DOWNLOAD_DIR}/annotation_layer_color_table.txt")

add_custom_command(
  DEPENDS
    ${layer_ontology_file}
    ${script}
    CellLocatorConfigureLauncher
    ${module_targets}
  OUTPUT
    ${layer_color_table}
  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:CellLocatorApp>
    --python-script ${script}
    --input ${layer_ontology_file}
    --allen2slicer ${annotation_color_allen2slicer_mapping_file}
    --output ${layer_color_table}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Generate layer color table"
  )

add_custom_target(CellLocatorGenerateLayerColorTable ALL
  DEPENDS
    ${layer_color_table}
    ${layer_ontology_file}
  )

CellLocator_install_datafiles(
  ${layer_color_table}
  ${layer_ontology_file}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
