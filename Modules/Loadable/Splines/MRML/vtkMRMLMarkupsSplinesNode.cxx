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
#include <vtkMRMLMarkupsDisplayNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkBoundingBox.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>

// Locator includes
#include "vtkMRMLMarkupsSplinesNode.h"
#include "vtkMRMLMarkupsSplinesStorageNode.h"

// STD includes
#include <sstream>

//----------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLMarkupsSplinesNode);

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesNode::vtkMRMLMarkupsSplinesNode()
{
  this->CurrentSpline = -1;
  this->DefaultClosed = true;
  this->DefaultThickness = 1.0;
}

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesNode::~vtkMRMLMarkupsSplinesNode()
{
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
  return this->CurrentSpline;
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
