import os
import json
import logging
import textwrap
import urllib.parse
import requests
import typing

import vtk, qt, ctk, slicer

from contextlib import contextmanager

from slicer.util import NodeModify, VTKObservationMixin
from slicer.ScriptedLoadableModule import *
from HomeLib import HomeResources as Resources
from HomeLib import CellLocatorConfig as Config

from SubjectHierarchyPlugins import AbstractScriptedSubjectHierarchyPlugin

@contextmanager
def tempfile(path):
  """Manage creation and deletion of a temporary file path within the slicer temporary directory.

  Creates the directory containing the file at path, if it does not exist. Automatically removes the file at path, leaving directories intact.

  Yields the absolute path for the temporary file.
  """

  abspath = os.path.join(slicer.app.temporaryPath, path)
  directory = os.path.dirname(abspath)

  os.makedirs(directory, exist_ok=True)

  yield abspath

  os.remove(abspath)


def matToList(mat: vtk.vtkMatrix4x4) -> list:
  """Convert a vtkMatrix4x4 to list."""

  dim = 4

  return [mat.GetElement(i, j) for i in range(dim) for j in range(dim)]


def listToMat(lst: list) -> vtk.vtkMatrix4x4:
  """Convert a list to vtkMatrix4x4."""

  dim = 4

  mat = vtk.vtkMatrix4x4()
  for i in range(dim):
    for j in range(dim):
      mat.SetElement(i, j, lst[i * dim + j])

  return mat


class Annotation(VTKObservationMixin):
  """Manage serialization of a single annotation."""

  DisplayName = 'Annotation'
  MarkupType = ''

  def __init__(self, markup=None):
    """Setup the annotation markup and model, and add each to the scene."""

    VTKObservationMixin.__init__(self)

    self.logic = slicer.vtkSlicerSplinesLogic()

    if markup is not None:
      self.markup = markup
    else:
      self.markup = slicer.mrmlScene.AddNewNodeByClass(self.MarkupType)
      self.markup.AddDefaultStorageNode()
      markupName = self.markup.GetName()
      markupTag = self.markup.GetNodeTagName()
      self.markup.SetName(markupName.replace(markupTag, self.DisplayName))

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.orientation = vtk.vtkMatrix4x4()
    self.orientation.DeepCopy(sliceNode.GetSliceToRAS())

    self.addObserver(self.markup, self.markup.PointAddedEvent, self.onMarkupModified)
    self.addObserver(self.markup, self.markup.PointModifiedEvent, self.onMarkupModified)

  def clear(self):
    """Teardown the annotation markup and model, and remove them from the scene."""

    self.removeObserver(self.markup, self.markup.PointAddedEvent, self.onMarkupModified)
    self.removeObserver(self.markup, self.markup.PointModifiedEvent, self.onMarkupModified)

  def onMarkupModified(self, caller, event):
    """Event handler to update the annotation model when the markup is modified."""
    self.update()

  def update(self):
    """Do any necessary updates when the annotation is initialized, markup is modified, etc."""
    pass

  def metadata(self) -> dict:
    """Create a dict of any additional values needed for serialization."""
    return {}

  def setMetadata(self, data: dict):
    """Set any additional values needed for deserialization."""
    pass

  def toDict(self) -> dict:
    """Convert this annotation to a dict representation, suitable for json serialization."""

    with tempfile('json/annotation.json') as filename:
      slicer.util.saveNode(self.markup, filename)

      with open(filename) as f:
        markup = json.load(f)
        markup = markup['markups'][0]

        # Remove optional keys
        del markup['display']
        del markup['locked']
        del markup['labelFormat']
        for controlPoint in markup['controlPoints']:
          del controlPoint['associatedNodeID']
          del controlPoint['description']
          del controlPoint['label']
          del controlPoint['locked']
          del controlPoint['positionStatus']
          del controlPoint['selected']
          del controlPoint['visibility']

    return {
      'markup': markup,
      'name': self.markup.GetName(),
      'orientation': matToList(self.orientation),
      **self.metadata()
    }

  @classmethod
  def fromMarkup(cls, markup):
    """Initialize an Annotation given an existing markup. Selects from subclasses based on that class's MarkupType.

    For example, FiducialsAnnotation is a subclass of Annotation, so it is queried. FiducialsAnnotation.MarkupType is
    'vtkMRMLMarkupsFiducialNode', so if markup is a fiducial node, a FiducialsAnnotation would be created.
    """

    # could also create an explicit mapping from markup type to annotation type, but this
    # way is DRY and ensures a new type could never be missed as long as it inherits Annotation.

    # downside is there would be no way to have multiple annotation types use the same markup
    # type... we might need to store extra info in the file in that case.

    for icls in cls.__subclasses__():
      if markup.IsA(icls.MarkupType):
        return icls(markup=markup)

    logging.error('Unsupported markup type %r', markup.GetClassName())
    return None

  @classmethod
  def fromDict(cls, data):
    """Convert a dict representation to an annotation, suitable for json deserialization."""

    with tempfile('json/annotation.json') as filename:
      with open(filename, 'w') as f:
        # Initialize Slicer specific properties
        for controlPoint in data['markup']['controlPoints']:
          controlPoint['associatedNodeID'] = 'vtkMRMLScalarVolumeNode1'

        json.dump({
          '@schema': 'https://raw.githubusercontent.com/slicer/slicer/master/Modules/Loadable/Markups/Resources/Schema/markups-schema-v1.0.0.json#',
          'markups': [
            data['markup']
          ]
        }, f)
      markup = slicer.util.loadMarkups(filename)

    # we want to use fromMarkup so the correct behavior (annotation type) is used for the given markup type.
    # since each annotation type may have extra parameters, we should use setMetadata

    annotation = cls.fromMarkup(markup)
    annotation.setMetadata(data)
    annotation.orientation.DeepCopy(listToMat(data['orientation']))

    if 'name' in data:
      annotationName = data['name']
    else:
      annotationName = 'Annotation'
      logging.warning("Annotation data is missing the 'name' key. Defaulting to '%s'." % annotationName)
    annotation.markup.SetName(annotationName)

    return annotation


class FiducialAnnotation(Annotation):
  DisplayName = 'Point'
  MarkupType = 'vtkMRMLMarkupsFiducialNode'

  def __init__(self, markup=None):
    super().__init__(markup=markup)


