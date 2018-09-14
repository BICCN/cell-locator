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

#include "vtkMRMLScene.h"
#include "vtkSlicerVersionConfigure.h"

#include "vtkObjectFactory.h"
#include "vtkStringArray.h"
#include <vtksys/SystemTools.hxx>
#include "vtkVariantArray.h"
#include "vtkDoubleArray.h"

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

  splinesNode->SetNthSplineClosed(n, markupsMap[key + "Closed"].ToInt());
  splinesNode->SetNthSplineThickness(n, markupsMap[key + "Thickness"].ToDouble());
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

  markupsMap[key + "Closed"] = splinesNode->GetNthSplineClosed(n) ? 1 : 0;
  markupsMap[key + "Thickness"] = splinesNode->GetNthSplineThickness(n);
  return 1;
}
