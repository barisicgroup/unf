#!/usr/bin/env python
# Code is using Python 3

import sys
import json
import datetime
import random
import modules.unf_utils as unfutils

LATTICE_SQUARE = "square"
LATTICE_HONEYCOMB = "honeycomb"
OUTPUT_FILE_NAME = "output.unf"

LSQ_INIT_ANGLE = 15
LHC_INIT_ANGLE = 160

# Indices of the corresponding prev/next vstrand/base ids
# in the cadnano's json file fields
CADNANO_PREV_VID = 0
CADNANO_PREV_BID = 1
CADNANO_NEXT_VID = 2
CADNANO_NEXT_BID = 3

globalIdGenerator = 0

# Strand part corresponds to a number of nucleotides being located at a particular location in a strand
class StrandPart:
    def __init__(self, globalId, vhelixId, baseId, prevVid, prevBid, nextVid, nextBid, nuclToRepresent, insIds):
        self.globalId = globalId
        self.vhelixId = vhelixId
        self.baseId = baseId
        self.prevVid = prevVid
        self.prevBid = prevBid
        self.nextVid = nextVid
        self.nextBid = nextBid
        # Nucl to represent stores the number of nucleotides represented by this strand part
        # For deletion, it is < 0, for normal cell 0 or 1, for insertion > 1
        self.nuclToRepresent = nuclToRepresent
        self.insertedNuclIds = insIds
        self.set_prev_next(None, None)
        self.set_prev_next_arr_pos(None, None)
        self.set_arr_pos(None)

    def __repr__(self):
        return ("vid: " + str(self.vhelixId) + ", bid " + str(self.baseId) + ", type " + self.get_strand_type() + "\n\t prev: " +
         ("None" if self.prevPart is None else str(self.prevPart.globalId)) + 
         "\n\t next: " + ("None" if self.nextPart is None else str(self.nextPart.globalId)))

    def set_prev_next(self, prevPart, nextPart):
        self.prevPart = prevPart
        self.nextPart = nextPart
    
    def set_prev_next_arr_pos(self, prevPos, nextPos):
        self.prevPartPos = prevPos
        self.nextPartPos = nextPos
    
    def set_arr_pos(self, pos):
        self.arrPos = pos

    def get_strand_type(self):
        if self.nuclToRepresent < 0:
            return "deletion"
        elif self.nuclToRepresent > 1:
            return "insertion of size " + str(self.nuclToRepresent - 1)
        else:
            return "normal"
    
    def get_unf_cell_type(self):
        if self.nuclToRepresent < 0:
            return "d"
        elif self.nuclToRepresent > 1:
            return "i"
        else:
            return "n"

class Vhelix:
    def __init__(self, id, row, col, latticeType, firstActiveCell, lastActiveCell, lastCell, stapColors):
        self.id = id
        self.row = row
        self.col = col
        self.latticeType = latticeType
        self.firstActiveCell = firstActiveCell
        self.lastActiveCell = lastActiveCell
        self.lastCell = lastCell
        self.stapColors = stapColors
    
    def __repr__(self):
        return ("vhelix: " + str(self.id) + " [" + str(self.row) + "," + str(self.col) +
         "] fac " + str(self.firstActiveCell) + ", lac " + 
         str(self.lastActiveCell) + ", lc " + str(self.lastCell))

def generate_component(startPart, components, partsProcessed):
    partsProcessed[startPart.arrPos] = True
    newComponent = []
    currPart = startPart
    newComponent.append(currPart)
    while currPart.nextPart != None:
        currPart = currPart.nextPart
        partsProcessed[currPart.arrPos] = True
        newComponent.append(currPart)
    components.append(newComponent)

def create_strand_components(strandArray):
    # Connect the parts together
    i = 0
    for strandPart in strandArray:
        prevIdx = next((i for i, x in enumerate(strandArray) if x.vhelixId == strandPart.prevVid and x.baseId == strandPart.prevBid), None)
        nextIdx = next((i for i, x in enumerate(strandArray) if x.vhelixId == strandPart.nextVid and x.baseId == strandPart.nextBid), None)

        prevPart = strandArray[prevIdx] if prevIdx != None else None
        nextPart = strandArray[nextIdx] if nextIdx != None else None
        
        strandPart.set_prev_next_arr_pos(prevIdx, nextIdx)
        strandPart.set_prev_next(prevPart, nextPart)
        strandPart.set_arr_pos(i)
        i += 1
    
    i = 0
    circCount = 0
    components = []
    partsProcessed = [False] * len(strandArray)

    for strandPart in strandArray:
        if partsProcessed[strandPart.arrPos] == True:
            continue

        # If this part has no previous part, then it is 5' nucleotide
        # and we can generate the whole strand component starting from it
        if strandPart.prevPart == None:
            generate_component(strandPart, components, partsProcessed)
        # If this part has a previous part, we need to check for circularity
        else:
            start = strandPart
            currPart = start
            isCirc = False
            while currPart.prevPart != None:
                currPart = currPart.prevPart
                if currPart == start:
                    isCirc = True
                    break
                elif currPart.prevPart == None:
                    generate_component(currPart, components, partsProcessed)
            # If circularity was detected, we need to process this component separately
            if isCirc:
                newComponent = []
                currPart = start
                partsProcessed[currPart.arrPos] = True
                newComponent.append(currPart)
                while currPart.nextPart != start:
                    currPart = currPart.nextPart
                    partsProcessed[currPart.arrPos] = True
                    newComponent.append(currPart)
                components.append(newComponent)
                circCount += 1                
        i += 1

    return (components, circCount)

