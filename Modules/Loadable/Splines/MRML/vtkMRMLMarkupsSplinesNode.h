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

#ifndef __vtkMRMLMarkupsSplinesNode_h
#define __vtkMRMLMarkupsSplinesNode_h

// MRML includes
#include <vtkMRMLMarkupsNode.h>

// Markups includes
#include "vtkSlicerSplinesModuleMRMLExport.h"

// VTK includes
#include <vtkSmartPointer.h>

class vtkMRMLCameraNode;
class vtkMRMLMarkupsDisplayNode;

//
//
class  VTK_SLICER_SPLINES_MODULE_MRML_EXPORT vtkMRMLMarkupsSplinesNode
  : public vtkMRMLMarkupsNode
{
public:
  static vtkMRMLMarkupsSplinesNode *New();
  vtkTypeMacro(vtkMRMLMarkupsSplinesNode, vtkMRMLMarkupsNode);

  virtual const char* GetIcon() VTK_OVERRIDE { return ":/Icons/SplinesMouseModePlace.png"; }

  //--------------------------------------------------------------------------
  // MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance() VTK_OVERRIDE;
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() VTK_OVERRIDE { return "MarkupsSpline"; };

  // Return the current spline index which may be modified.
  // -1 means no spline is selected.
  void SetCurrentSpline(int i);
  int GetCurrentSpline() const;

  // Add an empty spline and return its index. The new spline is automatically
  // the current spline.
  int AddSpline(vtkVector3d point);

  // Init the correct variable for the nth spline. The markup must already
  // exists.
  bool InitSpline(int n);

  /// Create and observe default display node(s)
  virtual void CreateDefaultDisplayNodes() VTK_OVERRIDE;

  /// Create and observe default storage node
  virtual vtkMRMLStorageNode* CreateDefaultStorageNode() VTK_OVERRIDE;

  void SetNthSplineClosed(int n, bool closed);
  bool GetNthSplineClosed(int n);

  void SetNthSplineThickness(int n, double thickness);
  double GetNthSplineThickness(int n);

  /// Set/Get default reference view
  ///
  /// \note This property is specific to CellLocator
  vtkGetMacro(DefaultReferenceView, std::string);
  vtkSetMacro(DefaultReferenceView, std::string);

  /// Set/Get the reference view of the Nth spline (Axial, Sagittal or Coronal)
  ///
  /// \note This property is specific to CellLocator
  void SetNthSplineReferenceView(int n, const std::string& orientationReference);
  std::string GetNthSplineReferenceView(int n);

  /// Set/Get camera position
  ///
  /// \note This property is specific to CellLocator
  void SetNthSplineCameraPosition(int n, double position[3]);
  void GetNthSplineCameraPosition(int n, double position[3]);

  /// Set/Get camera view up
  ///
  /// \note This property is specific to CellLocator
  void SetNthSplineCameraViewUp(int n, double viewUp[3]);
  void GetNthSplineCameraViewUp(int n, double viewUp[3]);

  /// Set/Get default step size
  vtkGetMacro(DefaultStepSize, double);
  vtkSetMacro(DefaultStepSize, double);

  /// Set/Get slice viewer step size
  ///
  /// \note This property is specific to CellLocator
  void SetNthSplineStepSize(int n, double stepSize);
  double GetNthSplineStepSize(int n);

  void SetNthSplineOrientation(int n, vtkMatrix4x4* matrix);
  vtkMatrix4x4* GetNthSplineOrientation(int n);

  int GetNthSplineSelectedPointIndex(int n);
  void SetNthSplineSelectedPointIndex(int n, int pointIndex);

  /// Set/Get default representation type
  vtkGetMacro(DefaultRepresentationType, std::string);
  vtkSetMacro(DefaultRepresentationType, std::string);

  /// Set/Get the representation type of the Nth spline (polyline or spline)
  std::string GetNthSplineRepresentationType(int n);
  void SetNthSplineRepresentationType(int n, const std::string& representationType);

protected:
  vtkMRMLMarkupsSplinesNode();
  ~vtkMRMLMarkupsSplinesNode();
  vtkMRMLMarkupsSplinesNode(const vtkMRMLMarkupsSplinesNode&);
  void operator=(const vtkMRMLMarkupsSplinesNode&);

  int CurrentSpline;
  bool DefaultClosed;
  std::vector<bool> Closed;
  double DefaultThickness;
  std::vector<double> Thickness;
  vtkSmartPointer<vtkMatrix4x4> DefaultSplineOrientation;
  std::vector< vtkSmartPointer<vtkMatrix4x4> > SplineOrientation;
  std::vector<int> SelectedPointIndex;
  std::string DefaultRepresentationType;
  std::vector<std::string> RepresentationType;
  std::string DefaultReferenceView;
  std::vector<std::string> ReferenceView;
  std::vector< std::array<double, 3> > CameraPosition;
  std::vector< std::array<double, 3> > CameraViewUp;
  double DefaultStepSize;
  std::vector<double> StepSize;
};

#endif
