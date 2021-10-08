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

    def __repr__(self):
        return ("vid: " + str(self.vhelixId) + ", bid " + str(self.baseId) + ", type " + self.get_strand_type() + "\n\t prev: " +
         ("None" if self.prevPart is None else str(self.prevPart.globalId)) + 
         "\n\t next: " + ("None" if self.nextPart is None else str(self.nextPart.globalId)))

    def set_prev_next(self, prevPart, nextPart):
        self.prevPart = prevPart
        self.nextPart = nextPart
    
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
    def __init__(self, id, row, col, latticeType, firstActiveCell, lastActiveCell, lastCell):
        self.id = id
        self.row = row
        self.col = col
        self.latticeType = latticeType
        self.firstActiveCell = firstActiveCell
        self.lastActiveCell = lastActiveCell
        self.lastCell = lastCell
    
    def __repr__(self):
        return ("vhelix: " + str(self.id) + " [" + str(self.row) + "," + str(self.col) +
         "] fac " + str(self.firstActiveCell) + ", lac " + 
         str(self.lastActiveCell) + ", lc " + str(self.lastCell))

def create_strand_components(strandArray, checkCircularScaffold):
    components = []
    
    for strandPart in strandArray:
        prevPart = next((x for x in strandArray if x.vhelixId == strandPart.prevVid and x.baseId == strandPart.prevBid), None)
        nextPart = next((x for x in strandArray if x.vhelixId == strandPart.nextVid and x.baseId == strandPart.nextBid), None)
        strandPart.set_prev_next(prevPart, nextPart)
    
    circScaffComps = []

    for strandPart in strandArray:
        if strandPart.prevPart == None:
            newComponent = []
            currPart = strandPart
            newComponent.append(currPart)
            while currPart.nextPart != None:
                currPart = currPart.nextPart
                newComponent.append(currPart)
            components.append(newComponent)
        elif checkCircularScaffold:
            # Test for circular scaffold
            start = strandPart
            currPart = start
            isCirc = False
            while currPart.nextPart != None:
                currPart = currPart.nextPart
                if currPart == start:
                    isCirc = True
                    break
            if isCirc:
                isAlreadyFound = False
                newComponent = []
                currPart = start
                newComponent.append(currPart)
                while currPart.nextPart != start:
                    currPart = currPart.nextPart
                    newComponent.append(currPart)
                for circComp in circScaffComps:
                    if start in circComp:
                        isAlreadyFound = True
                        break
                if not isAlreadyFound:
                    circScaffComps.append(newComponent)
                    components.append(newComponent)

    for circComp in circScaffComps:
        # TODO Circular scaffolds are simply cut at some random location at the moment.
        #      This is primarily to not break all the tools relying on existence of 5'/3'
        #      detected by having no prev/next nucleotide. Is it an issue? 
        print("Note: circular scaffold strand was found and processed by breaking it")

        circComp[0].prevVid = -1
        circComp[0].prevBid = -1
        circComp[0].set_prev_next(None, circComp[0].nextPart)

        circComp[-1].nextVid = -1
        circComp[-1].nextBid = -1
        circComp[-1].set_prev_next(circComp[-1].prevPart, None)

    return components

def process_cadnano_file(file_path, lattice_type):
    print("Loading structure '" + file_path + "' with " + lattice_type + " lattice.")
    
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
        
        processedVhelices.append(Vhelix(vstr['num'], vstr['row'], vstr['col'], lattice_type, firstActiveCell, lastActiveCell, lastCell))

    individualScaffoldStrands = create_strand_components(allScaffoldRecords, True)
    individualStapleStrands = create_strand_components(allStapleRecords, False)

    for vhelix in processedVhelices:
        print("Virtual helix: ", str(vhelix))
    
    for strandComp in individualScaffoldStrands:
        print("Scaffold strand found, routed via", len(strandComp), "cells")

    for strandComp in individualStapleStrands:
        print("Staple strand found, routed via", len(strandComp), "cells")     
    
    file.close()

    return (processedVhelices, individualScaffoldStrands, individualStapleStrands)

def strands_to_unf_data(unfFileData, thisStructure, strandsList, allStrandParts, areScaffolds):
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
            # For deletion, "deletion" cell exists but it contains no nucleotides
            # and is thus ignored on the level of DNA data structure.
            # The resulting strand, therefore, simply "goes through that cell without stopping".
            
        strandObject = {}

        strandObject['id'] = globalIdGenerator
        globalIdGenerator += 1
        strandObject['name'] = "DNA_strand"
        strandObject['naType'] = "DNA"
        strandObject['chainName'] = "NULL"
        strandObject['color'] = "#0000FF" if areScaffolds else "#{:02x}{:02x}{:02x}".format(r(), r(), r())
        strandObject['isScaffold'] = areScaffolds
        strandObject['pdbFileId'] = -1
        strandObject['fivePrimeId'] = ntIds[0]
        strandObject['threePrimeId'] = ntIds[-1]

        nucleotides = []
        for i in range(len(ntIds)):
            newNucl = {}
            newNucl['id'] = ntIds[i]
            newNucl['nbAbbrev'] = "A" # TODO Sequence is hardcoded now
            newNucl['pair'] = ntPairs[i]
            newNucl['prev'] = ntIds[i - 1] if i > 0 else -1
            newNucl['next'] = ntIds[i + 1] if i < len(ntIds) - 1 else - 1
            newNucl['pdbId'] = -1
            newNucl['altPositions'] = []

            nucleotides.append(newNucl)

        strandObject['nucleotides'] = nucleotides
        resultingObjects.append(strandObject)
        print("Scaffold" if areScaffolds else "Staple", "strand object generated with", len(nucleotides), "nucleotides.")

    thisStructure['naStrands'] = thisStructure['naStrands'] + resultingObjects

