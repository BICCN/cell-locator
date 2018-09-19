/*==============================================================================

  Program: 3D Slicer

  Portions (c) Copyright Kitware Inc. All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Johan Andruejol, Kitware Inc.
  and was partially funded by Allen Institute

==============================================================================*/

// SlicerQt includes
#include "qSlicerSplinesReader.h"

// Logic includes
#include "vtkSlicerSplinesLogic.h"

// VTK includes
#include <vtkSmartPointer.h>

//-----------------------------------------------------------------------------
class qSlicerSplinesReaderPrivate
{
  public:
  vtkSmartPointer<vtkSlicerSplinesLogic> SplinesLogic;
};

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_Annotations
//-----------------------------------------------------------------------------
qSlicerSplinesReader::qSlicerSplinesReader(QObject* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerSplinesReaderPrivate)
{
}

//-----------------------------------------------------------------------------
qSlicerSplinesReader
::qSlicerSplinesReader(
  vtkSlicerMarkupsLogic* markupsLogic,
  vtkSlicerSplinesLogic* splinesLogic,
  QObject* _parent)
  : Superclass(markupsLogic, _parent)
  , d_ptr(new qSlicerSplinesReaderPrivate)
{
  this->setMarkupsLogic(markupsLogic);
  this->setSplinesLogic(splinesLogic);
}

//-----------------------------------------------------------------------------
qSlicerSplinesReader::~qSlicerSplinesReader()
{
}

//-----------------------------------------------------------------------------
void qSlicerSplinesReader::setSplinesLogic(vtkSlicerSplinesLogic* logic)
{
  Q_D(qSlicerSplinesReader);
  d->SplinesLogic = logic;
}

//-----------------------------------------------------------------------------
vtkSlicerSplinesLogic* qSlicerSplinesReader::splinesLogic()const
{
  Q_D(const qSlicerSplinesReader);
  return d->SplinesLogic.GetPointer();
}

//-----------------------------------------------------------------------------
QString qSlicerSplinesReader::description()const
{
  return "MarkupsSplines";
}

//-----------------------------------------------------------------------------
qSlicerIO::IOFileType qSlicerSplinesReader::fileType()const
{
  return QString("MarkupsSplines");
}

//-----------------------------------------------------------------------------
char* qSlicerSplinesReader
::load(const QString& filename, const QString& name)
{
  return this->splinesLogic()->LoadMarkupsSplines(
    filename.toLatin1(), name.toLatin1());
}
