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
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Slice\">"
      "   <property name=\"orientation\" action=\"default\">Coronal</property>"
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

    # Slice view
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
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
    if not self.MarkupsAnnotationNode:
      return

    question = "The annotation has been modified. Do you want to save before creating a new one ?"
    if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
       self.onSaveAnnotationButtonClicked()

  def resetViews(self):
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.threeDView().resetFocalPoint()
    # TODO Reset 3D and 2D view

  def onNewAnnotationButtonClicked(self):
    self.saveAnnotationIfModified()
    if not self.MarkupsAnnotationNode:
      self.initializeAnnotation()

    self.onSaveAsAnnotationButtonClicked()
    self.MarkupsAnnotationNode.RemoveAllMarkups()
    self.resetViews()
    self.updateSaveButtonsState()

    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetActivePlaceNodeID(self.MarkupsAnnotationNode.GetID())
    interactionNode.SetCurrentInteractionMode(interactionNode.Place)
    interactionNode.SetPlaceModePersistence(1)

  def onSaveAnnotationButtonClicked(self):
    if not self.MarkupsAnnotationNode or \
       not self.MarkupsAnnotationNode.GetStorageNode():
      return

    self.MarkupsAnnotationNode.GetStorageNode().WriteData(self.MarkupsAnnotationNode)

  def onSaveAsAnnotationButtonClicked(self):
    slicer.app.ioManager().openDialog(
      "Markups", slicer.qSlicerFileDialog.Write, {"nodeID": self.MarkupsAnnotationNode.GetID()})
    self.onMarkupsAnnotationStorageNodeModified()

  def onLoadAnnotationButtonClicked(self):
    self.saveAnnotationIfModified()
    if not slicer.util.openAddMarkupsDialog():
      return

    self.initializeAnnotation(slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLMarkupsSplinesNode"))
    self.onMarkupsAnnotationStorageNodeModified()
    self.resetViews()
    self.updateSaveButtonsState()

  def onMarkupsAnnotationStorageNodeModified(self):
    self.Widget.AnnotationPathLineEdit.currentPath = self.MarkupsAnnotationNode.GetStorageNode().GetFileName()

  def onResetViewClicked(self, orientation):
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceNode = sliceWidget.mrmlSliceNode()

    matrix = sliceNode.GetSliceOrientationPreset(orientation)
    for i in range(3):
      for j in range(3):
        sliceNode.GetSliceToRAS().SetElement(i, j, matrix.GetElement(i, j))
    sliceNode.UpdateMatrices()

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

    self.setupConnections()

  def initializeAnnotation(self, newNode=None):
    if newNode:
      slicer.mrmlScene.RemoveNode(self.MarkupsAnnotationNode)
      self.MarkupsAnnotationNode = newNode
    else:
      self.MarkupsAnnotationNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLMarkupsSplinesNode())

    self.MarkupsAnnotationNode.SetName("Annotation")
    self.MarkupsAnnotationNode.AddDefaultStorageNode()

  def updateSaveButtonsState(self):
    self.get('SaveAnnotationButton').setEnabled(self.MarkupsAnnotationNode != None)
    self.get('SaveAsAnnotationButton').setEnabled(self.MarkupsAnnotationNode != None)

  def get(self, name):
    return slicer.util.findChildren(self.Widget, name)[0]

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)

    self.get('AxialPushButton').connect("clicked()", lambda: self.onResetViewClicked('Axial'))
    self.get('CoronalPushButton').connect("clicked()", lambda: self.onResetViewClicked('Coronal'))
    self.get('SagittalPushButton').connect("clicked()", lambda: self.onResetViewClicked('Sagittal'))

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

