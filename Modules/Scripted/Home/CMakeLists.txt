#-----------------------------------------------------------------------------
set(MODULE_NAME Home)

#-----------------------------------------------------------------------------
set(ccf_annotation_resolution 25) # Possible values are 25 or 50 (Used in CellLocatorConfig.py)

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

function(CellLocator_check_datafile dest_file expected_sha256 output_var)
  get_filename_component(filename ${dest_file} NAME)
  message(STATUS "Checking ${filename}")

  if(NOT EXISTS ${dest_file})
    message(STATUS "Checking ${filename} - nonexistent")
    set(${output_var} "nonexistent" PARENT_SCOPE)
    return()
  endif()

  file(SHA256 ${dest_file} current_hash)
  if(NOT ${current_hash} STREQUAL ${expected_sha256})
    message(STATUS "Checking ${filename} - expired")
    set(${output_var} "expired" PARENT_SCOPE)
    return()
  endif()

  message(STATUS "Checking ${filename} - up-to-date")
  set(${output_var} "ok" PARENT_SCOPE)
endfunction()

function(CellLocator_download_datafile dest_file url expected_sha256)
  get_filename_component(filename ${dest_file} NAME)

  CellLocator_check_datafile(${dest_file} ${expected_sha256} result)

  if(result MATCHES "^(nonexistent|expired)$")
    message(STATUS "Downloading ${filename}")
    file(DOWNLOAD ${url} ${dest_file} EXPECTED_HASH SHA256=${expected_sha256})
    message(STATUS "Downloading ${filename} - done")
  elseif(result STREQUAL "ok")
    return()
  else()
    message(FATAL_ERROR "Unknown result value: ${result}")
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

#-----------------------------------------------------------------------------
# Download CCF average template

message(STATUS "--------------------------")
message(STATUS "Downloading CCF data files [resolution: ${ccf_annotation_resolution}]")

set(ccf_average_template_file "${CellLocator_DOWNLOAD_DIR}/average_template_${ccf_annotation_resolution}.nrrd")
set(ccf_annotation_file "${CellLocator_DOWNLOAD_DIR}/annotation_${ccf_annotation_resolution}.nrrd")

