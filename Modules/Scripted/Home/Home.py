import os
import unittest
import vtk, qt, ctk, slicer
from slicer.util import VTKObservationMixin
from slicer.ScriptedLoadableModule import *
import logging

#
# Home
#

class SignalBlocker(object):
  def __init__(self, widget):
    self.widget = widget
    self.wasBlocking = widget.blockSignals(True)
  def __enter__(self):
    return self.widget
  def __exit__(self, type, value, traceback):
    self.widget.blockSignals(self.wasBlocking)

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
    self.ReferenceView = 'Coronal'

  def get(self, name):
    return slicer.util.findChildren(self.Widget, name)[0]

  def registerCustomLayouts(self):
    layoutLogic = self.LayoutManager.layoutLogic()
    customLayout = (
      "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Slice\">"
      "   <property name=\"orientation\" action=\"default\">%s</property>"
      "   <property name=\"viewlabel\" action=\"default\">R</property>"
      "   <property name=\"viewcolor\" action=\"default\">#4A50C8</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "    <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      "</layout>") %self.ReferenceView
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
    if not loaded:
      logging.error('Average template [%s] does not exists' %self.averageTemplateFilePath())

    # Set the min/max window level
    range = averageTemplate.GetImageData().GetScalarRange()
    averageTemplateDisplay = averageTemplate.GetDisplayNode()
    averageTemplateDisplay.SetAutoWindowLevel(0)
    # No option to set the window level to min/max through the node. Instead
    # do it manually (see qMRMLWindowLevelWidget::setMinMaxRangeValue)
    window = range[1] - range[0]
    level = 0.5 * (range[0] + range[1])
    averageTemplateDisplay.SetWindowLevel(window, level)

    # Lock the window level
    averageTemplateDisplay.SetWindowLevelLocked(True)

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
    compositeNode.SetLabelOpacity(0.4)

    # 3D view
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.mrmlViewNode().SetBoxVisible(False)

    return averageTemplate, annotation

  def onStartupCompleted(self, *unused):
    qt.QTimer.singleShot(0, lambda: self.onSceneEndClose(slicer.mrmlScene))

  def saveAnnotationIfModified(self):
    if not self.MarkupsAnnotationNode:
      return

    question = "The annotation has been modified. Do you want to save before creating a new one ?"
    if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
       self.onSaveAnnotationButtonClicked()

  def resetViews(self):
    # Reset 2D
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceWidget.sliceController().fitSliceToBackground()
    # Reset 3D
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.threeDView().resetFocalPoint()

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
    self.updateGUIFromMRML()
    self.onSliceNodeModified() # Init values
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
      self.updateGUIFromMRML()
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
    self.updateGUIFromMRML()

    self.resetViews()
    self.jumpSliceToAnnotation()
    self.setInteractionState('scrolling')

  def updateGUIFromMRML(self):
    self.updateGUIFromAnnotation()
    self.updateGUIFromSliceNode()

  def updateGUIFromAnnotation(self):
    self.onMarkupsAnnotationStorageNodeModified()

    self.updateSaveButtonsState()
    self.updateInteractingButtonsState()

  def updateGUIFromSliceNode(self):
    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # Update step size
    # Code to find the step size range taken from qMRMLSliceControllerWidgetPrivate::onSliceLogicModified
    sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
    bounds = [0, -1, 0, -1, 0, -1]
    sliceLogic.GetLowestVolumeSliceBounds(bounds)
    sliceOffset = sliceLogic.GetSliceOffset()
    spacingRange = bounds[5] - bounds[4]
    if spacingRange > 0:
      self.get('StepSizeSliderWidget').minimum = 0
      self.get('StepSizeSliderWidget').maximum = spacingRange
    else:
      self.get('StepSizeSliderWidget').minimum = 0
      self.get('StepSizeSliderWidget').maximum = 100

    if sliceNode.GetSliceSpacingMode != sliceNode.PrescribedSliceSpacingMode:
      initialSpacing = sliceLogic.GetLowestVolumeSliceSpacing()
      sliceNode.SetPrescribedSliceSpacing(initialSpacing)
      sliceNode.SetSliceSpacingModeToPrescribed()

    sliceSpacing = sliceNode.GetPrescribedSliceSpacing()
    self.get('StepSizeSliderWidget').value = sliceSpacing[2]

    # Update Roll/Pitch/Yaw
    referenceOrientation = sliceNode.GetSliceOrientationPreset(self.ReferenceView)
    referenceMatrix = vtk.vtkMatrix4x4()
    for row in range(3):
      for column in range(3):
        referenceMatrix.SetElement(row, column, referenceOrientation.GetElement(row, column))

    toWorld = vtk.vtkTransform()
    toWorld.SetMatrix(referenceMatrix)
    toWorld.Inverse()

    # Careful here: Transform is PreMultiply
    #  -> We want T(X) = M_to_world * M_slice_to_ras (X)
    transform = vtk.vtkTransform()
    transform.SetMatrix(sliceNode.GetSliceToRAS())
    transform.Concatenate(toWorld)
    transform.Update()

    angles = [0., 0., 0.]
    transform.GetOrientation(angles)

    with SignalBlocker(self.get('RollSpinBox')):
      self.get('RollSpinBox').value = angles[0]
    with SignalBlocker(self.get('PitchSpinBox')):
      self.get('PitchSpinBox').value = angles[1]
    with SignalBlocker(self.get('YawSpinBox')):
      self.get('YawSpinBox').value = angles[2]
    self.onViewOrientationChanged()

  def onViewOrientationChanged(self):
    roll = self.get('RollSpinBox').value
    yaw =  self.get('YawSpinBox').value
    pitch =  self.get('PitchSpinBox').value

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    referenceOrientation = sliceNode.GetSliceOrientationPreset(self.ReferenceView)
    referenceMatrix = vtk.vtkMatrix4x4()
    for row in range(3):
      for column in range(3):
        referenceMatrix.SetElement(row, column, referenceOrientation.GetElement(row, column))

    toReference = vtk.vtkTransform()
    toReference.SetMatrix(referenceMatrix)

    # Careful here: Transform is PreMultiply
    #  -> We want T(X) = M_to_reference * R_z*R_y*R_x (X)
    transform = vtk.vtkTransform()
    transform.RotateX(roll)
    transform.RotateY(pitch)
    transform.RotateZ(yaw)
    transform.Concatenate(toReference)

    newOrientation = transform.GetMatrix()
    for i in range(3):
      for j in range(3):
        sliceNode.GetSliceToRAS().SetElement(i, j, newOrientation.GetElement(i, j))
    sliceNode.UpdateMatrices()

  def onStepSizeChanged(self, spacing):
    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    sliceSpacing = sliceNode.GetPrescribedSliceSpacing()
    sliceNode.SetPrescribedSliceSpacing(sliceSpacing[0], sliceSpacing[1], spacing)

  def onMarkupsAnnotationStorageNodeModified(self):
    if not self.MarkupsAnnotationNode or not self.MarkupsAnnotationNode.GetStorageNode():
      return
    self.Widget.AnnotationPathLineEdit.currentPath = self.MarkupsAnnotationNode.GetStorageNode().GetFileName()

  def resetToReferenceView(self):
    referenceView = self.ReferenceView
    self.ReferenceView = ''
    self.onReferenceViewChanged(referenceView)

  def onReferenceViewChanged(self, orientation):
    if orientation == self.ReferenceView:
      return

    self.ReferenceView = orientation
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

  def jumpSliceToAnnotation(self):
    if not self.MarkupsAnnotationNode:
      return

    if self.MarkupsAnnotationNode.GetNumberOfMarkups() < 1:
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    sliceNode.GetSliceToRAS().DeepCopy(
      self.MarkupsAnnotationNode.GetNthSplineOrientation(0))
    sliceNode.UpdateMatrices()

  def onSliceNodeModified(self, caller=None, event=None):
    sliceNode = caller
    if not sliceNode:
      sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # GUI update
    self.updateGUIFromMRML()

    # Markup Annotation update
    if not self.MarkupsAnnotationNode:
      return

    wasModifying = self.MarkupsAnnotationNode.StartModify()

    # Update the spline's normal and origin
    for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      if not self.MarkupsAnnotationNode.GetNthMarkupLocked(i):
        self.MarkupsAnnotationNode.SetNthSplineOrientation(i,
          sliceNode.GetSliceToRAS())

    if self.InteractionState == 'scrolling':
      self.MarkupsAnnotationNode.EndModify(wasModifying)
      return

    normal = [0.0, 0.0, 0.0, 0.0]
    sliceNode.GetSliceToRAS().MultiplyPoint([0.0, 0.0, 1.0, 0.0], normal)
    normal = normal[:3]
    vtk.vtkMath.Normalize(normal)
    origin = [sliceNode.GetSliceToRAS().GetElement(i, 3) for i in range(3)]

    # Project points onto the current slice if needed
    for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      for n in range(self.MarkupsAnnotationNode.GetNumberOfPointsInNthMarkup(i)):
        point = [0.0, 0.0, 0.0]
        self.MarkupsAnnotationNode.GetMarkupPoint(i, n, point)
        proj = [0.0, 0.0, 0.0]
        vtk.vtkPlane.ProjectPoint(point, origin, normal, proj)
        self.MarkupsAnnotationNode.SetMarkupPointFromArray(i, n, proj)

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

    averageTemplate, annotation = self.loadData()

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.addObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModified)

    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    self.addObserver(interactionNode, vtk.vtkCommand.ModifiedEvent, self.onInteractionNodeModified)

    self.get('StepSizeSliderWidget').setMRMLScene(slicer.mrmlScene)

    # Create RAStoPIR transform - See https://github.com/BICCN/cell-locator/issues/48#issuecomment-443412860
    # 0 0 1 -1
    # 1 0 0 0
    # 0 1 0 0
    # 0 0 0 1
    ras2pirTransform = slicer.vtkMRMLTransformNode()
    ras2pirTransform.SetName("RAStoPIR")
    slicer.mrmlScene.AddNode(ras2pirTransform)
    transformMatrix = vtk.vtkMatrix4x4()
    transformMatrix.SetElement(0, 0,  0.0)
    transformMatrix.SetElement(1, 0,  1.0)
    transformMatrix.SetElement(2, 0,  0.0)
    transformMatrix.SetElement(3, 0,  0.0)
    transformMatrix.SetElement(0, 1,  0.0)
    transformMatrix.SetElement(1, 1,  0.0)
    transformMatrix.SetElement(2, 1,  1.0)
    transformMatrix.SetElement(3, 1,  0.0)
    transformMatrix.SetElement(0, 2,  1.0)
    transformMatrix.SetElement(1, 2,  0.0)
    transformMatrix.SetElement(2, 2,  0.0)
    transformMatrix.SetElement(3, 2,  0.0)
    transformMatrix.SetElement(0, 3, -1.0)
    transformMatrix.SetElement(1, 3,  0.0)
    transformMatrix.SetElement(2, 3,  0.0)
    transformMatrix.SetElement(3, 3,  1.0)
    ras2pirTransform.SetMatrixTransformToParent(transformMatrix)

    # Apply transform
    averageTemplate.SetAndObserveTransformNodeID(ras2pirTransform.GetID())
    annotation.SetAndObserveTransformNodeID(ras2pirTransform.GetID())

    # Update Coronal preset so that +x is +P - See https://github.com/BICCN/cell-locator/issues/48#issuecomment-443423073
    sliceNode.DisableModifiedEventOn()
    orientationMatrix = vtk.vtkMatrix3x3()
    slicer.vtkMRMLSliceNode.InitializeCoronalMatrix(orientationMatrix)
    orientationMatrix.SetElement(1, 2, -1.0)
    sliceNode.RemoveSliceOrientationPreset("Coronal")
    sliceNode.AddSliceOrientationPreset("Coronal", orientationMatrix)
    sliceNode.DisableModifiedEventOff()

    self.resetViews()

    self.updateGUIFromMRML()

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

    # Update the reference default button
    self.get('%sRadioButton' %self.ReferenceView).setChecked(True)

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

    # If we're going from scrolling to another state -> snap the slice to the
    # spline
    if self.InteractionState == 'scrolling':
      self.jumpSliceToAnnotation()

    self.InteractionState = newState

    self.ModifyingInteractionState = False

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)

    self.get('ResetToReferenceViewPushButton').connect("clicked()", self.resetToReferenceView)

    self.get('AxialRadioButton').connect("toggled(bool)", lambda: self.onReferenceViewChanged('Axial'))
    self.get('CoronalRadioButton').connect("toggled(bool)", lambda: self.onReferenceViewChanged('Coronal'))
    self.get('SagittalRadioButton').connect("toggled(bool)", lambda: self.onReferenceViewChanged('Sagittal'))

    self.get('RollSpinBox').connect("valueChanged(double)", self.onViewOrientationChanged)
    self.get('YawSpinBox').connect("valueChanged(double)", self.onViewOrientationChanged)
    self.get('PitchSpinBox').connect("valueChanged(double)", self.onViewOrientationChanged)

    self.get('StepSizeSliderWidget').connect("valueChanged(double)", self.onStepSizeChanged)

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

