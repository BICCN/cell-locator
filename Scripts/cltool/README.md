# Cell Locator Conversion Tool

```text
usage: main.py [-h] [-m MODEL_PATH] [-l LABELMAP_PATH] [-a ATLAS_PATH] [--pir]
               annotation

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

## Building and installation

Slicer is no longer required to execute the script, but pending vtkAddon PyPI package, this script requires access to a
local vtk installation, and vtkAddon python bindings and is prone to linker/loader issues. These linker/loader issues 
will be resolved by using the VTK SDK to build a wheel for vtkAddon.

### It is CRITICAL that vtkAddon and VTK be built together, against the same version of Python used to launch the script.

Basic commands to build VTK, vtkAddon, and add their artifacts to the `PYTHONPATH`:

```bash
$ git clone https://gitlab.kitware.com/vtk/vtk.git --branch 9.2.2 vtk-src
$ cmake -S vtk-src -B vtk-build -DPython3_EXECUTABLE=$(which python3) -DVTK_WRAP_PYTHON=ON
$ cmake --build vtk-build

$ git clone https://github.com/Slicer/vtkAddon.git --branch add-curve-generator vtkAddon-src
$ cmake -S vtkAddon-src -B vtkAddon-build -DVTK_DIR=vtk-build -DvtkAddon_WRAP_PYTHON=ON
$ cmake --build vtkAddon-build

$ export PYTHONPATH="$PWD/vtk-build/lib/python3*/site-packages:$PWD/vtkAddon-build/:$PYTHONPATH"
```

## Sample Usage

```bash
$ python main.py samples/H18_30_002_cortex_annotation.json \
    -a atlas/mni_annotation_contiguous.nii.gz \
    -v H18_30_002_cortex_labelmap.seg.nrrd \
    -m H18_30_002_cortex_model.vtk
    
$ python main.py samples/20220406_61307.001.05.json \
    -a ccf_annotation_25_contiguous.nii.gz \
    -l 20220406_61307.001.05_labelmap.seg.nrrd \
    -m 20220406_61307.001.05_model.vtk \
    --pir 
```

## Future work

- Add option for different strategies regarding merged/separated model files, or use a multi-valued segmentation format
  rather than binary labelmap.
