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

/// Markups Module MRML storage nodes
///
/// vtkMRMLMarkupsSplinesStorageNode - MRML node for markups storage
///
/// vtkMRMLMarkupsSplinesStorageNode nodes describe the markups storage
/// node that allows to read/write point data from/to JSON.

#ifndef __vtkMRMLMarkupsSplinesStorageNode_h
#define __vtkMRMLMarkupsSplinesStorageNode_h

#include "vtkSlicerSplinesModuleMRMLExport.h"
#include "vtkMRMLMarkupsGenericStorageNode.h"

class vtkMRMLMarkupsNode;

/// \ingroup Slicer_QtModules_Markups
class VTK_SLICER_SPLINES_MODULE_MRML_EXPORT vtkMRMLMarkupsSplinesStorageNode
  : public vtkMRMLMarkupsGenericStorageNode
{
public:
  static vtkMRMLMarkupsSplinesStorageNode *New();
  vtkTypeMacro(vtkMRMLMarkupsSplinesStorageNode, vtkMRMLMarkupsGenericStorageNode);

  virtual vtkMRMLNode* CreateNodeInstance() VTK_OVERRIDE;

  ///
  /// Get node XML tag name (like Storage, Model)
  virtual const char* GetNodeTagName() VTK_OVERRIDE {return "MarkupSplinesStorage";};

  virtual bool CanReadInReferenceNode(vtkMRMLNode *refNode) VTK_OVERRIDE;

protected:
  vtkMRMLMarkupsSplinesStorageNode();
  ~vtkMRMLMarkupsSplinesStorageNode();
  vtkMRMLMarkupsSplinesStorageNode(const vtkMRMLMarkupsSplinesStorageNode&);
  void operator=(const vtkMRMLMarkupsSplinesStorageNode&);

  virtual int ReadMarkupsNodeFromTranslationMap(
    vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap);

  virtual int WriteMarkupsNodeToTranslationMap(
    vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap);

  virtual int ReadNthMarkupFromTranslationMap(
    int n, std::string key,
    vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap);

  virtual int WriteNthMarkupToTranslationMap(
    int n, std::string key,
    vtkMRMLMarkupsNode* markupsNode, TranslationMap& markupsMap);
};

#endif