class ClosedCurveAnnotation(Annotation):
  DisplayName = 'Curve'
  MarkupType = 'vtkMRMLMarkupsClosedCurveNode'

  DefaultRepresentationType = 'spline'
  DefaultThickness = 50

  def __init__(self, markup=None):
    self.representationType = self.DefaultRepresentationType
    self.thickness = self.DefaultThickness

    self.model = slicer.mrmlScene.AddNode(slicer.vtkMRMLModelNode())
    self.model.CreateDefaultDisplayNodes()

    # need to have representationType, thickness, model, etc when the markup is created.
    super().__init__(markup=markup)

    generator = self.markup.GetCurveGenerator()
    generator.SetNumberOfPointsPerInterpolatingSegment(20)

    displayNode = self.model.GetDisplayNode()
    displayNode.SetColor(0.4, 0.4, 0.4)
    displayNode.EdgeVisibilityOff()
    displayNode.SetOpacity(0.6)

  def clear(self):
    super().clear()

    slicer.mrmlScene.RemoveNode(self.markup)
    slicer.mrmlScene.RemoveNode(self.model)

  def update(self):
    """Update the annotation model to match the annotation markup and orientation."""

    if self.markup.GetNumberOfControlPoints() < 3:
      self.model.SetAndObserveMesh(vtk.vtkPolyData())  # clear mesh
      return

    if self.representationType == 'spline':
      self.markup.GetCurveGenerator().SetCurveTypeToCardinalSpline()
    else:
      self.markup.GetCurveGenerator().SetCurveTypeToLinearSpline()

    orientation = self.orientation
    normal = orientation.MultiplyPoint([0, 0, 1, 0])[:3]
    normal = vtk.vtkVector3d(normal)
    normal.Normalize()

    contour = self.markup.GetCurve()
    thickness = self.thickness

    self.logic.BuildSplineModel(
      self.model,
      contour,
      normal,
      thickness
    )

  def metadata(self):
    return {
      'representationType': self.representationType,
      'thickness': self.thickness
    }

  def setMetadata(self, data):
    self.representationType = data['representationType']
    self.thickness = data['thickness']

