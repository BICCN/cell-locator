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

        for dann in data['markups']:
            dmark = dann['markup']

            ann = model.Annotation()
            ann.name = dann['name']
            ann.orientation = dann['orientation']
            ann.markup_type = dmark['type']

            if ann.markup_type == 'ClosedCurve':
                ann.representation_type = dann['representationType']
                ann.thickness = dann['thickness']

            ann.coordinate_system = dmark['coordinateSystem']
            if 'coordinateUnits' in dmark:
                ann.coordinate_units = dmark['coordinateUnits']

            for point in dmark['controlPoints']:
                position = tuple(point['position'])
                structure = point.get('structure', None)
                if structure:
                    structure = model.Structure(
                        structure['id'],
                        structure['acronym'],
                    )

                ann.points.append(model.Point(position, structure))

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
                    'coordinateUnits': ann.coordinate_units,
                    'controlPoints': [
                        {
                            'id': str(i),
                            'position': pt.position,
                            'orientation': [-1.0, -0.0, -0.0,
                                            -0.0, -1.0, -0.0,
                                            +0.0, +0.0, +1.0],
                            'structure': {
                                'id': pt.structure.id,
                                'acronym': pt.structure.acronym
                            } if pt.structure else None
                        }
                        for i, pt in enumerate(ann.points, start=1)
                    ],
                },
                'name': ann.name,
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
