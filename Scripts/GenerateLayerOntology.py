"""Generate layer ontology.

Prerequisites: pip install allensdk

Initial version  written by David Feng <davidf@alleninstitute.org>
See https://gist.github.com/dyf/056095756b15a6b76dfb28558c4633da
"""

from allensdk.api.queries.rma_api import RmaApi
import allensdk.core.json_utilities as ju


all_structs = []

root = RmaApi().model_query("Structure", criteria="[graph_id$eq1],[acronym$eqgrey]")[0]

all_structs.append(root)

layers = [ { 'id': 900000000, 'acronym': 'Isocortex1', 'name': 'Isocortex layer 1', 'color_hex_triplet': '7fc97f' },
           { 'id': 900000001, 'acronym': 'Isocortex2/3', 'name': 'Isocortex layer 2/3', 'color_hex_triplet': 'beaed4' },
           { 'id': 900000002, 'acronym': 'Isocortex4', 'name': 'Isocortex layer 4', 'color_hex_triplet': 'fdc086' },
           { 'id': 900000003, 'acronym': 'Isocortex5', 'name': 'Isocortex layer 5', 'color_hex_triplet': 'ffff99' },
           { 'id': 900000004, 'acronym': 'Isocortex6a', 'name': 'Isocortex layer 6a', 'color_hex_triplet': '386cb0' },
           { 'id': 900000005, 'acronym': 'Isocortex6b', 'name': 'Isocortex layer 6b', 'color_hex_triplet': 'f0027f' } ]

all_structs += layers

for layer in layers:
    layer['structure_id_path'] = '/%d/%d/' % (root['id'], layer['id'])
    layer['parent_structure_id'] = root['id']

    structs = RmaApi().model_query("Structure", criteria="structure_sets[name$eq'%s']"%layer['name'])

    for struct in structs:
        struct['structure_id_path'] = '/%d/%d/%d/' % (root['id'], layer['id'], struct['id'])
        struct['color_hex_triplet'] = layer['color_hex_triplet']
        struct['parent_structure_id'] = layer['id']

    all_structs += structs

ju.write("layer_structures.json", all_structs)


