import os
import json
import logging
import textwrap

import vtk, qt, ctk, slicer

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
    self.parent.contributors = ["Johan Andruejol (Kitware)", "Jean-Christophe Fillion-Robin (Kitware)"] # replace with "Firstname Lastname (Organization)"
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
    self.ReferenceView = 'Coronal'
    self._widget_cache = {}

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

  def registerCustomLayouts(self):
    layoutLogic = self.LayoutManager.layoutLogic()
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
      "</layout>") %self.ReferenceView
    self.ThreeDWithReformatCustomLayoutId = 503
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.ThreeDWithReformatCustomLayoutId, customLayout)

  def dataPath(self):
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
      self.AllenStructurePaths[structure["id"]] = " > ".join([allenStructureNames[int(structure_id)] for structure_id in structure["structure_id_path"][1:-1].split("/")])

    # Load "layer" ontology
    with open(self.layerOntologyFilePath()) as content:
      msg = json.load(content)["msg"]

    allenStructureNames = {997: "root"}
    for structure in msg:
      allenStructureNames[structure["id"]] = structure["acronym"]

    self.AllenLayerStructurePaths = {}
    for structure in msg:
      self.AllenLayerStructurePaths[structure["id"]] = " > ".join([allenStructureNames[int(structure_id)] for structure_id in structure["structure_id_path"][1:-1].split("/")])

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

    return averageTemplate, annotation

  def onStartupCompleted(self, *unused):
    qt.QTimer.singleShot(0, lambda: self.onSceneEndCloseEvent(slicer.mrmlScene))

  def saveAnnotationIfModified(self):
    if not self.MarkupsAnnotationNode:
      return

    question = "The annotation has been modified. Do you want to save before creating a new one ?"
    if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
       self.onSaveAnnotationButtonClicked()

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

  def onNewAnnotationButtonClicked(self):
    # Save current
    self.saveAnnotationIfModified()

    # Create
    self.initializeAnnotation()
    if not self.onSaveAsAnnotationButtonClicked():
      return

    self.updateGUIFromMRML()
    self.onSliceNodeModifiedEvent() # Init values

    self.setDefaultSettings()

  def onSaveAnnotationButtonClicked(self):
    if not self.MarkupsAnnotationNode or \
       not self.MarkupsAnnotationNode.GetStorageNode():
      return
    if not self.MarkupsAnnotationNode.GetStorageNode().GetFileName():
      self.onSaveAsAnnotationButtonClicked()
    else:
      self.MarkupsAnnotationNode.GetStorageNode().WriteData(self.MarkupsAnnotationNode)

  def onSaveAsAnnotationButtonClicked(self):
    return slicer.app.ioManager().openDialog(
      "MarkupsSplines", slicer.qSlicerFileDialog.Write, {"nodeID": self.MarkupsAnnotationNode.GetID()})

  def onLoadAnnotationButtonClicked(self):
    from slicer import app, qSlicerFileDialog

    viewNode = slicer.app.layoutManager().threeDWidget(0).threeDView().mrmlViewNode()
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)
    with NodeModify(cameraNode):

      self.removeAnnotation()
      self.saveAnnotationIfModified()
      if not app.coreIOManager().openDialog('MarkupsSplines', qSlicerFileDialog.Read):
        return

      nodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsSplinesNode')
      nodes.UnRegister(slicer.mrmlScene)
      newNode = nodes.GetItemAsObject(nodes.GetNumberOfItems() - 1)

      self.initializeAnnotation(newNode)
      self.updateGUIFromMRML()

      self.resetViews()
      self.setInteractionState('explore')

      # Camera
      position = [0., 0., 0.]
      self.MarkupsAnnotationNode.GetNthSplineCameraPosition(0, position)
      cameraNode.SetPosition(position)
      viewUp = [0., 0., 0.]
      self.MarkupsAnnotationNode.GetNthSplineCameraViewUp(0, viewUp)
      cameraNode.SetViewUp(viewUp)
      cameraNode.ResetClippingRange()

  def updateGUIFromMRML(self):
    self.updateGUIFromAnnotation()
    self.updateGUIFromSliceNode()

  def updateGUIFromAnnotation(self):
    self.onMarkupsAnnotationStorageNodeModifiedEvent()

    self.updateReferenceViewButtonsState()
    self.updateGUIFromAnnotationMarkup()

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
      self.get('StepSizeSliderWidget').maximum = spacingRange / 10
    else:
      self.get('StepSizeSliderWidget').minimum = 0
      self.get('StepSizeSliderWidget').maximum = 100

    if self.MarkupsAnnotationNode is None or self.MarkupsAnnotationNode.GetNumberOfMarkups() == 0:
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

    with SignalBlocker(self.get('RollSliderWidget')):
      self.get('RollSliderWidget').value = angles[0]
    with SignalBlocker(self.get('PitchSliderWidget')):
      self.get('PitchSliderWidget').value = angles[1]
    with SignalBlocker(self.get('YawSliderWidget')):
      self.get('YawSliderWidget').value = angles[2]

    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    self.get("SliceOffsetSlider", sliceWidget).prefix = "" # Hide orientation prefix

    self.get('ResetToReferenceViewPushButton').enabled = (angles != [0., 0., 0.])

  def onViewOrientationChanged(self):
    roll = self.get('RollSliderWidget').value
    yaw = self.get('YawSliderWidget').value
    pitch = self.get('PitchSliderWidget').value

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
    referenceView = self.ReferenceView
    self.ReferenceView = ''
    self.onReferenceViewChanged(referenceView)

    self.get('AdjustViewPushButton').enabled = False

    # Explicitly reset in if "Apply" was not used
    for axe in ['Roll', 'Yaw', 'Pitch']:
      with SignalBlocker(self.get('%sSliderWidget' % axe)):
        self.get('%sSliderWidget' % axe).value = 0

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

  def jumpSliceToAnnotation(self):
    if not self.MarkupsAnnotationNode:
      return

    if self.MarkupsAnnotationNode.GetNumberOfMarkups() < 1:
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    sliceNode.GetSliceToRAS().DeepCopy(
      self.MarkupsAnnotationNode.GetNthSplineOrientation(0))
    sliceNode.UpdateMatrices()

  def onSliceNodeModifiedEvent(self, caller=None, event=None):
    sliceNode = caller
    if not sliceNode:
      sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # GUI update
    self.updateGUIFromMRML()

    # Markup Annotation update
    if not self.MarkupsAnnotationNode:
      return

    with NodeModify(self.MarkupsAnnotationNode):

      # Update the spline's normal and origin
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
    if self.MarkupsAnnotationNode is None or self.MarkupsAnnotationNode.GetNumberOfMarkups() == 0:
      return
    markupIndex = 0
    position = [0., 0., 0.]
    cameraNode.GetPosition(position)
    self.MarkupsAnnotationNode.SetNthSplineCameraPosition(markupIndex, position)
    viewUp = [0., 0., 0.]
    cameraNode.GetViewUp(viewUp)
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

  def setupViewers(self):
    # Configure slice view
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustLightbox, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustWindowLevelBackground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.AdjustWindowLevelForeground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.Blend, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.SelectVolume, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkSliceViewInteractorStyle.Zoom, False)
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
    referenceViewComboBox.setCurrentText(self.ReferenceView) # Update the reference default button
    self.set(referenceViewComboBox)
    self.get("BarWidget", sliceWidget).layout().addWidget(referenceViewComboBox)
    # BarWidget layout
    self.get("BarWidget", sliceWidget).layout().setContentsMargins(6, 4, 6, 4)

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
      slider.singleStep = 5
      slider.pageStep = 25
      slider.minimum = -180
      slider.maximum = 180
      slider.tracking = False
      layout.addWidget(slider)
      self.set(slider)

    _add_slider("Yaw")
    _add_slider("Pitch")
    _add_slider("Roll")

    # Apply
    adjustViewPushButton = qt.QPushButton("Apply")
    adjustViewPushButton.objectName = "AdjustViewPushButton"
    adjustViewPushButton.enabled = False
    layout.addWidget(adjustViewPushButton)
    self.set(adjustViewPushButton)
    # Reset
    resetToReferenceViewPushButton = qt.QPushButton("Reset")
    resetToReferenceViewPushButton.objectName = "ResetToReferenceViewPushButton"
    resetToReferenceViewPushButton.enabled = False
    self.set(resetToReferenceViewPushButton)
    layout.addWidget(resetToReferenceViewPushButton)

  def setDefaultSettings(self):

    # StepSize
    self.get('StepSizeSliderWidget').value = self.DefaultStepSize

    # Thickness
    self.get('ThicknessSliderWidget').value = 50

    # AnnotationType
    self.get('SplineRadioButton').checked = True

    self.setInteractionState('explore')
    self.resetViews()

  def onSceneEndCloseEvent(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    self.MarkupsAnnotationNode = None

    # Configure UI
    self.get('ThicknessSliderWidget').enabled = False
    self.get('AdjustViewPushButton').enabled = False
    self.get('ResetToReferenceViewPushButton').enabled = False

    averageTemplate, annotation = self.loadData()

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
    threeDWidget.mrmlViewNode().SetBoxVisible(False)

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

    self.initializeAnnotation()
    self.onSliceNodeModifiedEvent() # Init values
    self.updateGUIFromMRML()

    self.setDefaultSettings()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

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
    self.registerCustomLayouts()
    #slicer.modules.celllocator.registerCustomViewFactories(self.LayoutManager)
    self.LayoutManager.setLayout(self.ThreeDWithReformatCustomLayoutId)

    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartCloseEvent)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onStartupCompleted)

    # Prevent accidental placement of polyline point by associating the 3D view
    # with its own interaction node.
    interactionNode = slicer.vtkMRMLInteractionNode()
    interactionNode.SetSingletonOff()
    slicer.mrmlScene.AddNode(interactionNode)
    self.LayoutManager.threeDWidget(0).threeDView().mrmlViewNode().SetInteractionNode(interactionNode)
    self.InteractionNode = interactionNode

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

  def addAnnotationObservations(self):
    self.addObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAddedEvent)
    self.addObserver(
      self.MarkupsAnnotationNode, slicer.vtkMRMLMarkupsNode.NthMarkupModifiedEvent, self.onNthMarkupModifiedEvent)

  def removeAnnotation(self):
    if self.MarkupsAnnotationNode is None:
      return
    self.removeAnnotationObservations()
    slicer.mrmlScene.RemoveNode(self.MarkupsAnnotationNode)
    self.MarkupsAnnotationNode = None

  def initializeAnnotation(self, newNode=None):
    if newNode:
      self.MarkupsAnnotationNode = newNode
    else:
      self.removeAnnotation()
      self.MarkupsAnnotationNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLMarkupsSplinesNode())
      self.MarkupsAnnotationNode.AddDefaultStorageNode()
      self.MarkupsAnnotationNode.SetDefaultReferenceView(self.get("ReferenceViewComboBox").currentText)

    self.MarkupsAnnotationNode.SetName("Annotation")
    self.addAnnotationObservations()

  def onMarkupAddedEvent(self, caller=None, event=None):
    self.onThicknessChanged(self.get('ThicknessSliderWidget').value)
    self.onSliceNodeModifiedEvent()

  def updateGUIFromAnnotationMarkup(self):
    self.get('ThicknessSliderWidget').enabled = False

    if self.MarkupsAnnotationNode is None or self.MarkupsAnnotationNode.GetNumberOfMarkups() == 0:
      return

    markupIndex = 0

    # Thickness
    if self.MarkupsAnnotationNode.GetNumberOfPointsInNthMarkup(markupIndex) > 0:
      self.get('ThicknessSliderWidget').enabled = True
      self.get('ThicknessSliderWidget').value = self.MarkupsAnnotationNode.GetNthSplineThickness(markupIndex)

    # ReferenceView
    self.get('ReferenceViewComboBox').currentText = self.MarkupsAnnotationNode.GetNthSplineReferenceView(markupIndex)

    # Type
    representationType = self.MarkupsAnnotationNode.GetNthSplineRepresentationType(markupIndex)
    self.get('%sRadioButton' % representationType.title()).setChecked(True)

    # StepSize
    self.get('StepSizeSliderWidget').value = self.MarkupsAnnotationNode.GetNthSplineStepSize(markupIndex)

    # Ontology
    self.get('OntologyComboBox').currentText = self.MarkupsAnnotationNode.GetNthSplineOntology(markupIndex)

  @vtk.calldata_type(vtk.VTK_INT)
  def onNthMarkupModifiedEvent(self, caller, event, callData=None):
    annotationNode = caller
    if not annotationNode or not annotationNode.IsA('vtkMRMLMarkupsSplinesNode'):
      return
    self.updateGUIFromAnnotationMarkup()

  def updateReferenceViewButtonsState(self):
    hasMarkups = self.MarkupsAnnotationNode is not None and self.MarkupsAnnotationNode.GetNumberOfMarkups() > 0
    self.get('ReferenceViewComboBox').setDisabled(hasMarkups)

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
        self.jumpSliceToAnnotation()

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)

    self.get('ResetFieldOfViewButton').connect("clicked()", self.resetFieldOfView)
    self.get('ReferenceViewComboBox').connect("currentTextChanged(QString)", self.onReferenceViewChanged)
    self.get('ResetToReferenceViewPushButton').connect("clicked()", self.resetToReferenceView)

    def setAdjustAndResetButtonsEnabled():
      self.get('AdjustViewPushButton').setEnabled(True)
      self.get('ResetToReferenceViewPushButton').setEnabled(True)

    for axe in ['Roll', 'Yaw', 'Pitch']:
      self.get('%sSliderWidget' % axe).connect("valueChanged(double)", setAdjustAndResetButtonsEnabled)
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
    shPluginHandler.getOwnerPluginForSubjectHierarchyItem(shItemID).setDisplayVisibility(shItemID, visible);

    if self.MarkupsAnnotationNode is None:
      return
    with NodeModify(self.MarkupsAnnotationNode):
      self.MarkupsAnnotationNode.SetDefaultOntology(ontology)
      for i in range(self.MarkupsAnnotationNode.GetNumberOfMarkups()):
        self.MarkupsAnnotationNode.SetNthSplineOntology(i, ontology)

  def onCursorPositionModifiedEvent(self, caller=None, event=None):
    crosshairNode = caller
    if not crosshairNode or not crosshairNode.IsA('vtkMRMLCrosshairNode'):
      return

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
      hasVolume = True
      xyToIJK = layerLogic.GetXYToIJKTransform()
      ijkFloat = xyToIJK.TransformDoublePoint(xyz)
      ijk = [_roundInt(value) for value in ijkFloat]

    self.get("DataProbeLabel").text = self.getPixelString(volumeNode, ijk, ras)

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