class AnnotationManager:
  """Manage serialization and bookkeeping for a collection of annotations."""

  FORMAT_VERSION = '0.1.1+2021.06.11'

  DefaultReferenceView = 'Coronal'
  DefaultOntology = 'Structure'
  DefaultStepSize = 1

  DefaultCameraPosition = (0.0, 0.0, 0.0)
  DefaultCameraViewUp = (1.0, 0.0, 0.0)

  def __init__(self):
    """Initialize an empty collection of annotations. Use add() to create empty annotations."""

    self.annotations: typing.List[Annotation] = []

    self.referenceView = self.DefaultReferenceView
    self.ontology = self.DefaultOntology
    self.stepSize = self.DefaultStepSize
    self.cameraPosition = list(self.DefaultCameraPosition)
    self.cameraViewUp = list(self.DefaultCameraViewUp)

    self.fileName = None

  @property
  def current(self) -> typing.Optional[Annotation]:
    """The current annotation, or None if currentId is not set."""

    tv = slicer.modules.HomeWidget.get('SubjectHierarchyTreeView')
    sh = tv.subjectHierarchyNode()

    currentId = tv.currentItem()

    for annotation in self.annotations:
      if currentId == sh.GetItemByDataNode(annotation.markup):
        return annotation

    return None

  @current.setter
  def current(self, annotation):
    tv = slicer.modules.HomeWidget.get('SubjectHierarchyTreeView')
    sh = tv.subjectHierarchyNode()

    itemId = sh.GetItemByDataNode(annotation.markup)
    tv.setCurrentItem(itemId)

  @property
  def currentIdx(self):
    """The index of the current annotation in self.annotations"""
    current = self.current

    if not current:
      return None

    return self.annotations.index(current)

  @currentIdx.setter
  def currentIdx(self, idx):
    self.current = self.annotations[idx]

  def add(self, annotation, setCurrent=True):
    """Add an annotation to the list. If setCurrent is True, then also make this the current annotation."""
    self.annotations.append(annotation)

    if setCurrent:
      self.current = annotation

  def setEnabled(self, annotation, enabled):
    """Enable or disable annotation and disable all the other ones.

    This means that the selected annotation is unlocked, individual control points
    can be moved, new point inserted and entire annotation translated or rotated
    using the interaction handles.
    """
    for _annotation in self.annotations:
      locked = True
      if _annotation == annotation:
        locked = not enabled
      _annotation.markup.SetLocked(locked)
      _annotation.markup.GetDisplayNode().SetHandlesInteractive(not locked)

    # Always hide interactive handles in 3D view
    threeDView = slicer.app.layoutManager().threeDWidget(0).threeDView()
    displayableManager = threeDView.displayableManagerByClassName("vtkMRMLMarkupsDisplayableManager")
    markupWidget = displayableManager.GetWidget(annotation.markup.GetDisplayNode())
    markupWidget.GetMarkupsRepresentation().SetInteractionPipelineVisibility(False)

  def clear(self):
    """Remove all annotations from the collection."""

    for annotation in self.annotations:
      annotation.clear()

    self.annotations.clear()

  def removeCurrent(self):
    self.remove(self.current)

  def remove(self, annotation):
    if annotation in self.annotations:
      self.annotations.remove(annotation)

    annotation.clear()

    if self.currentIdx is None and self.annotations:
      self.currentIdx = len(self.annotations) - 1

  def __iter__(self):
    return iter(self.annotations)

  def toDict(self):
    """Convert this collection to dict representation, suitable for json serialization."""

    return {
      'version': self.FORMAT_VERSION,
      'markups': [annotation.toDict() for annotation in self.annotations],
      'currentId': self.currentIdx,

      'referenceView': self.referenceView,
      'ontology': self.ontology,
      'stepSize': self.stepSize,

      'cameraPosition': self.cameraPosition,
      'cameraViewUp': self.cameraViewUp,
    }

  @classmethod
  def fromDict(cls, data):
    """Convert a dict representation to annotation collection, suitable for json deserialization."""

    manager = cls()

    manager.annotations = [Annotation.fromDict(item) for item in data['markups']]
    manager.currentIdx = data['currentId']

    manager.referenceView = data['referenceView']
    manager.ontology = data['ontology']
    manager.stepSize = data['stepSize']

    manager.cameraPosition = data['cameraPosition']
    manager.cameraViewUp = data['cameraViewUp']

    return manager

  def toFile(self, fileName=None, indent=2):
    """Save this annotation collection as a json file.

    If no fileName is provided, use the instance variable fileName.

    If one is provided, then the instance variable is updated so that subsequent
    calls to toFile() will save to the same location unless a new one is provided.

    indent is the same parameter for json.dump. Defaults to 2 to indent file by 2 spaces. Set to None to remove indentation.
    """

    if fileName is not None:
      self.fileName = fileName

    if self.fileName is None:
      raise IOError('filename not provided')

    data = self.toDict()

    with open(self.fileName, 'w') as f:
      json.dump(data, f, indent=indent)

  @classmethod
  def fromFile(cls, fileName):
    """Load an annotation collection from a json file.

    Instance variable fileName is set, so that subsequent calls to toFile() will
    update that same file.
    """

    with open(fileName) as f:
      data = json.load(f)

    manager = cls.fromDict(data)
    manager.fileName = fileName

    return manager


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
    self.parent.title = "Home"
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
    self.Annotations: AnnotationManager = None
    self.ThreeDWithReformatCustomLayoutId = None
    self.Widget = None
    self._widget_cache = {}

    self.PreviousViewport = None
    self.PreviousLayoutId = None

    self.ClearAction = None

    self.InteractionNode = None

    self._interactionState = 'explore'

    if slicer.app.commandOptions().referenceView:
      referenceView = slicer.app.commandOptions().referenceView
      if referenceView in ["Axial", "Coronal", "Sagittal"]:
        AnnotationManager.DefaultReferenceView = referenceView
      else:
        logging.error("Invalid value '%s' associated with --reference-view command-line argument. "
                      "Accepted values are %s" % (referenceView, ", ".join(["Axial", "Coronal", "Sagittal"])))

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

  def promptForAtlasSelection(self):
    """Prompt the user to select an atlas type.
    """
    dialog = slicer.util.loadUI(self.resourcePath('UI/AtlasSelection.ui'))
    dialog.setWindowFlags(qt.Qt.CustomizeWindowHint | qt.Qt.WindowCloseButtonHint)
    dialogUi = slicer.util.childWidgetVariables(dialog)
    dialog.setWindowIcon(qt.QIcon(self.resourcePath('Icons/Home.png')))
    dialogUi.CCFButton.clicked.connect(lambda: self.logic.setAtlasType(HomeLogic.CCF_ATLAS))
    dialogUi.MNIButton.clicked.connect(lambda: self.logic.setAtlasType(HomeLogic.MNI_ATLAS))
    # Comment copied from function "messageBox()" in Slicer/Base/Python/slicer/util.py
    # Windows 10 peek feature in taskbar shows all hidden but not destroyed windows
    # (after creating and closing a messagebox, hovering over the mouse on Slicer icon, moving up the
    # mouse to the peek thumbnail would show it again).
    # By calling deleteLater, the dialog is permanently deleted when the current call is completed.
    dialog.deleteLater()
    dialog.exec_()

  def onStartupCompleted(self, *unused):

    def postStartupInitialization():

      if not slicer.app.commandOptions().atlasType:
        if slicer.app.commandOptions().testingEnabled:
          self.logic.setAtlasType(HomeLogic.CCF_ATLAS)
        else:
          self.promptForAtlasSelection()
      else:
        self.logic.setAtlasType(slicer.app.commandOptions().atlasType)

      self.onSceneEndCloseEvent(slicer.mrmlScene)

      if slicer.app.commandOptions().argumentParsed("view-angle"):
        viewAngle = slicer.app.commandOptions().viewAngle

        angles = {'Roll': 0, 'Yaw': 0, 'Pitch': 0}
        if self.getReferenceView() == "Coronal":
          angles['Roll'] = viewAngle - 90
        elif self.getReferenceView() == "Sagittal":
          angles['Pitch'] = viewAngle - 90
        elif self.getReferenceView() == "Axial":
          angles['Yaw'] = viewAngle - 90

        for axe in angles:
          with SignalBlocker(self.get('%sSliderWidget' % axe)):
            self.get('%sSliderWidget' % axe).value = angles[axe]

        self.onViewOrientationChanged()

      annotationFilePath = slicer.app.commandOptions().annotationFilePath
      if annotationFilePath:
        annotations = AnnotationManager.fromFile(annotationFilePath)
        self.setAnnotations(annotations)
        self.annotationStored()

      limsSpecimenID = slicer.app.commandOptions().limsSpecimenID
      if limsSpecimenID:
        self.loadLIMSSpecimen(limsSpecimenID)

    qt.QTimer.singleShot(0, lambda: postStartupInitialization())

  def isAnnotationSavingRequired(self):
    if self.Annotations.current is None:
      return False

    storableNodes = slicer.mrmlScene.GetStorableNodesModifiedSinceReadByClass(
      "vtkMRMLMarkupsNode"
    )

    modified = slicer.mrmlScene.GetModifiedSinceRead()

    return storableNodes or modified

  def setAnnotations(self, annotations):
    if self.Annotations:
      self.Annotations.clear()

    self.Annotations = annotations
    self.updateGUIFromMRML()
    self.updateCameraFromAnnotations()
    self.updateSliceFromAnnotations()

    self.setInteractionState('explore')

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
      "Coronal": slicer.vtkMRMLCameraNode.Posterior,
      "Sagittal": slicer.vtkMRMLCameraNode.Left,
    }
    cameraNode.RotateTo(rotateTo[self.getReferenceView()])

    renderer = threeDView.renderer()
    resetRotation = False
    resetTranslation = True
    resetDistance = True
    cameraNode.Reset(resetRotation, resetTranslation, resetDistance, renderer)

  def saveIfRequired(self):
    """Save if annotation requires saving.

    returns True if safe to proceed (saving is not required, user chooses not to save, or saving is successful)
    returns False if saving fails
    """

    question = "The annotation has been modified. Do you want to save before creating a new one?"

    if self.isAnnotationSavingRequired():
      if slicer.util.confirmYesNoDisplay(question, parent=slicer.util.mainWindow()):
        return self.onSaveAnnotationButtonClicked()

    return True

  def onAddCurveAnnotationButtonClicked(self):
    """Add a curve annotation to the tree view."""

    self.Annotations.add(ClosedCurveAnnotation())

  def onAddPointAnnotationButtonClicked(self):
    """Add a point annotation to the tree view."""

    self.Annotations.add(FiducialAnnotation())

  def onCloneAnnotationButtonClicked(self):
    """Clone the current annotation and add it to the tree view."""

    # copy all attributes of the annotation, reusing the existing serialization logic.
    # convert to dict and back.
    data = self.Annotations.current.toDict()
    annotation = Annotation.fromDict(data)

    self.Annotations.add(annotation=annotation)

  def onRemoveAnnotationButtonClicked(self):
    """Remove an annotation from the tree view."""

    if self.Annotations.current:
      self.Annotations.removeCurrent()

  def onNewAnnotationButtonClicked(self):
    if not self.saveIfRequired(): return

    self.setInteractionState('explore')
    self.Annotations.fileName = None
    self.Annotations.clear()
    self.Annotations.add(ClosedCurveAnnotation())
    self.annotationStored()

  def onSaveAnnotationButtonClicked(self):
    if not self.Annotations.fileName:
      return self.onSaveAsAnnotationButtonClicked()

    self.Annotations.toFile()
    self.annotationStored()

  def onSaveAsAnnotationButtonClicked(self):

    defaultFileName = "annotation.json"
    directory = slicer.app.userSettings().value(
      "LastAnnotationDirectory", qt.QStandardPaths.writableLocation(qt.QStandardPaths.DocumentsLocation))
    if os.path.exists(directory):
      defaultFileName = directory + "/" + defaultFileName

    fileName = qt.QFileDialog.getSaveFileName(
      slicer.util.mainWindow(),
      'Save Annotation As',
      defaultFileName,
      'Annotations (*.json)'
    )

    if not fileName:
      return False

    self.Annotations.toFile(fileName)

    directory = os.path.dirname(fileName)
    slicer.app.userSettings().setValue("LastAnnotationDirectory", directory)
    self.annotationStored()

    return True

  def onLoadAnnotationButtonClicked(self):
    if not self.saveIfRequired(): return

    fileName = qt.QFileDialog.getOpenFileName(
      slicer.util.mainWindow(),
      'Load Annotation',
      None,
      'Annotations (*.json)'
    )

    if not fileName: return

    self.setInteractionState('explore')
    self.Annotations.clear()
    annotations = AnnotationManager.fromFile(fileName)
    self.setAnnotations(annotations)
    self.annotationStored()

  def loadLIMSSpecimen(self, specimenID):
    """Retrieve and load specimenID from LIMS.

    See :func:`HomeLogic.limsBaseURL()`:
    """
    logging.info('Loading LIMS specimen id %s', specimenID)

    path = '/specimen_metadata/view'
    url = urllib.parse.urljoin(HomeLogic.limsBaseURL(), path)

    query = {
      'kind': 'IVSCC cell locations',
      'specimen_id': specimenID
    }

    try:
      res = requests.get(url, params=query)
    except requests.exceptions.ConnectionError as exc:
      logging.error(exc)
      slicer.util.errorDisplay(
        'Failed to load annotations for LIMS specimen %s. '
        'Error: Failed to establish LIMS connection at %s' % (specimenID, HomeLogic.limsBaseURL()))
      return

    if res.status_code == 200:
      annotations = AnnotationManager.fromDict(res.json()['data'])
      self.setAnnotations(annotations)
    else:
      try:
        message = res.json()['message']
      except (json.JSONDecodeError, KeyError):
        message = res.reason

      logging.error(
        'Failed to load annotations for LIMS specimen %s. Error %s: %r',
        specimenID,
        res.status_code,
        message
      )

  def onUploadAnnotationButtonClicked(self):
    logging.info('Upload Annotation Button Clicked')

    limsSpecimenID = slicer.app.commandOptions().limsSpecimenID
    self.saveLIMSSpecimen(limsSpecimenID)

  def saveLIMSSpecimen(self, specimenID):
    """Publish annotations to LIMS as specimenID.

    See :func:`HomeLogic.limsBaseURL()`:
    """
    logging.info('Saving LIMS specimen id %s', specimenID)

    data = self.Annotations.toDict()

    path = '/specimen_metadata/store'
    url = urllib.parse.urljoin(HomeLogic.limsBaseURL(), path)

    body = {
      'kind': 'IVSCC cell locations',
      'specimen_id': specimenID,
      'data': data
    }

    try:
      res = requests.post(url, json=body)
    except requests.exceptions.ConnectionError as exc:
      logging.error(exc)
      slicer.util.errorDisplay(
        'Failed to save annotations for LIMS specimen %s. '
        'Error: Failed to establish LIMS connection at %s' % (specimenID, HomeLogic.limsBaseURL()))
      return

    if res.status_code == 200:
      self.annotationStored()
    else:
      try:
        message = res.json()['message']
      except (json.JSONDecodeError, KeyError):
        message = res.reason

      logging.error(
        'Failed to save annotations for LIMS specimen %s. Error %s: %r',
        specimenID,
        res.status_code,
        message
      )

  def annotationStored(self):
    """Update scene and annotation storage node stored time. This indicates
    no saving is required until the next scene or node update."""
    slicer.mrmlScene.StoredModified()

    if self.Annotations.current:
      self.Annotations.current.markup.GetStorageNode().StoredModified()

    if slicer.app.commandOptions().limsSpecimenID:
      self.get('AnnotationPathLineEdit').currentPath = 'LIMS Specimen %s' % slicer.app.commandOptions().limsSpecimenID
    else:
      self.get('AnnotationPathLineEdit').currentPath = str(self.Annotations.fileName)

  def updateCameraFromAnnotations(self):
    viewNode = slicer.app.layoutManager().threeDWidget(0).threeDView().mrmlViewNode()
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)

    with NodeModify(cameraNode):
      position = self.Annotations.cameraPosition
      viewUp = self.Annotations.cameraViewUp
      cameraNode.SetPosition(position)
      cameraNode.SetViewUp(viewUp)
      cameraNode.ResetClippingRange()

  def updateSliceFromAnnotations(self):
    if not self.Annotations.current:
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    with NodeModify(sliceNode):
      sliceNode.GetSliceToRAS().DeepCopy(self.Annotations.current.orientation)
      sliceNode.UpdateMatrices()

  def updateGUIFromMRML(self):
    self.onMarkupsAnnotationStorageNodeModifiedEvent()
    self.updateGUIFromAnnotation()
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
      stepSize = {'minimum': 0.1, 'maximum': spacingRange / 10}
    else:
      stepSize = {'minimum': 0.1, 'maximum': 100}
    with SignalBlocker(self.get('StepSizeSliderWidget')):
      self.get('StepSizeSliderWidget').minimum = stepSize['minimum']
      self.get('StepSizeSliderWidget').maximum = stepSize['maximum']

    if self.Annotations.current is None or self.Annotations.current.markup.GetNumberOfMarkups() == 0:
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

    self.Annotations.stepSize = spacing

  def onMarkupsAnnotationStorageNodeModifiedEvent(self):
    if not self.Annotations or not self.Annotations.fileName:
      return

    self.get('AnnotationPathLineEdit').currentPath = self.Annotations.fileName

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

    self.Annotations.referenceView = orientation

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
    self.get('ContrastSlider').setValues(self.logic.DefaultWindowLevelMin, self.logic.DefaultWindowLevelMax)

  def onThicknessChanged(self, value):
    self.Annotations.current.thickness = value
    self.Annotations.current.update()

  def onAnnotationTypeChanged(self):
    if self.get('SplineRadioButton').checked:
      representationType = 'spline'
    else:
      representationType = 'polyline'

    self.Annotations.current.representationType = representationType
    self.Annotations.current.update()

  def onSliceNodeModifiedEvent(self, caller=None, event=None):
    sliceNode = caller
    if not sliceNode:
      sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # GUI update
    self.updateGUIFromSliceNode()

    # Markup Annotation update
    if not self.Annotations.current:
      return

    markup = self.Annotations.current.markup

    with NodeModify(markup):
      if self.getInteractionState() == 'explore':
        return

      self.Annotations.current.orientation.DeepCopy(sliceNode.GetSliceToRAS())

      normal = [0.0, 0.0, 0.0, 0.0]
      sliceNode.GetSliceToRAS().MultiplyPoint([0.0, 0.0, 1.0, 0.0], normal)
      normal = normal[:3]
      vtk.vtkMath.Normalize(normal)
      origin = [sliceNode.GetSliceToRAS().GetElement(i, 3) for i in range(3)]

      # Project points onto the current slice if needed
      for i in range(markup.GetNumberOfControlPoints()):
        point = [0.0, 0.0, 0.0]
        markup.GetNthControlPointPosition(i, point)
        proj = [0.0, 0.0, 0.0]
        vtk.vtkPlane.ProjectPoint(point, origin, normal, proj)
        markup.SetNthControlPointPositionFromArray(i, proj)

  def onCameraNodeModifiedEvent(self, caller, event):
    cameraNode = caller
    if self.Annotations.current is None:
      return

    position = [0., 0., 0.]
    cameraNode.GetPosition(position)
    self.Annotations.cameraPosition = position

    viewUp = [0., 0., 0.]
    cameraNode.GetViewUp(viewUp)
    self.Annotations.cameraViewUp = viewUp

  def onSceneStartCloseEvent(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')
    self.removeObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModifiedEvent)

    viewNode = slicer.app.layoutManager().threeDWidget(0).threeDView().mrmlViewNode()
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode)
    self.removeObserver(cameraNode, vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModifiedEvent)

    if self.Annotations:
      self.Annotations.clear()

  def setupViewers(self):
    # Configure slice view
    sliceWidget = self.LayoutManager.sliceWidget("Slice")
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.AdjustLightbox, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.AdjustWindowLevelBackground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.AdjustWindowLevelForeground, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.Blend, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.SelectVolume, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.ShowSlice, False)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.Translate, True)
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.Zoom, True)
    # TODO Explicitly re-enable SetCursorPosition last to workaround https://github.com/Slicer/Slicer/issues/5175
    sliceWidget.sliceView().interactorStyle().SetActionEnabled(slicer.vtkMRMLSliceViewInteractorStyle.SetCursorPosition, True)
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

    # Configure sideebar for multi-annotation support

    #  tool buttons
    addCurveButton = qt.QPushButton('Add Curve')
    addCurveButton.objectName = 'AddCurveAnnotationButton'
    self.set(addCurveButton)
    addCurveButton.setIcon(qt.QIcon(":/Icons/add_icon.svg.png"))

    addPointButton = qt.QPushButton('Add Point')
    addPointButton.objectName = 'AddPointAnnotationButton'
    self.set(addPointButton)
    addPointButton.setIcon(qt.QIcon(":/Icons/add_icon.svg.png"))

    cloneButton = qt.QPushButton('Clone')
    cloneButton.objectName = 'CloneAnnotationButton'
    self.set(cloneButton)
    cloneButton.setIcon(qt.QIcon(":/Icons/clone_icon.svg.png"))

    removeButton = qt.QPushButton('Remove')
    removeButton.objectName = 'RemoveAnnotationButton'
    self.set(removeButton)
    removeButton.setIcon(qt.QIcon(":/Icons/remove_icon.svg.png"))

    sideBarToolLayout = qt.QHBoxLayout()
    sideBarToolLayout.addWidget(addCurveButton)
    sideBarToolLayout.addWidget(addPointButton)
    sideBarToolLayout.addWidget(cloneButton)
    sideBarToolLayout.addWidget(removeButton)

    sideBarTools = qt.QWidget()
    sideBarTools.setLayout(sideBarToolLayout)

    #  tree view
    treeView = slicer.qMRMLSubjectHierarchyTreeView()
    treeView.objectName = 'SubjectHierarchyTreeView'
    self.set(treeView)
    treeView.setMRMLScene(slicer.mrmlScene)
    treeView.nodeTypes = ('vtkMRMLMarkupsNode',)
    treeView.multiSelection = False
    treeView.contextMenuEnabled = False
    treeView.editMenuActionVisible = False
    treeView.selectRoleSubMenuVisible = False
    treeView.setColumnHidden(treeView.model().colorColumn, True)
    treeView.setColumnHidden(treeView.model().transformColumn, True)
    treeView.setColumnHidden(treeView.model().idColumn, True)

    sidebarLayout = qt.QVBoxLayout()
    sidebarLayout.addWidget(sideBarTools)
    sidebarLayout.addWidget(treeView)
    sidebar = qt.QWidget()
    sidebar.objectName = 'SubjectHierarchyWidget'
    self.set(sidebar)
    sidebar.setLayout(sidebarLayout)

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
    self.setInteractionState('explore')
    self.resetViews()

  def onSceneEndCloseEvent(self, caller=None, event=None):
    scene = caller
    if not scene or not scene.IsA('vtkMRMLScene'):
      return

    # Configure UI
    self.get('AdjustViewPushButton').enabled = False

    averageTemplate, annotation = self.logic.loadData(self.logic.atlasType())

    sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice')

    # Default StepSize
    sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
    initialSpacing = sliceLogic.GetLowestVolumeSliceSpacing()
    sliceNode.SetPrescribedSliceSpacing(initialSpacing)
    self.DefaultStepSize = initialSpacing[2]

    # Ontology
    ontologyComboBox = self.get('OntologyComboBox')
    with SignalBlocker(ontologyComboBox):
      ontologyComboBox.clear()
      if self.logic.atlasType() == HomeLogic.CCF_ATLAS:
        ontologyComboBox.addItems(['Structure', 'Layer', 'None'])
      else:
        ontologyComboBox.addItems(['Structure', 'None'])

    # Configure unit
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    unitNode = selectionNode.GetUnitNode("length")
    with NodeModify(unitNode):
      unitNode.SetSuffix({
        HomeLogic.CCF_ATLAS: "um",
        HomeLogic.MNI_ATLAS: "mm"
      }[self.logic.atlasType()])
    # HACK Since modifying the unit node is not sufficient, force update calling SetUnitNodeID
    selectionNode.SetUnitNodeID(unitNode.GetID(), "length")

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

    if self.logic.atlasType() == HomeLogic.CCF_ATLAS:
      # Flip coronal axis to match PIR convention
      threeDNode.SetAxisLabel(2, "A")  # P -> A
      threeDNode.SetAxisLabel(3, "P")  # A -> P

    # Configure annotation list
    #   Since the viewport is managed elsewhere, we need to insert the sidebar
    #   ourselves. The viewport layout is horizontal LTR by default, so inserting
    #   at index 0 puts it on the left.
    sidebar = self.get("SubjectHierarchyWidget")
    viewport = self.LayoutManager.viewport()
    viewport.layout().insertWidget(0, sidebar)
    sidebar.setVisible(True)
    #   We want the sidebar to resize with the rest of the screen. Keep it 1/3 the
    #   width of the slice and 3D views.
    viewport.layout().setStretchFactor(sliceWidget, 3)
    viewport.layout().setStretchFactor(threeDWidget, 3)
    viewport.layout().setStretchFactor(sidebar, 1)

    # Connections
    self.addObserver(sliceNode, vtk.vtkCommand.ModifiedEvent, self.onSliceNodeModifiedEvent)
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(threeDWidget.threeDView().mrmlViewNode())
    self.addObserver(cameraNode, vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModifiedEvent)

    if self.logic.atlasType() == HomeLogic.CCF_ATLAS:
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
      #   1  0  0
      #   0  0  1
      #   0  1  0
      #

    sliceNode.DisableModifiedEventOn()
    orientationMatrix = vtk.vtkMatrix3x3()
    slicer.vtkMRMLSliceNode.GetCoronalSliceToRASMatrix(orientationMatrix)
    orientationMatrix.SetElement(0, 0, 1.0)
    orientationMatrix.SetElement(1, 2, 1.0)
    orientationMatrix.SetElement(2, 1, 1.0)
    sliceNode.RemoveSliceOrientationPreset("Coronal")
    sliceNode.AddSliceOrientationPreset("Coronal", orientationMatrix)
    sliceNode.DisableModifiedEventOff()

    # Setup Annotations
    annotations = AnnotationManager()
    annotations.add(ClosedCurveAnnotation())
    self.setAnnotations(annotations)
    self.setDefaultSettings()
    self.annotationStored()

    self.Annotations.current.orientation.DeepCopy(sliceNode.GetSliceToRAS())

    self.setInteractionState('explore')

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

    # Keep track of original viewport and layout
    self.PreviousViewport = self.LayoutManager.viewport()
    self.PreviousLayoutId = self.LayoutManager.layout

    # Update layout manager viewport
    slicer.util.findChildren(name="CentralWidget")[0].visible = False
    self.LayoutManager.setViewport(self.get('LayoutWidget'))

    # Configure layout
    # slicer.modules.celllocator.registerCustomViewFactories(self.LayoutManager)
    self.LayoutManager.setLayout(
      self.logic.registerCustomLayouts(
        self.LayoutManager.layoutLogic(),
        AnnotationManager.DefaultReferenceView)
    )

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

    if slicer.app.commandOptions().limsSpecimenID:
      self.get('FileButtons').setVisible(False)
      self.get('LIMSButtons').setVisible(True)
    else:
      self.get('FileButtons').setVisible(True)
      self.get('LIMSButtons').setVisible(False)

    self.setupViewers()
    self.setupConnections()

  def updateGUIFromAnnotation(self):
    annotations = self.Annotations
    current = self.Annotations.current

    isClosedCurve = isinstance(current, ClosedCurveAnnotation)
    if isClosedCurve:
      thickness = annotations.current.thickness
      representation = annotations.current.representationType.title()
    else:
      thickness = ClosedCurveAnnotation.DefaultThickness
      representation = ClosedCurveAnnotation.DefaultRepresentationType.title()

    self.get('ThicknessSliderWidget').value = thickness
    self.get('%sRadioButton' % representation).setChecked(True)

    self.get('OntologyComboBox').currentText = annotations.ontology
    self.get('ReferenceViewComboBox').currentText = annotations.referenceView
    self.get('StepSizeSliderWidget').value = annotations.stepSize

    self.setAttributeWidgetsEnabled()

  def getReferenceView(self):
    return self.get('ReferenceViewComboBox').currentText

  @contextmanager
  def interactionState(self, newState):
    previousState = self.getInteractionState()
    self.setInteractionState(newState)
    yield
    self.setInteractionState(previousState)

  def getInteractionState(self):
    return self._interactionState

  def setInteractionState(self, newState):
    newState = newState.lower()
    assert newState in ('explore', 'annotate', 'place')

    self._interactionState = newState

    button = self.get('%sRadioButton'%newState.title())
    with SignalBlocker(button):
      button.setChecked(True)

    if not self.Annotations.current:
      return

    # 1: update selection node
    markup = self.Annotations.current.markup
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetActivePlaceNodeID(markup.GetID())
    selectionNode.SetReferenceActivePlaceNodeClassName(markup.GetClassName())

    # 2: update interaction mode:
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    if newState == 'place':
      interactionNode.SwitchToPersistentPlaceMode()
    else:
      interactionNode.SwitchToViewTransformMode()

    # 3: enable annotation based on the current state
    enabled = newState in ('place', 'annotate')
    self.Annotations.setEnabled(self.Annotations.current, enabled)

    # 4: update slice
    if enabled:
      with NodeModify(self.Annotations.current.markup):
        self.updateSliceFromAnnotations()
        self.onSliceNodeModifiedEvent()

  def setupConnections(self):
    slicer.app.connect("startupCompleted()", self.onStartupCompleted)
    self.get('NewAnnotationButton').connect("clicked()", self.onNewAnnotationButtonClicked)
    self.get('SaveAnnotationButton').connect("clicked()", self.onSaveAnnotationButtonClicked)
    self.get('SaveAsAnnotationButton').connect("clicked()", self.onSaveAsAnnotationButtonClicked)
    self.get('LoadAnnotationButton').connect("clicked()", self.onLoadAnnotationButtonClicked)
    self.get('UploadAnnotationButton').connect("clicked()", self.onUploadAnnotationButtonClicked)

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

    def interactionStateSetter(state):
      def handler(mode):
        if mode:
          self.setInteractionState(state)

      return handler

    self.get('ExploreRadioButton').connect('toggled(bool)', interactionStateSetter('explore'))
    self.get('AnnotateRadioButton').connect('toggled(bool)', interactionStateSetter('annotate'))
    self.get('PlaceRadioButton').connect('toggled(bool)', interactionStateSetter('place'))

    self.get('OntologyComboBox').connect("currentTextChanged(QString)", self.onOntologyChanged)

    self.get('AddCurveAnnotationButton').connect('clicked()', self.onAddCurveAnnotationButtonClicked)
    self.get('AddPointAnnotationButton').connect('clicked()', self.onAddPointAnnotationButtonClicked)
    self.get('RemoveAnnotationButton').connect('clicked()', self.onRemoveAnnotationButtonClicked)
    self.get('CloneAnnotationButton').connect('clicked()', self.onCloneAnnotationButtonClicked)
    self.get('SubjectHierarchyTreeView').connect('currentItemChanged(vtkIdType)', self.onCurrentItemChanged)

    self.ClearAction = qt.QAction(slicer.util.mainWindow())
    self.ClearAction.shortcut = qt.QKeySequence("Ctrl+W")
    self.ClearAction.connect("triggered()", lambda: slicer.mrmlScene.Clear(False))
    slicer.util.mainWindow().addAction(self.ClearAction)

    # Observe the crosshair node to get the current cursor position
    crosshairNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCrosshairNode')
    self.addObserver(crosshairNode, slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.onCursorPositionModifiedEvent)

    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    self.addObserver(interactionNode, interactionNode.InteractionModeChangedEvent, self.onInteractionModeChanged)

  def setAttributeWidgetsEnabled(self):
    if not self.Annotations: 
      return

    current = self.Annotations.current
    isClosedCurve = isinstance(current, ClosedCurveAnnotation)
    self.get('ThicknessSliderWidget').enabled = isClosedCurve
    self.get('PolylineRadioButton').enabled = isClosedCurve
    self.get('SplineRadioButton').enabled = isClosedCurve

  def onCurrentItemChanged(self, vtkId):
    # If things aren't initialized yet then we shouldn't do anything. This will happen a few times during setup while
    # other nodes are added to the subject hierarchy.
    if not self.Annotations or not self.Annotations.current:
      return

    # We need to re-initialize the interaction mode for the current markup. The easiest way is to go to explore, then
    # back to the original mode. If the mode already is explore, then nothing will happen. That's okay, since explore
    # does not interact with the current annotation.
    old = self.getInteractionState()
    self.setInteractionState('explore')
    self.setInteractionState(old)

    self.setAttributeWidgetsEnabled()

  def onOntologyChanged(self, ontology):
    annotation = slicer.mrmlScene.GetFirstNodeByName(
      os.path.splitext(os.path.basename(HomeLogic.annotationFilePath(self.logic.atlasType())))[0])
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

    self.Annotations.ontology = ontology

  def onCursorPositionModifiedEvent(self, caller=None, event=None):
    crosshairNode = caller
    if not crosshairNode or not crosshairNode.IsA('vtkMRMLCrosshairNode'):
      return
    self.get("DataProbeLabel").text = self.logic.getCrosshairPixelString(crosshairNode)

  def onInteractionModeChanged(self, caller, event):
    if self.getInteractionState() == 'annotate':
      return

    if caller.GetLastInteractionMode() != caller.Place:
      return

    if caller.GetCurrentInteractionMode() != caller.ViewTransform:
      return

    self.setInteractionState('annotate')

  def cleanup(self):
    self.get('SubjectHierarchyTreeView').disconnect('currentItemChanged(vtkIdType)', self.onCurrentItemChanged)
    self.onSceneStartCloseEvent(slicer.mrmlScene)
    self.LayoutManager.setViewport(self.PreviousViewport)
    self.LayoutManager.layout = self.PreviousLayoutId
    self.Widget = None


