"""
Convert a single version of the file format to the normalized model, or vice versa.

For information on the file format update process, see:

https://cell-locator.readthedocs.io/en/latest/developer_guide/AnnotationFileFormat.html#versioning-guidelines
https://cell-locator.readthedocs.io/en/latest/developer_guide/Annotations.html#modifying-the-file-format
https://cell-locator.readthedocs.io/en/latest/developer_guide/AnnotationFileConverter.html#converter-api
"""

from cl_convert import model


class Converter(model.Converter):
    @classmethod
    def normalize(cls, data: dict):
        doc = model.Document()
        doc.current_id = data['currentId']
        doc.reference_view = data['referenceView']
        doc.ontology = data['ontology']
        doc.stepSize = data['stepSize']
        doc.camera_position = tuple(data['cameraPosition'])
        doc.camera_view_up = tuple(data['cameraViewUp'])

        for i, dann in enumerate(data['markups'], start=1):
            dmark = dann['markup']

            ann = model.Annotation()
            ann.name = f'Annotation {i}'
            ann.orientation = dann['orientation']
            ann.representation_type = dann['representationType']
            ann.thickness = dann['thickness']

            ann.markup_type = dmark['type']
            ann.coordinate_system = dmark['coordinateSystem']
            if 'coordinateUnits' in dmark:
                ann.coordinate_units = dmark['coordinateUnits']

            for point in dmark['controlPoints']:
                ann.points.append(model.Point(tuple(point['position'])))

            doc.annotations.append(ann)

        return doc

    @classmethod
    @model.versioned
    def specialize(cls, doc: model.Document):
        data = dict()
        data['markups'] = [
            {
                'markup': {
                    'type': ann.markup_type,
                    'coordinateSystem': ann.coordinate_system,
                    'locked': False,
                    'labelFormat': '%N-%d',
                    'controlPoints': [
                        {
                            'id': str(i),
                            'label': f'MarkupsClosedCurve-{i}',
                            'description': '',
                            'associatedNodeID': 'vtkMRMLScalarVolumeNode1',
                            'position': pt.position,
                            'orientation': [-1.0, -0.0, -0.0,
                                            -0.0, -1.0, -0.0,
                                            +0.0, +0.0, +1.0],
                            'selected': False,
                            'locked': False,
                            'visibility': True,
                            'positionStatus': 'defined',
                        }
                        for i, pt in enumerate(ann.points, start=1)
                    ],
                    'display': {
                        "visibility": True,
                        "opacity": 1.0,
                        "color": (0.4, 1.0, 1.0),
                        "selectedColor": (1.0, 0.5, 0.5),
                        "propertiesLabelVisibility": True,
                        "pointLabelsVisibility": False,
                        "textScale": 3.0,
                        "glyphType": "Sphere3D",
                        "glyphScale": 1.0,
                        "glyphSize": 5.0,
                        "useGlyphScale": True,
                        "sliceProjection": False,
                        "sliceProjectionUseFiducialColor": True,
                        "sliceProjectionOutlinedBehindSlicePlane": False,
                        "sliceProjectionColor": (1.0, 1.0, 1.0),
                        "sliceProjectionOpacity": 0.6,
                        "lineThickness": 0.2,
                        "lineColorFadingStart": 1.0,
                        "lineColorFadingEnd": 10.0,
                        "lineColorFadingSaturation": 1.0,
                        "lineColorFadingHueOffset": 0.0,
                        "handlesInteractive": False,
                        "snapMode": "toVisibleSurface"
                    }
                },
                'orientation': ann.orientation,
                'representationType': ann.representation_type,
                'thickness': ann.thickness
            }
            for ann in doc.annotations
        ]
        data['currentId'] = doc.current_id
        data['referenceView'] = doc.reference_view
        data['ontology'] = doc.ontology
        data['stepSize'] = doc.stepSize
        data['cameraPosition'] = doc.camera_position
        data['cameraViewUp'] = doc.camera_view_up

        return data
