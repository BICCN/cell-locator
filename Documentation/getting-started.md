# Getting Started

## Installing Cell Locator

Download the [latest release on GitHub](https://github.com/BICCN/cell-locator/releases/latest)

## System Requirements

Cell Locator is built using 3D Slicer, so refer to the 
[3D Slicer System Requirements](https://slicer.readthedocs.io/en/latest/user_guide/getting_started.html#system-requirements).

:::{admonition} Cross-platform Availability
:class: tip

Installers are only generated for 64-bit Windows, however it is possible to build Cell Locator from source on any platform which supports 3D Slicer. Refer to the [developer guide](developer-guide/building.md) for build instructions.
:::

## Using Cell Locator

### Quick Start

After starting Cell Locator, you will choose an atlas.

:::{figure-md}
:align: center

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/app_atlas_selection_dialog.png" width="50%" class="no-scaled-link"/>

Atlas Selection Startup Dialog
:::

After selecting an atlas, the application is ready with an annotation named _Curve_ already created.

Before adding points to the annotation:

1. Switch to _Edit_ interaction mode.

2. Use the reformat widget available in the 3D viewer on the right to update the orientation and identify a slice plane of interest.

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/getting_started_1.png" width="80%" align="center" class="no-scaled-link"/>

:::{admonition} Hint
:class: tip

Alternatively, you may directly set the the raw, pitch and yaw angles.
:::

You can  switch to _Place_ interaction mode and start adding points to the annotation.

1. Left-Click to add (or place) points.

2. Right-Click to switch back to the _Edit_ interaction mode.

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/getting_started_2.png" width="80%" align="center" class="no-scaled-link"/>

Once you are done adding points, you can update annotation properties.

1. Switch the annotation type from _Spline_ to _PolyLine_.

2. Renane the extension.

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/getting_started_3.png" width="80%" align="center" class="no-scaled-link"/>

Finally, you can save the annotation as a `.json` file by clicking on the _Save_ button.

<img src="https://github.com/BICCN/cell-locator/releases/download/docs-resources/getting_started_4.png" width="80%" align="center" class="no-scaled-link"/>

### User manual

Browse the [Application Overview](app-overview.md) section to learn about the application user interface.