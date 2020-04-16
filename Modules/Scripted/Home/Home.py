import os
import json
import logging
import textwrap

import vtk, qt, ctk, slicer

from contextlib import contextmanager

from slicer.util import NodeModify, VTKObservationMixin
from slicer.ScriptedLoadableModule import *
from HomeLib import HomeResources as Resources
from HomeLib import CellLocatorConfig as Config

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
    self.parent.contributors = ["Johan Andruejol (Kitware)", "Jean-Christophe Fillion-Robin (Kitware)"]
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
    self.logic = None
    self.LayoutManager = slicer.app.layoutManager()
    self.MarkupsAnnotationNode = None
    self.ThreeDWithReformatCustomLayoutId = None
    self.Widget = None
    self._widget_cache = {}

    self.ClearAction = None

    self.InteractionNode = None

    self.DefaultAnnotationType = 'spline'
    self.DefaultReferenceView = 'Coronal'
    self.DefaultStepSize = 1
    self.DefaultThickness = 50

  def get(self, name, parent=None):
    """Lookup widget by ``name``.

    By default, widget is searched among the children of ``self.Widget``. Setting
    ``parent`` allows to search in a different widget.

    Once a widget is found, an entry into a local cache is added. This allows
    faster subsequent lookup.
    """
    if parent is None:
      parent = self.Widget
    key = "%s-%s" % (parent, name)
    try:
      widget = self._widget_cache[key]
    except KeyError:
      widget = slicer.util.findChildren(parent, name)[0]
      self._widget_cache[key] = widget
    return widget

  def set(self, widget):
    """Explicitly update local widget cache.
    """
    if not widget.objectName:
      raise RuntimeError("widget is not associated with an objectName")
    parent = self.Widget
    key = "%s-%s" % (parent, widget.objectName)
    self._widget_cache[key] = widget

  def onStartupCompleted(self, *unused):
    qt.QTimer.singleShot(0, lambda: self.onSceneEndCloseEvent(slicer.mrmlScene))

  def isAnnotationSavingRequired(self):
    shouldSave = (slicer.mrmlScene.GetStorableNodesModifiedSinceReadByClass("vtkMRMLMarkupsSplinesNode")
                  or slicer.mrmlScene.GetModifiedSinceRead())
    if self.MarkupsAnnotationNode is None:
      return False
    for markupIndex in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
      if self.MarkupsAnnotationNode.GetNumberOfPointsInNthMarkup(markupIndex) > 0:
        return shouldSave
    return False

  def resetFieldOfView(self):
    # Reset 2D
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceWidget.sliceController().fitSliceToBackground()
    # Reset 3D
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.threeDView().resetFocalPoint()

  def resetViews(self):
    self.resetToReferenceView()
    self.resetFieldOfView()
    self.resetCamera()

  def resetCamera(self):
    threeDView = slicer.app.layoutManager().threeDWidget(0).threeDView()

    cameraNode = threeDView.interactorStyle().GetCameraNode()
    rotateTo ={
      "Axial": slicer.vtkMRMLCameraNode.Inferior,
      "Coronal": slicer.vtkMRMLCameraNode.Anterior,
      "Sagittal": slicer.vtkMRMLCameraNode.Left,
    }
    cameraNode.RotateTo(rotateTo[self.getReferenceView()])

    renderer = threeDView.renderer()
    resetRotation = False
    resetTranslation = True
    resetDistance = True
    cameraNode.Reset(resetRotation, resetTranslation, resetDistance, renderer)

  def onNewAnnotationButtonClicked(self):
    # Save current
    if self.isAnnotationSavingRequired():
      question = "The annotation has been modified. Do you want to save before creating a new one ?"
      if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
         if not self.onSaveAnnotationButtonClicked():
           return

    # Create a new one
    newAnnotationNode = self.createAnnotation()
    title = "New Annotation File Name"
    if not self.onSaveAsAnnotationButtonClicked(newAnnotationNode, windowTitle=title):
      # If user cancel, remove the temporary one
      slicer.mrmlScene.RemoveNode(newAnnotationNode)
      return

    # Remove existing annotation, and observe the new one
    self.removeAnnotation()
    self.addAnnotationObservations(newAnnotationNode)
    self.MarkupsAnnotationNode = newAnnotationNode

    self.updateGUIFromMRML()
    self.onSliceNodeModifiedEvent() # Init values

  def onSaveAnnotationButtonClicked(self):
    if not self.MarkupsAnnotationNode or \
       not self.MarkupsAnnotationNode.GetStorageNode():
      return False

    if not self.MarkupsAnnotationNode.GetStorageNode().GetFileName():
      return self.onSaveAsAnnotationButtonClicked(self.MarkupsAnnotationNode)
    else:
      with self.interactionState('explore'):
        self.MarkupsAnnotationNode.GetStorageNode().WriteData(self.MarkupsAnnotationNode)
        self.logic.annotationStored(self.MarkupsAnnotationNode)
      self.updateGUIFromMRML()
      return True

  def onSaveAsAnnotationButtonClicked(self, annotationNode=None, windowTitle=None):

    if annotationNode is None:
      annotationNode = self.MarkupsAnnotationNode

    defaultFileName = "annotation.json"
    directory = slicer.app.userSettings().value("LastAnnotationDirectory", qt.QStandardPaths.writableLocation(qt.QStandardPaths.DocumentsLocation))
    if os.path.exists(directory):
      defaultFileName = directory + "/" + defaultFileName

    properties = {
      "nodeID": annotationNode.GetID(),
      "defaultFileName": defaultFileName
    }
    if windowTitle is not None:
      properties["windowTitle"] = windowTitle

    with self.interactionState('explore'):
      success = slicer.app.ioManager().openDialog(
        "MarkupsSplines", slicer.qSlicerFileDialog.Write, properties)

    if success:
      directory = os.path.dirname(annotationNode.GetStorageNode().GetFileName())
      slicer.app.userSettings().setValue("LastAnnotationDirectory", directory)
      self.logic.annotationStored(annotationNode)

    self.updateGUIFromMRML()

    return success

  def onLoadAnnotationButtonClicked(self):
    from slicer import app, qSlicerFileDialog

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    viewNode = slicer.app.layoutManager().threeDWidget(0).threeDView().mrmlViewNode()
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)
    with NodeModify(cameraNode), NodeModify(sliceNode):

      # Save current one
      if self.isAnnotationSavingRequired():
        question = "The annotation has been modified. Do you want to save before loading a new one ?"
        if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
          if not self.onSaveAnnotationButtonClicked():
            return

      directory = slicer.app.userSettings().value("LastAnnotationDirectory", qt.QStandardPaths.writableLocation(
        qt.QStandardPaths.DocumentsLocation))

      # Load a new one
      properties = {
        "defaultFileName": os.path.join(directory, "annotation.json"),
      }
      loadedNodes = vtk.vtkCollection()
      if not app.ioManager().openDialog('MarkupsSplines', qSlicerFileDialog.Read, properties, loadedNodes):
        return

      # Get reference to loaded node
      assert loadedNodes.GetNumberOfItems() == 1
      newAnnotationNode = loadedNodes.GetItemAsObject(0)
      newAnnotationNode.SetName("Annotation")

      # Remove existing annotation, and observe the new one
      self.removeAnnotation()
      self.addAnnotationObservations(newAnnotationNode)
      self.MarkupsAnnotationNode = newAnnotationNode

      self.updateGUIFromMRML()

      self.resetViews()
      self.setInteractionState('explore')

      # Camera
      position = [0., 0., 0.]
      viewUp = [0., 0., 0.]
      if self.MarkupsAnnotationNode.GetNumberOfMarkups() == 0:
        position = self.MarkupsAnnotationNode.GetDefaultCameraPosition()
        viewUp = self.MarkupsAnnotationNode.GetDefaultCameraViewUp()
      else:
        markupIndex = 0
        self.MarkupsAnnotationNode.GetNthSplineCameraPosition(markupIndex, position)
        self.MarkupsAnnotationNode.GetNthSplineCameraViewUp(markupIndex, viewUp)
      cameraNode.SetPosition(position)
      cameraNode.SetViewUp(viewUp)
      cameraNode.ResetClippingRange()

      # SplineOrientation
      self.logic.jumpSliceToAnnotation(self.MarkupsAnnotationNode)

  def updateGUIFromMRML(self):
    self.onMarkupsAnnotationStorageNodeModifiedEvent()
    self.updateGUIFromAnnotationMarkup(self.MarkupsAnnotationNode)
    self.updateGUIFromSliceNode()

  def updateGUIFromSliceNode(self):
    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # Update step size
    # Code to find the step size range taken from qMRMLSliceControllerWidgetPrivate::onSliceLogicModified
    sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
    bounds = [0, -1, 0, -1, 0, -1]
    sliceLogic.GetLowestVolumeSliceBounds(bounds)
    spacingRange = bounds[5] - bounds[4]
    if spacingRange > 0:
      self.get('StepSizeSliderWidget').minimum = 1
      self.get('StepSizeSliderWidget').maximum = spacingRange / 10
    else:
      self.get('StepSizeSliderWidget').minimum = 1
      self.get('StepSizeSliderWidget').maximum = 100

    if self.MarkupsAnnotationNode is None or self.MarkupsAnnotationNode.GetNumberOfMarkups() == 0:
      sliceSpacing = sliceNode.GetPrescribedSliceSpacing()
      self.get('StepSizeSliderWidget').value = sliceSpacing[2]

    # Update Roll/Pitch/Yaw
    referenceOrientation = sliceNode.GetSliceOrientationPreset(self.getReferenceView())
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

    with SignalBlocker(self.get('RollSliderWidget')):
      self.get('RollSliderWidget').value = angles[0]
    with SignalBlocker(self.get('PitchSliderWidget')):
      self.get('PitchSliderWidget').value = angles[1]
    with SignalBlocker(self.get('YawSliderWidget')):
      self.get('YawSliderWidget').value = angles[2]

    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    self.get("SliceOffsetSlider", sliceWidget).prefix = "" # Hide orientation prefix

    # Update window/level min/max
    sliceCompositeNode = sliceWidget.mrmlSliceCompositeNode()
    background = slicer.mrmlScene.GetNodeByID(sliceCompositeNode.GetBackgroundVolumeID())
    backgroundDisplay = background.GetDisplayNode()

    self.get('ContrastSlider').setRange(-600, 600)
    self.get('ContrastSlider').setValues(backgroundDisplay.GetWindowLevelMin(), backgroundDisplay.GetWindowLevelMax())

  def onViewOrientationChanged(self):
    roll = self.get('RollSliderWidget').value
    yaw = self.get('YawSliderWidget').value
    pitch = self.get('PitchSliderWidget').value

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    referenceOrientation = sliceNode.GetSliceOrientationPreset(self.getReferenceView())
    referenceMatrix = vtk.vtkMatrix4x4()
    for row in range(3):
      for column in range(3):
        referenceMatrix.SetElement(row, column, referenceOrientation.GetElement(row, column))

    toReference = vtk.vtkTransform()
    toReference.SetMatrix(referenceMatrix)

    # Careful here: Transform is PreMultiply
    #  -> We want T(X) = M_to_reference * R_z*R_y*R_x (X)
    transform = vtk.vtkTransform()
    transform.Identity()
    transform.PreMultiply()
    transform.RotateZ(yaw)
    transform.RotateX(roll)
    transform.RotateY(pitch)
    transform.Concatenate(toReference)

    newOrientation = transform.GetMatrix()
    for i in range(3):
      for j in range(3):
        sliceNode.GetSliceToRAS().SetElement(i, j, newOrientation.GetElement(i, j))
    sliceNode.UpdateMatrices()

    self.get('AdjustViewPushButton').enabled = False

  def onStepSizeChanged(self, spacing):
    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    sliceSpacing = sliceNode.GetPrescribedSliceSpacing()
    sliceNode.SetPrescribedSliceSpacing(sliceSpacing[0], sliceSpacing[1], spacing)

    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    self.get("SliceOffsetSlider", sliceWidget).singleStep = spacing

    if self.MarkupsAnnotationNode is None:
      return

    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultStepSize(spacing)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineStepSize(i, spacing)

  def onMarkupsAnnotationStorageNodeModifiedEvent(self):
    if not self.MarkupsAnnotationNode or not self.MarkupsAnnotationNode.GetStorageNode():
      return
    self.get('AnnotationPathLineEdit').currentPath = self.MarkupsAnnotationNode.GetStorageNode().GetFileName()

  def resetToReferenceView(self):
    self.setReferenceView(self.getReferenceView())

    self.get('AdjustViewPushButton').enabled = False

    # Explicitly reset orientation sliders if "Apply" was not used
    for axe in ['Roll', 'Yaw', 'Pitch']:
      with SignalBlocker(self.get('%sSliderWidget' % axe)):
        self.get('%sSliderWidget' % axe).value = 0

  def setReferenceView(self, orientation):
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceNode = sliceWidget.mrmlSliceNode()

    matrix = sliceNode.GetSliceOrientationPreset(orientation)
    for i in range(3):
      for j in range(3):
        sliceNode.GetSliceToRAS().SetElement(i, j, matrix.GetElement(i, j))
    sliceNode.UpdateMatrices()

    self.resetCamera()

    if self.MarkupsAnnotationNode is None:
      return

    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultReferenceView(orientation)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineReferenceView(i, orientation)

  def onContrastValuesChanged(self, minValue, maxValue):
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceCompositeNode = sliceWidget.mrmlSliceCompositeNode()
    background = slicer.mrmlScene.GetNodeByID(sliceCompositeNode.GetBackgroundVolumeID())
    backgroundDisplay = background.GetDisplayNode()
    window = maxValue - minValue
    level = 0.5*(minValue + maxValue)
    backgroundDisplay.SetWindowLevel(window, level)

  def onResetContrastButtonClicked(self):
    self.get('ContrastSlider').setRange(-600, 600)
    self.get('ContrastSlider').setValues(self.DefaultWindowLevelMin, self.DefaultWindowLevelMax)

  def onThicknessChanged(self, value):
    if not self.MarkupsAnnotationNode:
      return
    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultThickness(value)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineThickness(i, value)

  def onAnnotationTypeChanged(self):
    if not self.MarkupsAnnotationNode:
      return

    if self.get('SplineRadioButton').checked:
      representationType = 'spline'
    else:
      representationType = 'polyline'

    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultRepresentationType(representationType)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineRepresentationType(i, representationType)

  def onSliceNodeModifiedEvent(self, caller=None, event=None):
    sliceNode = caller
    if not sliceNode:
      sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # GUI update
    self.updateGUIFromSliceNode()

    # Markup Annotation update
    if not self.MarkupsAnnotationNode:
      return

    with NodeModify(self.MarkupsAnnotationNode):

      # Update the spline's normal and origin
      self.MarkupsAnnotationNode.SetDefaultSplineOrientation(sliceNode.GetSliceToRAS())
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        if not self.MarkupsAnnotationNode.GetNthMarkupLocked(i):
          self.MarkupsAnnotationNode.SetNthSplineOrientation(i,
            sliceNode.GetSliceToRAS())

      if self.getInteractionState() == 'explore':
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

  def onCameraNodeModifiedEvent(self, caller, event):
    cameraNode = caller
    if self.MarkupsAnnotationNode is None:
      return
    with NodeModify(self.MarkupsAnnotationNode):
      position = [0., 0., 0.]
      cameraNode.GetPosition(position)
      self.MarkupsAnnotationNode.SetDefaultCameraPosition(position)

      viewUp = [0., 0., 0.]
      cameraNode.GetViewUp(viewUp)
      self.MarkupsAnnotationNode.SetDefaultCameraViewUp(viewUp)

      markupIndex = 0
      if self.MarkupsAnnotationNode.GetNumberOfMarkups() > 0:
        self.MarkupsAnnotationNode.SetNthSplineCameraPosition(markupIndex, position)
        self.MarkupsAnnotationNode.SetNthSplineCameraViewUp(markupIndex, viewUp)

  def onSceneStartCloseEvent(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.removeObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModifiedEvent)

    viewNode = slicer.app.layoutManager().threeDWidget(0).threeDView().mrmlViewNode()
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)
    self.removeObserver(cameraNode, vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModifiedEvent)

    self.removeAnnotation()

  def setupViewers(self):
    # Configure slice view
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustLightbox, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustWindowLevelBackground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustWindowLevelForeground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.Blend, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.SelectVolume, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.ShowSlice, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.Translate, True)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.Zoom, True)
    self.get("PinButton", sliceWidget).visible = False
    self.get("ViewLabel", sliceWidget).visible = False
    self.get("FitToWindowToolButton", sliceWidget).visible = False
    # ResetFieldOfView
    resetFieldOfViewButton = qt.QToolButton()
    resetFieldOfViewButton.objectName = "ResetFieldOfViewButton"
    resetFieldOfViewButton.setIcon(qt.QIcon(":/Icons/reset_field_of_view.svg.png"))
    resetFieldOfViewButton.setToolTip("Adjust the Slice Viewer's field of view to match the extent of the atlas.")
    self.set(resetFieldOfViewButton)
    self.get("BarWidget", sliceWidget).layout().addWidget(resetFieldOfViewButton)
    # ReferenceView
    referenceViewComboBox = qt.QComboBox()
    referenceViewComboBox.objectName = "ReferenceViewComboBox"
    referenceViewComboBox.addItems(["Axial", "Coronal", "Sagittal"])
    self.set(referenceViewComboBox)
    self.get("BarWidget", sliceWidget).layout().addWidget(referenceViewComboBox)
    # BarWidget layout
    self.get("BarWidget", sliceWidget).layout().setContentsMargins(6, 4, 6, 4)
    # ContrastSlider
    contrastSlider = ctk.ctkRangeSlider()
    contrastSlider.setOrientation(qt.Qt.Horizontal)
    contrastSlider.symmetricMoves = True
    contrastSlider.objectName = "ContrastSlider"
    contrastSlider.setToolTip("Adjust grayscale CCF background contrast.")
    self.set(contrastSlider)
    # ResetContrastButton
    resetContrastButton = qt.QToolButton()
    resetContrastButton.objectName = "ResetContrastButton"
    resetContrastButton.setIcon(qt.QIcon(":/Icons/reset_field_of_view.svg.png"))
    resetContrastButton.setToolTip("Reset grayscale CCF background contrast.")
    self.set(resetContrastButton)
    # Layout
    nextLineLayout = qt.QHBoxLayout()
    nextLineLayout.setContentsMargins(6, 4, 6, 4)
    nextLineLayout.addWidget(qt.QLabel("Contrast"))
    nextLineLayout.addWidget(contrastSlider)
    nextLineLayout.addWidget(resetContrastButton)
    sliceWidget.layout().addLayout(nextLineLayout)

    # Configure 3D view
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDWidget.mrmlViewNode().SetBoxVisible(False)
    threeDWidget.threeDController().visible = False
    horizontalSpacer = qt.QSpacerItem(0, 0, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    threeDWidget.layout().insertSpacerItem(0, horizontalSpacer)
    layout = qt.QHBoxLayout()
    layout.setSpacing(6)
    layout.setContentsMargins(6, 6, 6, 6)
    threeDWidget.layout().insertLayout(0, layout)

    # Yaw/Pitch/Roll
    def _add_slider(axeName):
      label = qt.QLabel("%s:" % axeName)
      layout.addWidget(label)
      slider = ctk.ctkSliderWidget()
      slider.objectName = "%sSliderWidget" % axeName
      slider.decimals = 0
      slider.singleStep = 1
      slider.pageStep = 5
      slider.minimum = -180
      slider.maximum = 180
      slider.tracking = True
      layout.addWidget(slider)
      self.set(slider)

    _add_slider("Roll")
    _add_slider("Pitch")
    _add_slider("Yaw")

    # Apply
    adjustViewPushButton = qt.QPushButton("Apply")
    adjustViewPushButton.objectName = "AdjustViewPushButton"
    adjustViewPushButton.enabled = False
    layout.addWidget(adjustViewPushButton)
    self.set(adjustViewPushButton)
    # Reset
    resetToReferenceViewPushButton = qt.QPushButton("Reset")
    resetToReferenceViewPushButton.objectName = "ResetToReferenceViewPushButton"
    self.set(resetToReferenceViewPushButton)
    layout.addWidget(resetToReferenceViewPushButton)

  def setDefaultSettings(self):

    # StepSize
    self.get('StepSizeSliderWidget').value = self.DefaultStepSize

    # Thickness
    self.get('ThicknessSliderWidget').value = self.DefaultThickness

    # AnnotationType
    self.get('SplineRadioButton').checked = (self.DefaultAnnotationType == 'spline')

    # ReferenceView
    self.get('ReferenceViewComboBox').currentText = self.DefaultReferenceView

    self.setInteractionState('explore')
    self.resetViews()

  def onSceneEndCloseEvent(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    self.MarkupsAnnotationNode = None

    # Configure UI
    self.get('AdjustViewPushButton').enabled = False

    averageTemplate, annotation = self.logic.loadData()

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # Default StepSize
    sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
    initialSpacing = sliceLogic.GetLowestVolumeSliceSpacing()
    sliceNode.SetPrescribedSliceSpacing(initialSpacing)
    self.DefaultStepSize = initialSpacing[2]

    # Configure slice view
    sliceNode.SetSliceSpacingModeToPrescribed()
    sliceNode.SetSliceVisible(True)
    sliceNode.SetWidgetVisible(True) # Show reformat widget
    sliceNode.SetWidgetOutlineVisible(False) # Hide reformat widget box
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    self.get("BarWidget", sliceWidget).setPalette(slicer.app.palette())
    self.get("SpinBox", self.get("BarWidget", sliceWidget)).setPalette(slicer.app.palette())
    # Disable Precision to allow customization of the singleStep property
    self.get("SliceOffsetSlider", sliceWidget).unitAwareProperties ^= self.get("SliceOffsetSlider", sliceWidget).Precision

    compositeNode = sliceWidget.mrmlSliceCompositeNode()
    compositeNode.SetBackgroundVolumeID(averageTemplate.GetID())
    compositeNode.SetLabelVolumeID(annotation.GetID())
    compositeNode.SetLabelOpacity(0.4)

    # Configure 3D view
    threeDWidget = self.LayoutManager.threeDWidget(0)
    threeDNode = threeDWidget.mrmlViewNode()
    threeDNode.SetBoxVisible(False)
    threeDNode.SetAxisLabel(4, "V") # I -> V
    threeDNode.SetAxisLabel(5, "D") # S -> D

    # Connections
    self.addObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModifiedEvent)
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(threeDWidget.threeDView().mrmlViewNode())
    self.addObserver(cameraNode, vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModifiedEvent)

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
    # Original matrix:
    #  -1  0  0
    #   0  0  1
    #   0  1  0
    #
    # Updated matrix:
    #  -1  0  0
    #   0  0  1
    #   0 -1  0
    #
    sliceNode.DisableModifiedEventOn()
    orientationMatrix = vtk.vtkMatrix3x3()
    slicer.vtkMRMLSliceNode.InitializeCoronalMatrix(orientationMatrix)
    orientationMatrix.SetElement(1, 2, -1.0)
    sliceNode.RemoveSliceOrientationPreset("Coronal")
    sliceNode.AddSliceOrientationPreset("Coronal", orientationMatrix)
    sliceNode.DisableModifiedEventOff()

    self.MarkupsAnnotationNode = self.createAnnotation()
    self.addAnnotationObservations(self.MarkupsAnnotationNode)
    self.onSliceNodeModifiedEvent() # Init values
    self.updateGUIFromMRML()

    self.setDefaultSettings()
    self.logic.annotationStored(self.MarkupsAnnotationNode)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = HomeLogic()

    # Style
    slicer.app.styleSheet = textwrap.dedent("""
    QPushButton {
        border: 1px solid #60A7E5;
        border-radius: 3px;
        background-color: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                                          stop: 0 rgba(108,185,252,1), stop: 1 rgba(96,167,229,1));
        min-width: 80px;
        min-height: 24px;
        color: white;
    }

    QPushButton:hover {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 rgba(118,180,244,1), stop: 1 rgba(144,203,255,1));
    }

    QPushButton:pressed {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 rgba(108,185,252,1), stop: 1 rgba(96,167,229,1));
    }

    QPushButton:disabled {
        background-color: #CDCDCD;
        border: 1px solid #999999;
        color: #777777;
    }

    QComboBox {
        min-height: 24px;
    }
    """)

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

    # Configure layout
    #slicer.modules.celllocator.registerCustomViewFactories(self.LayoutManager)
    self.LayoutManager.setLayout(
      self.logic.registerCustomLayouts(self.LayoutManager.layoutLogic(), self.DefaultReferenceView))

    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartCloseEvent)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onStartupCompleted)

    # Prevent accidental placement of polyline point by associating the 3D view
    # with its own interaction node.
    interactionNode = slicer.vtkMRMLInteractionNode()
    interactionNode.SetSingletonOff()
    slicer.mrmlScene.AddNode(interactionNode)
    self.LayoutManager.threeDWidget(0).threeDView().mrmlViewNode().SetInteractionNode(interactionNode)
    self.InteractionNode = interactionNode

    # Disable verbose IO
    slicer.app.ioManager().verbose = False

    # Configure sliders
    self.get('StepSizeSliderWidget').setMRMLScene(slicer.mrmlScene)
    self.get('ThicknessSliderWidget').setMRMLScene(slicer.mrmlScene)

    self.setupViewers()
    self.setupConnections()

  def removeAnnotationObservations(self):
    self.removeObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAddedEvent)
    self.removeObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.NthMarkupModifiedEvent, self.onNthMarkupModifiedEvent)

  def addAnnotationObservations(self, annotationNode):
    self.addObserver(annotationNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAddedEvent)
    self.addObserver(annotationNode, slicer.vtkMRMLMarkupsNode.NthMarkupModifiedEvent, self.onNthMarkupModifiedEvent)

  def createAnnotation(self):
    annotationNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLMarkupsSplinesNode())
    annotationNode.AddDefaultStorageNode()
    annotationNode.SetName("Annotation")
    return annotationNode

  def removeAnnotation(self):
    if self.MarkupsAnnotationNode is None:
      return
    self.removeAnnotationObservations()
    slicer.mrmlScene.RemoveNode(self.MarkupsAnnotationNode)
    self.MarkupsAnnotationNode = None

  def onMarkupAddedEvent(self, caller=None, event=None):
    self.onThicknessChanged(self.get('ThicknessSliderWidget').value)
    self.onSliceNodeModifiedEvent()

  def updateGUIFromAnnotationMarkup(self, annotationNode):
    if annotationNode is None:
      return

    if annotationNode.GetNumberOfMarkups() == 0:
      # DefaultDefaultOntology
      self.get('OntologyComboBox').currentText = annotationNode.GetDefaultOntology()
      # DefaultReferenceView
      self.get('ReferenceViewComboBox').currentText = annotationNode.GetDefaultReferenceView()
      # DefaultRepresentationType
      representationType = annotationNode.GetDefaultRepresentationType()
      self.get('%sRadioButton' % representationType.title()).setChecked(True)
      # DefaultStepSize
      self.get('StepSizeSliderWidget').value = annotationNode.GetDefaultStepSize()
      # DefaultThickness
      self.get('ThicknessSliderWidget').value = annotationNode.GetDefaultThickness()
    else:
      markupIndex = 0
      # Ontology
      self.get('OntologyComboBox').currentText = annotationNode.GetNthSplineOntology(markupIndex)
      # ReferenceView
      self.get('ReferenceViewComboBox').currentText = annotationNode.GetNthSplineReferenceView(markupIndex)
      # RepresentationType
      representationType = annotationNode.GetNthSplineRepresentationType(markupIndex)
      self.get('%sRadioButton' % representationType.title()).setChecked(True)
      # StepSize
      self.get('StepSizeSliderWidget').value = annotationNode.GetNthSplineStepSize(markupIndex)
      # Thickness
      self.get('ThicknessSliderWidget').value = annotationNode.GetNthSplineThickness(markupIndex)


  @vtk.calldata_type(vtk.VTK_INT)
  def onNthMarkupModifiedEvent(self, caller, event, callData=None):
    annotationNode = caller
    if not annotationNode or not annotationNode.IsA('vtkMRMLMarkupsSplinesNode'):
      return
    self.updateGUIFromAnnotationMarkup(annotationNode)

  def getReferenceView(self):
    return self.get('ReferenceViewComboBox').currentText

  @contextmanager
  def interactionState(self, newState):
    previousState = self.getInteractionState()
    self.setInteractionState(newState)
    yield
    self.setInteractionState(previousState)

  def getInteractionState(self):
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    if interactionNode.GetCurrentInteractionMode() == interactionNode.Place:
      return 'annotate'
    else:
      return 'explore'

  def setInteractionState(self, newState):

    # Update the GUI if we need to
    with SignalBlocker(self.get('AnnotateRadioButton')), SignalBlocker(self.get('ExploreRadioButton')):
      self.get('%sRadioButton' % newState.title()).setChecked(True)

    if self.getInteractionState() == newState:
      return

    # 1: update selection node
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetActivePlaceNodeID(self.MarkupsAnnotationNode.GetID())

    # 2: update interaction mode:
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    if newState == 'annotate':
      interactionNode.SwitchToPersistentPlaceMode()
    else:
      interactionNode.SwitchToViewTransformMode()

    with NodeModify(self.MarkupsAnnotationNode):
      # 3: update markup as locked
      locked = (newState == 'explore')
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthMarkupLocked(i, locked)

      # 4: if any, select first spline
      if self.MarkupsAnnotationNode.GetNumberOfMarkups() > 0:
        self.MarkupsAnnotationNode.SetCurrentSpline(0)

      # 5: Snap the slice to the spline
      if newState == 'annotate':
        self.logic.jumpSliceToAnnotation(self.MarkupsAnnotationNode)

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)

    self.get('ResetFieldOfViewButton').connect("clicked()", self.resetFieldOfView)
    self.get('ReferenceViewComboBox').connect("currentTextChanged(QString)", self.setReferenceView)
    self.get('ResetToReferenceViewPushButton').connect("clicked()", self.resetViews)
    self.get('ContrastSlider').connect("valuesChanged(int, int)", self.onContrastValuesChanged)
    self.get('ResetContrastButton').connect("clicked()", self.onResetContrastButtonClicked)

    def setAdjustAndResetButtonsEnabled():
      self.get('AdjustViewPushButton').setEnabled(True)

    for axe in ['Roll', 'Yaw', 'Pitch']:
      self.get('%sSliderWidget' % axe).connect("valueChanged(double)", setAdjustAndResetButtonsEnabled)
      self.get('%sSliderWidget' % axe).spinBox().lineEdit().connect("returnPressed()", self.onViewOrientationChanged)
      self.get('%sSliderWidget' % axe).slider().connect("returnPressed()", self.onViewOrientationChanged)
    self.get('AdjustViewPushButton').connect("clicked()", self.onViewOrientationChanged)

    self.get('StepSizeSliderWidget').connect("valueChanged(double)", self.onStepSizeChanged)
    self.get('ThicknessSliderWidget').connect("valueChanged(double)", self.onThicknessChanged)
    self.get('PolylineRadioButton').connect("toggled(bool)", self.onAnnotationTypeChanged)
    self.get('SplineRadioButton').connect("toggled(bool)", self.onAnnotationTypeChanged)

    def onAnnotateRadioButtonToggled(annotate):
      if annotate:
        self.setInteractionState('annotate')
      else:
        self.setInteractionState('explore')

    self.get('AnnotateRadioButton').connect('toggled(bool)', onAnnotateRadioButtonToggled)

    self.get('OntologyComboBox').connect("currentTextChanged(QString)", self.onOntologyChanged)

    self.ClearAction = qt.QAction(slicer.util.mainWindow())
    self.ClearAction.shortcut = qt.QKeySequence("Ctrl+W")
    self.ClearAction.connect("triggered()", lambda: slicer.mrmlScene.Clear(False))
    slicer.util.mainWindow().addAction(self.ClearAction)

    # Observe the crosshair node to get the current cursor position
    crosshairNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCrosshairNode')
    self.addObserver(crosshairNode, slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onCursorPositionModifiedEvent)

  def onOntologyChanged(self, ontology):
    annotation = slicer.mrmlScene.GetFirstNodeByName("annotation_%s_contiguous" % Config.ANNOTATION_RESOLUTION)
    if ontology == "Structure":
      colorNodeID = slicer.mrmlScene.GetFirstNodeByName("allen").GetID()
    elif ontology == "Layer":
      colorNodeID = slicer.mrmlScene.GetFirstNodeByName("allen_layer").GetID()
    elif ontology == "None":
      colorNodeID = None
    else:
      raise RuntimeError("Unknown ontology: %s" % ontology)

    visible = 0
    if colorNodeID is not None:
      annotation.GetDisplayNode().SetAndObserveColorNodeID(colorNodeID)
      visible = 1

    # Hide or show label map
    shPluginHandler = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shItemID = shPluginHandler.subjectHierarchyNode().GetItemByDataNode(annotation)
    shPluginHandler.getOwnerPluginForSubjectHierarchyItem(shItemID).setDisplayVisibility(shItemID, visible)

    if self.MarkupsAnnotationNode is None:
      return
    self.MarkupsAnnotationNode.SetDefaultOntology(ontology)
    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultOntology(ontology)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineOntology(i, ontology)

  def onCursorPositionModifiedEvent(self, caller=None, event=None):
    crosshairNode = caller
    if not crosshairNode or not crosshairNode.IsA('vtkMRMLCrosshairNode'):
      return
    self.get("DataProbeLabel").text = self.logic.getCrosshairPixelString(crosshairNode)

  def cleanup(self):
    self.Widget = None


