#!/usr/bin/env python
# Code is using Python 2

# TODO The converter currently ignores advanced functions like loops and skips

import sys
import json
import datetime
import random

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

class StrandPart:
    def __init__(self, globalId, vhelixId, baseId, prevVid, prevBid, nextVid, nextBid):
        self.globalId = globalId
        self.vhelixId = vhelixId
        self.baseId = baseId
        self.prevVid = prevVid
        self.prevBid = prevBid
        self.nextVid = nextVid
        self.nextBid = nextBid

    def __repr__(self):
        return ("vid: " + str(self.vhelixId) + ", bid " + str(self.baseId) + "\n\t prev: " +
         ("None" if self.prevPart is None else str(self.prevPart.globalId)) + 
         "\n\t next: " + ("None" if self.nextPart is None else str(self.nextPart.globalId)))

    def set_prev_next(self, prevPart, nextPart):
        self.prevPart = prevPart
        self.nextPart = nextPart

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
        print "Note: circular scaffold strand was found and processed by breaking it"

        circComp[0].prevVid = -1
        circComp[0].prevBid = -1
        circComp[0].set_prev_next(None, circComp[0].nextPart)

        circComp[-1].nextVid = -1
        circComp[-1].nextBid = -1
        circComp[-1].set_prev_next(circComp[-1].prevPart, None)

    return components

def process_cadnano_file(file_path, lattice_type):
    print "Loading structure '" + file_path + "' with " + lattice_type + " lattice."
    
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

        for idx, scaf in enumerate(vstr['scaf']):
            isValidRecord = scaf[CADNANO_PREV_VID] >= 0 or scaf[CADNANO_NEXT_VID] >= 0
            if isValidRecord:
                allScaffoldRecords.append(StrandPart(globalIdGenerator, vstr['num'], idx, scaf[CADNANO_PREV_VID], 
                scaf[CADNANO_PREV_BID], scaf[CADNANO_NEXT_VID], scaf[CADNANO_NEXT_BID]))
                globalIdGenerator += 1
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)

        for idx, stap in enumerate(vstr['stap']):
            isValidRecord = stap[CADNANO_PREV_VID] >= 0 or stap[CADNANO_NEXT_VID] >= 0
            if isValidRecord:
                allStapleRecords.append(StrandPart(globalIdGenerator, vstr['num'], idx, stap[CADNANO_PREV_VID], 
                stap[CADNANO_PREV_BID], stap[CADNANO_NEXT_VID], stap[CADNANO_NEXT_BID]))
                globalIdGenerator += 1
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)
        
        processedVhelices.append(Vhelix(vstr['num'], vstr['row'], vstr['col'], lattice_type, firstActiveCell, lastActiveCell, lastCell))

    individualScaffoldStrands = create_strand_components(allScaffoldRecords, True)
    individualStapleStrands = create_strand_components(allStapleRecords, False)

    for vhelix in processedVhelices:
        print "Virtual helix: ", str(vhelix)
    
    for strandComp in individualScaffoldStrands:
        print "Scaffold strand found of length: ", len(strandComp)

    for strandComp in individualStapleStrands:
        print "Staple strand found of length: ", len(strandComp)     
    
    file.close()

    return (processedVhelices, individualScaffoldStrands, individualStapleStrands)

def initialize_unf_file_data_object():
    unfFileData = {}

    unfFileData['format'] = "unf"
    unfFileData['version'] = 0.6
    unfFileData['lengthUnits'] = "A"
    unfFileData['angularUnits'] = "deg"
    unfFileData['name'] = "cadnano_converted_structure" # TODO add real structure name
    unfFileData['author'] = "Cadnano to UNF Python Converter Script"
    unfFileData['creationDate'] = datetime.datetime.now().replace(microsecond=0).isoformat()
    unfFileData['doi'] = "NULL"
    unfFileData['externalFiles'] = []
    unfFileData['lattices'] = []
    unfFileData['naStrands'] = []
    unfFileData['groups'] = []
    unfFileData['proteins'] = []
    unfFileData['connections'] = []
    unfFileData['modifications'] = []
    unfFileData['misc'] = {}
    unfFileData['molecules'] = {}
    unfFileData['molecules']['ligands'] = []
    unfFileData['molecules']['nanostructures'] = []
    unfFileData['molecules']['others'] = []

    return unfFileData

