# Application Overview

## User Interface

## Keyboard Shortcuts

## Command-line arguments

Cell Locator supports the same CLI arguments as 3D Slicer, in addition to these options:

```{option} --reference-view <view>
Initial slice position. View may be one of `Axial`, `Coronal`, `Saggital`. Default value is `Coronal`
```

```{option} --view-angle <angle>
View angle in degrees; specifies an angle from --reference-view.
```

```{option} --annotation-file <path>
Path to an existing annotation file to be immediately loaded.
```

```{option} --atlas-type <type>
The atlas type to load. Type may be one of `ccf`, `mni`. If not provided, prompt user before startup.
```

```{option} --lims-specimen-id <id>
LIMS specimen id to retrieve and load
```

```{option} --lims-specimen-kind <kind>
LIMS specimen kind to load or save. Default is `'IVSCC cell locations'`
```

```{option} --lims-base-url <url>
LIMS base url
```
