# Welcome to Cell Locator's documentation!

Cell Locator is a free, open source and multi-platform pinning tool to facilitate mapping samples into common 3D spaces.

![](https://github.com/BICCN/cell-locator/releases/download/docs-resources/cell-locator-ccf-ui.png)

A desktop application based on [3D Slicer](https://slicer.org/) that displays the Allen Institute for Brain Science CCF or MNI atlas, color segmented by structure of the brain, and allows a user to create a planar polyline annotation to facilitate mapping samples into the corresponding atlas.

## Features

* Create, save, and load spline or polyline based annotation.
* Manage and save multiple annotations per file.
* Save annotations as JSON containing Spline or Polyline points as well
  as orientation and thickness.
* Download from / Upload to a LIMS system. See [LIMS integration](lims-integration.md)
* 3 interaction modes: Explore, Edit or Place point.
* Reslicing in arbitrary directions.
* Ontology selection: layer vs area.
* Input of Roll/Pitch/Yaw.
* Load CCF or MNI atlas. See [command-line arguments](app-overview.md#command-line-arguments).

```{toctree}
:maxdepth: 2
:caption: Contents
app-overview.md
getting-started.md
reference-atlases.md
coordinate-systems.md
lims-integration.md
command-line-tools.md
developer-guide/index.md
acknowledgments.md
```

# Indices and tables

* {ref}`genindex`
* {ref}`search`
