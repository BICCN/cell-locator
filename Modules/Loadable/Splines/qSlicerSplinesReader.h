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

  This file was originally developed by Johan Andruejol, Kitware Inc.
  and was partially funded by Allen Institute

==============================================================================*/

#ifndef __qSlicerSplinesReader_h
#define __qSlicerSplinesReader_h

// SlicerQt includes
#include "qSlicerMarkupsReader.h"

class qSlicerSplinesReaderPrivate;
class vtkSlicerSplinesLogic;
class vtkSlicerMarkupsLogic;

//----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_Splines
class qSlicerSplinesReader : public qSlicerMarkupsReader
{
  Q_OBJECT
public:
  typedef qSlicerMarkupsReader Superclass;
  qSlicerSplinesReader(QObject* parent = 0);
  qSlicerSplinesReader(vtkSlicerMarkupsLogic* logic,
    vtkSlicerSplinesLogic* splinesLogic,
    QObject* parent = 0);
  virtual ~qSlicerSplinesReader();

  vtkSlicerSplinesLogic* splinesLogic()const;
  void setSplinesLogic(vtkSlicerSplinesLogic* logic);

  virtual QString description()const;
  virtual IOFileType fileType()const;

protected:
  QScopedPointer<qSlicerSplinesReaderPrivate> d_ptr;

  virtual char* load(const QString& filename, const QString& name);

private:
  Q_DECLARE_PRIVATE(qSlicerSplinesReader);
  Q_DISABLE_COPY(qSlicerSplinesReader);
};

#endif