def process_cadnano_file(file_path, lattice_type):
    print("Loading structure '" + file_path + "' with " + lattice_type + " lattice.\n")
    
    file = open(file_path, "r")
    parsedData = json.loads(file.read())

    processedVhelices = []
    allScaffoldRecords = []
    allStapleRecords = []
    global globalIdGenerator

    for vstr in parsedData['vstrands']: 
        firstActiveCell = max(len(vstr['stap']), len(vstr['scaf']))
        lastActiveCell = 0
        lastCell = 0

        arrToProcess = [(vstr['scaf'], allScaffoldRecords, "scaffold"), (vstr['stap'], allStapleRecords, "staple")]

        for arrDestPair in arrToProcess:
            for idx, strRec in enumerate(arrDestPair[0]):
                isValidRecord = strRec[CADNANO_PREV_VID] >= 0 or strRec[CADNANO_NEXT_VID] >= 0
                nuclToRepr = vstr['skip'][idx] if vstr['skip'][idx] < 0 else ((vstr['loop'][idx] + 1) if vstr['loop'][idx] > 0 else 1)
                if isValidRecord:
                    thisId = globalIdGenerator
                    globalIdGenerator += 1
                    insIds = []
                    for lId in range(nuclToRepr - 1):
                        insIds.append(globalIdGenerator)
                        globalIdGenerator += 1
                    arrDestPair[1].append(StrandPart(thisId, vstr['num'], idx, strRec[CADNANO_PREV_VID], 
                    strRec[CADNANO_PREV_BID], strRec[CADNANO_NEXT_VID], strRec[CADNANO_NEXT_BID], nuclToRepr, insIds))
                lastCell = max(lastCell, idx)
                if nuclToRepr < 0 or nuclToRepr > 1:
                    print("Found", arrDestPair[2], arrDestPair[1][-1].get_strand_type())

                firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
                lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)
        
        processedVhelices.append(Vhelix(vstr['num'], vstr['row'], vstr['col'], lattice_type, firstActiveCell, lastActiveCell, lastCell, vstr['stap_colors']))

    individualScaffoldStrands = create_strand_components(allScaffoldRecords)
    individualStapleStrands = create_strand_components(allStapleRecords)

    print("Found:", len(processedVhelices), "virtual helices,", len(individualScaffoldStrands[0]),
    "scaffolds (", individualScaffoldStrands[1], " circular ),", len(individualStapleStrands[0]),
     "staples (", individualStapleStrands[1], " circular ).")

    for vhelix in processedVhelices:
        print(" Virtual helix: ", str(vhelix))
    
    for strandComp in individualScaffoldStrands[0]:
        print(" Scaffold strand routed via", len(strandComp), "cells")

    for strandComp in individualStapleStrands[0]:
        print(" Staple strand routed via", len(strandComp), "cells")     
    
    print()

    file.close()

    return (processedVhelices, individualScaffoldStrands[0], individualStapleStrands[0])

