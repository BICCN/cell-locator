## Next Release

Fixes:

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