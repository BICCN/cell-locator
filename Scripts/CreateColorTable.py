import argparse
import json
import sys

# Read and convert a json file to a slicer compatible color table.
# The json file is assumed to be obtained from:
# http://api.brain-map.org/api/v2/data/Structure/query.json?criteria=%5Bgraph_id$eq1%5D&num_rows=2000

# Optional, you can prettify the file doing:
#
# python -m json.tool query.json query-pretty.json

# Copied from: https://gist.github.com/matthewkremer/3295567
# Note - Assumes no transparency.
def hex_to_rgb(_hex):
  _hex = _hex.lstrip('#')
  hlen = len(_hex)
  return tuple(int(_hex[i:i+int(hlen/3)], 16) for i in range(0, hlen, int(hlen/3)))

def read_convert_write(_input, output, a2s_mapping):

  # Read json
  with open(_input) as input_file:
    json_data = json.load(input_file)

  if not json_data:
    print('Error while reading %s' % _input)
    return

  # Some sanity checking
  if not json_data['success']:
    print('Json is incorrect. Make sure the query used worked.')
    return

  num_rows = json_data['num_rows']
  if not num_rows == json_data['total_rows']:
    print('The number of queried rows (%s) is lower than the total number of rows (%s).' %(num_rows, json_data['total_rows']))
    return

  ctb_data = {}
  for i in range(num_rows):
    pixel_value = json_data['msg'][i]['id']

    # Slicer does no support null values and negative values
    if not pixel_value or pixel_value < 0:
      continue

    _hex = json_data['msg'][i]['color_hex_triplet']
    try:
      name = json_data['msg'][i]['safe_name']
    except KeyError:
      name = json_data['msg'][i]['name']
    # Slicer does not support spaces in names, replace them by underscores
    name = name.replace(" ", "_")

    rgb = hex_to_rgb(_hex)
    ctb_data[pixel_value] = [name, rgb]
    
    if not _hex or not pixel_value or not name:
      print("Error for %s - %s " %(i, ctb_data[i]))

  # Add missing entries
  missing = set(a2s_mapping.keys()) - set(ctb_data.keys())
  for pixel_value in missing:
    rgb = hex_to_rgb("000000")
    ctb_data[pixel_value] = ["unknown", rgb]

  pixel_values = sorted(ctb_data.keys())

  with open(output, 'w') as output_file:
    for pixel_value in pixel_values:
      if pixel_value not in a2s_mapping:
        continue
      output_file.write(
        '%i %s %i %i %i 255\n'
        %(a2s_mapping[pixel_value],
          ctb_data[pixel_value][0],
          ctb_data[pixel_value][1][0],
          ctb_data[pixel_value][1][1],
          ctb_data[pixel_value][1][2]
          )
        )


def load_mapping(file_path):
  with open(file_path) as content:
    mapping = json.load(content)
    return {int(key): int(value) for (key, value) in mapping.items()}


def main(argv):
  parser = argparse.ArgumentParser(
    description='Create a color table from the brain map json.'
    )
  parser.add_argument(
    '--input',
    metavar='/path/to/file.json',
    required=True,
    help='Path to the input json file'
    )
  parser.add_argument(
    '--allen2slicer',
    metavar='/path/to/file.json',
    required=True,
    help='Path to the allen2slicer mapping json file'
    )
  parser.add_argument(
    '--output',
    metavar='/path/to/file.ctbl',
    required=True,
    help='Path to the output color table file'
    )

  args = parser.parse_args(argv)

  read_convert_write(args.input, args.output, load_mapping(args.allen2slicer))

if __name__ == '__main__':
  main(sys.argv[1:])
