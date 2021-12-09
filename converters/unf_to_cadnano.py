#!/usr/bin/env python
# Code is using Python 3

import sys
import json
import modules.unf_utils as unfutils

OUTPUT_FILE_NAME_BASICS = "output"
OUTPUT_FILE_NAME_EXTENSION = ".json"

def process_unf_file(unf_path):
    file = open(unf_path, "r")
    fileContent = file.read()
    jsonPartEndIdx = fileContent.find("#INCLUDED_FILE ")
    if jsonPartEndIdx > -1:
        jsonPart = fileContent[0:jsonPartEndIdx]
    else:
        jsonPart = fileContent
    parsedData = json.loads(jsonPart)

    id_to_str_nucl_tuple = get_nucl_id_dict(parsedData["structures"])

    counter = 1
    for lattice in parsedData["lattices"]:
        convert_unf_lattice_to_cadnano(lattice, counter, id_to_str_nucl_tuple)
        counter += 1

def convert_unf_lattice_to_cadnano(lattice, counter, id_to_str_nucl_tuple):
    outputFileName = OUTPUT_FILE_NAME_BASICS + str(counter) + OUTPUT_FILE_NAME_EXTENSION 
    outputFileData = init_cadnano_file_structure(outputFileName)

    nucl_id_to_cell_data = {}
    
    # vstrands where the scaffold is in the 5'3' direction carry even "num" value 
    #          in the cadnano files          
    evenNum = 0
    oddNum = 1
    
    for vhelix in lattice["virtualHelices"]:
        stapColors = []
        
        # Check for current num
        isScafFiveToThree = False
        for cell in vhelix["cells"]:
            for ftt in cell["fiveToThreeNts"]:
                strand = id_to_str_nucl_tuple[ftt][0]
                if strand["isScaffold"]:
                    isScafFiveToThree = True
                elif strand["fivePrimeId"] == ftt:
                    stapColors.append([cell["number"], unfutils.hex_color_to_dec(strand["color"])])
            for ttf in cell["threeToFiveNts"]:
                strand = id_to_str_nucl_tuple[ttf][0]
                if strand["isScaffold"]:
                    isScafFiveToThree = False
                elif strand["fivePrimeId"] == ttf:
                    stapColors.append([cell["number"], unfutils.hex_color_to_dec(strand["color"])])

        num = 0
        if isScafFiveToThree:
            num = evenNum
            evenNum += 2
        else:
            num = oddNum
            oddNum += 2

        vstrData = init_vstrand(num, vhelix["latticePosition"][0], vhelix["latticePosition"][1], vhelix["lastCell"] + 1)
        vstrData["stap_colors"] = stapColors

        for cell in vhelix["cells"]:
            for ftt in cell["fiveToThreeNts"]:
                nucl_id_to_cell_data[ftt] = (num, cell)
            
            for ttf in cell["threeToFiveNts"]:
                nucl_id_to_cell_data[ttf] = (num, cell)

            if cell["type"] == "d":
                vstrData["skip"][cell["number"]] = -1
            elif cell["type"] == "i":
                vstrData["loop"][cell["number"]] = max(len(cell["fiveToThreeNts"]), len(cell["threeToFiveNts"])) - 1

        outputFileData["vstrands"].append(vstrData)

    for vhelix in lattice["virtualHelices"]:
        for cell in vhelix["cells"]:
            for ftt in cell["fiveToThreeNts"]:
                vc_tup = nucl_id_to_cell_data[ftt]
                sn_tup = id_to_str_nucl_tuple[ftt]
                isScaf = sn_tup[0]["isScaffold"]
                prevId = sn_tup[1]["prev"]
                nextId = sn_tup[1]["next"]

                cellNum = cell["number"]
                vstrand = next(x for x in outputFileData["vstrands"] if x["num"] == vc_tup[0])
                if prevId >= 0 and nucl_id_to_cell_data[prevId][1] != cell:
                    strArr = "stap"
                    if isScaf:
                        strArr = "scaf"
                    vstrand[strArr][cellNum][0] = nucl_id_to_cell_data[prevId][0]
                    vstrand[strArr][cellNum][1] = nucl_id_to_cell_data[prevId][1]["number"]

                if nextId >= 0 and nucl_id_to_cell_data[nextId][1] != cell:
                    strArr = "stap"
                    if isScaf:
                        strArr = "scaf"
                    vstrand[strArr][cellNum][2] = nucl_id_to_cell_data[nextId][0]
                    vstrand[strArr][cellNum][3] = nucl_id_to_cell_data[nextId][1]["number"]
            
            for ttf in cell["threeToFiveNts"]:
                vc_tup = nucl_id_to_cell_data[ttf]
                sn_tup = id_to_str_nucl_tuple[ttf]
                isScaf = sn_tup[0]["isScaffold"]
                prevId = sn_tup[1]["prev"]
                nextId = sn_tup[1]["next"]

                cellNum = cell["number"]
                vstrand = next(x for x in outputFileData["vstrands"] if x["num"] == vc_tup[0])
                if prevId >= 0 and nucl_id_to_cell_data[prevId][1] != cell:
                    strArr = "stap"
                    if isScaf:
                        strArr = "scaf"
                    vstrand[strArr][cellNum][0] = nucl_id_to_cell_data[prevId][0]
                    vstrand[strArr][cellNum][1] = nucl_id_to_cell_data[prevId][1]["number"]

                if nextId >= 0 and nucl_id_to_cell_data[nextId][1] != cell:
                    strArr = "stap"
                    if isScaf:
                        strArr = "scaf"
                    vstrand[strArr][cellNum][2] = nucl_id_to_cell_data[nextId][0]
                    vstrand[strArr][cellNum][3] = nucl_id_to_cell_data[nextId][1]["number"]

    with open(outputFileName, 'w') as outfile:
        print("Processed and outputed UNF lattice to a file: " + outputFileName)
        json.dump(outputFileData, outfile)


def init_cadnano_file_structure(name):
    fileData = {}
    fileData["name"] = name
    fileData["vstrands"] = []
    
    return fileData

def init_vstrand(num, row, col, length):
    strand = {}
    strand["num"] = num
    strand["row"] = row
    strand["col"] = col
    strand["stap_colors"] = []
    strand["scafLoop"] = []
    strand["stap"] = []
    strand["skip"] = []
    strand["scaf"] = []
    strand["stapLoop"] = []
    strand["loop"] = []

    for i in range(0, length):
        strand["stap"].append([-1, -1, -1, -1])
        strand["scaf"].append([-1, -1, -1, -1])
        strand["loop"].append(0)
        strand["skip"].append(0)
    
    return strand

def get_nucl_id_dict(structures):
    id_dict = {}
    for structure in structures:
        for naStrand in structure["naStrands"]:
            for nucleotide in naStrand["nucleotides"]:
                id_dict[nucleotide["id"]] = (naStrand, nucleotide)
    return id_dict

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        print("usage: unf_to_cadnano.py <unf_file_path>")
        sys.exit(1)

    unf_path = sys.argv[1]
    process_unf_file(unf_path)

if __name__ == '__main__':
  main()