def strands_to_unf_data(unfFileData, thisStructure, strandsList, allStrandParts, areScaffolds, stapleStartToColor):
    resultingObjects = []
    r = lambda: random.randint(0, 230)
    global globalIdGenerator

    for strand in strandsList:
        # Each strand is an array of strand parts (StrandPart).
        # Since one strand part may represent different number of nucleotides
        # or possibly none at all, the parts will be preprocessed to work
        # with a consecutive sequence of nucleotides where deleted ones are omitted
        # and insertions are "expanded".
        
        # Index i refers to i-th nucleotide of a strand
        # Its next/prev nucleotides have neighboring IDs in the ntIds array
        ntIds = []
        ntPairs = []
        
        strandColor = ""

        for strandPart in strand:
            cellType = strandPart.get_unf_cell_type()
            if cellType == "n":
                ntIds.append(strandPart.globalId)
                ntPairs.append(next((x.globalId for y in allStrandParts for x in y if x.vhelixId == strandPart.vhelixId and
                 x.baseId == strandPart.baseId and x.globalId != strandPart.globalId), -1))
            elif cellType == "i":
                idsToAdd = [strandPart.globalId] + strandPart.insertedNuclIds
                pairPart = next((x for y in allStrandParts for x in y if x.vhelixId == strandPart.vhelixId and
                 x.baseId == strandPart.baseId and x.globalId != strandPart.globalId), None)

                pairsToAdd = []
                if pairPart != None:
                    pairsToAdd = pairPart.insertedNuclIds[::-1] + [pairPart.globalId]
                else:
                    pairsToAdd = [-1] * len(idsToAdd)
                
                ntIds += idsToAdd
                ntPairs += pairsToAdd
            
            # NOTE Cadnano does not seem to store color for circular staples
            #      Therefore, random color is generated for them
            if cellType != "d" and not areScaffolds and len(strandColor) == 0:
                vid = strandPart.vhelixId
                bid = strandPart.baseId
                colRec = stapleStartToColor[(vid, bid)] if (vid, bid) in stapleStartToColor else None
                if colRec != None:
                    strandColor = colRec
            # For deletion, "deletion" cell exists but it contains no nucleotides
            # and is thus ignored on the level of DNA data structure.
            # The resulting strand, therefore, simply "goes through that cell without stopping".

        if len(strandColor) == 0:
            strandColor = "#0000FF" if areScaffolds else "#{:02x}{:02x}{:02x}".format(r(), r(), r())

        strandObject = {}

        strandObject['id'] = globalIdGenerator
        globalIdGenerator += 1
        strandObject['name'] = "DNA_strand"
        strandObject['naType'] = "DNA"
        strandObject['chainName'] = "NULL"
        strandObject['color'] = strandColor
        strandObject['isScaffold'] = areScaffolds
        strandObject['pdbFileId'] = -1
        strandObject['fivePrimeId'] = ntIds[0]
        strandObject['threePrimeId'] = ntIds[-1]

        nucleotides = []
        for i in range(len(ntIds)):
            newNucl = {}
            newNucl['id'] = ntIds[i]
            newNucl['nbAbbrev'] = "N"
            newNucl['pair'] = ntPairs[i]
            newNucl['prev'] = ntIds[i - 1] if i > 0 else -1
            newNucl['next'] = ntIds[i + 1] if i < len(ntIds) - 1 else - 1
            newNucl['pdbId'] = -1
            newNucl['altPositions'] = []

            nucleotides.append(newNucl)

        # Maintain circularity
        circStr = "[acyclic]"
        if strand[-1].nextPart == strand[0]:
            nucleotides[0]['prev'] = ntIds[-1]
            nucleotides[-1]['next'] = ntIds[0]
            circStr = "[circular]"

        strandObject['nucleotides'] = nucleotides
        resultingObjects.append(strandObject)
        print(circStr, "Scaffold" if areScaffolds else "Staple", "strand object generated with", len(nucleotides), "nucleotides.")
        print(" Color:", strandColor)

    thisStructure['naStrands'] = thisStructure['naStrands'] + resultingObjects

