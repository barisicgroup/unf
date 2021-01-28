 #!/usr/bin/env python
# Code is using Python 2

# TODO The converter currently ignores advanced functions like loops and skips

import sys
import json
import datetime

LATTICE_SQUARE = "square"
LATTICE_HONEYCOMB = "honeycomb"
OUTPUT_FILE_NAME = "output.unf"

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
        return "vid: " + str(self.vhelixId) + ", bid " + str(self.baseId) + "\n\t prev: " + str(self.prevPart) + "\n\t next: " + str(self.nextPart)

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
        return "vhelix: " + str(self.id) + " [" + str(self.row) + "," + str(self.col) + "] fac " + str(self.firstActiveCell) + ", lac " + str(self.lastActiveCell) + ", lc " + str(self.lastCell)

def create_strand_components(strandArray):
    components = []
    
    for strand in strandArray:
        prevPart = next((x for x in strandArray if x.vhelixId == strand.prevVid and x.baseId == strand.prevBid), None)
        nextPart = next((x for x in strandArray if x.vhelixId == strand.nextVid and x.baseId == strand.nextBid), None)
        strand.set_prev_next(prevPart, nextPart)
    
    for strand in strandArray:
        if strand.prevPart == None:
            newComponent = []
            currPart = strand
            newComponent.append(currPart)
            while currPart.nextPart != None:
                currPart = currPart.nextPart
                newComponent.append(currPart)
            components.append(newComponent)
    
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
        firstActiveCell = len(vstr['scaf'])
        lastActiveCell = 0
        lastCell = 0

        for idx, scaf in enumerate(vstr['scaf']):
            isValidRecord = scaf[0] >= 0 or scaf[2] >= 0
            if isValidRecord:
                allScaffoldRecords.append(StrandPart(globalIdGenerator, vstr['num'], idx, scaf[0], scaf[1], scaf[2], scaf[3]))
                globalIdGenerator += 1
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell) # TODO UNF expects these (first|last)ActiveCell values to be increasing for every vhelix ... thus right now, they are incorrect
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)

        for idx, stap in enumerate(vstr['stap']):
            isValidRecord = stap[0] >= 0 or stap[2] >= 0
            if isValidRecord:
                allStapleRecords.append(StrandPart(globalIdGenerator, vstr['num'], idx, stap[0], stap[1], stap[2], stap[3]))
                globalIdGenerator += 1
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)
        
        processedVhelices.append(Vhelix(vstr['num'], vstr['row'], vstr['col'], lattice_type, firstActiveCell, lastActiveCell, lastCell))

    individualScaffoldStrands = create_strand_components(allScaffoldRecords)
    individualStapleStrands = create_strand_components(allStapleRecords)

    for vhelix in processedVhelices:
        print str(vhelix)
    
    for strandComp in individualScaffoldStrands:
        print "Scaffold strand found of length: ", len(strandComp)

    for strandComp in individualStapleStrands:
        print "Staple strand found of length: ", len(strandComp)     
    
    file.close()

    return (processedVhelices, individualScaffoldStrands, individualStapleStrands)

