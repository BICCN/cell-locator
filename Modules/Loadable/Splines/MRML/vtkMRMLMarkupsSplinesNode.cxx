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

// MRML includes
#include <vtkMRMLCameraNode.h>
#include <vtkMRMLMarkupsDisplayNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkBoundingBox.h>
#include <vtkMathUtilities.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkMatrix4x4.h>
#include <vtkAddonMathUtilities.h>

// Locator includes
#include "vtkMRMLMarkupsSplinesNode.h"
#include "vtkMRMLMarkupsSplinesStorageNode.h"

// STD includes
#include <array>
#include <sstream>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLMarkupsSplinesNode);

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesNode::vtkMRMLMarkupsSplinesNode()
{
  this->CurrentSpline = -1;
  this->DefaultClosed = true;
  this->DefaultThickness = 1000.0;
  this->DefaultReferenceView = "Coronal";
  this->DefaultSplineOrientation = vtkSmartPointer<vtkMatrix4x4>::New();
  this->DefaultRepresentationType = "spline";
  this->DefaultStepSize = 1.0;
  this->DefaultOntology = "Structure";
}

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesNode::~vtkMRMLMarkupsSplinesNode()
{
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);

  vtkMRMLPrintBeginMacro(os, indent);
  vtkMRMLPrintIntMacro(CurrentSpline);
  vtkMRMLPrintVectorMacro(DefaultCameraPosition, double, 3);
  vtkMRMLPrintVectorMacro(DefaultCameraViewUp, double, 3);
  vtkMRMLPrintStdStringMacro(DefaultOntology);
  vtkMRMLPrintStdStringMacro(DefaultReferenceView);
  vtkMRMLPrintStdStringMacro(DefaultRepresentationType);
  vtkMRMLPrintIntMacro(DefaultStepSize);
  vtkMRMLPrintStdStringMacro(DefaultOntology);
  for(int markupIndex = 0; markupIndex < this->GetNumberOfMarkups(); ++markupIndex)
    {
    os << indent << "Spline " << markupIndex << "\n";
    vtkIndent markupIndent = indent.GetNextIndent();
    os << markupIndent << "SplineClosed              = " << this->GetNthSplineClosed(markupIndex) << "\n";
    os << markupIndent << "SplineThickness           = " << this->GetNthSplineThickness(markupIndex) << "\n";
    os << markupIndent << "SplineReferenceView       = " << this->GetNthSplineReferenceView(markupIndex) << "\n";
    os << markupIndent << "SplineRepresentationType  = " << this->GetNthSplineRepresentationType(markupIndex) << "\n";

    double cameraPosition[3] = {0.};
    this->GetNthSplineCameraPosition(markupIndex, cameraPosition);
    os << markupIndent << "SplineCameraPosition      = " << cameraPosition[0] << ", " << cameraPosition[1] << ", " << cameraPosition[2] << "\n";

    double cameraViewUp[3] = {0.};
    this->GetNthSplineCameraViewUp(markupIndex, cameraViewUp);
    os << markupIndent << "SplineCameraViewUp        = " << cameraViewUp[0] << ", " << cameraViewUp[1] << ", " << cameraViewUp[2] << "\n";

    os << markupIndent << "SplineStepSize            = " << this->GetNthSplineStepSize(markupIndex) << "\n";
    os << markupIndent << "SplineOntology            = " << this->GetNthSplineOntology(markupIndex) << "\n";

    os << markupIndent << "SplineOrientation         = " << "\n";
    this->GetNthSplineOrientation(markupIndex)->PrintSelf(os, markupIndent.GetNextIndent());

    os << markupIndent << "SplineSelectedPointIndex  = " << this->GetNthSplineSelectedPointIndex(markupIndex) << "\n";
    os << markupIndent << "SplineRepresentationType  = " << this->GetNthSplineRepresentationType(markupIndex) << "\n";
    }
  vtkMRMLPrintEndMacro();
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetCurrentSpline(int i)
{
  if (this->CurrentSpline == i)
  {
    return;
  }
  this->CurrentSpline = i;
  this->Modified();
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesNode::GetCurrentSpline() const
{
  return this->CurrentSpline;
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesNode::AddSpline(vtkVector3d point)
{
  this->CurrentSpline = this->AddPointToNewMarkup(point);
  this->Closed.push_back(this->DefaultClosed);
  this->Thickness.push_back(this->DefaultThickness);
  this->ReferenceView.push_back(this->DefaultReferenceView);
  vtkNew<vtkMatrix4x4> orientation;
  orientation->DeepCopy(this->DefaultSplineOrientation);
  this->SplineOrientation.push_back(orientation);
  this->SelectedPointIndex.push_back(-1);
  this->RepresentationType.push_back(this->DefaultRepresentationType);

  std::array<double, 3> cameraPosition = {0.};
  this->GetDefaultCameraPosition(cameraPosition.data());
  this->CameraPosition.push_back(cameraPosition);

  std::array<double, 3> cameraViewUp = {0.};
  this->GetDefaultCameraViewUp(cameraViewUp.data());
  this->CameraViewUp.push_back(cameraViewUp);

  this->StepSize.push_back(this->DefaultStepSize);
  this->Ontology.push_back(this->DefaultOntology);
  return this->CurrentSpline;
}

//----------------------------------------------------------------------------
bool vtkMRMLMarkupsSplinesNode::InitSpline(int n)
{
  if (!this->MarkupExists(n))
  {
    return false;
  }

  for (int i = this->Closed.size(); i < n+1; ++i)
  {
    this->Closed.push_back(this->DefaultClosed);
    this->Thickness.push_back(this->DefaultThickness);
    this->ReferenceView.push_back(this->DefaultReferenceView);
    vtkNew<vtkMatrix4x4> orientation;
    orientation->DeepCopy(this->DefaultSplineOrientation);
    this->SplineOrientation.push_back(orientation);
    this->SelectedPointIndex.push_back(-1);
    this->RepresentationType.push_back(this->DefaultRepresentationType);
    std::array<double, 3> cameraPosition = {0., 0., 0.};
    this->CameraPosition.push_back(cameraPosition);
    std::array<double, 3> cameraViewUp = {0., 0., 0.};
    this->CameraViewUp.push_back(cameraViewUp);
    this->StepSize.push_back(this->DefaultStepSize);
    this->Ontology.push_back(this->DefaultOntology);
  }
  return true;
}

//-------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::CreateDefaultDisplayNodes()
{
  if (this->GetDisplayNode() != NULL &&
    vtkMRMLMarkupsDisplayNode::SafeDownCast(this->GetDisplayNode()) != NULL)
  {
    // display node already exists
    return;
  }
  if (this->GetScene() == NULL)
  {
    vtkErrorMacro(
      "vtkMRMLMarkupsSplinesNode::CreateDefaultDisplayNodes failed: scene is invalid");
    return;
  }
  vtkNew<vtkMRMLMarkupsDisplayNode> dispNode;
  this->GetScene()->AddNode(dispNode.GetPointer());
  this->SetAndObserveDisplayNodeID(dispNode->GetID());
}

//-------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLMarkupsSplinesNode::CreateDefaultStorageNode()
{
  return vtkMRMLMarkupsSplinesStorageNode::New();
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineClosed(int n, bool closed)
{
  if (static_cast<size_t>(n) >= this->Closed.size() || this->Closed[static_cast<size_t>(n)] == closed)
  {
    return;
  }

  this->Closed[static_cast<size_t>(n)] = closed;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
bool vtkMRMLMarkupsSplinesNode::GetNthSplineClosed(int n)
{
  if (static_cast<size_t>(n) >= this->Closed.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultClosed;
  }
  return this->Closed[static_cast<size_t>(n)];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineThickness(int n, double thickness)
{
  if (static_cast<size_t>(n) >= this->Thickness.size()
    || this->Thickness[static_cast<size_t>(n)] == thickness)
  {
    return;
  }

  this->Thickness[static_cast<size_t>(n)] = thickness;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
double vtkMRMLMarkupsSplinesNode::GetNthSplineThickness(int n)
{
  if (static_cast<size_t>(n) >= this->Thickness.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultThickness;
  }
  return this->Thickness[static_cast<size_t>(n)];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineReferenceView(int n, const std::string& orientationReference)
{
  if (static_cast<size_t>(n) >= this->ReferenceView.size()
    || this->ReferenceView[static_cast<size_t>(n)] == orientationReference)
  {
    return;
  }

  this->ReferenceView[static_cast<size_t>(n)] = orientationReference;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
std::string vtkMRMLMarkupsSplinesNode::GetNthSplineReferenceView(int n)
{
  if (static_cast<size_t>(n) >= this->ReferenceView.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultReferenceView;
  }
  return this->ReferenceView[static_cast<size_t>(n)];
}

namespace
{

//----------------------------------------------------------------------------
bool ArrayAreEqual(const std::array<double, 3>& a1,
                   double a2[3],
                   double tolerance = 1e-3)
{
  for (size_t i = 0; i < a1.size(); i++)
    {
    if (!vtkMathUtilities::FuzzyCompare<double>(a1[i], a2[i], tolerance))
      {
      return false;
      }
    }
  return true;
}

}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineCameraPosition(int n, double position[3])
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->CameraPosition.size()
    || ArrayAreEqual(this->CameraPosition[i], position))
  {
    return;
  }
  this->CameraPosition[i][0] = position[0];
  this->CameraPosition[i][1] = position[1];
  this->CameraPosition[i][2] = position[2];
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::GetNthSplineCameraPosition(int n, double position[3])
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->CameraPosition.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    position[0] = position[1] = position[2] = 0.;
    return;
  }
  position[0] = this->CameraPosition[i][0];
  position[1] = this->CameraPosition[i][1];
  position[2] = this->CameraPosition[i][2];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineCameraViewUp(int n, double viewUp[3])
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->CameraViewUp.size()
    || ArrayAreEqual(this->CameraViewUp[i], viewUp))
  {
    return;
  }
  this->CameraViewUp[i][0] = viewUp[0];
  this->CameraViewUp[i][1] = viewUp[1];
  this->CameraViewUp[i][2] = viewUp[2];
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::GetNthSplineCameraViewUp(int n, double viewUp[3])
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->CameraViewUp.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    viewUp[0] = viewUp[1] = viewUp[2] = 0.;
    return;
  }
  viewUp[0] = this->CameraViewUp[i][0];
  viewUp[1] = this->CameraViewUp[i][1];
  viewUp[2] = this->CameraViewUp[i][2];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineStepSize(int n, double stepSize)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->StepSize.size()
    || vtkMathUtilities::FuzzyCompare<double>(this->StepSize[i], stepSize, 1e-3))
  {
    return;
  }
  this->StepSize[i] = stepSize;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
double vtkMRMLMarkupsSplinesNode::GetNthSplineStepSize(int n)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->StepSize.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return 0.0;
  }
  return this->StepSize[i];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineOntology(int n, const std::string& ontology)
{
  if (static_cast<size_t>(n) >= this->Ontology.size()
    || this->Ontology[static_cast<size_t>(n)] == ontology)
  {
    return;
  }

  this->Ontology[static_cast<size_t>(n)] = ontology;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
std::string vtkMRMLMarkupsSplinesNode::GetNthSplineOntology(int n)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->Ontology.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultOntology;
  }
  return this->Ontology[i];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineOrientation(int n, vtkMatrix4x4* matrix)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->SplineOrientation.size()
    || !matrix
    || vtkAddonMathUtilities::MatrixAreEqual(this->SplineOrientation[i], matrix))
  {
    return;
  }

  vtkNew<vtkMatrix4x4> orientation;
  orientation->DeepCopy(matrix);
  this->SplineOrientation[i] = orientation;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
vtkMatrix4x4* vtkMRMLMarkupsSplinesNode::GetNthSplineOrientation(int n)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->SplineOrientation.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultSplineOrientation;
  }
  return this->SplineOrientation[i];
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesNode::GetNthSplineSelectedPointIndex(int n)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->SelectedPointIndex.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return -1;
  }
  return this->SelectedPointIndex[i];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineSelectedPointIndex(int n, int pointIndex)
{
  if (static_cast<size_t>(n) >= this->SelectedPointIndex.size()
    || this->SelectedPointIndex[static_cast<size_t>(n)] == pointIndex)
  {
    return;
  }

  this->SelectedPointIndex[static_cast<size_t>(n)] = pointIndex;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}

//----------------------------------------------------------------------------
std::string vtkMRMLMarkupsSplinesNode::GetNthSplineRepresentationType(int n)
{
  size_t i = static_cast<size_t>(n);
  if (i >= this->RepresentationType.size())
  {
    vtkErrorMacro("The " << n << "th spline doesn't exist");
    return this->DefaultRepresentationType;
  }
  return this->RepresentationType[i];
}

//----------------------------------------------------------------------------
void vtkMRMLMarkupsSplinesNode::SetNthSplineRepresentationType(int n, const std::string& representationType)
{
  if (static_cast<size_t>(n) >= this->RepresentationType.size()
    || this->RepresentationType[static_cast<size_t>(n)] == representationType)
  {
    return;
  }

  this->RepresentationType[static_cast<size_t>(n)] = representationType;
  this->Modified();
  this->InvokeCustomModifiedEvent(
    vtkMRMLMarkupsNode::NthMarkupModifiedEvent, (void*)&n);
}
