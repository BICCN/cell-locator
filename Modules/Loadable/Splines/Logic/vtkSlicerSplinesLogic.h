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

// .NAME vtkSlicerSplinesLogic - slicer logic class splines manipulation
// .SECTION Description

#ifndef __vtkSlicerSplinesLogic_h
#define __vtkSlicerSplinesLogic_h

// Slicer includes
#include "vtkSlicerModuleLogic.h"

//// MRML includes
class vtkMRMLMarkupsClosedCurveNode;
class vtkMRMLModelNode;
//class vtkMRMLSelectionNode;

// VTK includes
#include <vtkSmartPointer.h>
#include <vtkVector.h>
class vtkPolyData;

#include "vtkSlicerSplinesModuleLogicExport.h"

class VTK_SLICER_SPLINES_MODULE_LOGIC_EXPORT vtkSlicerSplinesLogic : public vtkSlicerModuleLogic
{
public:

  static vtkSlicerSplinesLogic *New();
  vtkTypeMacro(vtkSlicerSplinesLogic, vtkSlicerModuleLogic);
  void PrintSelf(ostream& os, vtkIndent indent);

  /// Create a 3D slab from the given contour, normal and thickness.
  static vtkSmartPointer<vtkPolyData> CreateModelFromContour(
    vtkPolyData* inputContour, vtkVector3d normal, double thickness);

  void BuildSplineModel(vtkMRMLModelNode* modelNode, vtkPolyData *contour, vtkVector3d normal, double thickness);

protected:
  vtkSlicerSplinesLogic();
  virtual ~vtkSlicerSplinesLogic();

  // The following VTK_OVERRIDE methods are required to satisfy the vtkSlicerModuleLogic contract.
  virtual void RegisterNodes() VTK_OVERRIDE {}
  virtual void ObserveMRMLScene() VTK_OVERRIDE {}
  virtual void SetMRMLSceneInternal(vtkMRMLScene* newScene) VTK_OVERRIDE {}
  virtual void OnMRMLNodeModified(vtkMRMLNode* node) VTK_OVERRIDE {}
  virtual void OnMRMLSceneNodeAdded(vtkMRMLNode* node) VTK_OVERRIDE {}
  virtual void OnMRMLSceneNodeRemoved(vtkMRMLNode* node) VTK_OVERRIDE {}

private:
  vtkSlicerSplinesLogic(const vtkSlicerSplinesLogic&); // Not implemented
  void operator=(const vtkSlicerSplinesLogic&); // Not implemented
};

#endif
