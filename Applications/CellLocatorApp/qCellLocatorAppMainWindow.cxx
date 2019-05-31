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
#include <QAbstractButton>
#include <QDesktopWidget>
#include <QMessageBox>
#include <QPushButton>

// PythonQt includes
#include <PythonQt.h>

// CTK includes
#include <ctkAbstractPythonManager.h>
#include <ctkMessageBox.h>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"

// MRML includes
#include <vtkMRMLNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLStorableNode.h>

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

  // Hide the menus and disable associated shortcuts
  this->menubar->setVisible(false);
  //this->FileMenu->setVisible(false);
  //this->EditMenu->setVisible(false);
  //this->ViewMenu->setVisible(false);
  //this->LayoutMenu->setVisible(false);
  //this->HelpMenu->setVisible(false);


  // Hide the modules panel
  //this->PanelDockWidget->setVisible(false);
  //this->DataProbeCollapsibleWidget->setCollapsed(true);
  this->DataProbeCollapsibleWidget->setVisible(false);
  this->StatusBar->setVisible(false);
}

//-----------------------------------------------------------------------------
PyObject* qCellLocatorAppMainWindowPrivate::callPythonFunction(
    const QString& objectPath, const QString& functionName, PyObject * arguments)
{
  PyObject * module = ctkAbstractPythonManager::pythonObject(objectPath.toLatin1());
  if (!module)
    {
    PythonQt::self()->handleError();
    return 0;
    }
  if (!PyObject_HasAttrString(module, functionName.toLatin1()))
    {
    qWarning() << "Failed to lookup 'confirmCloseApplication' python method";
    return 0;
    }
  PythonQtObjectPtr method;
  method.setNewRef(PyObject_GetAttrString(module, functionName.toLatin1()));

  PyObject * result = PyObject_CallObject(method, arguments);
  if (PythonQt::self()->handleError())
    {
    return 0;
    }
  return result;
}

//-----------------------------------------------------------------------------
bool qCellLocatorAppMainWindowPrivate::isSavingRequired()
{
  QString functionName = "isAnnotationSavingRequired";
  PyObject* result = Self::callPythonFunction("slicer.modules.HomeWidget", functionName);
  if (!PyBool_Check(result))
    {
    qWarning() << "function" << functionName << "is expected to return a boolean";
    return false;
    }
  return result == Py_True;
}

//-----------------------------------------------------------------------------
bool qCellLocatorAppMainWindowPrivate::saveAnnotation()
{
  QString functionName = "onSaveAnnotationButtonClicked";
  PyObject* result = Self::callPythonFunction("slicer.modules.HomeWidget", functionName);
  if (!PyBool_Check(result))
    {
    qWarning() << "function" << functionName << "is expected to return a boolean";
    return false;
    }
  return result == Py_True;
}

//-----------------------------------------------------------------------------
bool qCellLocatorAppMainWindowPrivate::confirmCloseApplication()
{
  Q_Q(qCellLocatorAppMainWindow);

  QString question;
  if (Self::isSavingRequired())
    {
    question = q->tr("Annotation has been created or modified. Do you want to save before exit?");
    }

  bool close = false;
  if (!question.isEmpty())
    {
    QMessageBox* messageBox = new QMessageBox(QMessageBox::Warning, q->tr("Save before exit?"), question, QMessageBox::NoButton);
    QAbstractButton* saveButton = messageBox->addButton(q->tr("Save"), QMessageBox::ActionRole);
    QAbstractButton* exitButton = messageBox->addButton(q->tr("Exit (discard modifications)"), QMessageBox::ActionRole);
    QAbstractButton* cancelButton = messageBox->addButton(q->tr("Cancel exit"), QMessageBox::ActionRole);
    Q_UNUSED(cancelButton);
    messageBox->exec();
    if (messageBox->clickedButton() == saveButton)
      {
      close = Self::saveAnnotation();
      }
    else if (messageBox->clickedButton() == exitButton)
      {
      close = true;
      }
    messageBox->deleteLater();
    }
  else
    {
    close = ctkMessageBox::confirmExit("MainWindow/DontConfirmExit", q);
    }
  return close;
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
