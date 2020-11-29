 #!/usr/bin/env python
# Code is using Python 2

import sys
import json

LATTICE_SQUARE = "square"
LATTICE_HONEYCOMB = "honeycomb"

def process_cadnano_file(file_path, lattice_type):
    print "Loading structure '" + file_path + "' with " + lattice_type + " lattice."
    
    file = open(file_path, "r")
    data = json.loads(file.read())

    for vstr in data['vstrands']:
        print vstr['stap_colors']

    file.close()


def main():
    if len(sys.argv) != 3 or sys.argv[1] == "-h" or (sys.argv[2] != LATTICE_SQUARE and sys.argv[2] != LATTICE_HONEYCOMB):
        print "usage: cadnano_unf.py <file_path> <lattice_type>"
        print "lattice_type = square|honeycomb"
        sys.exit(1)
    process_cadnano_file(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
  main()