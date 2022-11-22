import argparse
import json
import numpy as np
import os
import subprocess
import sys

from CreateColorTable import main as create_color_table


def generate_contiguous_annotation(
        annotation_input_filepath, ontology_input_filepath,
        annotation_output_filepath, colortable_output_filepath,
        annotation_color_a2s_mapping_output_filepath, annotation_color_s2a_mapping_output_filepath):
  """Pre-process structure ontology and annotation volume.

  This function takes care of the following steps:

    1. Load annotation_input_filepath as a volume

    2. Update values to be contiguous

    3. Save `annotation_output_filepath`

    4. Generate `<data_dir>/annotation_color_table.txt`

    5. Attempt to load generated color table
  """

  data_dir = os.path.dirname(annotation_output_filepath)
  print("data_dir: %s" % data_dir)

  node = slicer.util.loadLabelVolume(annotation_input_filepath, returnNode=True)[1]

  data = slicer.util.arrayFromVolume(node)
  df = data.flatten()
  labels = np.unique(df)

  a2s_mapping = {str(value): str(idx) for idx, value in enumerate(labels)}
  with open(annotation_color_a2s_mapping_output_filepath, 'w') as fileContents:
    fileContents.write(json.dumps(a2s_mapping, sort_keys=True, indent=4))

  s2a_mapping = {str(idx): str(value) for idx, value in enumerate(labels)}
  with open(annotation_color_s2a_mapping_output_filepath, 'w') as fileContents:
    fileContents.write(json.dumps(s2a_mapping, sort_keys=True, indent=4))

  # Update annotation data
  for idx, value in enumerate(labels):
    if value == idx:
      continue
    #print(idx, value)
    data[data == value] = idx

  # Save updated images
  slicer.util.saveNode(node, annotation_output_filepath, {})

  #python /path/to/CreateColorTable.py --input $data_dir/query-pretty.json --output $data_dir/annotation_color_table.txt --allen2slicer $data_dir/annotation_color_allen2slicer_mapping.json

  # Generate color table
  create_color_table([
    "--input", ontology_input_filepath,
    "--allen2slicer", annotation_color_a2s_mapping_output_filepath,
    "--output", colortable_output_filepath,
  ])

  # Attempt to load generated color table
  cl = slicer.modules.colors.logic()
  colornode = cl.LoadColorFile(colortable_output_filepath, "allen")
  assert colornode is not None


def main(argv):
  parser = argparse.ArgumentParser(
    description='Create contiguous annotation label map, color table and color mapping files'
                'from the original annotation label map and brain map json ontology.'
    )
  parser.add_argument(
    '--annotation-input',
    metavar='/path/to/annotation.nrrd',
    required=True,
    help='Path to the input annotation nrrd volume'
    )
  parser.add_argument(
    '--ontology-input',
    metavar='/path/to/ontology.json',
    required=True,
    help='Path to the input ontology json file'
    )
  parser.add_argument(
    '--annotation-output',
    metavar='/path/to/annotation-contiguous.nrrd',
    required=True,
    help='Path to the output annotation nrrd volume'
    )
  parser.add_argument(
    '--colortable-output',
    metavar='/path/to/color_table.txt',
    required=True,
    help='Path to the output Slicer color table file'
    )
  parser.add_argument(
    '--annotation-color-allen2slicer-mapping-output',
    metavar='/path/to/annotation_color_allen2slicer_mapping.json',
    required=True,
    help='Path to the output Allen to Slicer annotation color file'
  )
  parser.add_argument(
    '--annotation-color-slicer2allen-mapping-output',
    metavar='/path/to/annotation_color_slicer2allen_mapping.json',
    required=True,
    help='Path to the output Slicer to Allen annotation color file'
  )

  args = parser.parse_args(argv)

  def _path(path):
    return os.path.abspath(os.path.expanduser(path))

  generate_contiguous_annotation(
    _path(args.annotation_input),
    _path(args.ontology_input),
    _path(args.annotation_output),
    _path(args.colortable_output),
    _path(args.annotation_color_allen2slicer_mapping_output),
    _path(args.annotation_color_slicer2allen_mapping_output)
    )


if __name__ == '__main__':
  main(sys.argv[1:])