def initialize_unf_file_data_object():
    unfFileData = {}

    unfFileData['version'] = 0.4
    unfFileData['name'] = "cadnano_converted_structure" # TODO add real structure name
    unfFileData['author'] = "cadnano_unf.py"
    unfFileData['creationDate'] = datetime.datetime.now().replace(microsecond=0).isoformat()
    unfFileData['doi'] = "NULL"
    unfFileData['externalFiles'] = []
    unfFileData['virtualHelices'] = []
    unfFileData['singleStrands'] = []
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
    global globalIdGenerator


    for strand in strandsList:
        strandObject = {}

        strandObject['id'] = globalIdGenerator
        globalIdGenerator += 1
        strandObject['chainName'] = "NULL"
        strandObject['color'] = "#0000FF" if areScaffolds else "#FF0000"
        strandObject['isScaffold'] = "true" if areScaffolds else "false"
        strandObject['pdbFileId'] = -1
        strandObject['fivePrimeId'] = strand[0].globalId
        strandObject['threePrimeId'] = strand[-1].globalId
        strandObject['confFilesIds'] = []

        nucleotides = []
        for strandPart in strand:
            newNucl = {}
            newNucl['id'] = strandPart.globalId
            newNucl['nbAbbrev'] = "A"
            newNucl['naType'] = "DNA"
            newNucl['pair'] = next((x.globalId for y in allStrandParts for x in y if x.vhelixId == strandPart.vhelixId and x.baseId == strandPart.baseId and x.globalId != strandPart.globalId), -1)
            newNucl['prev'] = strandPart.prevPart.globalId if strandPart.prevPart is not None else -1
            newNucl['next'] = strandPart.nextPart.globalId if strandPart.nextPart is not None else -1
            newNucl['oxdnaConfRow'] = -1
            newNucl['pdbId'] = -1
            newNucl['altPositions'] = [[]]
            newNucl['altOrientations'] = [[]]

            nucleotides.append(newNucl)

        strandObject['nucleotides'] = nucleotides
        resultingObjects.append(strandObject)

    unfFileData['singleStrands'] += resultingObjects

def convert_data_to_unf_file(vhelices, scaffoldStrands, stapleStrands):
    unfFileData = initialize_unf_file_data_object()
    global globalIdGenerator
    allStrandParts = scaffoldStrands + stapleStrands

    for vhelix in vhelices:
        outputVhelix = {}
        outputVhelix['id'] = globalIdGenerator
        globalIdGenerator += 1
        outputVhelix['firstActiveCell'] = vhelix.firstActiveCell
        outputVhelix['lastActiveCell'] = vhelix.lastActiveCell
        outputVhelix['lastCell'] = vhelix.lastCell
        outputVhelix['gridPosition'] = [vhelix.col, vhelix.row]
        outputVhelix['orientation'] = [0, 0, 0]
        outputVhelix['grid'] = vhelix.latticeType
        outputVhelix['altPosition'] = []
        outputVhelix['altOrientation'] = []
        
        cells = []
        for i in range(vhelix.lastActiveCell + 1):
            newCell = {}
            newCell['id'] = globalIdGenerator
            globalIdGenerator += 1
            newCell['number'] = i
            newCell['altPosition'] = []
            newCell['type'] = 0
            
            leftNucl =  next((x for y in allStrandParts for x in y if x.vhelixId == vhelix.id and x.baseId == i and (x.nextBid >= x.baseId or x.prevBid <= x.baseId)), None)
            if leftNucl is not None:
                newCell['left'] = leftNucl.globalId
            else:
                newCell['left'] = -1

            rightNucl =  next((x for y in allStrandParts for x in y if x.vhelixId == vhelix.id and x.baseId == i and (x.nextBid <= x.baseId or x.prevBid >= x.baseId)), None)
            if rightNucl is not None:
                newCell['right'] = rightNucl.globalId
            else:
                newCell['right'] = -1

            cells.append(newCell)


        outputVhelix['cells'] = cells
        unfFileData['virtualHelices'].append(outputVhelix)
    
    strands_to_unf_data(unfFileData, scaffoldStrands, allStrandParts, True)
    strands_to_unf_data(unfFileData, stapleStrands, allStrandParts, False)
    
    with open(OUTPUT_FILE_NAME, 'w') as outfile:
        json.dump(unfFileData, outfile)


def main():
    if len(sys.argv) != 3 or sys.argv[1] == "-h" or (sys.argv[2] != LATTICE_SQUARE and sys.argv[2] != LATTICE_HONEYCOMB):
        print "usage: cadnano_unf.py <file_path> <lattice_type>"
        print "lattice_type = square|honeycomb"
        sys.exit(1)
    convert_data_to_unf_file(*process_cadnano_file(sys.argv[1], sys.argv[2]))

if __name__ == '__main__':
  main()