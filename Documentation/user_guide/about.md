# About Cell-Locator

## What is Cell-Locator?

A free, open source and multi-platform pinning tool to facilitate mapping samples into
common 3D spaces.

A desktop application based on 3D Slicer that displays the Allen Institute for Brain Science
CCF or MNI atlas, color segmented by structure of the brain, and allows a user to create a
planar polyline annotation to facilitate mapping samples into the corresponding atlas.

## Features

* Create, save, and load spline or polyline based annotation.
* Manage and save multiple annotations per file.
* Save annotations as JSON containing Spline or Polyline points as well
  as orientation and thickness.
* Download from / Upload to a LIMS system. See [LIMS integration](user_interface.html#lims-integration)
* 3 interaction modes: Explore, Edit or Place point.
* Reslicing in arbitrary directions.
* Ontology selection: layer vs area.
* Input of Roll/Pitch/Yaw.
* Load CCF or MNI atlas. See [command-line arguments](user_interface.html#command-line-arguments).

## Screenshots

Example of annotations mapped into the CCF:

![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/cell-locator-ccf-ui.png)

Example of annotations mapped into the MNI:

![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/cell-locator-mni-ui.png)

## Known Issues

* For Roll, pitch and yaw, the angle mappings differ from the coordinate system the lab uses. See [#81](https://github.com/BICCN/cell-locator/issues/81)
