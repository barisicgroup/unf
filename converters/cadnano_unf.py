 #!/usr/bin/env python
# Code is using Python 2

import sys
import json

LATTICE_SQUARE = "square"
LATTICE_HONEYCOMB = "honeycomb"
OUTPUT_FILE_NAME = "output.json"

class StrandPart:
    def __init__(self, vhelixId, baseId, prevVid, prevBid, nextVid, nextBid):
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
    def __init__(self, id, row, col, firstActiveCell, lastActiveCell, lastCell):
        self.id = id
        self.row = row
        self.col = col
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

    for vstr in parsedData['vstrands']: 
        firstActiveCell = len(vstr['scaf'])
        lastActiveCell = 0
        lastCell = 0

        for idx, scaf in enumerate(vstr['scaf']):
            isValidRecord = scaf[0] >= 0 or scaf[2] >= 0
            if isValidRecord:
                allScaffoldRecords.append(StrandPart(vstr['num'], idx, scaf[0], scaf[1], scaf[2], scaf[3]))
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)

        for idx, stap in enumerate(vstr['stap']):
            isValidRecord = stap[0] >= 0 or stap[2] >= 0
            if isValidRecord:
                allStapleRecords.append(StrandPart(vstr['num'], idx, stap[0], stap[1], stap[2], stap[3]))
            lastCell = max(lastCell, idx)
            firstActiveCell = min(firstActiveCell, idx if isValidRecord else firstActiveCell)
            lastActiveCell = max(lastActiveCell, idx if isValidRecord else lastActiveCell)
        
        processedVhelices.append(Vhelix(vstr['num'], vstr['row'], vstr['col'], firstActiveCell, lastActiveCell, lastCell))

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

def convert_data_to_unf_file((vhelices, scaffoldStrands, stapleStrands)):
    print len(vhelices)

def main():
    if len(sys.argv) != 3 or sys.argv[1] == "-h" or (sys.argv[2] != LATTICE_SQUARE and sys.argv[2] != LATTICE_HONEYCOMB):
        print "usage: cadnano_unf.py <file_path> <lattice_type>"
        print "lattice_type = square|honeycomb"
        sys.exit(1)
    convert_data_to_unf_file(process_cadnano_file(sys.argv[1], sys.argv[2]))

if __name__ == '__main__':
  main()