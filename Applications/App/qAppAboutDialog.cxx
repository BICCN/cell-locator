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

#include <QDebug>

// SlicerApp includes
#include "qAppAboutDialog.h"
#include "qSlicerApplication.h"
#include "ui_qAppAboutDialog.h"

//-----------------------------------------------------------------------------
class qAppAboutDialogPrivate: public Ui_qAppAboutDialog
{
public:
};

//-----------------------------------------------------------------------------
// qAppAboutDialogPrivate methods


//-----------------------------------------------------------------------------
// qAppAboutDialog methods
qAppAboutDialog::qAppAboutDialog(QWidget* parentWidget)
  : QDialog(parentWidget)
  , d_ptr(new qAppAboutDialogPrivate)
{
  Q_D(qAppAboutDialog);
  d->setupUi(this);
  qSlicerApplication* slicer = qSlicerApplication::application();
  d->CreditsTextBrowser->setFontPointSize(25);
  d->CreditsTextBrowser->append(slicer->applicationName());
  d->CreditsTextBrowser->setFontPointSize(11);
  d->CreditsTextBrowser->append("");
  d->CreditsTextBrowser->append(
    slicer->applicationVersion()+ " "
    + "r" + slicer->repositoryRevision());
  d->CreditsTextBrowser->append("");
  d->CreditsTextBrowser->insertHtml(slicer->acknowledgment());
  d->CreditsTextBrowser->insertHtml(slicer->libraries());
  d->SlicerLinksTextBrowser->insertHtml(slicer->copyrights());
  d->CreditsTextBrowser->moveCursor(QTextCursor::Start, QTextCursor::MoveAnchor);
}

//-----------------------------------------------------------------------------
qAppAboutDialog::~qAppAboutDialog()
{
}