def convert_data_to_unf_file(latticesData, latticesPositions):
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
        posId += 1
        outputLattice['orientation'] = [0, 0, 0]  
        outputLattice['virtualHelices'] = []

        for vhelix in vhelices:
            outputVhelix = {}
            outputVhelix['id'] = globalIdGenerator
            globalIdGenerator += 1
            outputVhelix['firstActiveCell'] = vhelix.firstActiveCell
            outputVhelix['lastActiveCell'] = vhelix.lastActiveCell
            outputVhelix['lastCell'] = vhelix.lastCell
            outputVhelix['latticePosition'] = [vhelix.row, vhelix.col]
            outputVhelix['initialAngle'] = 240 # TODO Should equal cadnano. Just a rough guess atm.
            outputVhelix['altPosition'] = []
            outputVhelix['altOrientation'] = []
        
            outputLattice['type'] = vhelix.latticeType

            cells = []
            for i in range(vhelix.lastActiveCell + 1):
                newCell = {}
                newCell['id'] = globalIdGenerator
                globalIdGenerator += 1
                newCell['number'] = i
                newCell['type'] = "n"
                newCell['left'] = []
                newCell['right'] = []

                # This is very computationally inoptimal.
                # In any case, the purpose of this code is to
                # find out the extent of a single strand in one given virtual helix
                # to detect the strand directionality in that virtual helix.
                for sp in allStrandParts:
                    for x in sp:
                        if x.vhelixId == vhelix.id and x.baseId == i:
                            currPart = x
                            cellType = currPart.get_unf_cell_type()
                            newCell['type'] = cellType        
                            
                            if cellType != "d":
                                strVhelixStartPart = currPart
                                strVhelixEndPart = currPart
                                
                                while currPart.prevPart != None and currPart.prevPart.vhelixId == vhelix.id:
                                    currPart = currPart.prevPart
                                    strVhelixStartPart = currPart
                            
                                while currPart.nextPart != None and currPart.nextPart.vhelixId == vhelix.id:
                                    currPart = currPart.nextPart
                                    strVhelixEndPart = currPart
                                
                                # We can afford "and" instead of "or" because the start/end parts are initialized
                                # with this strand part and the comparsion includes equality
                                if strVhelixStartPart.baseId <= x.baseId and strVhelixEndPart.baseId >= x.baseId:
                                    if len(newCell['left']) > 0:
                                        print("Error! Rewriting content of a valid cell with a new value.", vhelix.row,
                                         vhelix.col, i, newCell['left'], x.globalId)
                                    newCell['left'] = [x.globalId] + x.insertedNuclIds
                                elif strVhelixStartPart.baseId >= x.baseId and strVhelixEndPart.baseId <= x.baseId:
                                    if len(newCell['right']) > 0:
                                        print("Error! Rewriting content of a valid cell with a new value.", vhelix.row, 
                                        vhelix.col, i, newCell['right'], x.globalId)
                                    newCell['right'] = [x.globalId] + x.insertedNuclIds
              
                cells.append(newCell)

            outputVhelix['cells'] = cells
            outputLattice['virtualHelices'].append(outputVhelix)

        unfFileData['lattices'].append(outputLattice)

        newStructure = {}
        newStructure['id'] = globalIdGenerator
        globalIdGenerator += 1
        newStructure['name'] = "Lattice-based structure"
        newStructure['naStrands'] = []
        newStructure['aaChains'] = []
        strands_to_unf_data(unfFileData, newStructure, scaffoldStrands, allStrandParts, True)
        strands_to_unf_data(unfFileData, newStructure, stapleStrands, allStrandParts, False)
        unfFileData['structures'].append(newStructure)
    
    unfFileData['idCounter'] = globalIdGenerator

    with open(OUTPUT_FILE_NAME, 'w') as outfile:
        json.dump(unfFileData, outfile)

def getInputFilesToProcess(argv):
    resPaths = []
    resTypes = []
    resPositions = []

    for i in range(1, len(argv)):
        thisArg = argv[i]
        splitArr = thisArg.split(':')
        if len(splitArr) != 3:
            print("Invalid argument!", thisArg, splitArr)
            sys.exit(1)
        else:
            resPaths.append(splitArr[0]) # Path to file
            resTypes.append(splitArr[1]) # Its lattice type
            resPositions.append(splitArr[2]) # The lattice position
    
    return (resPaths, resTypes, resPositions)

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        print("usage: cadnano_to_unf.py <file_1_path>:<lattice_type>:<position> <file_2_path>:<lattice_type>:<position> (...) <file_n_path>:<lattice_type>:<position>")
        print("lattice_type = square|honeycomb")
        print("position = x,y,z (angstroms)")
        print("")
        print("At least one input file is mandatory.")
        sys.exit(1)
    
    filesToProcess = getInputFilesToProcess(sys.argv)
    processedFilesData = []
    
    for i in range(0, len(filesToProcess[0])):
        processedFilesData.append(process_cadnano_file(filesToProcess[0][i], filesToProcess[1][i]))

    convert_data_to_unf_file(processedFilesData, filesToProcess[2])

if __name__ == '__main__':
  main()