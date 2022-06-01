"""cltool export script. Convert Cell Locator annotation JSON to VTK model or segmentations.

=======================================================================================================================

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

Slicer is no longer required to execute the script, but pending vtkAddon PyPI package, this script requires access to a
local vtk installation, and vtkAddon python bindings and is prone to linker/loader issues.

=======================================================================================================================
 It is CRITICAL that vtkAddon and VTK be built together, against the same version of Python used to launch the script.
 These linker/loader issues will be resolved by using the VTK SDK to build a wheel for vtkAddon.
=======================================================================================================================

Basic commands to build VTK, vtkAddon, and add their artifacts to the PYTHONPATH:

$ git clone https://gitlab.kitware.com/vtk/vtk.git --branch 9.2.2 vtk-src
$ cmake -S vtk-src -B vtk-build -DPython3_EXECUTABLE=$(which python3) -DVTK_WRAP_PYTHON=ON
$ cmake --build vtk-build

$ git clone https://github.com/Slicer/vtkAddon.git --branch add-curve-generator vtkAddon-src
$ cmake -S vtkAddon-src -B vtkAddon-build -DVTK_DIR=vtk-build -DvtkAddon_WRAP_PYTHON=ON
$ cmake --build vtkAddon-build

$ export PYTHONPATH="$PWD/vtk-build/lib/python3*/site-packages:$PWD/vtkAddon-build/:$PYTHONPATH"

=======================================================================================================================

Sample usage:

$ python main.py samples/H18_30_002_cortex_annotation.json \
    -a atlas/mni_annotation_contiguous.nii.gz \
    -v H18_30_002_cortex_labelmap.seg.nrrd \
    -m H18_30_002_cortex_model.vtk

$ python main.py samples/20220406_61307.001.05.json \
    -a ccf_annotation_25_contiguous.nii.gz \
    -l 20220406_61307.001.05_labelmap.seg.nrrd \
    -m 20220406_61307.001.05_model.vtk \
    --pir
"""

import argparse
import json
import sys

from pathlib import Path
from typing import Iterator

import vtk
from vtkmodules.vtkCommonCore import vtkMath
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonExecutionModel import vtkPolyDataAlgorithm
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkAppendPolyData
from vtkmodules.vtkFiltersGeneral import vtkContourTriangulator
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersModeling import vtkLinearExtrusionFilter
from vtkmodules.vtkIOLegacy import vtkPolyDataWriter
from vtkmodules.vtkImagingStencil import vtkImageStencil
from vtkmodules.vtkImagingStencil import vtkPolyDataToImageStencil

import SimpleITK as sitk
from vtk2sitk import vtk2sitk

# must come after `import vtk` or else segfault. todo replace with wheel
from vtkAddonPython import vtkCurveGenerator


def make_curve(
    points: vtkPoints, normal: list, curve_type: str
) -> vtkPolyDataAlgorithm:
    curve_gen = vtkCurveGenerator()

    if curve_type == "spline":
        curve_gen.SetCurveTypeToCardinalSpline()
    elif curve_type == "polyline":
        curve_gen.SetCurveTypeToLinearSpline()
    else:
        raise ValueError("Unrecognized curve type {!r}".format(curve_type))

    curve_gen.SetCurveIsClosed(True)
    curve_gen.SetNumberOfPointsPerInterpolatingSegment(32)
    curve_gen.SetInputPoints(points)

    triangulator = vtkContourTriangulator()
    triangulator.SetInputConnection(curve_gen.GetOutputPort())

    # so the result is centered on the curve plane
    offset = list(normal)
    vtkMath.MultiplyScalar(offset, -0.5)
    offset_tf = vtkTransform()
    offset_tf.Translate(offset)

    bottom = vtkTransformPolyDataFilter()
    bottom.SetTransform(offset_tf)
    bottom.SetInputConnection(triangulator.GetOutputPort())

    extrude = vtkLinearExtrusionFilter()
    extrude.SetExtrusionTypeToVectorExtrusion()
    extrude.SetVector(normal)
    extrude.CappingOn()
    extrude.SetInputConnection(bottom.GetOutputPort())

    return extrude


RAS_TO_PIR_TF = vtkTransform()
RAS_TO_PIR_TF.GetMatrix().DeepCopy([
    .0, +1, .0, .0,
    .0, .0, -1, .0,
    -1, .0, .0, -1,
    .0, .0, .0, +1,
])


def ras_to_pir(model: vtkPolyDataAlgorithm) -> vtkPolyDataAlgorithm:
    tform = vtkTransformPolyDataFilter()
    tform.SetInputConnection(model.GetOutputPort())
    tform.SetTransform(RAS_TO_PIR_TF)
    return tform


