#-----------------------------------------------------------------------------
set(MODULE_NAME Home)

#-----------------------------------------------------------------------------
set(ccf_annotation_resolution 25) # Possible values are 25 or 50 (Used in CellLocatorConfig.py)
set(mni_average_template_filename "mni_icbm152_t1_tal_nlin_sym_09b_hires.nii") # Used in CellLocatorConfig.py

#-----------------------------------------------------------------------------
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
  Resources/UI/AtlasSelection.ui
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

set(ccf_average_template_file "${CellLocator_DOWNLOAD_DIR}/ccf_average_template_${ccf_annotation_resolution}.nrrd")
set(ccf_annotation_file "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_${ccf_annotation_resolution}.nrrd")

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

set(mni_annotation_file "${CellLocator_DOWNLOAD_DIR}/mni_annotation_full.nii.gz")
CellLocator_download_datafile(${mni_annotation_file}
  "http://download.alleninstitute.org/informatics-archive/allen_human_reference_atlas_3d_2020/version_1/annotation_full.nii.gz"
  "2b05581e39c44f2623d9b0a69f64e3df0823c20d054abef92973812313335dc3"
  )

message(STATUS "--------------------------")

#-----------------------------------------------------------------------------
function(CellLocator_download_ontology atlas_name ontology_download_url ontology_original_file)
  set(script "${CMAKE_BINARY_DIR}/${atlas_name}_ontology_download.cmake")

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
    COMMENT "Downloading ${atlas_name} ontology"
    )
endfunction()

function(CellLocator_prettify_ontology atlas_name ontology_original_file ontology_file)
  add_custom_command(
    OUTPUT
      ${ontology_file}
    DEPENDS
      ${ontology_original_file}
    COMMAND ${PYTHON_EXECUTABLE} -m json.tool ${ontology_original_file} ${ontology_file}
    WORKING_DIRECTORY ${CellLocator_BINARY_DIR}
    COMMENT "Prettifying ${atlas_name} ontology file"
    )
endfunction()

#-----------------------------------------------------------------------------
# Download Ontology

set(ccf_ontology_original_file "${CellLocator_DOWNLOAD_DIR}/ccf-ontology-original.json")
CellLocator_download_ontology("ccf"
  "http://api.brain-map.org/api/v2/data/Structure/query.json?criteria=%5Bgraph_id$eq1%5D&num_rows=2000"
  ${ccf_ontology_original_file}
  )

set(mni_ontology_original_file "${CellLocator_DOWNLOAD_DIR}/mni-ontology-original.json")
CellLocator_download_ontology("mni"
  "http://api.brain-map.org/api/v2/data/query.json?criteria=model::Structure,rma::criteria,%5Bgraph_id$eq16%5D,rma::options%5Border$eq'structures.graph_order'%5D%5Bnum_rows$eqall%5D"
  ${mni_ontology_original_file}
  )

#-----------------------------------------------------------------------------
# Format ontology file (filename hardcoded in Home.py)

set(ccf_ontology_file "${CellLocator_DOWNLOAD_DIR}/ccf-ontology-formatted.json")
CellLocator_prettify_ontology("ccf"
  ${ccf_ontology_original_file}
  ${ccf_ontology_file}
  )

set(mni_ontology_file "${CellLocator_DOWNLOAD_DIR}/mni-ontology-formatted.json")
CellLocator_prettify_ontology("mni"
  ${mni_ontology_original_file}
  ${mni_ontology_file}
  )

#-----------------------------------------------------------------------------
# Generate CCF contiguous annotation and color tables

set(script ${CMAKE_CURRENT_SOURCE_DIR}/Data/GenerateContiguousAnnotation.py)

# Outputs: These filenames are hardcoded in Home.py
set(ccf_annotation_contiguous_file "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_${ccf_annotation_resolution}_contiguous.nrrd")
set(ccf_color_table "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_color_table.txt")

# Outputs: These filenames are hardcoded in Home.py
set(ccf_annotation_color_allen2slicer_mapping_file "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_color_allen2slicer_mapping.json")
set(ccf_annotation_color_slicer2allen_mapping_file "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_color_slicer2allen_mapping.json")

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
    --annotation-color-allen2slicer-mapping-output ${ccf_annotation_color_allen2slicer_mapping_file}
    --annotation-color-slicer2allen-mapping-output ${ccf_annotation_color_slicer2allen_mapping_file}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Pre-processing CCF structure ontology and annotation volume"
  )

