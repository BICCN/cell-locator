import os
import unittest
import vtk, qt, ctk, slicer
from slicer.util import VTKObservationMixin
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

class HomeWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  def __init__(self, parent = None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)
    self.LayoutManager = slicer.app.layoutManager()
    self.MarkupsAnnotationNode = None
    self.ThreeDWithReformatCustomLayoutId = None
    self.Widget = None
    self.InteractionState = 'scrolling'
    self.ModifyingInteractionState = False

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
    loaded, averageTemplate = slicer.util.loadVolume(
      self.averageTemplateFilePath(), returnNode=True)

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
      loaded, annotation = slicer.util.loadVolume(
        self.annotationFilePath(),
        properties={
          "labelmap": "1",
          "colorNodeID": colorNodeID
        },
        returnNode=True
        )
    else:
      logging.error("Annotation file [%s] does not exist" % self.annotationFilePath())

    # Slice view
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceController = sliceWidget.sliceController()
    sliceController.setSliceVisible(True)
    sliceController.showReformatWidget(True)
    sliceWidget.mrmlSliceNode().SetWidgetOutlineVisible(False)

    compositeNode = sliceWidget.mrmlSliceCompositeNode()
    compositeNode.SetBackgroundVolumeID(averageTemplate.GetID())
    compositeNode.SetLabelVolumeID(annotation.GetID())

    # 3D view
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.mrmlViewNode().SetBoxVisible(False)

    self.resetViews()

  def onStartupCompleted(self, *unused):
    qt.QTimer.singleShot(0, lambda: self.onSceneEndClose(slicer.mrmlScene))

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

    if self.MarkupsAnnotationNode:
      self.removeAnnotation()

    if not self.MarkupsAnnotationNode:
      self.initializeAnnotation()

    if not self.onSaveAsAnnotationButtonClicked():
      self.removeAnnotation()
      return

    self.resetViews()
    self.updateSaveButtonsState()
    self.updateInteractingButtonsState()

    self.setInteractionState('placing')

  def onSaveAnnotationButtonClicked(self):
    if not self.MarkupsAnnotationNode or \
       not self.MarkupsAnnotationNode.GetStorageNode():
      return

    self.MarkupsAnnotationNode.GetStorageNode().WriteData(self.MarkupsAnnotationNode)

  def onSaveAsAnnotationButtonClicked(self):
    valid = slicer.app.ioManager().openDialog(
      "MarkupsSplines", slicer.qSlicerFileDialog.Write, {"nodeID": self.MarkupsAnnotationNode.GetID()})
    if valid:
      self.onMarkupsAnnotationStorageNodeModified()
    return valid

  def onLoadAnnotationButtonClicked(self):
    from slicer import app, qSlicerFileDialog

    self.saveAnnotationIfModified()
    if not app.coreIOManager().openDialog('MarkupsSplines', qSlicerFileDialog.Read):
      return

    nodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsSplinesNode')
    nodes.UnRegister(slicer.mrmlScene)
    newNode = nodes.GetItemAsObject(nodes.GetNumberOfItems() - 1)
    self.initializeAnnotation(newNode)
    self.onMarkupsAnnotationStorageNodeModified()
    self.resetViews()
    self.updateSaveButtonsState()
    self.updateInteractingButtonsState()
    self.setInteractionState('scrolling')

  def onMarkupsAnnotationStorageNodeModified(self):
    if not self.MarkupsAnnotationNode:
      return
    self.Widget.AnnotationPathLineEdit.currentPath = self.MarkupsAnnotationNode.GetStorageNode().GetFileName()

  def onResetViewClicked(self, orientation):
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceNode = sliceWidget.mrmlSliceNode()

    matrix = sliceNode.GetSliceOrientationPreset(orientation)
    for i in range(3):
      for j in range(3):
        sliceNode.GetSliceToRAS().SetElement(i, j, matrix.GetElement(i, j))
    sliceNode.UpdateMatrices()

  def onThicknessChanged(self, value):
    if not self.MarkupsAnnotationNode:
      return

    for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      self.MarkupsAnnotationNode.SetNthSplineThickness(i, value)

  def onSliceNodeModified(self, caller=None, event=None):
    if not self.MarkupsAnnotationNode:
      return

    sliceNode = caller
    if not sliceNode:
      sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    wasModifying = self.MarkupsAnnotationNode.StartModify()

    normal = [0.0, 0.0, 0.0, 0.0]
    sliceNode.GetSliceToRAS().MultiplyPoint([0.0, 0.0, 1.0, 0.0], normal)
    normal = normal[:3]
    vtk.vtkMath.Normalize(normal)
    origin = [sliceNode.GetSliceToRAS().GetElement(i, 3) for i in range(3)]

    # Project points onto the current slice if needed
    if self.InteractionState == 'placing':
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        for n in range(self.MarkupsAnnotationNode.GetNumberOfPointsInNthMarkup(i)):
          point = [0.0, 0.0, 0.0]
          self.MarkupsAnnotationNode.GetMarkupPoint(i, n, point)
          proj = [0.0, 0.0, 0.0]
          vtk.vtkPlane.ProjectPoint(point, origin, normal, proj)
          self.MarkupsAnnotationNode.SetMarkupPointFromArray(i, n, proj)

    # Update the spline's normal
    for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      if not self.MarkupsAnnotationNode.GetNthMarkupLocked(i):
        self.MarkupsAnnotationNode.SetNthSplineNormal(i,
          vtk.vtkVector3d(normal))

    self.MarkupsAnnotationNode.EndModify(wasModifying)

  def onSceneStartClose(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.removeObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModified)

    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    self.removeObserver(interactionNode, vtk.vtkCommand.ModifiedEvent, self.onInteractionNodeModified)

  def onSceneEndClose(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    self.loadData()

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.addObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModified)

    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    self.addObserver(interactionNode, vtk.vtkCommand.ModifiedEvent, self.onInteractionNodeModified)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.registerCustomLayouts()
    self.LayoutManager.setLayout(self.ThreeDWithReformatCustomLayoutId)

    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onStartupCompleted)

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

  def removeAnnotationObservations(self):
    self.removeObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.OnMarkupAddedEvent)

  def addAnnotationObservations(self):
    self.addObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.OnMarkupAddedEvent)

  def removeAnnotation(self):
    self.removeAnnotationObservations()
    slicer.mrmlScene.RemoveNode(self.MarkupsAnnotationNode)
    self.MarkupsAnnotationNode = None

  def initializeAnnotation(self, newNode=None):
    if newNode:
      if self.MarkupsAnnotationNode:
        self.removeAnnotation()
      self.MarkupsAnnotationNode = newNode
    else:
      self.MarkupsAnnotationNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLMarkupsSplinesNode())
      self.MarkupsAnnotationNode.AddDefaultStorageNode()

    self.MarkupsAnnotationNode.SetName("Annotation")
    self.addAnnotationObservations()

  def OnMarkupAddedEvent(self, caller=None, event=None):
    self.onThicknessChanged(self.get('ThicknessSliderWidget').value)
    self.onSliceNodeModified()

  def updateSaveButtonsState(self):
    self.get('SaveAnnotationButton').setEnabled(self.MarkupsAnnotationNode != None)
    self.get('SaveAsAnnotationButton').setEnabled(self.MarkupsAnnotationNode != None)

  def updateInteractingButtonsState(self):
    self.get('PlacingRadioButton').setEnabled(self.MarkupsAnnotationNode != None)
    self.get('InteractingRadioButton').setEnabled(self.MarkupsAnnotationNode != None)

  def get(self, name):
    return slicer.util.findChildren(self.Widget, name)[0]

  def onInteractionNodeModified(self, caller=None, event=None):
    interactionNode = caller
    if not interactionNode or not interactionNode.IsA('vtkMRMLInteractionNode'):
      return

    if (interactionNode.GetCurrentInteractionMode() == interactionNode.ViewTransform
        and not self.ModifyingInteractionState):
      self.setInteractionState('scrolling')

  def setInteractionState(self, newState):
    if self.InteractionState == newState:
      return

    # Update the GUI if we need to
    buttonName = '%sRadioButton' %newState.title()
    if not self.get(buttonName).isChecked():
      self.get(buttonName).setChecked(True)
      return

    self.ModifyingInteractionState = True

    # 1: update selection node
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetActivePlaceNodeID(self.MarkupsAnnotationNode.GetID())

    # 2: update interaction mode:
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    interactionMode = interactionNode.ViewTransform
    if newState == 'placing':
      interactionMode = interactionNode.Place
    interactionNode.SetCurrentInteractionMode(interactionMode)
    interactionNode.SetPlaceModePersistence(1)

    # 3: update markup as locked
    locked = (newState == 'scrolling')
    for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      self.MarkupsAnnotationNode.SetNthMarkupLocked(i, locked)

    # 4: update markup location
    if newState == 'placing':
      self.onSliceNodeModified()

    self.InteractionState = newState
    self.ModifyingInteractionState = False


  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)

    self.get('AxialPushButton').connect("clicked()", lambda: self.onResetViewClicked('Axial'))
    self.get('CoronalPushButton').connect("clicked()", lambda: self.onResetViewClicked('Coronal'))
    self.get('SagittalPushButton').connect("clicked()", lambda: self.onResetViewClicked('Sagittal'))

    self.get('ThicknessSliderWidget').connect("valueChanged(double)", self.onThicknessChanged)

    self.get('ScrollingRadioButton').connect('toggled(bool)', lambda: self.setInteractionState('scrolling'))
    self.get('PlacingRadioButton').connect('toggled(bool)', lambda: self.setInteractionState('placing'))
    self.get('InteractingRadioButton').connect('toggled(bool)', lambda: self.setInteractionState('interacting'))

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

