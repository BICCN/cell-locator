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

        # expect these to be present, even though we don't actually need them.
        # conversion will still fail so that inference works correctly.
        _ = data["DefaultCameraPosition"]
        _ = data["DefaultCameraViewUp"]
        _ = data["DefaultOntology"]
        _ = data["DefaultReferenceView"]
        _ = data["DefaultRepresentationType"]
        _ = data["DefaultSplineOrientation"]
        _ = data["DefaultStepSize"]
        _ = data["DefaultThickness"]

        # set document-wide values based on the currently selected markup.
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

        # copy markup-specific values
        for i, dmark in enumerate(data['Markups']):
            ann = model.Annotation()
            ann.name = dmark['Label']
            ann.markup_type = 'ClosedCurve'

            ann.coordinate_system = 'LPS'
            ann.points = [
                model.Point((-p['x'], -p['y'], p['z']))  # RAS → LPS conversion
                for p in dmark['Points']
            ]

            ann.thickness = dmark['Thickness']
            ann.orientation = dmark['SplineOrientation']
            ann.representation_type = dmark['RepresentationType']

            doc.annotations.append(ann)

        return doc

    @classmethod
    @model.versioned
    def specialize(cls, doc: model.Document):
        data = dict()

        data["DefaultCameraPosition"] = doc.camera_position
        data["DefaultCameraViewUp"] = doc.camera_view_up
        data["DefaultOntology"] = doc.ontology
        data["DefaultReferenceView"] = doc.reference_view
        data["DefaultRepresentationType"] = "polyline"

        current_ann = doc.annotations[doc.current_id]
        data["DefaultSplineOrientation"] = current_ann.orientation
        data["DefaultStepSize"] = doc.stepSize
        data["DefaultThickness"] = current_ann.thickness
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

        data['Markups_Count'] = len(doc.annotations)
        data['TextList'] = [None]
        data['TextList_Count'] = 0

        return data
