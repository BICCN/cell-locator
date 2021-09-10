# User Interface

## Command-line arguments

List of command-line arguments specific to CellLocator

| Argument             | Description                                                            |
|----------------------|------------------------------------------------------------------------|
| `--reference-view`   | Accepted value: `Axial`, `Coronal` or `Sagittal`. Default is `Coronal` |                       |
| `--view-angle`       | Angle in degree                                                        |
| `--annotation-file`  | Path to an existing annotation file                                    |
| `--lims-specimen-id` | LIMS specimen id to retrieve and load                                  |
| `--lims-base-url`    | LIMS base url                                                          |
| `--atlas-type`       | Specify the atlas type to load: `ccf` or `mni`. Default is `ccf`       |

## Keyboard Accelerators and Mouse Operations

_On macOS use the Command key (⌘) instead of the Control (Ctrl) key_

### General

| Key      | Effect                                 |
|----------|----------------------------------------|
| Ctrl + n | Create a new annotation                |
| Ctrl + s | Save current annotation                |
| Ctrl + o | Load an annotation from file           |
| Ctrl + w | Reset views discarding current changes |

_If it applies, user will be prompted with a save dialog before creating, saving
or loading a annotation._


### 2D Viewer

| Key                             | Effect                                                   |
|---------------------------------|----------------------------------------------------------|
| f                               | Increment Slice offset                                   |
| b                               | Decrement Slice offset                                   |
| r                               | Adjust field of view to match the extent of the atlas    |


#### Zoom and Pan (available in Exploration and Edit mode)

| Interface Device                | Zoom                             | Pan                       |
|---------------------------------|----------------------------------|---------------------------|
| 3-button mouse                  | Right-Click & vertical drag      | Middle-Click & drag       |
| 2-button mouse                  | Right-Click & vertical drag      | Shift+Left-Click & drag   |
| 1-button mouse                  | Ctrl+Left-Click & vertical drag  | Shift+Left-Click & drag   |
| Trackpad                        | two-fingers & vertical drag      | Shift+Left-Click & drag   |


#### Annotation (available in Edit and Place modes)

| Key or mouse operation                        | Effect                                         |
|-----------------------------------------------|------------------------------------------------|
| `Left-Click` on annotation line               | Add annotation point                           |
| `Right-Click` on point then `Delete`          | Delete currently selected annotation point     |
| `Ctrl + Left-Click` on annotation line        | Insert annotation point                        |
| `Alt + Left-Click` on annotation line & drag  | Rotate annotation                              |
| `Alt + Right-Click` on annotation line & drag | Scale annotation                               |
| `Middle-Click` on annotation line & drag      | Translate annotation                           |



### 3D Viewer


| Key                             | Effect                                                   |
|---------------------------------|----------------------------------------------------------|
| f                               | Increment Slice offset                                   |
| b                               | Decrement Slice offset                                   |
| r                               | Adjust field of view to match the extent of the atlas    |

### SpinBoxes and Sliders

* Right/Left key: SingleStep increment
* PageUp/PageDown key: PageStep increment

|                       | SingleStep increment | PageStep increment       |
|-----------------------|----------------------|--------------------------|
| Raw/Pitch/Yaw         | 1                    | 5                        |
| Annotation Thickness  | 1                    | 10                       |
| Slice Step Size       | 1                    | 10                       |
| Slice Offset          | `<slice step size>`  | `<slice step size> * 10` |

### Annotation List

| Action                       | Effect               |
|------------------------------|----------------------|
| Double-click annotation name | Edit annotation name |

## LIMS integration

Support is enabled specifying command-line flags `--lims-specimen-id` and `--lims-base-url`.

If `--lims-specimen-id` command-line flag is provided, it is used:
* At application startup time to (1) retrieve the corresponding annotation from LIMS and
  load it by using the `/specimen_metadata/view` endpoint and (2) to enable the "Upload Annotation" button
* After user initiate annotation upload to LIMS while using the `/specimen_metadata/store` endpoint.

The "kind" parameter for both  endpoints `/specimen_metadata/view` and `/specimen_metadata/store`
is set to "IVSCC cell locations"

IVSCC expected cell count is currently unsupported.

For testing this functionality, a mock server as been implemented. Relevant instructions
are available here: [https://github.com/KitwareMedical/AllenInstituteMockLIMS](https://github.com/KitwareMedical/AllenInstituteMockLIMS)