class HomeLogic(object):

  def __init__(self):
    self.AllenStructurePaths = {}
    self.AllenLayerStructurePaths = {}
    self.SlicerToAllenMapping = {}
    self.AllenToSlicerMapping = {}

    self.DefaultWindowLevelMin = 0.
    self.DefaultWindowLevelMax = 0.

  @staticmethod
  def registerCustomLayouts(layoutLogic, defaultReferenceView):
    customLayout = (
      "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Slice\">"
      "   <property name=\"orientation\" action=\"default\">%s</property>"
      "   <property name=\"viewlabel\" action=\"default\">R</property>"
      "   <property name=\"viewcolor\" action=\"default\">#EFEFEF</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "    <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      "</layout>") % defaultReferenceView
    threeDWithReformatCustomLayoutId = 503
    layoutLogic.GetLayoutNode().AddLayoutDescription(threeDWithReformatCustomLayoutId, customLayout)
    return threeDWithReformatCustomLayoutId

  @staticmethod
  def jumpSliceToAnnotation(annotationNode, markupIndex=0):
    if not annotationNode:
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    if annotationNode.GetNumberOfMarkups() == 0:
      sliceNode.GetSliceToRAS().DeepCopy(
        annotationNode.GetDefaultSplineOrientation())
    else:
      sliceNode.GetSliceToRAS().DeepCopy(
        annotationNode.GetNthSplineOrientation(markupIndex))
    sliceNode.UpdateMatrices()

  @staticmethod
  def annotationStored(annotationNode):
    """Update scene and annotation storage node stored time. This indicates
    no saving is required until the next scene or node update."""
    slicer.mrmlScene.StoredModified()
    annotationNode.GetStorageNode().StoredModified()

  @staticmethod
  def dataPath():
    return os.path.join(os.path.dirname(slicer.util.modulePath('Home')), 'CellLocatorData')

  def averageTemplateFilePath(self):
    return os.path.join(self.dataPath(), 'average_template_%s.nrrd' % Config.ANNOTATION_RESOLUTION)

  def annotationFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_%s_contiguous.nrrd' % Config.ANNOTATION_RESOLUTION)

  def colorTableFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_color_table.txt')

  def layerColorTableFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_layer_color_table.txt')

  def ontologyFilePath(self):
    return os.path.join(self.dataPath(), 'ontology-formatted.json')

  def layerOntologyFilePath(self):
    return os.path.join(self.dataPath(), 'layer-ontology-formatted.json')

  def slicerToAllenMappingFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_color_slicer2allen_mapping.json')

  def allenToSlicerMappingFilePath(self):
    return os.path.join(self.dataPath(), 'annotation_color_allen2slicer_mapping.json')

  def loadData(self):
    """Load average template, annotation and associated color table.
    """

    # Load template
    loaded, averageTemplate = slicer.util.loadVolume(
      self.averageTemplateFilePath(), returnNode=True)
    if not loaded:
      logging.error('Average template [%s] does not exists' % self.averageTemplateFilePath())

    # Set the min/max window level
    range = averageTemplate.GetImageData().GetScalarRange()
    averageTemplateDisplay = averageTemplate.GetDisplayNode()
    averageTemplateDisplay.SetAutoWindowLevel(0)
    # No option to set the window level to min/max through the node. Instead
    # do it manually (see qMRMLWindowLevelWidget::setMinMaxRangeValue)
    window = range[1] - range[0]
    level = 0.5 * (range[0] + range[1])

    averageTemplateDisplay.SetWindowLevel(window, level)

    self.DefaultWindowLevelMin = range[0]
    self.DefaultWindowLevelMax = range[1]

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

    # Load Allen "layer" color table
    if os.path.exists(self.layerColorTableFilePath()):
      colorLogic.LoadColorFile(self.layerColorTableFilePath(), "allen_layer")
    else:
      logging.error("Color table [%s] does not exist" % self.layerColorTableFilePath())

    # Load slicer2allen mapping
    with open(self.slicerToAllenMappingFilePath()) as content:
      mapping = json.load(content)
      self.SlicerToAllenMapping = {int(key): int(value) for (key, value) in mapping.items()}

    # Load allen2slicer mapping
    with open(self.allenToSlicerMappingFilePath()) as content:
      mapping = json.load(content)
      self.AllenToSlicerMapping = {int(key): int(value) for (key, value) in mapping.items()}

    # Load ontology
    with open(self.ontologyFilePath()) as content:
      msg = json.load(content)["msg"]

    allenStructureNames = {}
    for structure in msg:
      allenStructureNames[structure["id"]] = structure["acronym"]

    self.AllenStructurePaths = {}
    for structure in msg:
      self.AllenStructurePaths[structure["id"]] = " > ".join(
        [allenStructureNames[int(structure_id)] for structure_id in structure["structure_id_path"][1:-1].split("/")])

    # Load "layer" ontology
    with open(self.layerOntologyFilePath()) as content:
      msg = json.load(content)["msg"]

    allenStructureNames = {997: "root"}
    for structure in msg:
      allenStructureNames[structure["id"]] = structure["acronym"]

    self.AllenLayerStructurePaths = {}
    for structure in msg:
      self.AllenLayerStructurePaths[structure["id"]] = " > ".join(
        [allenStructureNames[int(structure_id)] for structure_id in structure["structure_id_path"][1:-1].split("/")])

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
      annotation = None
      logging.error("Annotation file [%s] does not exist" % self.annotationFilePath())

    return averageTemplate, annotation

  def getCrosshairPixelString(self, crosshairNode):
    """Given a crosshair node, create a human readable string describing
    the contents associated with crosshair cursor position."""
    ras = [0.0,0.0,0.0]
    xyz = [0.0,0.0,0.0]
    insideView = crosshairNode.GetCursorPositionRAS(ras)
    sliceNode = crosshairNode.GetCursorPositionXYZ(xyz)
    appLogic = slicer.app.applicationLogic()
    sliceLogic = appLogic.GetSliceLogic(sliceNode)
    if not insideView or not sliceNode or not sliceLogic:
      return

    def _roundInt(value):
      try:
        return int(round(value))
      except ValueError:
        return 0

    layerLogic = sliceLogic.GetLabelLayer()
    volumeNode = layerLogic.GetVolumeNode()
    ijk = [0, 0, 0]
    if volumeNode:
      xyToIJK = layerLogic.GetXYToIJKTransform()
      ijkFloat = xyToIJK.TransformDoublePoint(xyz)
      ijk = [_roundInt(value) for value in ijkFloat]

    return self.getPixelString(volumeNode, ijk, ras)

  def getPixelString(self,volumeNode,ijk,ras):
    """Given a volume node, create a human readable
    string describing the contents"""
    if not volumeNode:
      return ""
    imageData = volumeNode.GetImageData()
    if not imageData:
      return ""
    dims = imageData.GetDimensions()
    for ele in xrange(3):
      if ijk[ele] < 0 or ijk[ele] >= dims[ele]:
        return ""  # Out of frame
    rasStr = "{ras_x:3.1f} {ras_y:3.1f} {ras_z:3.1f}".format(ras_x=abs(ras[0]), ras_y=abs(ras[1]), ras_z=abs(ras[2]))
    if volumeNode.IsA("vtkMRMLLabelMapVolumeNode"):
      labelIndex = int(imageData.GetScalarComponentAsDouble(ijk[0], ijk[1], ijk[2], 0))
      labelValue = "Unknown"
      displayNode = volumeNode.GetDisplayNode()
      if displayNode:
        colorNode = displayNode.GetColorNode()
        if colorNode and labelIndex > 0:
          allenLabelIndex = self.SlicerToAllenMapping[labelIndex]
          try:
            if colorNode.GetName() == "allen":
              labelValue = self.AllenStructurePaths[allenLabelIndex]
            elif colorNode.GetName() == "allen_layer":
              labelValue = self.AllenLayerStructurePaths[allenLabelIndex]
            return "%s | %s (%d)" % (rasStr, labelValue, allenLabelIndex)
          except KeyError:
            #print(allenLabelIndex)
            return rasStr

    return ""


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

