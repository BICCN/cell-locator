# Application Overview

## User Interface

## Keyboard and Mouse Shortcuts

_On macOS use the Command key (⌘) instead of the Control (Ctrl) key_

### General

| Key        | Effect                                                |
|------------|-------------------------------------------------------|
| `Ctrl + n` | Create a new annotation                               |
| `Ctrl + s` | Save current annotation                               |
| `Ctrl + o` | Load an annotation from file                          |
| `Ctrl + w` | Reset views discarding current changes                |
| `f`        | Increment Slice offset                                |
| `b`        | Decrement Slice offset                                |
| `r`        | Adjust field of view to match the extent of the atlas |

The user will be prompted with a save dialog before overwriting unsaved changes.

### 2D Viewer - Zoom and Pan

These interactions are enabled only in Exploration and Edit mode.

| Interface Device | Zoom                              | Pan                       |
|------------------|-----------------------------------|---------------------------|
| 3-button mouse   | Vertical drag `Right-Click`       | Drag `Middle-Click`       |
| 2-button mouse   | Vertical drag `Right-Click`       | Drag `Shift + Left-Click` |
| 1-button mouse   | Vertical drag `Ctrl + Left-Click` | Drag `Shift + Left-Click` |
| Trackpad         | Vertical drag two fingers         | Drag `Shift + Left-Click` |

### 2D Viewer - Annotation

These interactions are enabled only in Edit and Place modes.

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
