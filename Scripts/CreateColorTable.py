import argparse
import json
import sys

# Read and convert a json file to a slicer compatible color table.
# The json file is assumed to be obtained from:
# http://api.brain-map.org/api/v2/data/Structure/query.json?criteria=%5Bgraph_id$eq1%5D&num_rows=2000

# Copied from: https://gist.github.com/matthewkremer/3295567
# Note - Assumes no transparency.
def hex_to_rgb(hex):
  hex = hex.lstrip('#')
  hlen = len(hex)
  return tuple(int(hex[i:i+hlen/3], 16) for i in range(0, hlen, hlen/3))

def read_convert_write(input, output):

  # Read json
  with open(input) as input_file:
    json_data = json.load(input_file)

  if not json_data:
    print('Error while reading %s' %input)
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

    hex = json_data['msg'][i]['color_hex_triplet']
    name = json_data['msg'][i]['safe_name']
    # Slicer does not support spaces in names, replace them by underscores
    name = name.replace(" ", "_")

    rgb = hex_to_rgb(hex)
    ctb_data[pixel_value] = [name, rgb]
    
    if not hex or not pixel_value or not name:
      print("Error for %s - %s " %(i, ctb_data[i]))

  pixel_values = ctb_data.keys()
  pixel_values.sort()

  with open(output, 'w') as output_file:
    for pixel_value in pixel_values:
      output_file.write(
        '%i %s %i %i %i 255\n'
        %(pixel_value,
          ctb_data[pixel_value][0],
          ctb_data[pixel_value][1][0],
          ctb_data[pixel_value][1][1],
          ctb_data[pixel_value][1][2]
          )
        )

def main(argv):
  parser = argparse.ArgumentParser(
    description='Create a color table from the brain map json.'
    )
  parser.add_argument(
    '--input',
    metavar='/path/to/file.json',
    type=str,
    required=True,
    help='Path to the input json file'
    )
  parser.add_argument(
    '--output',
    metavar='/path/to/file.ctbl',
    type=str,
    required=True,
    help='Path to the output color table file file'
    )

  args = parser.parse_args(argv)

  read_convert_write(args.input, args.output)

if __name__ == '__main__':
  main(sys.argv[1:])
