/*==============================================================================

Program: 3D Slicer

Copyright (c) Kitware Inc.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file was originally developed by Julien Finet, Kitware Inc.
and was partially funded by Allen Institute

==============================================================================*/

// Splines Logic includes
#include "vtkSlicerSplinesLogic.h"

// MRML includes
#include <vtkMRMLModelNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLSelectionNode.h>
#include <vtkMRMLMarkupsClosedCurveNode.h>

// VTK includes
#include <vtkEventBroker.h>
#include <vtkIntArray.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkPolyData.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkTriangle.h>
#include <vtkPoints.h>
#include <vtkCellArray.h>
#include <vtkPolyDataWriter.h>
#include <vtkAppendPolyData.h>
#include <vtkCleanPolyData.h>
#include <vtkContourTriangulator.h>

// STD includes
#include <cassert>

//----------------------------------------------------------------------------
vtkStandardNewMacro(vtkSlicerSplinesLogic);

//----------------------------------------------------------------------------
vtkSlicerSplinesLogic::vtkSlicerSplinesLogic()
{
}

//----------------------------------------------------------------------------
vtkSlicerSplinesLogic::~vtkSlicerSplinesLogic()
{
}

//----------------------------------------------------------------------------
void vtkSlicerSplinesLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os, indent);
}

//---------------------------------------------------------------------------
vtkSmartPointer<vtkPolyData> vtkSlicerSplinesLogic::CreateModelFromContour(
  vtkPolyData* inputContour, vtkVector3d normal, double thickness)
{
  if (!inputContour
    || !inputContour->GetPoints()
    || inputContour->GetPoints()->GetNumberOfPoints() < 3)
  {
    return nullptr;
  }

  vtkNew<vtkContourTriangulator> contourTriangulator;
  contourTriangulator->SetInputData(inputContour);

  vtkNew<vtkTransform> topHalfTransform;
  topHalfTransform->Translate(
    thickness * 0.5 * normal.GetX(),
    thickness * 0.5 * normal.GetY(),
    thickness * 0.5 * normal.GetZ());
  vtkNew<vtkTransform> bottomHalfTransform;
  bottomHalfTransform->Translate(
    -thickness * 0.5 * normal.GetX(),
    -thickness * 0.5 * normal.GetY(),
    -thickness * 0.5 * normal.GetZ());

  vtkNew<vtkTransformPolyDataFilter> topHalfFilter;
  topHalfFilter->SetInputConnection(contourTriangulator->GetOutputPort());
  topHalfFilter->SetTransform(topHalfTransform.GetPointer());
  topHalfFilter->Update();

  vtkNew<vtkTransformPolyDataFilter> bottomHalfFilter;
  bottomHalfFilter->SetInputConnection(contourTriangulator->GetOutputPort());
  bottomHalfFilter->SetTransform(bottomHalfTransform.GetPointer());
  bottomHalfFilter->Update();

  vtkPolyData* topHalf = topHalfFilter->GetOutput();
  vtkPolyData* bottomHalf = bottomHalfFilter->GetOutput();
  vtkNew<vtkPoints> points;
  for (vtkIdType i = 0; i < topHalf->GetNumberOfPoints(); ++i)
  {
    points->InsertNextPoint(topHalf->GetPoint(i));
    points->InsertNextPoint(bottomHalf->GetPoint(i));
  }

  vtkNew<vtkCellArray> cells;
  for (vtkIdType i = 0; i < points->GetNumberOfPoints() - 2; i += 2)
  {
    vtkNew<vtkTriangle> beltTriangle1;
    beltTriangle1->GetPointIds()->SetId(0, i);
    beltTriangle1->GetPointIds()->SetId(1, i + 1);
    beltTriangle1->GetPointIds()->SetId(2, i + 2);
    cells->InsertNextCell(beltTriangle1.GetPointer());

    vtkNew<vtkTriangle> beltTriangle2;
    beltTriangle2->GetPointIds()->SetId(0, i + 1);
    beltTriangle2->GetPointIds()->SetId(1, i + 3);
    beltTriangle2->GetPointIds()->SetId(2, i + 2);
    cells->InsertNextCell(beltTriangle2.GetPointer());
  }

  vtkNew<vtkPolyData> beltSurface;
  beltSurface->SetPoints(points.GetPointer());
  beltSurface->SetPolys(cells.GetPointer());

  vtkNew<vtkAppendPolyData> appendFilter;
  appendFilter->AddInputConnection(bottomHalfFilter->GetOutputPort());
  appendFilter->AddInputData(beltSurface);
  appendFilter->AddInputConnection(topHalfFilter->GetOutputPort());

  vtkNew<vtkCleanPolyData> cleanFilter;
  cleanFilter->SetInputConnection(appendFilter->GetOutputPort());
  cleanFilter->Update();

  return cleanFilter->GetOutput();
}

void vtkSlicerSplinesLogic::BuildSplineModel(vtkMRMLModelNode* modelNode, vtkPolyData *contour, vtkVector3d normal, double thickness) {
    if (!contour || !modelNode) return;

    vtkSmartPointer<vtkPolyData> mesh = CreateModelFromContour(
        contour, normal, thickness
    );

    modelNode->SetAndObserveMesh(mesh);

    return;
}
