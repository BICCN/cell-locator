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

// CellLocator includes
#include "qCellLocatorAppMainWindow.h"
#include "qCellLocatorAppMainWindow_p.h"

// Qt includes
#include <QDesktopWidget>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"

//-----------------------------------------------------------------------------
// qCellLocatorAppMainWindowPrivate methods

qCellLocatorAppMainWindowPrivate::qCellLocatorAppMainWindowPrivate(qCellLocatorAppMainWindow& object)
  : Superclass(object)
{
}

//-----------------------------------------------------------------------------
qCellLocatorAppMainWindowPrivate::~qCellLocatorAppMainWindowPrivate()
{
}

//-----------------------------------------------------------------------------
void qCellLocatorAppMainWindowPrivate::init()
{
  Q_Q(qCellLocatorAppMainWindow);
  this->Superclass::init();
}

//-----------------------------------------------------------------------------
void qCellLocatorAppMainWindowPrivate::setupUi(QMainWindow * mainWindow)
{
  qSlicerApplication * app = qSlicerApplication::application();

  //----------------------------------------------------------------------------
  // Add actions
  //----------------------------------------------------------------------------
  QAction* helpAboutSlicerAppAction = new QAction(mainWindow);
  helpAboutSlicerAppAction->setObjectName("HelpAboutCellLocatorAppAction");
  helpAboutSlicerAppAction->setText("About " + app->applicationName());

  //----------------------------------------------------------------------------
  // Calling "setupUi()" after adding the actions above allows the call
  // to "QMetaObject::connectSlotsByName()" done in "setupUi()" to
  // successfully connect each slot with its corresponding action.
  this->Superclass::setupUi(mainWindow);

  //----------------------------------------------------------------------------
  // Configure
  //----------------------------------------------------------------------------
  mainWindow->setWindowIcon(QIcon(":/Icons/Medium/DesktopIcon.png"));

//  QPixmap logo(":/LogoFull.png");
//#if (QT_VERSION >= QT_VERSION_CHECK(5, 0, 0))
//  qreal dpr = sqrt(app->desktop()->logicalDpiX()*qreal(app->desktop()->logicalDpiY()) / (app->desktop()->physicalDpiX()*app->desktop()->physicalDpiY()));
//  logo.setDevicePixelRatio(dpr);
//#endif
//  this->LogoLabel->setPixmap(logo);
  this->LogoLabel->setVisible(false);
  this->ModulePanel->setHelpAndAcknowledgmentVisible(false);

  // Hide the toolbars
  this->MainToolBar->setVisible(false);
  this->ModuleSelectorToolBar->setVisible(false);
  this->ModuleToolBar->setVisible(false);
  this->ViewToolBar->setVisible(false);
  this->MouseModeToolBar->setVisible(false);
  this->CaptureToolBar->setVisible(false);
  this->ViewersToolBar->setVisible(false);
  this->DialogToolBar->setVisible(false);

  // Hide the menus
  //this->menubar->setVisible(false);
  //this->FileMenu->setVisible(false);
  //this->EditMenu->setVisible(false);
  //this->ViewMenu->setVisible(false);
  //this->LayoutMenu->setVisible(false);
  //this->HelpMenu->setVisible(false);

  // Disable actions and associated shortcuts
  this->FileSaveSceneAction->setEnabled(false);

  // Hide the modules panel
  //this->PanelDockWidget->setVisible(false);
  //this->DataProbeCollapsibleWidget->setCollapsed(true);
  this->DataProbeCollapsibleWidget->setVisible(false);
  this->StatusBar->setVisible(false);
}

//-----------------------------------------------------------------------------
// qCellLocatorAppMainWindow methods

//-----------------------------------------------------------------------------
qCellLocatorAppMainWindow::qCellLocatorAppMainWindow(QWidget* windowParent)
  : Superclass(new qCellLocatorAppMainWindowPrivate(*this), windowParent)
{
  Q_D(qCellLocatorAppMainWindow);
  d->init();
}

//-----------------------------------------------------------------------------
qCellLocatorAppMainWindow::qCellLocatorAppMainWindow(
  qCellLocatorAppMainWindowPrivate* pimpl, QWidget* windowParent)
  : Superclass(pimpl, windowParent)
{
  // init() is called by derived class.
}

//-----------------------------------------------------------------------------
qCellLocatorAppMainWindow::~qCellLocatorAppMainWindow()
{
}

//-----------------------------------------------------------------------------
void qCellLocatorAppMainWindow::on_HelpAboutCellLocatorAppAction_triggered()
{
  qSlicerAboutDialog about(this);
  about.setLogo(QPixmap(":/Logo.png"));
  about.exec();
}
