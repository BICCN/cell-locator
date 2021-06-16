# Annotations

## Markups, Models, and Annotations

Each annotation in the scene has a markup associated with it, and also a translucent 3d
model to represent the thickness of that annotation. So for each element in the scene,
we need to manage a `vtkMRMLMarkupsNode` *and* a `vtkMRMLModelNode`. The
`Annotation` class in Python does this and handles serialization to JSON.

`Annotation` is an abstract class, currently with two concrete implementations:
`FiducialAnnotation` and `ClosedCurveAnnotation`.

`FiducialAnnotation` consists only of points with no thickness. Since this behavior is
provided by `vtkMRMLMarkupsFiducialNode`; so the annotation does not need to update a
model.

`ClosedCurveAnnotation` does have thickness. Its markup is a
`vtkMRMLMarkupsClosedCurveNode`, and a model is generated from this markup using
`vtkSlicerSplinesLogic::CreateModelFromContour` [(see here)][create-model-from-contour]

[create-model-from-contour]: https://github.com/BICCN/cell-locator/blob/master/Modules/Loadable/Splines/Logic/vtkSlicerSplinesLogic.cxx#L68-L142

## Creating Annotation Types

Below is a template for creating a new type of Annotation. Keep in mind that
`Annotation` does not create a model, so if you need one (or any other nodes) for the
new type, you must create those in `NewAnnotation.__init__`.

```python3
class NewAnnotation(Annotation):
    DisplayName = 'Sample'   # default name for this annotation type
    MarkupType = 'vtkMRMLMarkupsFiducialNode'  # markup type managed by this annotation type
    
    def __init__(self, markup=None):
        # set any type-specific attributes, models, etc
    
        super().__init__(markup=markup)
    
        # do any DisplayNode customizations
    
    def clear(self):
        # do any cleanup of type-specific attributes
    
    def update(self):
        # update any type-specific attributes; models, etc
    
    def metadata(self):
        # convert type-specific attributes to dict for serialization
    
    def setMetadata(self, data):
        # set any type-specific attributes from dict for deserialization
```

[(More info here)][pull169]

[pull169]: https://github.com/BICCN/cell-locator/pull/169

`Annotation.update` is invoked each time the markup changes, so we can implement it to
re-generate a model. Any other nodes or data that need to be synchronized with the
markup can be updated here.

### Serialization

Annotations are serialized to JSON using `Annotation.toDict`. The markup is converted
to JSON by Slicer [(see here)][slicer-markups]. Any annotation-specific metadata (thickness, etc) is
included using `Annotation.getMetdata`.

[slicer-markups]: https://slicer.readthedocs.io/en/latest/developer_guide/modules/markups.html

### Deserialization

Annotations are deserialized using `Annotation.fromDict`. The specific annotation
type is determined using the markup type, and the annotation type's `MarkupType`
class attribute.

```python3
class PlaneAnnotation(Annotation):
    MarkupType = 'vtkMRMLMarkupsPlaneNode'
```

For example, if the above class is defined and a `vtkMRMLMarkupsPlaneNode` is stored
in the JSON, then the resulting annotation will be an instance of `PlaneAnnotation`.

The JSON contents will then be sent to `PlaneAnnotation.setMetadata` so that any
attributes specific to `PlaneAnnotation` may be deserialized.

## File Format

The Cell Locator annotation format is non-standard and exists purely as an
implementation detail. While structural changes will be documented, the file
organization may change from version to version without notice.

We mean it.

```{toctree}
:maxdepth: 2
Converter Script <AnnotationFileConverter>
Version History <AnnotationFileFormat>
```
