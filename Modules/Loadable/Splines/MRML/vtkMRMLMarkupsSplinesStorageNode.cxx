/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Johan Andruejol, Kitware Inc.
  and was partially funded by Allen Institute.

==============================================================================*/

#include "vtkMRMLMarkupsDisplayNode.h"
#include "vtkMRMLMarkupsSplinesStorageNode.h"
#include "vtkMRMLMarkupsSplinesNode.h"
#include "vtkMRMLMarkupsNode.h"

#include "vtkMRMLCameraNode.h"
#include "vtkMRMLScene.h"
#include "vtkSlicerVersionConfigure.h"

#include "vtkObjectFactory.h"
#include "vtkStringArray.h"
#include <vtksys/SystemTools.hxx>
#include "vtkVariantArray.h"
#include "vtkDoubleArray.h"
#include "vtkMatrix4x4.h"

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLMarkupsSplinesStorageNode);

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesStorageNode::vtkMRMLMarkupsSplinesStorageNode()
{
  this->DefaultWriteFileExtension = "markups.json";
}

//----------------------------------------------------------------------------
vtkMRMLMarkupsSplinesStorageNode::~vtkMRMLMarkupsSplinesStorageNode()
{
}

//----------------------------------------------------------------------------
bool vtkMRMLMarkupsSplinesStorageNode::CanReadInReferenceNode(vtkMRMLNode *refNode)
{
  return refNode->IsA("vtkMRMLMarkupsSplinesNode");
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesStorageNode::ReadMarkupsNodeFromTranslationMap(
    vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap)
{
  int success =
      this->Superclass::ReadMarkupsNodeFromTranslationMap(markupsNode, markupsMap);

  vtkMRMLMarkupsSplinesNode* splinesNode =
    vtkMRMLMarkupsSplinesNode::SafeDownCast(markupsNode);
  if (!success || !splinesNode)
  {
    return 0;
  }

  splinesNode->SetDefaultOntology(markupsMap["/DefaultOntology"].ToString());
  splinesNode->SetDefaultReferenceView(markupsMap["/DefaultReferenceView"].ToString());
  splinesNode->SetDefaultRepresentationType(markupsMap["/DefaultRepresentationType"].ToString());
  splinesNode->SetDefaultStepSize(markupsMap["/DefaultStepSize"].ToDouble());
  splinesNode->SetDefaultThickness(markupsMap["/DefaultThickness"].ToDouble());

  {
    vtkNew<vtkMatrix4x4> matrix;
    for (int i = 0; i < 4; ++i)
    {
      for (int j = 0; j < 4; ++j)
      {
        std::stringstream orientationKey;
        orientationKey << "/DefaultSplineOrientation/" << i * 4 + j;
        matrix->SetElement(i, j, markupsMap[orientationKey.str()].ToDouble());
      }
    }
    splinesNode->SetDefaultSplineOrientation(matrix);
  }

  {
    double position[3] = {0., 0., 0.};
    for (int i = 0; i < 3; ++i)
    {
      std::stringstream key;
      key << "/DefaultCameraPosition/" << i;
      position[i] = markupsMap[key.str()].ToDouble();
    }
    splinesNode->SetDefaultCameraPosition(position);
  }

  {
    double viewUp[3] = {0., 0., 0.};
    for (int i = 0; i < 3; ++i)
    {
      std::stringstream key;
      key << "/DefaultCameraViewUp/" << i;
      viewUp[i] = markupsMap[key.str()].ToDouble();
    }
    splinesNode->SetDefaultCameraViewUp(viewUp);
  }

  return 1;
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesStorageNode::WriteMarkupsNodeToTranslationMap(
  vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap)
{
  int success =
      this->Superclass::WriteMarkupsNodeToTranslationMap(markupsNode, markupsMap);

  vtkMRMLMarkupsSplinesNode* splinesNode =
      vtkMRMLMarkupsSplinesNode::SafeDownCast(markupsNode);
  if (!success || !splinesNode)
  {
    return 0;
  }

  markupsMap["/DefaultOntology"] = splinesNode->GetDefaultOntology().c_str();
  markupsMap["/DefaultRepresentationType"] = splinesNode->GetDefaultRepresentationType().c_str();
  markupsMap["/DefaultReferenceView"] = splinesNode->GetDefaultReferenceView().c_str();
  markupsMap["/DefaultStepSize"] = splinesNode->GetDefaultStepSize();
  markupsMap["/DefaultThickness"] = splinesNode->GetDefaultThickness();

  {
    vtkMatrix4x4* matrix = splinesNode->GetDefaultSplineOrientation();
    for (int i = 0; i < 4; ++i)
    {
      for (int j = 0; j < 4; ++j)
      {
        std::stringstream orientationKey;
        orientationKey << "/DefaultSplineOrientation/" << i * 4 + j;
        markupsMap[orientationKey.str()] = matrix->GetElement(i, j);
      }
    }
  }

  {
    double position[3] = {0.};
    splinesNode->GetDefaultCameraPosition(position);
    for (int i = 0; i < 3; ++i)
    {
      std::stringstream key;
      key << "/DefaultCameraPosition/" << i;
      markupsMap[key.str()] = position[i];
    }
  }

  {
    double viewUp[3] = {0.};
    splinesNode->GetDefaultCameraViewUp(viewUp);
    for (int i = 0; i < 3; ++i)
    {
      std::stringstream key;
      key << "/DefaultCameraViewUp/" << i;
      markupsMap[key.str()] = viewUp[i];
    }
  }

  return 1;
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesStorageNode::ReadNthMarkupFromTranslationMap(
  int n, std::string key,
  vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap)
{
  int success =
    Superclass::ReadNthMarkupFromTranslationMap(n, key, markupsNode, markupsMap);

  vtkMRMLMarkupsSplinesNode* splinesNode =
    vtkMRMLMarkupsSplinesNode::SafeDownCast(markupsNode);
  if (!success || !splinesNode)
  {
    return 0;
  }

  splinesNode->InitSpline(n);
  splinesNode->SetNthSplineRepresentationType(n, markupsMap[key + "RepresentationType"].ToString());
  splinesNode->SetNthSplineClosed(n, markupsMap[key + "Closed"].ToInt());
  splinesNode->SetNthSplineThickness(n, markupsMap[key + "Thickness"].ToDouble());
  splinesNode->SetNthSplineReferenceView(n, markupsMap[key + "ReferenceView"].ToString());
  splinesNode->SetNthSplineStepSize(n, markupsMap[key + "StepSize"].ToDouble());
  splinesNode->SetNthSplineOntology(n, markupsMap[key + "Ontology"].ToString());

  vtkNew<vtkMatrix4x4> matrix;
  for (int i = 0; i < 4; ++i)
  {
    for (int j = 0; j < 4; ++j)
    {
      std::stringstream orientationKey;
      orientationKey << key << "SplineOrientation/" << i * 4 + j;
      matrix->SetElement(i, j, markupsMap[orientationKey.str()].ToDouble());
    }
  }
  splinesNode->SetNthSplineOrientation(n, matrix);

  double position[3] = {0., 0., 0.};
  for (int i = 0; i < 3; ++i)
  {
    std::stringstream cameraPositionKey;
    cameraPositionKey << key << "CameraPosition/" << i;
    position[i] = markupsMap[cameraPositionKey.str()].ToDouble();
  }
  splinesNode->SetNthSplineCameraPosition(n, position);

  double viewUp[3] = {0., 0., 0.};
  for (int i = 0; i < 3; ++i)
  {
    std::stringstream cameraViewUpKey;
    cameraViewUpKey << key << "CameraViewUp/" << i;
    viewUp[i] = markupsMap[cameraViewUpKey.str()].ToDouble();
  }
  splinesNode->SetNthSplineCameraViewUp(n, viewUp);

  return 1;
}

//----------------------------------------------------------------------------
int vtkMRMLMarkupsSplinesStorageNode::WriteNthMarkupToTranslationMap(
  int n, std::string key,
  vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap)
{
  int success =
    Superclass::WriteNthMarkupToTranslationMap(n, key, markupsNode, markupsMap);
  vtkMRMLMarkupsSplinesNode* splinesNode =
    vtkMRMLMarkupsSplinesNode::SafeDownCast(markupsNode);
  if (!success || !splinesNode)
  {
    return 0;
  }

  markupsMap[key + "RepresentationType"] = vtkStdString(splinesNode->GetNthSplineRepresentationType(n));
  markupsMap[key + "Closed"] = splinesNode->GetNthSplineClosed(n) ? 1 : 0;
  markupsMap[key + "Thickness"] = splinesNode->GetNthSplineThickness(n);
  markupsMap[key + "ReferenceView"] = vtkStdString(splinesNode->GetNthSplineReferenceView(n));
  markupsMap[key + "StepSize"] = splinesNode->GetNthSplineStepSize(n);
  markupsMap[key + "Ontology"] = vtkStdString(splinesNode->GetNthSplineOntology(n));

  vtkMatrix4x4* matrix = splinesNode->GetNthSplineOrientation(n);
  for (int i = 0; i < 4; ++i)
  {
    for (int j = 0; j < 4; ++j)
    {
      std::stringstream orientationKey;
      orientationKey << key << "SplineOrientation/" << i * 4 + j;
      markupsMap[orientationKey.str()] = matrix->GetElement(i, j);
    }
  }

  double position[3] = {0., 0., 0.};
  splinesNode->GetNthSplineCameraPosition(n, position);
  for (int i = 0; i < 3; ++i)
  {
    std::stringstream cameraPositionKey;
    cameraPositionKey << key << "CameraPosition/" << i;
    markupsMap[cameraPositionKey.str()] = position[i];
  }

  double viewUp[3] = {0., 0., 0.};
  splinesNode->GetNthSplineCameraViewUp(n, viewUp);
  for (int i = 0; i < 3; ++i)
  {
    std::stringstream cameraViewUpKey;
    cameraViewUpKey << key << "CameraViewUp/" << i;
    markupsMap[cameraViewUpKey.str()] = viewUp[i];
  }

  return 1;
}
