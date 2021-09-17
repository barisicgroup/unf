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
        return "vid: " + str(self.vhelixId) + ", bid " + str(self.baseId) + "\n\t prev: " + ("None" if self.prevPart is None else str(self.prevPart.globalId)) + "\n\t next: " + ("None" if self.nextPart is None else str(self.nextPart.globalId))

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

def create_strand_components(strandArray, checkCircularScaffold):
    components = []
    
    for strand in strandArray:
        prevPart = next((x for x in strandArray if x.vhelixId == strand.prevVid and x.baseId == strand.prevBid), None)
        nextPart = next((x for x in strandArray if x.vhelixId == strand.nextVid and x.baseId == strand.nextBid), None)
        strand.set_prev_next(prevPart, nextPart)
    
    circScaffComps = []

    for strand in strandArray:
        if strand.prevPart == None:
            newComponent = []
            currPart = strand
            newComponent.append(currPart)
            while currPart.nextPart != None:
                currPart = currPart.nextPart
                newComponent.append(currPart)
            components.append(newComponent)
        elif checkCircularScaffold:
            # Test for circular scaffold
            start = strand
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
        circComp[0].set_prev_next(None, circComp[0].nextPart)
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
        firstActiveCell = len(vstr['scaf'])
        lastActiveCell = 0
        lastCell = 0

        for idx, scaf in enumerate(vstr['scaf']):
            isValidRecord = scaf[0] >= 0 or scaf[2] >= 0
            if isValidRecord:
                allScaffoldRecords.append(StrandPart(globalIdGenerator, vstr['num'], idx, scaf[0], scaf[1], scaf[2], scaf[3]))
                globalIdGenerator += 1
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
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
    global globalIdGenerator

    for strand in strandsList:
        strandObject = {}

        strandObject['id'] = globalIdGenerator
        globalIdGenerator += 1
        strandObject['name'] = "DNA_strand"
        strandObject['naType'] = "DNA"
        strandObject['chainName'] = "NULL"
        strandObject['color'] = "#0000FF" if areScaffolds else "#FF0000"
        strandObject['isScaffold'] = areScaffolds
        strandObject['pdbFileId'] = -1
        strandObject['fivePrimeId'] = strand[0].globalId
        strandObject['threePrimeId'] = strand[-1].globalId
        strandObject['confFilesIds'] = []

        nucleotides = []
        for strandPart in strand:
            newNucl = {}
            newNucl['id'] = strandPart.globalId
            newNucl['nbAbbrev'] = "A" # TODO Does cadnano contain nb type data?
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
            outputVhelix['initialAngle'] = 0 # TODO Should equal cadnano. Depends on lattice?
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
            outputLattice['virtualHelices'].append(outputVhelix)

        unfFileData['lattices'].append(outputLattice)
        strands_to_unf_data(unfFileData, scaffoldStrands, allStrandParts, True)
        strands_to_unf_data(unfFileData, stapleStrands, allStrandParts, False)
    
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