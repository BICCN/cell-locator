import model

class Converter(model.Converter):
    @classmethod
    def normalize(cls, data: dict):
        doc = model.Document()

        # this format only supports one markup
        doc.current_id = 0
        for i, dmark in enumerate(data['Markups']):
            if dmark['Selected']:
                doc.current_id = i

                doc.reference_view = dmark['ReferenceView']
                doc.ontology = dmark['Ontology']
                doc.stepSize = dmark['StepSize']
                doc.camera_position = tuple(dmark['CameraPosition'])
                doc.camera_view_up = tuple(dmark['CameraViewUp'])

                break

        for i, dmark in enumerate(data['Markups']):
            ann = model.Annotation()
            ann.name = dmark['Label']
            ann.markup_type = 'ClosedCurve'

            ann.coordinate_system = 'LPS'
            ann.points = [
                (-p['x'], -p['y'], p['z'])  # RAS → LPS conversion
                for p in dmark['Points']
            ]

            ann.thickness = dmark['Thickness']
            ann.orientation = dmark['SplineOrientation']
            ann.representation_type = dmark['RepresentationType']

            doc.annotations.append(ann)

        return doc

    @classmethod
    def specialize(cls, doc: model.Document):
        data = dict()
        data['version'] = '0.0.0+2019.01.26'

        data["Locked"] = 0
        data["MarkupLabelFormat"] = "%N-%d"

        data['Markups'] = [
            {
                'AssociatedNodeID': f'vtkMRMLModelNode{i}',
                'CameraPosition': doc.camera_position,
                'CameraViewUp': doc.camera_view_up,
                'Closed': 1,
                'Description': '',
                'ID': f'vtkMRMLMarkupsSplinesNode_{i}',
                'Label': ann.name,
                'Locked': 1,
                'Ontology': doc.ontology,
                'OrientationWXYZ': [0.0, 0.0, 0.0, 1.0],
                'Points': [
                    {'x': -x, 'y': -y, 'z': z}
                    for x, y, z in ann.points
                ],
                'Points_Count': str(len(ann.points)),
                'ReferenceView': doc.reference_view,
                'RepresentationType': ann.representation_type,
                'Selected': 0,  # set later
                'SplineOrientation': ann.orientation,
                'StepSize': doc.stepSize,
                'Thickness': ann.thickness,
                'Visibility': 1
            }
            for i, ann in enumerate(doc.annotations)
        ]

        data['Markups'][doc.current_id]['Selected'] = 1
        data['Markups'][doc.current_id]['Locked'] = 0

        data['Markups_Count'] = len(doc.annotations)
        data['TextList'] = [None]
        data['TextList_Count'] = 0

        return data
