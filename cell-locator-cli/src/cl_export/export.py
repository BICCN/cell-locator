import argparse
import json
import sys

from pathlib import Path
from typing import Iterator

from vtkmodules.vtkAddon import vtkCurveGenerator
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR
from vtkmodules.vtkCommonCore import vtkMath
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonExecutionModel import vtkPolyDataAlgorithm
from vtkmodules.vtkCommonMath import vtkMatrix3x3
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

from cl_export.vtk2sitk import vtk2sitk


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


RAS_TO_PIR_MATRIX = vtkMatrix4x4()
RAS_TO_PIR_MATRIX.DeepCopy([
    .0, +1, .0, .0,
    .0, .0, -1, .0,
    -1, .0, .0, -1,
    .0, .0, .0, +1,
])
RAS_TO_PIR_TF = vtkTransform()
RAS_TO_PIR_TF.SetMatrix(RAS_TO_PIR_MATRIX)


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

    direction = vtkMatrix3x3()
    direction.DeepCopy(reader.GetDirection())

    image = vtkImageData()
    image.SetDirectionMatrix(direction)
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

    matrix = vtkMatrix4x4()
    matrix.DeepCopy(tform.GetMatrix())

    for i in range(3):
        for j in range(3):
            matrix.SetElement(i, j, image.GetDirectionMatrix().GetElement(i, j))

    tform.SetMatrix(matrix)
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
    parser = argparse.ArgumentParser(
        description='Export Cell Locator annotations to VTK model or labelmap.',
    )
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
        image.AllocateScalars(VTK_UNSIGNED_CHAR, 1)
        image.GetPointData().GetScalars().Fill(0)

        for i, model in enumerate(models, 1):
            image = apply_stencil(model, image, i)

        writer = sitk.ImageFileWriter()
        writer.SetFileName(str(args.labelmap_path))
        writer.Execute(vtk2sitk(image))


if __name__ == "__main__":
    main()
