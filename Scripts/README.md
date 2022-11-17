# Cell Locator CLI Tools

Provides some utility CLI tools for dealing with Cell Locator annotation files.

- cl-export enables converting an annotation file to VTK model or binary labelmap.
- cl-convert enables upgrading annotation files for compatibility with different versions of Cell Locator.

# Quick Start

## Installation

```bash
$ pip install cell-locator-cli
```

## Sample Usage

Update an old annotation file

```bash
$ cl-convert convert -v'?' -t v0.2 older.json newer.json
Inferred version 'v0.0.0+2020.08.26'
$ cl-convert infer newer.json                           
v0.2.1+2022.03.04
```

Export a CCF annotation to labelmap and model

```bash
$ cl-export \
  ccf-annotation.json \
  -m ccf-annotation.vtk \
  -l ccf-annotation.label.nrrd \
  -a ccf_annotation_25_contiguous.nrrd \
  --pir
$ f3d ccf-annotation.vtk
$ f3d -v ccf-annotation.label.nrrd
```

Export a MNI annotation to labelmap and model

```bash
$ cl-export \
   mni-annotation.json \
  -m mni-annotation.vtk \
  -l mni-annotation.label.nrrd \
  -a mni_annotation_contiguous.nrrd
$ f3d mni-annotation.vtk
$ f3d -v mni-annotation.label.nrrd
```

# CLI Documentation

## cl-export

```text
usage: cl-export [-h] [-m MODEL_PATH] [-l LABELMAP_PATH] [-a ATLAS_PATH]
                 [--pir]
                 annotation

Export Cell Locator annotations to VTK model or labelmap.

positional arguments:
  annotation            Input Cell Locator annotation file (JSON).

options:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model MODEL_PATH
                        Output path for annotation model. If not provided,
                        model generation is skipped.
  -l LABELMAP_PATH, --labelmap LABELMAP_PATH
                        Output path for annotation labelmap. If not provided,
                        labelmap generation is skipped. Requires --atlas for
                        spacing information.
  -a ATLAS_PATH, --atlas ATLAS_PATH
                        Atlas volume or labelmap. Used to set
                        spacing/direction on the output labelmap.
  --pir                 If set, read the annotation in PIR format rather than
                        RAS. This should only be necessary for old-style CCF
                        annotations.
```

### Future Work

- Add option for different strategies regarding merged/separated model files, or use a multi-valued segmentation format
  rather than binary labelmap.

## cl-convert

```text
usage: cl-convert convert [-h] -v VERSION [-t TARGET] [--no-indent] src dst

positional arguments:
  src                   Source JSON file. Use '-' to read from stdin.
  dst                   Destination JSON file. Use '-' to write to stdout.

options:
  -h, --help            show this help message and exit
  -v VERSION, --version VERSION
                        Source file version. Use '-v?' to infer the version.
  -t TARGET, --target TARGET
                        Target file version. Defaults to the latest version.
  --no-indent           Do not indent output JSON.
```

```text
usage: cl-convert versions [-h] [target]

positional arguments:
  target      Show versions matching this target. If empty, show all versions.

options:
  -h, --help  show this help message and exit
```

```text
usage: cl-convert infer [-h] src

positional arguments:
  src         Source JSON file. Use '-' to read from stdin.

options:
  -h, --help  show this help message and exit
```