def load_annotation(filename: str) -> Iterator[vtkPolyDataAlgorithm]:
    with open(filename) as f:
        data = json.load(f)

    for markup in data["markups"]:
        curve_type = markup["representationType"]

        points = vtkPoints()
        for control_point in markup["markup"]["controlPoints"]:
            points.InsertNextPoint(control_point["position"])

        orientation = vtkMatrix4x4()
        orientation.DeepCopy(markup["orientation"])

        thickness = markup["thickness"]
        normal = orientation.MultiplyPoint([0, 0, 1, 0])[:3]
        normal = list(normal)
        vtkMath.Normalize(normal)
        vtkMath.MultiplyScalar(normal, thickness)

        yield make_curve(points, normal, curve_type)


def vtkImageData_like(filename):
    reader = sitk.ImageFileReader()
    reader.SetFileName(str(filename))

    reader.LoadPrivateTagsOn()
    reader.ReadImageInformation()

    image = vtkImageData()
    image.GetDirectionMatrix().DeepCopy(reader.GetDirection())
    image.SetOrigin(*reader.GetOrigin())
    image.SetSpacing(*reader.GetSpacing())
    image.SetDimensions(*reader.GetSize())

    return image


def apply_stencil(
    model: vtkPolyDataAlgorithm, image: vtkImageData, val
) -> vtkImageData:
    # vtkPolyDataToImageStencil and vtkImageStencil do not respect image Direction. They do respect Origin and Spacing.
    #
    # However since the linear part of the transformation comes before the translation part, we must handle Direction
    # and Origin together. The scaling part comes last, so we can let vtkImageStencil handle Spacing.
    #
    # Compute the linear and translational parts of the transform; then use the _inverse_ of that to move the model
    # into the "local" space of the image.

    tform = vtkTransform()
    tform.Translate(image.GetOrigin())
    for i in range(3):
        for j in range(3):
            tform.GetMatrix().SetElement(
                i, j, image.GetDirectionMatrix().GetElement(i, j)
            )
    tform.Inverse()

    model_local = vtkTransformPolyDataFilter()
    model_local.SetInputConnection(model.GetOutputPort())
    model_local.SetTransform(tform)

    # Now that the model is in "local" space of the image, we can safely ignore Direction and Origin and use
    # vtkImageStencil as normal.
    to_stencil = vtkPolyDataToImageStencil()
    to_stencil.SetInputConnection(model_local.GetOutputPort())
    to_stencil.SetOutputSpacing(image.GetSpacing())
    to_stencil.SetOutputWholeExtent(image.GetExtent())

    stencil = vtkImageStencil()
    stencil.SetInputData(image)
    stencil.SetStencilConnection(to_stencil.GetOutputPort())
    stencil.ReverseStencilOn()
    stencil.SetBackgroundValue(val)

    stencil.Update()

    # Up to this point we operated in "local" space for the image; the stencil is done now propagate the
    # Direction/Origin to the output image.
    output = stencil.GetOutput()
    output.SetDirectionMatrix(image.GetDirectionMatrix())
    output.SetOrigin(image.GetOrigin())
    output.SetSpacing(image.GetSpacing())
    output.SetExtent(image.GetExtent())

    return output


def _parser():
    prog = Path(__file__).name
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        metavar="annotation",
        dest="annotation_path",
        type=Path,
        help="Input Cell Locator annotation file (JSON).",
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model_path",
        type=Path,
        help="Output path for annotation model. If not provided, model generation is skipped.",
        default=None,
    )
    parser.add_argument(
        "-l",
        "--labelmap",
        dest="labelmap_path",
        type=Path,
        help=(
            "Output path for annotation labelmap. If not provided, labelmap generation is skipped. Requires --atlas "
            "for spacing information. "
        ),
        default=None,
    )
    parser.add_argument(
        "-a",
        "--atlas",
        dest="atlas_path",
        type=Path,
        help="Atlas volume or labelmap. Used to set spacing/direction on the output labelmap.",
        default=None,
    )
    parser.add_argument(
        "--pir",
        action="store_true",
        dest="pir",
        help=(
            "If set, read the annotation in PIR format rather than RAS. This should only be necessary for old-style "
            "CCF annotations. "
        ),
        default=False,
    )

    return parser


def main():
    parser = _parser()
    args = parser.parse_args()

    if args.labelmap_path and not args.atlas_path:
        print(
            "--labelmap requires --atlas to determine output spacing/orientation.",
            file=sys.stderr,
        )
        exit(-1)

    models = list(load_annotation(args.annotation_path))

    if args.pir:
        models = [ras_to_pir(model) for model in models]

    if args.model_path:
        append = vtkAppendPolyData()
        for model in models:
            append.AddInputConnection(model.GetOutputPort())

        writer = vtkPolyDataWriter()
        writer.SetFileName(str(args.model_path))
        writer.SetInputConnection(append.GetOutputPort())
        writer.Update()

    if args.labelmap_path:
        image = vtkImageData_like(args.atlas_path)
        image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
        image.GetPointData().GetScalars().Fill(0)

        for i, model in enumerate(models, 1):
            image = apply_stencil(model, image, i)

        writer = sitk.ImageFileWriter()
        writer.SetFileName(str(args.labelmap_path))
        writer.Execute(vtk2sitk(image))


if __name__ == "__main__":
    main()