def strands_to_unf_data(unfFileData, strandsList, allStrandParts, areScaffolds):
    resultingObjects = []
    r = lambda: random.randint(0, 230)
    global globalIdGenerator

    for strand in strandsList:
        strandObject = {}

        strandObject['id'] = globalIdGenerator
        globalIdGenerator += 1
        strandObject['name'] = "DNA_strand"
        strandObject['naType'] = "DNA"
        strandObject['chainName'] = "NULL"
        strandObject['color'] = "#0000FF" if areScaffolds else "#{:02x}{:02x}{:02x}".format(r(), r(), r())
        strandObject['isScaffold'] = areScaffolds
        strandObject['pdbFileId'] = -1
        strandObject['fivePrimeId'] = strand[0].globalId
        strandObject['threePrimeId'] = strand[-1].globalId
        strandObject['confFilesIds'] = []

        nucleotides = []
        for strandPart in strand:
            newNucl = {}
            newNucl['id'] = strandPart.globalId
            newNucl['nbAbbrev'] = "A" # TODO Sequence is hardcoded now
            newNucl['pair'] = next((x.globalId for y in allStrandParts for x in y if x.vhelixId == strandPart.vhelixId and
                 x.baseId == strandPart.baseId and x.globalId != strandPart.globalId), -1)
            newNucl['prev'] = strandPart.prevPart.globalId if strandPart.prevPart is not None else -1
            newNucl['next'] = strandPart.nextPart.globalId if strandPart.nextPart is not None else -1
            newNucl['oxdnaConfRow'] = -1
            newNucl['pdbId'] = -1
            newNucl['altPositions'] = []

            nucleotides.append(newNucl)

        strandObject['nucleotides'] = nucleotides
        resultingObjects.append(strandObject)

    unfFileData['naStrands'] += resultingObjects

def convert_data_to_unf_file(latticesData):
    unfFileData = initialize_unf_file_data_object()
    global globalIdGenerator
    
    for lattData in latticesData:
        vhelices = lattData[0]
        scaffoldStrands = lattData[1]
        stapleStrands = lattData[2]

        allStrandParts = scaffoldStrands + stapleStrands

        outputLattice = {}
        outputLattice['id'] = globalIdGenerator
        globalIdGenerator += 1
        outputLattice['name'] = 'lattice_from_cadnano'
        outputLattice['position'] = [0, 0, 0]
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
                newCell['left'] = -1
                newCell['right'] = -1

                # This is very computationally inoptimal.
                # In any case, the purpose of this code is to
                # find out the extent of a single strand in one given virtual helix
                # to detect the strand directionality in that virtual helix.
                for sp in allStrandParts:
                    for x in sp:
                        if x.vhelixId == vhelix.id and x.baseId == i:
                            currPart = x
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
                                if newCell['left'] >= 0:
                                    print "Error! Rewriting content of a valid cell with a new value.", newCell['left'], x.globalId
                                newCell['left'] = x.globalId
                            elif strVhelixStartPart.baseId >= x.baseId and strVhelixEndPart.baseId <= x.baseId:
                                if newCell['right'] >= 0:
                                    print "Error! Rewriting content of a valid cell with a new value.", newCell['right'], x.globalId
                                newCell['right'] = x.globalId

                cells.append(newCell)

            outputVhelix['cells'] = cells
            outputLattice['virtualHelices'].append(outputVhelix)

        unfFileData['lattices'].append(outputLattice)
        strands_to_unf_data(unfFileData, scaffoldStrands, allStrandParts, True)
        strands_to_unf_data(unfFileData, stapleStrands, allStrandParts, False)
    
    unfFileData['idCounter'] = globalIdGenerator

    with open(OUTPUT_FILE_NAME, 'w') as outfile:
        json.dump(unfFileData, outfile)

def getInputFilesToProcess(argv):
    resPaths = []
    resTypes = []

    for i in range(1, len(argv)):
        thisArg = argv[i]
        splitArr = thisArg.rsplit(':', 1)
        resPaths.append(splitArr[0]) # Path to file
        resTypes.append(splitArr[1]) # Its lattice type
    
    return (resPaths, resTypes)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        print "usage: cadnano_to_unf.py <file_1_path>:<lattice_type> <file_2_path>:<lattice_type> (...) <file_n_path>:<lattice_type>"
        print "lattice_type = square|honeycomb"
        print ""
        print "At least one input file is mandatory."
        sys.exit(1)
    
    filesToProcess = getInputFilesToProcess(sys.argv)
    processedFilesData = []
    
    for i in range(0, len(filesToProcess[0])):
        processedFilesData.append(process_cadnano_file(filesToProcess[0][i], filesToProcess[1][i]))

    convert_data_to_unf_file(processedFilesData)

if __name__ == '__main__':
  main()