# Command Line Tools

Utility CLI tools for processing Cell Locator annotation files.

For information on extending `cl-convert`, see the [Converter API Documentation](developer-guide/index.md)

## Installation

```bash
$ pip install cell-locator-cli
```

## Tools

```{eval-rst}
.. autoprogram:: cl_export.export:_parser()
    :prog: cl-export
```

```{eval-rst}
.. autoprogram:: cl_convert.convert:_parser()
    :prog: cl-convert
```

## Sample Usage

Export an MNI annotation to labelmap and model

```bash
$ cl-export \
   mni-annotation.json \
  -m mni-annotation.vtk \
  -l mni-annotation.label.nrrd \
  -a mni_annotation_contiguous.nrrd
$ f3d mni-annotation.vtk
$ f3d -v mni-annotation.label.nrrd
```

Export a CCF annotation to labelmap only

```bash
$ cl-export \
  ccf-annotation.json \
  -l ccf-annotation.label.nrrd \
  -a ccf_annotation_25_contiguous.nrrd \
  --pir
$ f3d ccf-annotation.vtk
$ f3d -v ccf-annotation.label.nrrd
```

Update an old annotation file

```bash
$ cl-convert convert -v'?' -t v0.2 older.json newer.json
Inferred version 'v0.0.0+2020.08.26'
$ cl-convert infer newer.json                           
v0.2.1+2022.03.04
```