if(ccf_annotation_resolution STREQUAL "50")
  CellLocator_download_datafile(${ccf_average_template_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/average_template_50.nrrd"
    "6114c341d526f9782ca93b314b3244bb0c4c6cea17045f432d4cda63339915aa"
    )
  CellLocator_download_datafile(${ccf_annotation_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_50.nrrd"
    "84e7cecea1b03af16e923c3639602b8324929f833425ba03582bf56f962ea0d4"
    )
elseif(ccf_annotation_resolution STREQUAL "25")
  CellLocator_download_datafile(${ccf_average_template_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/average_template_25.nrrd"
    "e4a2b483e842b4c8c1b5452d940ea59e14bc1ebaa38fe6a9c3bacac6db2a8f4b"
    )
  CellLocator_download_datafile(${ccf_annotation_file}
    "http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/annotation/ccf_2017/annotation_25.nrrd"
    "c620cbcc562183e4dcd40250d440130501781f74b41de35b1c1bdabace290c42"
    )
else()
  message(FATAL_ERROR "Unknown annotation resolution: ${ccf_annotation_resolution}")
endif()

#-----------------------------------------------------------------------------
# Download MNI average template

message(STATUS "--------------------------")
message(STATUS "Downloading MNI data files")

set(mni_average_template_filename "mni_icbm152_t1_tal_nlin_sym_09b_hires.nii") # Used in CellLocatorConfig.py

set(mni_average_template_extract_directory ${CellLocator_DOWNLOAD_DIR}/mni_icbm152_nlin_sym_09b_nifti)

set(mni_average_template_file "${CellLocator_DOWNLOAD_DIR}/${mni_average_template_filename}")
set(mni_average_template_file_sha256 "b2ca5ca7c94471f0ca77b64485c0d9655737b9029ec19ef7486ab89f1ce4bf79")

set(mni_average_template_archive_file "${CellLocator_DOWNLOAD_DIR}/mni_icbm152_nlin_sym_09b_nifti.zip")
set(mni_average_template_archive_file_sha256 "acce3b85039176aaf7de2c3169272551ddfcae5d9a4e5ce642025b795f9f1d20")

CellLocator_check_datafile(${mni_average_template_file} ${mni_average_template_file_sha256} result)
if(result MATCHES "^(nonexistent|expired)$")
  CellLocator_download_datafile(${mni_average_template_archive_file}
    "http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09b_nifti.zip"
    "${mni_average_template_archive_file_sha256}"
    )
  # Extract archive
  get_filename_component(filename ${mni_average_template_archive_file} NAME)
  message(STATUS "Extracting ${filename}")
  execute_process(
    COMMAND ${CMAKE_COMMAND} -E make_directory ${mni_average_template_extract_directory}
    )
  execute_process(
    COMMAND ${CMAKE_COMMAND} -E tar xfz ${mni_average_template_archive_file}
    WORKING_DIRECTORY ${mni_average_template_extract_directory}
    RESULT_VARIABLE rv
    )
  if(rv EQUAL 0)
    message(STATUS "Extracting ${filename} - done")

    # Copy file
    message(STATUS "Copying ${filename}")
    file(
      COPY ${mni_average_template_extract_directory}/mni_icbm152_nlin_sym_09b/${mni_average_template_filename}
      DESTINATION ${CellLocator_DOWNLOAD_DIR}
      )
    message(STATUS "Copying ${filename} - done")

    CellLocator_check_datafile(${mni_average_template_file} ${mni_average_template_file_sha256} result)
    if(result MATCHES "^(nonexistent|expired)$")
      message(FATAL_ERROR "error: Problem downloading ${mni_average_template_file}")
    endif()
  else()
    message(FATAL_ERROR "Extracting ${filename} - failed")
  endif()
endif()

message(STATUS "--------------------------")

#-----------------------------------------------------------------------------
# Download CCF Ontology

set(script "${CMAKE_BINARY_DIR}/ontology_download.cmake")
set(ccf_ontology_download_url "http://api.brain-map.org/api/v2/data/Structure/query.json?criteria=%5Bgraph_id$eq1%5D&num_rows=2000")
set(ccf_ontology_original_file "${CellLocator_DOWNLOAD_DIR}/ontology-original.json")

file(WRITE ${script} "
set(url \"${ccf_ontology_download_url}\")
set(dest_file \"${ccf_ontology_original_file}\")
get_filename_component(filename \${dest_file} NAME)
message(STATUS \"Downloading \${filename}\")
file(DOWNLOAD \${url} \${dest_file})
message(STATUS \"Downloading \${filename} - done\")
")

add_custom_command(
  OUTPUT
    ${ccf_ontology_original_file}
  COMMAND ${CMAKE_COMMAND} -P ${script}
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMENT "Downloading ontology"
  )

#-----------------------------------------------------------------------------
# Format ontology file (filename hardcoded in Home.py)
set(ccf_ontology_file "${CellLocator_DOWNLOAD_DIR}/ontology-formatted.json")

add_custom_command(
  OUTPUT
    ${ccf_ontology_file}
  DEPENDS
    ${ccf_ontology_original_file}
  COMMAND ${PYTHON_EXECUTABLE} -m json.tool ${ccf_ontology_original_file} ${ccf_ontology_file}
  WORKING_DIRECTORY ${CellLocator_BINARY_DIR}
  COMMENT "Prettifying ontology file"
  )

#-----------------------------------------------------------------------------
# Generate contiguous annotation and color table
set(script ${CellLocator_SOURCE_DIR}/Scripts/GenerateContiguousAnnotation.py)

# Outputs: These filenames are hardcoded in Home.py
set(ccf_annotation_contiguous_file "${CellLocator_DOWNLOAD_DIR}/annotation_${ccf_annotation_resolution}_contiguous.nrrd")
set(ccf_color_table "${CellLocator_DOWNLOAD_DIR}/annotation_color_table.txt")

# Outputs: These filenames are hardcoded in Home.py and GenerateContiguousAnnotation.py
set(ccf_annotation_color_allen2slicer_mapping_file "${CellLocator_DOWNLOAD_DIR}/annotation_color_allen2slicer_mapping.json")
set(ccf_annotation_color_slicer2allen_mapping_file "${CellLocator_DOWNLOAD_DIR}/annotation_color_slicer2allen_mapping.json")

get_property(module_targets GLOBAL PROPERTY SLICER_MODULE_TARGETS)

add_custom_command(
  DEPENDS
    ${ccf_annotation_file}
    ${ccf_ontology_file}
    ${script}
    CellLocatorConfigureLauncher
    ${module_targets}
  OUTPUT
    ${ccf_annotation_contiguous_file}
    ${ccf_color_table}
    ${ccf_annotation_color_allen2slicer_mapping_file}
    ${ccf_annotation_color_slicer2allen_mapping_file}
  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:CellLocatorApp>
    --python-script ${script}
    --annotation-input ${ccf_annotation_file}
    --ontology-input ${ccf_ontology_file}
    --annotation-output ${ccf_annotation_contiguous_file}
    --colortable-output ${ccf_color_table}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Pre-processing structure ontology and annotation volume"
  )

add_custom_target(CellLocatorGenerateContiguousAnnotation ALL
  DEPENDS
    ${ccf_annotation_contiguous_file}
    ${ccf_color_table}
    ${ccf_annotation_color_allen2slicer_mapping_file}
    ${ccf_annotation_color_slicer2allen_mapping_file}
  )

CellLocator_install_datafiles(
  # CCF
  ${ccf_average_template_file}
  ${ccf_annotation_contiguous_file}
  ${ccf_color_table}
  ${ccf_annotation_color_allen2slicer_mapping_file}
  ${ccf_annotation_color_slicer2allen_mapping_file}
  ${ccf_ontology_file}
  # MNI
  ${mni_average_template_file}
  )

#-----------------------------------------------------------------------------
# Prepare layer ontology file

# File generated doing:
#
#  pip install allensdk
#  python /path/to/Scripts/GenerateLayerOntology.py --output /path/to/layer-ontology-formatted.json
#

set(ccf_layer_ontology_file "${CellLocator_DOWNLOAD_DIR}/layer-ontology-formatted.json")

configure_file(
  ${CellLocator_SOURCE_DIR}/Scripts/data/layer-ontology-formatted.json
  ${ccf_layer_ontology_file}
  COPYONLY
  )

#-----------------------------------------------------------------------------
# Generate layer color table
set(script ${CellLocator_SOURCE_DIR}/Scripts/CreateColorTable.py)

# Outputs: These filenames are hardcoded in Home.py
set(ccf_layer_color_table "${CellLocator_DOWNLOAD_DIR}/annotation_layer_color_table.txt")

add_custom_command(
  DEPENDS
    ${ccf_layer_ontology_file}
    ${ccf_annotation_color_allen2slicer_mapping_file}
    ${script}
    CellLocatorConfigureLauncher
    ${module_targets}
  OUTPUT
    ${ccf_layer_color_table}
  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:CellLocatorApp>
    --python-script ${script}
    --input ${ccf_layer_ontology_file}
    --allen2slicer ${ccf_annotation_color_allen2slicer_mapping_file}
    --output ${ccf_layer_color_table}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Generate layer color table"
  )

add_custom_target(CellLocatorGenerateLayerColorTable ALL
  DEPENDS
    ${ccf_layer_color_table}
    ${ccf_layer_ontology_file}
  )

CellLocator_install_datafiles(
  ${ccf_layer_color_table}
  ${ccf_layer_ontology_file}
  )

#-----------------------------------------------------------------------------
configure_file(
  ${MODULE_NAME}Lib/CellLocatorConfig.py.in
  ${CMAKE_CURRENT_BINARY_DIR}/${MODULE_NAME}Lib/CellLocatorConfig.py
  @ONLY
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
