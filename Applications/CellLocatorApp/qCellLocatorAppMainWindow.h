/*==============================================================================

  Copyright (c) Kitware, Inc.

  See http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Julien Finet, Kitware, Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

#ifndef __qCellLocatorAppMainWindow_h
#define __qCellLocatorAppMainWindow_h

// CellLocator includes
#include "qCellLocatorAppExport.h"
class qCellLocatorAppMainWindowPrivate;

// Slicer includes
#include "qSlicerMainWindow.h"

class Q_CELLLOCATOR_APP_EXPORT qCellLocatorAppMainWindow : public qSlicerMainWindow
{
  Q_OBJECT
public:
  typedef qSlicerMainWindow Superclass;

  qCellLocatorAppMainWindow(QWidget *parent=0);
  virtual ~qCellLocatorAppMainWindow();

public slots:
  void on_HelpAboutCellLocatorAppAction_triggered();

protected:
  qCellLocatorAppMainWindow(qCellLocatorAppMainWindowPrivate* pimpl, QWidget* parent);

private:
  Q_DECLARE_PRIVATE(qCellLocatorAppMainWindow);
  Q_DISABLE_COPY(qCellLocatorAppMainWindow);
};

#endif
