import model


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
            ann.representation_type = dann['representationType']
            ann.thickness = dann['thickness']

            ann.markup_type = dmark['type']
            ann.coordinate_system = dmark['coordinateSystem']
            if 'coordinateUnits' in dmark:
                ann.coordinate_units = dmark['coordinateUnits']

            for point in dmark['controlPoints']:
                ann.points.append(tuple(point['position']))

            doc.annotations.append(ann)

        return doc

    @classmethod
    def specialize(cls, doc: model.Document):
        data = dict()
        data['version'] = '0.1.0+2020.09.18'
        data['markups'] = [
            {
                'markup': {
                    'type': ann.markup_type,
                    'coordinateSystem': ann.coordinate_system,
                    'coordinateUnits': ann.coordinate_units,
                    'controlPoints': [
                        {
                            'id': str(i),
                            'position': pt,
                            'orientation': [-1.0, -0.0, -0.0,
                                            -0.0, -1.0, -0.0,
                                            +0.0, +0.0, +1.0]
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
