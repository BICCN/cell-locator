import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# Home
#

class Home(ScriptedLoadableModule):
  """
  """
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Home" # TODO make this more human readable by adding spaces
    self.parent.categories = [""]
    self.parent.dependencies = []
    self.parent.contributors = ["Johan Andruejol (Kitware Inc.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """""" # replace with organization, grant and thanks.
    self.parent = parent

#
# HomeWidget
#

class HomeWidget(ScriptedLoadableModuleWidget):
  def __init__(self, parent = None):
    self.Widget = None
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.layoutManager = slicer.app.layoutManager()

  def get(self, name):
    return slicer.util.findChildren(self.Widget, name)[0]

  def registerCustomLayouts(self):
    layoutLogic = self.layoutManager.layoutLogic()
    customLayout = (
      "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Reformat\">"
      "   <property name=\"orientation\" action=\"default\">Axial</property>"
      "   <property name=\"viewlabel\" action=\"default\">R</property>"
      "   <property name=\"viewcolor\" action=\"default\">#4A50C8</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "    <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      "</layout>")
    self.threeDWithReformatCustomLayoutId = 503
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.threeDWithReformatCustomLayoutId, customLayout)
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.registerCustomLayouts()
    self.layoutManager.setLayout(self.threeDWithReformatCustomLayoutId)

    # Load UI file
    moduleName = 'Home'
    scriptedModulesPath = os.path.dirname(slicer.util.modulePath(moduleName))
    path = os.path.join(scriptedModulesPath, 'Resources', 'UI', moduleName + '.ui')

    self.Widget = slicer.util.loadUI(path)
    self.layout.addWidget(self.Widget)

    # Setup data buttons
    numberOfColumns = 2
    iconPath = os.path.join(os.path.dirname(__file__).replace('\\','/'), 'Resources','Icons')
    desktop = qt.QDesktopWidget()
    mainScreenSize = desktop.availableGeometry(desktop.primaryScreen)
    iconSize = qt.QSize(mainScreenSize.width()/15,mainScreenSize.height()/10)

    buttonsLayout = self.get('DataCollapsibleGroupBox').layout()
    columnIndex = 0
    rowIndex = 0

    files = {
      'annotation_25': os.path.join(scriptedModulesPath, 'CellLocatorData', 'annotation_25.nrrd'),
      'annotation_50': os.path.join(scriptedModulesPath, 'CellLocatorData', 'annotation_50.nrrd')
      }
    for (file, filepath) in files.iteritems():
      button = qt.QToolButton()
      button.setText(file)

      # Set thumbnail
      thumbnailFileName = os.path.join(scriptedModulesPath, 'Resources', 'Icons', file + '.png')
      button.setIcon(qt.QIcon(thumbnailFileName))
      button.setIconSize(iconSize)
      button.setToolButtonStyle(qt.Qt.ToolButtonTextUnderIcon)
      qSize = qt.QSizePolicy()
      qSize.setHorizontalPolicy(qt.QSizePolicy.Expanding)
      button.setSizePolicy(qSize)

      button.name = '%sPushButton' % file
      buttonsLayout.addWidget(button, rowIndex, columnIndex)
      columnIndex += 1
      if columnIndex==numberOfColumns:
        rowIndex += 1
        columnIndex = 0
      button.connect('clicked()', lambda p=filepath: slicer.util.loadVolume(p))

#
# HomeLogic
#

class HomeLogic(ScriptedLoadableModuleLogic):
  """
  """
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)


class HomeTest(ScriptedLoadableModuleTest):
  """
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    #self.test_Home1()

