# Release Notes

## Next Release

Features:

Fixes:

- Don't show exit confirmation when file (or LIMS specimen) is unchanged. [#204](https://github.com/BICCN/cell-locator/pull/204)

Documentation:

- Document double-click action to rename annotations. [#206](https://github.com/BICCN/cell-locator/pull/206)
- Update expected Slice Offset values in QA template. [#203](https://github.com/BICCN/cell-locator/pull/204); see [#139 (comment)](https://github.com/BICCN/cell-locator/issues/139#issuecomment-916986725) for details.

## Cell Locator 0.2.0 2021-08-12

Features:

- Created script to convert between Cell Locator file formats. [#181](https://github.com/BICCN/cell-locator/pull/181), [#182](https://github.com/BICCN/cell-locator/pull/182)

Fixes:

- Fixed new `"measurements"` key being incorrectly included in serialization. [#182](https://github.com/BICCN/cell-locator/issues/182)
- Fixed changing ontology resetting slice view. [#178](https://github.com/BICCN/cell-locator/issues/178)
- Fixed GUI desync when editing multiple annotations. [#179](https://github.com/BICCN/cell-locator/issues/179), [#180](https://github.com/BICCN/cell-locator/issues/180)
- Fixed polyline annotations incorrectly loading as splines. [#184](https://github.com/BICCN/cell-locator/issues/184)
- Fixed point annotations persisting after scene clear. [#185](https://github.com/BICCN/cell-locator/issues/185)

Documentation:

- Document the Annotation type hierarchy.
- Provide documentation and example of how to create new Annotation types.
- Document the mock LIMS server and LIMS API.
- Switch from recommonmark to [MyST](https://myst-parser.readthedocs.io/en/latest/); so that reStructuredText may be avoided entirely. See [Slicer#5662](https://github.com/Slicer/Slicer/pull/5662).
- File Format Version bumped to `0.2.0+2021-08-12` [#198](https://github.com/BICCN/cell-locator/pull/198)

## Cell Locator 0.1.0 2021-05-21

Features:

* Add support for adding "point" annotations. See [#164](https://github.com/BICCN/cell-locator/issues/161) and [#164](https://github.com/BICCN/cell-locator/issues/169).

* Add support for user selection of atlas through the UI at startup if no atlas is specified on the command line. See [#165](https://github.com/BICCN/cell-locator/issues/165)

* Add a version number to the file format using [semantic versioning](https://semver.org/). See [#170](https://github.com/BICCN/cell-locator/issues/170)

Fixes:

* Fix orientation of MNI atlas. See [#163](https://github.com/BICCN/cell-locator/issues/163)

* Use full annotations for MNI atlas, instead of single side annotation. See [#164](https://github.com/BICCN/cell-locator/issues/164)

* Fix errors when changing interaction mode while there are no annotations in the scene. See [#173](https://github.com/BICCN/cell-locator/issues/173)

Documentation:

* Add [Documentation/CoordinateSystem.md](https://github.com/BICCN/cell-locator/blob/master/Documentation/CoordinateSystem.md) with `Updates` section.

* Add versioning history to [Documentation/AnnotationFileFormat.md](https://github.com/BICCN/cell-locator/blob/master/Documentation/AnnotationFileFormat.md). The current version is `0.1.0+2020.09.18`

## Cell Locator 0.1.0 2020-09-18
  
Features:

* Add support for editing multiple annotations in one file. See [#90](https://github.com/BICCN/cell-locator/issues/90)
  * List of annotations displayed on left sidebar.
  * Add button  for _adding_, _cloning_, and _removing?_ annotations. See [#102](https://github.com/BICCN/cell-locator/issues/102)

* Responsive UI depending on whether CellLocator was launched by LIMS
  * If launched with LIMS enabled, hide the file controls (New, Save, Load, Save As). Otherwise, hide the LIMS controls (Save to LIMS)

* Save and load annotations by name
  * Double-click annotation to rename

* Display interaction handles allowing to rotate or translate current annotation. See [#141](https://github.com/BICCN/cell-locator/issues/141) and [#118](https://github.com/BICCN/cell-locator/issues/118)

* Display error dialog when LIMS connection failed to be established.

* Add support for loading MNI atlas. See [#99](https://github.com/BICCN/cell-locator/issues/99)
  * Accept `--atlas-type` command line argument.
  * Supported value for atlas type are `mni` and `ccf`.
  * Display `mm` unit suffix for `mni` atlas and `um` for `ccf` atlas.

File format:

* Simplify annotation format removing unneeded keys. See [#150](https://github.com/BICCN/cell-locator/issues/150)

Fixes:

* Drawing a second polygon results in an empty json file.  See [#108](https://github.com/BICCN/cell-locator/issues/108)
* Use of contrast "reset" button. See [#136](https://github.com/BICCN/cell-locator/issues/136)
* Use of Ctrl+W shortcut to reset application state. See [#134](https://github.com/BICCN/cell-locator/issues/134)
* Crash on application shutdown. See [#154](https://github.com/BICCN/cell-locator/issues/154)
* Remember last saved directory. See [#137](https://github.com/BICCN/cell-locator/issues/137)
* Initialize annotation base name to `Annotation` instead of `MarkupsClosedCurve`.
* Ensure only current annotation can be updated when `annotate` or `place` mode is activated.
* Hide irrelevant annotation control point right click menu entries.
* Handle annotation payload with missing `data` key.
* Fix annotation scaling. See [#156](https://github.com/BICCN/cell-locator/issues/156)
* Spline polygons do not save, but also do not disappear in a session involving multiple files. See [#112](https://github.com/BICCN/cell-locator/issues/112)
* After using Ctrl+w and restarting the application, `mm` unit prefix is displayed instead of `um`. See [#89](https://github.com/BICCN/cell-locator/issues/89)
* Support loading annotation from network path. See [#103](https://github.com/BICCN/cell-locator/issues/103)

Documentation:

* Add [MAINTAINERS.md](https://github.com/BICCN/cell-locator/blob/master/MAINTAINERS.md) with `Making a release` section.
* Update `Keyboard Accelerators and Mouse Operations / Annotation` section in `README.md`.

Testing:

* Update [AllenInstituteMockLIMS](https://github.com/KitwareMedical/AllenInstituteMockLIMS#getting-started)
  adding _Getting Started_ section to `README.md`.

## Cell Locator 0.1.0 2020-08-26

Features:

* In addition of `Explore` and `Annotate` mode, introduce the `Place` interaction mode.
  * `Annotate`: Used for editing existing control points.
  * `Place`: Used for adding new control points
  * `Explore`: Used for exploring the space

Infrastructure:

* Update Slicer to version from 2020-08-14.
  See [KitwareMedical/Slicer@cell-locator-v4.11.0-2020-08-14-376d405c2b](https://github.com/KitwareMedical/Slicer/commits/cell-locator-v4.11.0-2020-08-14-376d405c2b)
  and  [#96](https://github.com/BICCN/cell-locator/issues/96)
* Update to Python 3
* Introduce `Annotation` and `AnnotationManager` classes for interfacing with built-in Slicer markups nodes.

Fixes:

* Improve LIMS integration to address the feedback in [#93](https://github.com/BICCN/cell-locator/issues/93#issuecomment-675102826).
  * Switch to the `requests` library to properly handle request headers. POST requests use the `json` argument, which sets `Content-Type: application/json`.
  * Change failure messages to be more helpful. Now includes the error status code and message.
  For example: `Failed to load annotations for LIMS specimen <ID>. Error <STATUS>: '<REASON>'`
  * Current LIMS specimen ID is shown in the file path box below "Save to LIMS".

* Ensure updating annotation point do not move the whole polygon. See [#109](https://github.com/BICCN/cell-locator/issues/109)
* Improve insertion of point in existing annotation. See [#80](https://github.com/BICCN/cell-locator/issues/80)

## Cell Locator 0.1.0 2020-07-30

Features:

* Add LIMS support. See [#93](https://github.com/BICCN/cell-locator/issues/93)
  * Support command-line flags `--lims-specimen-id` and `--lims-base-url`.
  * Add new section to [README](README.md#lims-integration)

Tests:

* Add mock server to test LIMS functionalities. See instructions at
  https://github.com/KitwareMedical/AllenInstituteMockLIMS

## Cell Locator 0.1.0 2020-04-30

Features:

* Add support for ``--reference-view``, ``--view-angle`` and ``--annotation-file``
  command-line arguments. See [#97](https://github.com/BICCN/cell-locator/issues/97)

Fixes:

* Ensure that +x is +P in both slice view and 3D view. See [#101](https://github.com/BICCN/cell-locator/issues/101#issuecomment-615406252)

* Ensure load dialog is associated with directory last used for loading. See [#105](https://github.com/BICCN/cell-locator/issues/105)

## Cell Locator 0.1.0 2020-04-16

Fixes:

* Ensure Coronal referenceView is coherent between 2D and 3D view. See [#101](https://github.com/BICCN/cell-locator/issues/101)


## Cell Locator 0.1.0 2019-06-03

Features:

* Reset camera position on reset. See [#71](https://github.com/BICCN/cell-locator/issues/71)
* Leave the camera alone when creating a new annotation. See [#70](https://github.com/BICCN/cell-locator/issues/70)
  Motivation: better workflow for pinning multiple cells to the same slice
* Add a window/level slider for the background image. See [#69](https://github.com/BICCN/cell-locator/issues/69)
* Enable 2D Viewer pan and zoom. See [#68](https://github.com/BICCN/cell-locator/issues/68)
* Support for loading an annotation using `Ctrl+O` shortcut
* Support saving of view properties even if no annotation was added

Documentation:

* Add "Known Issues" section to README
* Add issue templates for QA, feature request and bug report
* Update "Keyboard Accelerators and Mouse Operations"

Fixes:

* Ensure referenceView is not reset when adding point to an annotation. See [#72](https://github.com/BICCN/cell-locator/issues/72)
* Ensure entering Roll/Pitch/Yaw values does NOT automatically Apply. See [#75](https://github.com/BICCN/cell-locator/issues/75) and [#67](https://github.com/BICCN/cell-locator/issues/67)
* Ensure Sagittal referenceView is coherent between 2D and 3D view. See [#74](https://github.com/BICCN/cell-locator/issues/74)
* Fix handling of New/Save/SaveAs/Load. See [#65](https://github.com/BICCN/cell-locator/issues/65)
* Fix "Load -> Cancel -> SaveAs" workflow. See [#86](https://github.com/BICCN/cell-locator/issues/86)
* Disable unneeded keyboard shortcuts in 3D viewer
* Update roll/pitch/yaw slides to use single step of 1 and pageStep of 5. See [#82](https://github.com/BICCN/cell-locator/issues/82)
* Only associate Unit prefix with StepSize and Thickness sliders
* Ensure loaded annotation are snapped when switching to edit mode
* Ensure load dialog is associated with directory last use for saving. See [#85](https://github.com/BICCN/cell-locator/issues/85)

## Cell Locator 0.1.0 2019-02-19

Documentation:

* Add "Keyboard Accelerators" section to README

Fixes:

* Rename S/I axis to D/V. See [#66](https://github.com/BICCN/cell-locator/issues/66)
* Fix transparency of application windows icon. See [#66](https://github.com/BICCN/cell-locator/issues/66)
* Set dialog title when creating new annotation. See [#66](https://github.com/BICCN/cell-locator/issues/66)
* Improve logo. See [#13](https://github.com/BICCN/cell-locator/issues/13)
* Ensure launcher splashscreen remains visible

## Cell Locator 0.1.0 2019-02-15

Fixes:

* Improve handling of default save location. By default, the "Documents" location is used.
  In subsequent save operation, the last known saved directory is suggested. See [#62](https://github.com/BICCN/cell-locator/issues/62)
* Do not keep track of last annotation save directory if unsuccessful saving. See [#62](https://github.com/BICCN/cell-locator/issues/62)
* Re-order orientation sliders
* Ensure the "Apply" button is always enabled when setting roll/pitch/raw
* Ensure slice orientation is restored when loading annotation
* Update SplashScreen, logo and icon. See [#13](https://github.com/BICCN/cell-locator/issues/13)

## Cell Locator 0.1.0 2019-01-26

Features:

* Add support for changing annotation type from "spline" to "polyline". [#57](https://github.com/BICCN/cell-locator/issues/57)
* Support selecting "None" Color. See [#61](https://github.com/BICCN/cell-locator/issues/61)
* Pretty-print serialized annotation file. See [#63](https://github.com/BICCN/cell-locator/issues/63)
* Add reset field of view button. See [#64](https://github.com/BICCN/cell-locator/issues/64)
* Serialize ReferenceView, StepSize, Ontology and Camera Position&ViewUp in annotation json file. See [#22](https://github.com/BICCN/cell-locator/issues/22)
* Add `Ctrl+N`, `Ctrl+S` and `Ctrl+W` shortcuts
* Do not require user to click "New" after starting the application

Fixes:

* Ensure the selected annotation point is removed. See [#42](https://github.com/BICCN/cell-locator/issues/42)
* Prevent downsizing of "New" icon
* Ensure interaction state is always up-to-date
* Improve state management of Apply, Reset and orientation sliders. Enable or disable the widget if appropriate.
* Ensure thickness is set after loading annotation
* Fix crash when loading -> closing scene -> loading
* Properly handle of view Reset without Apply
* Ensure stepSize slider singleStep is set
* Fix handling of interaction state to support "annotate" mode after loading

## Cell Locator 0.1.0 2019-01-21

* Initial Release
