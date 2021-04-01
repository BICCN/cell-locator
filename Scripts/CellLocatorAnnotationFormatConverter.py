import argparse
import json
import sys


def from_20190126_to_20200918(input_content):

    markups = []

    referenceView = input_content["DefaultReferenceView"]
    ontology = input_content["DefaultOntology"]
    stepSize = input_content["DefaultStepSize"]
    cameraPosition = input_content["DefaultCameraPosition"]
    cameraViewUp = input_content["DefaultCameraViewUp"]

    for idx_markup, input_markup in enumerate(input_content["Markups"], start=1):
        control_points = []

        referenceView = input_markup["ReferenceView"]
        ontology = input_markup["Ontology"]
        stepSize = input_markup["StepSize"]
        cameraPosition = input_markup["CameraPosition"]
        cameraViewUp = input_markup["CameraViewUp"]

        transform_point = {
            "x": -1,
            "y": -1,
            "z": 1,
        }

        transform_orientation = {
            "Axial": [1] * 4 * 4,
            "Sagittal": [1] * 4 * 4,
            "Coronal": [
                -1, 1, 1, 1,
                1, 1, -1, 1,
                1, 1, 1, 1,
                1, 1, 1, 1
            ],
        }

        splineOrientation = [a * b  for a, b in zip(input_markup["SplineOrientation"], transform_orientation[referenceView])]

        for idx_control_point, intput_control_point in enumerate(input_markup["Points"], start=1):
            control_points.append({
                "id": "%d" % idx_control_point,
                "position": [
                    intput_control_point["x"] * transform_point["x"],
                    intput_control_point["y"] * transform_point["y"],
                    intput_control_point["z"] * transform_point["z"],
                ],
                "orientation": [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]
            })

        markups.append({
            "markup": {
                "type": "ClosedCurve",
                "coordinateSystem": "LPS",
                "controlPoints": control_points
            },
            "name": "Annotation-%d" % idx_markup,
            "orientation": splineOrientation,
            "representationType": input_markup["RepresentationType"],
            "thickness": input_markup["Thickness"]
        })

    output_content = {
        "markups": markups,
        "currentId": 0,
        "referenceView": referenceView,
        "ontology": ontology,
        "stepSize": stepSize,
        "cameraPosition": cameraPosition,
        "cameraViewUp": cameraViewUp
    }
    return output_content


RULES = {
    '20190126-20200918': from_20190126_to_20200918
}


def convert(input_format, input_path, output_format, output_path):

    rule_id = "%s-%s" % (input_format, output_format)
    if rule_id not in RULES:
        raise RuntimeError("No rule to convert from %s to %s" % (input_format, output_format))

    with open(input_path) as input_text:
        input_content = json.load(input_text)

    output_content = RULES[rule_id](input_content)

    with open(output_path, "w") as fp:
        json.dump(output_content, fp, indent=2)


def main(argv):
    parser = argparse.ArgumentParser(
      description='Convert between Cell Locator Annotation format.'
    )
    parser.add_argument(
        '--from',
        dest='input_format',
        metavar='YYYYMMDD',
        required=True,
        help='input format specified as YYYYMMDD'
    )
    parser.add_argument(
        '--to',
        dest='output_format',
        metavar='YYYYMMDD',
        default='20200918',
        help='output format specified as YYYYMMDD'
    )
    parser.add_argument(
        '--input',
        dest='input_path',
        metavar='/path/to/file.json',
        required=True,
        help='Path to the input json file'
    )
    parser.add_argument(
        '--output',
        dest='output_path',
        metavar='/path/to/file.json',
        required=True,
        help='Path to the output json file'
    )
    args = parser.parse_args(argv)
    convert(args.input_format, args.input_path, args.output_format, args.output_path)


if __name__ == "__main__":
    main(sys.argv[1:])