def convert_data_to_unf_file(latticesData, latticesPositions, latticeOrientations):
    unfFileData = unfutils.initialize_unf_file_data_object("cadnano_converted_structure", "Cadnano to UNF Python Converter Script")
    global globalIdGenerator
    posId = 0

    for lattData in latticesData:
        vhelices = lattData[0]
        scaffoldStrands = lattData[1]
        stapleStrands = lattData[2]

        allStrandParts = scaffoldStrands + stapleStrands

        outputLattice = {}
        outputLattice['id'] = globalIdGenerator
        globalIdGenerator += 1
        outputLattice['name'] = 'lattice_from_cadnano'
        outputLattice['position'] = [int(pos) for pos in latticesPositions[posId].split(",")]
        outputLattice['orientation'] = [int(rot) for rot in latticeOrientations[posId].split(",")]
        posId += 1
        outputLattice['virtualHelices'] = []

        stapleStartToColor = {}

        for vhelix in vhelices:
            outputVhelix = {}
            outputVhelix['id'] = globalIdGenerator
            globalIdGenerator += 1
            outputVhelix['firstActiveCell'] = vhelix.firstActiveCell
            outputVhelix['lastActiveCell'] = vhelix.lastActiveCell
            outputVhelix['lastCell'] = vhelix.lastCell
            outputVhelix['latticePosition'] = [vhelix.row, vhelix.col]
            outputVhelix['initialAngle'] = LSQ_INIT_ANGLE if vhelix.latticeType == LATTICE_SQUARE else LHC_INIT_ANGLE 
        
            outputLattice['type'] = vhelix.latticeType

            for stapColPair in vhelix.stapColors:
                stapleStartToColor[(vhelix.id, stapColPair[0])] = unfutils.dec_color_to_hex(stapColPair[1])

            cells = []
            for i in range(vhelix.lastActiveCell + 1):
                newCell = {}
                newCell['id'] = globalIdGenerator
                globalIdGenerator += 1
                newCell['number'] = i
                newCell['type'] = "n"
                newCell['fiveToThreeNts'] = []
                newCell['threeToFiveNts'] = []

                # The purpose of this (computationally not ideal) code is to
                # find out the directionality of this strand in this virtual helix.
                for sp in allStrandParts:
                    for x in sp:
                        if x.vhelixId == vhelix.id and x.baseId == i:
                            currPart = x
                            cellType = currPart.get_unf_cell_type()
                            newCell['type'] = cellType        
                            
                            if cellType != "d":
                                strVhelixStartPart = currPart.prevPart if currPart.prevPart != None and currPart.prevPart.vhelixId == vhelix.id else currPart
                                strVhelixEndPart = currPart.nextPart if currPart.nextPart != None and currPart.nextPart.vhelixId == vhelix.id else currPart
                                
                                # We can afford "and" instead of "or" because the start/end parts are initialized
                                # with this strand part and the comparsion includes equality
                                if strVhelixStartPart.baseId <= currPart.baseId and strVhelixEndPart.baseId >= currPart.baseId:
                                    if len(newCell['fiveToThreeNts']) > 0:
                                        print("Error! Rewriting content of a valid cell", vhelix.row,
                                         vhelix.col, i, "with a new 5'3' value.", newCell['fiveToThreeNts'], "->", currPart.globalId)
                                    newCell['fiveToThreeNts'] = [currPart.globalId] + currPart.insertedNuclIds
                                elif strVhelixStartPart.baseId >= currPart.baseId and strVhelixEndPart.baseId <= currPart.baseId:
                                    if len(newCell['threeToFiveNts']) > 0:
                                        print("Error! Rewriting content of a valid cell", vhelix.row, 
                                        vhelix.col, i, "with a new 3'5' value.", newCell['threeToFiveNts'], "->", currPart.globalId)
                                    newCell['threeToFiveNts'] = [currPart.globalId] + currPart.insertedNuclIds
                    if len(newCell['fiveToThreeNts']) > 0 and len(newCell['threeToFiveNts']) > 0:
                        break
              
                cells.append(newCell)

            outputVhelix['cells'] = cells
            outputLattice['virtualHelices'].append(outputVhelix)

        unfFileData['lattices'].append(outputLattice)

        newStructure = {}
        newStructure['id'] = globalIdGenerator
        globalIdGenerator += 1
        newStructure['name'] = "Multilayer structure"
        newStructure['naStrands'] = []
        newStructure['aaChains'] = []
        strands_to_unf_data(unfFileData, newStructure, scaffoldStrands, allStrandParts, True, stapleStartToColor)
        strands_to_unf_data(unfFileData, newStructure, stapleStrands, allStrandParts, False, stapleStartToColor)
        unfFileData['structures'].append(newStructure)
    
    unfFileData['idCounter'] = globalIdGenerator

    with open(OUTPUT_FILE_NAME, 'w') as outfile:
        json.dump(unfFileData, outfile)

def getInputFilesToProcess(argv):
    resPaths = []
    resTypes = []
    resPositions = []
    resOrientations = []

    for i in range(1, len(argv)):
        thisArg = argv[i]
        splitArr = thisArg.split(':')
        if len(splitArr) < 2:
            print("Invalid argument!", thisArg, splitArr)
            sys.exit(1)
        else:
            resPaths.append(splitArr[0]) # Path to file
            resTypes.append(splitArr[1]) # Its lattice type
            
            if len(splitArr) > 2:
                resPositions.append(splitArr[2]) # The lattice position
            else:
                resPositions.append("0,0,0")
            
            if len(splitArr) > 3:
                resOrientations.append(splitArr[3]) # The lattice orientation
            else:
                resOrientations.append("0,0,0")
    
    return (resPaths, resTypes, resPositions, resOrientations)

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        print("usage: cadnano_to_unf.py <file_1_path>:<lattice_type>:<position>:<orientation> <file_2_path>:<lattice_type>:<position>:<orientation> (...) <file_n_path>:<lattice_type>:<position>:<orientation>")
        print("lattice_type = square|honeycomb")
        print("position = x,y,z (angstroms) [default 0,0,0]")
        print("rotation = x,y,z (degrees) [default 0,0,0]")
        print("")
        print("At least one input file is mandatory.")
        sys.exit(1)
    
    filesToProcess = getInputFilesToProcess(sys.argv)
    processedFilesData = []
    
    for i in range(0, len(filesToProcess[0])):
        processedFilesData.append(process_cadnano_file(filesToProcess[0][i], filesToProcess[1][i]))

    convert_data_to_unf_file(processedFilesData, filesToProcess[2], filesToProcess[3])

if __name__ == '__main__':
  main()