class HomeLogic(object):

  CCF_ATLAS = 'ccf'
  MNI_ATLAS = 'mni'

  def __init__(self):
    self.AllenStructurePaths = {}
    self.AllenLayerStructurePaths = {}
    self.SlicerToAllenMapping = {}
    self.AllenToSlicerMapping = {}

    self.DefaultWindowLevelMin = 0.
    self.DefaultWindowLevelMax = 0.

    self._atlasType = None

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
  def dataPath():
    return os.path.join(os.path.dirname(slicer.util.modulePath('Home')), 'CellLocatorData')

  @staticmethod
  def averageTemplateFilePath(atlas_type=CCF_ATLAS):
    """Average template file path"""
    return os.path.join(HomeLogic.dataPath(), {
      HomeLogic.CCF_ATLAS: 'ccf_average_template_%s.nrrd' % Config.CCF_ANNOTATION_RESOLUTION,
      HomeLogic.MNI_ATLAS: Config.MNI_AVERAGE_TEMPLATE_FILENAME
    }[atlas_type])

  @staticmethod
  def annotationFilePath(atlas_type=CCF_ATLAS):
    """Annotation file path"""
    return os.path.join(HomeLogic.dataPath(), {
      HomeLogic.CCF_ATLAS: 'ccf_annotation_%s_contiguous.nrrd' % Config.CCF_ANNOTATION_RESOLUTION,
      HomeLogic.MNI_ATLAS: 'mni_annotation_contiguous.nrrd'
    }[atlas_type])

  @staticmethod
  def colorTableFilePath(atlas_type=CCF_ATLAS):
    """Color table for structures"""
    return os.path.join(HomeLogic.dataPath(), '%s_annotation_color_table.txt' % atlas_type)

  @staticmethod
  def layerColorTableFilePath(atlas_type=CCF_ATLAS):
    """Color table for layers"""
    return os.path.join(HomeLogic.dataPath(), '%s_annotation_layer_color_table.txt' % atlas_type)

  @staticmethod
  def ontologyFilePath(atlas_type=CCF_ATLAS):
    """Ontology for structures"""
    return os.path.join(HomeLogic.dataPath(), '%s-ontology-formatted.json' % atlas_type)

  @staticmethod
  def layerOntologyFilePath(atlas_type=CCF_ATLAS):
    """Ontology for layers"""
    return os.path.join(HomeLogic.dataPath(), '%s-layer-ontology-formatted.json' % atlas_type)

  @staticmethod
  def slicerToAllenMappingFilePath(atlas_type=CCF_ATLAS):
    """Mapping of Slicer color labels to Allen color labels"""
    return os.path.join(HomeLogic.dataPath(), '%s_annotation_color_slicer2allen_mapping.json' % atlas_type)

  @staticmethod
  def allenToSlicerMappingFilePath(atlas_type=CCF_ATLAS):
    """Mapping of Allen color labels to Slicer color labels"""
    return os.path.join(HomeLogic.dataPath(), '%s_annotation_color_allen2slicer_mapping.json' % atlas_type)

  def loadData(self, atlas_type):
    """Load average template, annotation and associated color tables for the selected atlas
    """

    # Load template
    try:
      averageTemplate = slicer.util.loadVolume(self.averageTemplateFilePath(atlas_type=atlas_type))
    except RuntimeError:
      logging.error('Average template [%s] does not exists' % self.averageTemplateFilePath(atlas_type=atlas_type))

    # Set the min/max window level
    scalarRange = averageTemplate.GetImageData().GetScalarRange()
    averageTemplateDisplay = averageTemplate.GetDisplayNode()
    averageTemplateDisplay.SetAutoWindowLevel(0)
    # No option to set the window level to min/max through the node. Instead
    # do it manually (see qMRMLWindowLevelWidget::setMinMaxRangeValue)
    window = scalarRange[1] - scalarRange[0]
    level = 0.5 * (scalarRange[0] + scalarRange[1])

    averageTemplateDisplay.SetWindowLevel(window, level)

    self.DefaultWindowLevelMin = scalarRange[0]
    self.DefaultWindowLevelMax = scalarRange[1]

    # Lock the window level
    averageTemplateDisplay.SetWindowLevelLocked(True)

    # Load Allen color table
    colorLogic = slicer.modules.colors.logic()
    colorNodeID = None
    if os.path.exists(self.colorTableFilePath(atlas_type=atlas_type)):
      colorNode = colorLogic.LoadColorFile(self.colorTableFilePath(atlas_type=atlas_type), "allen")
      colorNodeID = colorNode.GetID()
    else:
      logging.error("Color table [%s] does not exist" % self.colorTableFilePath(atlas_type=atlas_type))

    # Load Allen "layer" color table (only available for the CCF atlas type)
    if atlas_type == HomeLogic.CCF_ATLAS:
      if os.path.exists(self.layerColorTableFilePath()):
        colorLogic.LoadColorFile(self.layerColorTableFilePath(), "allen_layer")
      else:
        logging.error("Color table [%s] does not exist" % self.layerColorTableFilePath())

    # Load slicer2allen mapping
    with open(self.slicerToAllenMappingFilePath(atlas_type=atlas_type)) as content:
      mapping = json.load(content)
      self.SlicerToAllenMapping = {int(key): int(value) for (key, value) in mapping.items()}

    # Load allen2slicer mapping
    with open(self.allenToSlicerMappingFilePath(atlas_type=atlas_type)) as content:
      mapping = json.load(content)
      self.AllenToSlicerMapping = {int(key): int(value) for (key, value) in mapping.items()}

    # Load ontology
    with open(self.ontologyFilePath(atlas_type=atlas_type)) as content:
      msg = json.load(content)["msg"]

    allenStructureNames = {}
    for structure in msg:
      allenStructureNames[structure["id"]] = structure["acronym"]

    self.AllenStructurePaths = {}
    for structure in msg:
      self.AllenStructurePaths[structure["id"]] = " > ".join(
        [allenStructureNames[int(structure_id)] for structure_id in structure["structure_id_path"][1:-1].split("/")])

    # Load "layer" ontology (only available for the CCF atlas type)
    if atlas_type == HomeLogic.CCF_ATLAS:
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
    try:
      annotation = slicer.util.loadVolume(
        self.annotationFilePath(atlas_type=atlas_type),
        properties={
          "labelmap": "1",
          "colorNodeID": colorNodeID
        }
      )
    except RuntimeError:
      annotation = None
      logging.error("Annotation file [%s] does not exist" % self.annotationFilePath(atlas_type=atlas_type))

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
    for ele in range(3):
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

  @staticmethod
  def limsBaseURL():
    return slicer.app.commandOptions().limsBaseURL or 'http://localhost:5000/'

  def atlasType(self):
    return self._atlasType

  def setAtlasType(self, atlasType):
    self._atlasType = atlasType


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

