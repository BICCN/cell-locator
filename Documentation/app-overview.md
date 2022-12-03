# Application Overview

## Atlas Selection

After starting Cell Locator, the user is prompted with a dialog asking to choose which [reference atlas](reference-atlases.md) to load.

:::{admonition} Resetting Views
:class: tip

The `Ctrl + w` keyboard shortcut allows to reset views discarding current changes and asking to choose which reference atlas to load.
:::

:::{figure-md}
:align: center

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_atlas_selection_dialog.png" width="50%" class="no-scaled-link"/>

Atlas Selection Startup Dialog
:::

:::{admonition} Automatic Atlas Selection
:class: tip

Starting the application specifying the `--atlas-type` [command-line argument](#general-options) will skip the atlas selection startup dialog and directly load the requested altas. In this case, resetting the views also skips the atlas selection dialog.
:::

## User Interface

![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_overview.png)

### Lifecycle

* **New** allows to create a new annotation file.
* **Save** and **Save As** allow to save the current annotation(s) to file.
* **Load** allows to load annotation(s) from file.

:::{warning}
If the current annotation(s) have been modified, the user is asked if they should be saved to file before creating or loading new ones.
:::

### Annotation List

To to add, remove or duplicate an annotation, the user may click on the corresponding button:

* **Add Curve** and **Add Point** allow to add an annotation.
* **Clone** allows to duplicate the selected annotation.
* **Remove** allows to delete the selected annotation.

To rename an annotation, the user may Double-`Left-Click` on its name.

To show or hide an annotation in both viewers, the user may click on the eye icon.

:::{note}
* A `Curve` annotation is expected to have multiple points and the corresponding type can be set using the [Property Editor](#property-editor).
:::

### Interaction Modes

* **Explore** mode allows to interact with the viewers without updating the orientation of the currently selected annotation.
* **Edit** mode allows to update the selected annotation.
  * Position and size can be updated in the [2D Viewer](#2d-viewer).
  * Orientation can be updated in the [3D Viewer](#3d-viewer) by using the reformat widget or by setting specific angles.
* **Place** mode allows to add point(s) to the currently selected annotation by clicking one the slice displayed in the [2D Viewer](#2d-viewer).

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_interaction_mode.png" width="50%" align="center" class="no-scaled-link"/>

### 2D Viewer

### 3D Viewer

### Property Editor

* **Slice Step Size** configures how the [2D Viewer](#2d-viewer) slicer offset may be adjusted.
* **Annotation Thickess** updates the width of selected `Curve` annotation.
* **Annotation Type** updates how the annotation is represented in both viewers.

:::{admonition} Numeric Inputs
:class: tip

After clicking in either the **Slice Step Size** or **Annotation Thickess** spin box, its value may be updated using a "large" step as described in the [Numeric Inputs](#numeric-inputs) keyboard shortcuts.
:::

### Status Bar

* **Ontology Selector** allows to select between `None`, `Structure` and `Layer` (only available for the CFF atlas).
* **Text** about what is visible at the current mouse pointer position.

The status bar text is formatted as
  ```
  x y z | <path> (<label index>)
  ```
where:
  * `x y z` corresponds to the world coordinates (RAS).
  * `<path>` is formatted as `> structure 1 > structure 2 > ...` (or `> layer 1 > layer 2 > ...`).
  * `<label index>` corresponds to the value in the annotation volume.

| Ontology  |  Example of text |
|-----------|---|
| structure | ![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_ontology_structure.png) |
| layer     | ![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_ontology_layer.png) |

## Keyboard and Mouse Shortcuts

_On macOS use the Command key (⌘) instead of the Control (Ctrl) key_

### General

| Key        | Effect                                                |
|------------|-------------------------------------------------------|
| `Ctrl + n` | Create a new annotation                               |
| `Ctrl + s` | Save current annotation(s)                            |
| `Ctrl + o` | Load annotation(s) from file                          |
| `Ctrl + w` | Reset views discarding current changes                |
| `f`        | Increment Slice offset                                |
| `b`        | Decrement Slice offset                                |
| `r`        | Adjust field of view to match the extent of the atlas |

The user will be prompted with a save dialog before overwriting unsaved changes.

### 2D Viewer - Zoom and Pan

These interactions are enabled only in _Explore_ and _Edit_ mode.

| Interface Device | Zoom                              | Pan                       |
|------------------|-----------------------------------|---------------------------|
| 3-button mouse   | Vertical drag `Right-Click`       | Drag `Middle-Click`       |
| 2-button mouse   | Vertical drag `Right-Click`       | Drag `Shift + Left-Click` |
| 1-button mouse   | Vertical drag `Ctrl + Left-Click` | Drag `Shift + Left-Click` |
| Trackpad         | Vertical drag two fingers         | Drag `Shift + Left-Click` |

### 2D Viewer - Annotation

These interactions are enabled only in _Edit_ and _Place_ modes.

| Key or mouse operation                      | Effect                                     |
|---------------------------------------------|--------------------------------------------|
| `Left-Click` on annotation line             | Add annotation point                       |
| `Right-Click` on point then `Delete`        | Delete currently selected annotation point |
| `Ctrl + Left-Click` on annotation line      | Insert annotation point                    |
| Drag `Alt + Left-Click` on annotation line  | Rotate annotation                          |
| Drag `Alt + Right-Click` on annotation line | Scale annotation                           |
| Drag `Middle-Click` on annotation line      | Translate annotation                       |

### Numeric Inputs

`Left`/`Right` keys increment by 1, and `PgUp`/`PgDn` keys increment by a contextual "large" step.

Large step for angle inputs is 5&deg; and for distance inputs is 10mm. The `Slice Offset` steps in multiples of
the `Slice Step Size`.

### Annotation List

| Action                         | Effect               |
|--------------------------------|----------------------|
| Double-`Left-Click` annotation | Edit annotation name |
| `Left-Click` on eye icon       | Show/hide annotation |

## Command-line arguments

Cell Locator supports the same CLI arguments as 3D Slicer, as well as the following:

### General options

```{option} --annotation-file <path>
Path to an existing annotation file to be immediately loaded.
```

```{option} --reference-view <view>
Initial slice position. View may be one of `Axial`, `Coronal`, `Saggital`. Default value is `Coronal`
```

```{option} --view-angle <angle>
View angle in degrees; specifies an angle from --reference-view.
```

```{option} --atlas-type <type>
The atlas type to load. Type may be one of `ccf`, `mni`. If not provided, prompt user before startup.
```

### LIMS options

See [LIMS Integration](/lims-integration.md) for LIMS API documentation.

```{option} --lims-specimen-id <id>
LIMS specimen id to retrieve and load.
```

```{option} --lims-specimen-kind <kind>
LIMS specimen kind to load or save. Default is `'IVSCC cell locations'`.
```

```{option} --lims-base-url <url>
LIMS base url.
```