add_custom_target(CellLocatorGenerateCCFContiguousAnnotation ALL
  DEPENDS
    ${ccf_annotation_contiguous_file}
    ${ccf_color_table}
    ${ccf_annotation_color_allen2slicer_mapping_file}
    ${ccf_annotation_color_slicer2allen_mapping_file}
  )

CellLocator_install_datafiles(
  ${ccf_average_template_file}
  ${ccf_annotation_contiguous_file}
  ${ccf_color_table}
  ${ccf_annotation_color_allen2slicer_mapping_file}
  ${ccf_annotation_color_slicer2allen_mapping_file}
  ${ccf_ontology_file}
  )

#-----------------------------------------------------------------------------
# Generate MNI contiguous annotation and color tables

set(script ${CMAKE_CURRENT_SOURCE_DIR}/Data/GenerateContiguousAnnotation.py)

# Outputs: These filenames are hardcoded in Home.py
set(mni_annotation_contiguous_file "${CellLocator_DOWNLOAD_DIR}/mni_annotation_contiguous.nrrd")
set(mni_color_table "${CellLocator_DOWNLOAD_DIR}/mni_annotation_color_table.txt")

# Outputs: These filenames are hardcoded in Home.py
set(mni_annotation_color_allen2slicer_mapping_file "${CellLocator_DOWNLOAD_DIR}/mni_annotation_color_allen2slicer_mapping.json")
set(mni_annotation_color_slicer2allen_mapping_file "${CellLocator_DOWNLOAD_DIR}/mni_annotation_color_slicer2allen_mapping.json")

add_custom_command(
  DEPENDS
    ${mni_annotation_file}
    ${mni_ontology_file}
    ${script}
    CellLocatorConfigureLauncher
    ${module_targets}
  OUTPUT
    ${mni_annotation_contiguous_file}
    ${mni_color_table}
    ${mni_annotation_color_allen2slicer_mapping_file}
    ${mni_annotation_color_slicer2allen_mapping_file}
  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:CellLocatorApp>
    --python-script ${script}
    --annotation-input ${mni_annotation_file}
    --ontology-input ${mni_ontology_file}
    --annotation-output ${mni_annotation_contiguous_file}
    --colortable-output ${mni_color_table}
    --annotation-color-allen2slicer-mapping-output ${mni_annotation_color_allen2slicer_mapping_file}
    --annotation-color-slicer2allen-mapping-output ${mni_annotation_color_slicer2allen_mapping_file}
    --exit-after-startup
    --modules-to-ignore Home
    --no-main-window
    --no-splash
  WORKING_DIRECTORY ${CellLocator_DOWNLOAD_DIR}
  COMMENT "Pre-processing MNI structure ontology and annotation volume"
  )

add_custom_target(CellLocatorGenerateMNIContiguousAnnotation ALL
  DEPENDS
    ${mni_annotation_contiguous_file}
    ${mni_color_table}
    ${mni_annotation_color_allen2slicer_mapping_file}
    ${mni_annotation_color_slicer2allen_mapping_file}
  )

CellLocator_install_datafiles(
  ${mni_average_template_file}
  ${mni_annotation_contiguous_file}
  ${mni_color_table}
  ${mni_annotation_color_allen2slicer_mapping_file}
  ${mni_annotation_color_slicer2allen_mapping_file}
  ${mni_ontology_file}
  )

#-----------------------------------------------------------------------------
# Prepare CCF layer ontology file

# File generated doing:
#
#  pip install allensdk
#  python /path/to/Scripts/GenerateLayerOntology.py --output /path/to/layer-ontology-formatted.json
#

set(ccf_layer_ontology_file "${CellLocator_DOWNLOAD_DIR}/ccf-layer-ontology-formatted.json")

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/Data/ccf-layer-ontology-formatted.json
  ${ccf_layer_ontology_file}
  COPYONLY
  )

#-----------------------------------------------------------------------------
# Generate CCF layer color table
set(script ${CMAKE_CURRENT_SOURCE_DIR}/Data/CreateColorTable.py)

# Outputs: These filenames are hardcoded in Home.py
set(ccf_layer_color_table "${CellLocator_DOWNLOAD_DIR}/ccf_annotation_layer_color_table.txt")

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
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
