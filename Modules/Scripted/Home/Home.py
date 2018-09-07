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
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.LayoutManager = slicer.app.layoutManager()
    self.MarkupsAnnotationNode = None
    self.ThreeDWithReformatCustomLayoutId = None
    self.Widget = None

  def get(self, name):
    return slicer.util.findChildren(self.Widget, name)[0]

  def registerCustomLayouts(self):
    layoutLogic = self.LayoutManager.layoutLogic()
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
    self.ThreeDWithReformatCustomLayoutId = 503
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.ThreeDWithReformatCustomLayoutId, customLayout)

  def dataPath(self):
    return os.path.join(os.path.dirname(slicer.util.modulePath('Home')), 'CellLocatorData')

  def averageTemplateFilePath(self, resolution=50):
    return os.path.join(self.dataPath(), 'average_template_%s.nrrd' % resolution)

  def annotationFilePath(self, resolution=50):
    return os.path.join(self.dataPath(), 'annotation_%s_contiguous.nrrd' % resolution)

  def colorTableFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_color_table.txt')

  def loadData(self):

    # Load template
    slicer.util.loadVolume(self.averageTemplateFilePath())

    # Load Allen color table
    colorLogic = slicer.modules.colors.logic()
    colorNodeID = None
    if os.path.exists(self.colorTableFilePath()):
      colorNode = colorLogic.LoadColorFile(self.colorTableFilePath(), "allen")
      colorNodeID = colorNode.GetID()
    else:
      logging.error("Color table [%s] does not exist" % self.colorTableFilePath())

    # Load annotation
    if os.path.exists(self.annotationFilePath()):
      slicer.util.loadVolume(self.annotationFilePath(), properties={
        "labelmap": "1",
        "colorNodeID": colorNodeID
      })
    else:
      logging.error("Annotation file [%s] does not exist" % self.annotationFilePath())

    # Reformat view
    sliceWidget = self.LayoutManager.sliceWidget("Reformat")
    sliceController = sliceWidget.sliceController()
    sliceController.setSliceVisible(True)
    sliceController.showReformatWidget(True)
    sliceWidget.mrmlSliceNode().SetWidgetOutlineVisible(False)

    # 3D view
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.mrmlViewNode().SetBoxVisible(False)

    self.resetViews()

  def onStartupCompleted(self):
    qt.QTimer.singleShot(0, self.loadData)


  def saveAnnotationIfModified(self):
    if self.MarkupsAnnotationNode.GetStorageNode() is not None and \
         slicer.mrmlScene.GetStorableNodesModifiedSinceRead():
      question = "The annotation has been modified. Do you want to save before creating a new one ?"
      if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
         self.onSaveAnnotationButtonClicked()

  def resetViews(self):
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.threeDView().resetFocalPoint()
    # TODO Reset 3D and 2D view

  def onNewAnnotationButtonClicked(self):
    self.saveAnnotationIfModified()
    self.onSaveAsAnnotationButtonClicked()
    self.MarkupsAnnotationNode.RemoveAllMarkups()
    self.resetViews()

  def onSaveAnnotationButtonClicked(self):
    if self.MarkupsAnnotationNode.GetStorageNode() is None:
      self.onSaveAsAnnotationButtonClicked()
    else:
      self.MarkupsAnnotationNode.GetStorageNode().WriteData(self.MarkupsAnnotationNode)

  def onSaveAsAnnotationButtonClicked(self):
    slicer.app.ioManager().openDialog(
      "MarkupsFiducials", slicer.qSlicerFileDialog.Write, {"nodeID": self.MarkupsAnnotationNode.GetID()})
    self.onMarkupsAnnotationStorageNodeModified()

  def onLoadAnnotationButtonClicked(self):
    self.saveAnnotationIfModified()
    if slicer.util.openAddMarkupsDialog():
      slicer.mrmlScene.RemoveNode(self.MarkupsAnnotationNode)
      self.MarkupsAnnotationNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLMarkupsFiducialNode")
      self.onMarkupsAnnotationStorageNodeModified()
      self.resetViews()

  def onMarkupsAnnotationStorageNodeModified(self):
    self.Widget.AnnotationPathLineEdit.currentPath = self.MarkupsAnnotationNode.GetStorageNode().GetFileName()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.registerCustomLayouts()
    self.LayoutManager.setLayout(self.ThreeDWithReformatCustomLayoutId)

    # Load UI file
    moduleName = 'Home'
    scriptedModulesPath = os.path.dirname(slicer.util.modulePath(moduleName))
    path = os.path.join(scriptedModulesPath, 'Resources', 'UI', moduleName + '.ui')

    self.Widget = slicer.util.loadUI(path)
    self.layout.addWidget(self.Widget)

    # Disable undocking/docking of the module panel
    panelDockWidget = slicer.util.findChildren(name="PanelDockWidget")[0]
    panelDockWidget.setFeatures(qt.QDockWidget.NoDockWidgetFeatures)

    # Update layout manager viewport
    slicer.util.findChildren(name="CentralWidget")[0].visible = False
    self.LayoutManager.setViewport(self.Widget.LayoutWidget)

    # Add markups annotation
    self.MarkupsAnnotationNode = slicer.vtkMRMLMarkupsFiducialNode()
    self.MarkupsAnnotationNode.SetName("Annotation");
    slicer.mrmlScene.AddNode(self.MarkupsAnnotationNode)

    self.setupConnections()

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.Widget.NewAnnotationButton.connect("clicked()", self.onNewAnnotationButtonClicked)
    self.Widget.SaveAnnotationButton.connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.Widget.SaveAsAnnotationButton.connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.Widget.LoadAnnotationButton.connect("clicked()", self.onLoadAnnotationButtonClicked)

  def cleanup(self):
    self.Widget = None


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

