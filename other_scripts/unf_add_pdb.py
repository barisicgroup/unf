#!/usr/bin/env python
# Code is using Python 3

import sys
import json
import re
import hashlib

OUTPUT_FILE_NAME = "output.unf"

def parse_args(argv):
    unfFile = argv[1]
    pdbFile = argv[2]
    molName = argv[3]
    molPos = argv[4].split(",")
    molRot = argv[5].split(",")

    return (unfFile, pdbFile, molName, molPos, molRot)

def modify_unf(unfFile, pdbFile, molName, molPos, molRot):
    file = open(unfFile, "r")
    parsedData = json.loads(file.read())

    idCounter = parsedData["idCounter"]
    
    newExternalFile = {}
    newExternalFile["id"] = idCounter
    idCounter += 1
    newExternalFile["path"] = pdbFile
    newExternalFile["isIncluded"] = True

    with open(pdbFile, "r") as file:
        pdbFullContent = file.read()
        pdbContent = re.sub("\r\n|\n|\r", "", pdbFullContent)

    newExternalFile["hash"] = hashlib.md5(pdbContent).hexdigest()
    parsedData["externalFiles"].append(newExternalFile)

    newMolecule = {}
    newMolecule["id"] = idCounter
    idCounter += 1
    newMolecule["name"] = molName
    newMolecule["type"] = "NULL"
    newMolecule["externalFileId"] = idCounter - 2
    newMolecule["positions"] = [[int(mp) for mp in molPos]]
    newMolecule["orientations"] = [[int(mr) for mr in molRot]]

    parsedData["molecules"]["others"].append(newMolecule)
    parsedData["idCounter"] = idCounter

    with open(OUTPUT_FILE_NAME, "w") as outfile:
        json.dump(parsedData, outfile)

    # After the JSON-based operations are finished, let's
    # append the PDB content to the end of the UNF file
    with open(OUTPUT_FILE_NAME, "a") as outfile:
        outfile.write("\n#INCLUDED_FILE ")
        outfile.write(pdbFile + "\n")
        outfile.write(pdbFullContent)

def main():
    if len(sys.argv) != 6 or sys.argv[1] == "-h":
        print("usage unf_add_pdb.py <unf_path> <pdb_path> <molecule_name> <x_pos,y_pos,z_pos> <x_rot,y_rot,z_rot>")
        sys.exit(1)

    modify_unf(*parse_args(sys.argv))    

if __name__ == '__main__':
  main()