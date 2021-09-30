#!/usr/bin/env python
# Code is using Python 3

# The converter now preserves the IDs (pdbId field) and chain names from the PDB file
# on the respective residues/chains but intentionally does not reference the source PDB itself
# to keep this file fully independent. 
# If this was added, it would be possible to easily trace back the atoms
# used for the generation of coarse-grained data for arbitrary residue.

import sys
import os
import json
import atomium # Using atomium library for PDB parsing; pip3 install atomium
import itertools
import numpy as np
from pprint import pprint
import modules.unf_utils as unfutils

OUTPUT_FILE_NAME = "output.unf"
globalIdGenerator = 0

class AminoAcidChain:
    def __init__(self, id, name, color, nTermAa, cTermAa):
        self.id = id
        self.name = name
        self.color = color
        self.nTermAa = nTermAa
        self.cTermAa = cTermAa

    def __repr__(self):
        return "chain " + self.name

class AminoAcid:
    def __init__(self, id, aaName, prevAa, nextAa, CApos, pdbId):
        self.id = id
        self.aaName = aaName
        self.prev = prevAa
        self.next = nextAa
        self.CApos = CApos
        self.pdbId = pdbId
    
    def set_prev_next(self, prevAa, nextAa):
        self.prev = prevAa
        self.next = nextAa

class NucleicAcidStrand:
    def __init__(self, id, name, naType, color, fivePrime, threePrime):
        self.id = id
        self.name = name
        self.naType = naType
        self.color = color
        self.fivePrime = fivePrime
        self.threePrime = threePrime
    
    def __repr__(self):
        return "strand " + self.name

class NucleotidePos:
    def __init__(self, nbCenter, bbCenter, baseNormal, hydrogenFaceDir):
        self.nbCenter = nbCenter
        self.bbCenter = bbCenter
        self.baseNormal = baseNormal
        self.hydrogenFaceDir = hydrogenFaceDir

class NucleicAcid:
    def __init__(self, id, nbName, prevNa, nextNa, pdbId, ntPos):
        self.id = id
        self.nbName = nbName
        self.prev = prevNa
        self.next = nextNa
        self.pdbId = pdbId
        self.ntPos = ntPos
    
    def set_prev_next(self, prevNa, nextNa):
        self.prev = prevNa
        self.next = nextNa

# a1 computed in accordance with tacoxDNA (PDB -> oxDNA Python converter)
def get_a1(residue, atNamesMap):
    res_vector = np.array([0.0, 0.0, 0.0])

    if "C" in residue.name or "T" in residue.name or "U" in residue.name:
        pairs = [ ["N3", "C6"], ["C2", "N1"], ["C4", "C5"] ]
    else:
        pairs = [ ["N1", "C4"], ["C2", "N3"], ["C6", "C5"] ]

    for pair in pairs:
        p = atNamesMap[pair[0]]
        q = atNamesMap[pair[1]]
        diff = np.subtract(np.asarray(p.location), np.asarray(q.location))
        res_vector = np.add(res_vector, diff)

    return unfutils.normalize(res_vector)

# a3 computed in accordance with tacoxDNA (PDB -> oxDNA Python converter)
def get_a3(residue, atNamesMap, nbCenter):
    parallel_to = np.subtract(np.asarray(atNamesMap["O4'"].location), nbCenter)
    a3 = np.array([0.0, 0.0, 0.0])

    for perm in itertools.permutations(unfutils.NUCLEOBASE_RING_COMMON_ATOMS, 3):
        p = atNamesMap[perm[0]]
        q = atNamesMap[perm[1]]
        r = atNamesMap[perm[2]]   
        
        v1 = unfutils.normalize(
            np.subtract(np.asarray(p.location), np.asarray(q.location)))
        v2 = unfutils.normalize(
            np.subtract(np.asarray(p.location), np.asarray(r.location)))

        if abs(np.dot(v1, v2)) > 0.01 or 1:
            curr_a3 = unfutils.normalize(np.cross(v1, v2))
            if np.dot(curr_a3, parallel_to) < 0.0:
                curr_a3 = -curr_a3
            a3 = np.add(a3, curr_a3)
        
        return unfutils.normalize(a3)

def get_nt_pos(residue):
    bbCenter = np.array([0.0, 0.0, 0.0])
    bbCount = 0
    
    nbCenter = np.array([0.0, 0.0, 0.0])
    nbCount = 0

    atNamesMap = {}

    for atom in residue.atoms():
        atLoc = np.asarray(atom.location)
        atNamesMap[atom.name] = atom
        if unfutils.is_drna_backbone(atom.name):
            bbCenter = np.add(bbCenter, atLoc)
            bbCount += 1
        else:
            nbCenter = np.add(nbCenter, atLoc)
            nbCount += 1
       
    bbCenter = np.true_divide(bbCenter, bbCount)
    nbCenter = np.true_divide(nbCenter, nbCount)

    a1 = get_a1(residue, atNamesMap)
    a3 = get_a3(residue, atNamesMap, nbCenter)

    return NucleotidePos(nbCenter, bbCenter, 
    a3, a1)
    
def process_na_strand(chainName, residues, naType):
    print("Processing", naType, "strand with", len(residues), "nucleotides.")
    global globalIdGenerator
    nucleotides = []

    for res in residues:
        newNtId = globalIdGenerator
        globalIdGenerator += 1
        nucleotides.append(NucleicAcid(newNtId, res.name, None, None, res.id, get_nt_pos(res)))
    
    for i in range(len(nucleotides)):
        nucleotides[i].set_prev_next(
            nucleotides[i - 1] if i > 0 else None,
            nucleotides[i + 1] if i < len(nucleotides) - 1 else None)
    
    newStrand = NucleicAcidStrand(globalIdGenerator, chainName, naType, "#FF0000", nucleotides[0], nucleotides[-1])
    globalIdGenerator += 1
    print("\tProcessing finished:", newStrand.name, len(nucleotides))
    return newStrand

def get_aa_pos(residue):
    for atom in residue.atoms():
        if atom.name == "CA":
            return np.asarray(atom.location)
    # Just a fallback in case alpha carbon is not found for some reason
    return residue.center_of_mass

def process_aa_chain(chainName, residues):
    print("Processing protein chain with", len(residues), "residues.")
    global globalIdGenerator
    aminoAcids = []

    for res in residues:
        newAaId = globalIdGenerator
        globalIdGenerator += 1
        aminoAcids.append(AminoAcid(newAaId, res.name, None, None, get_aa_pos(res), res.id))
    
    for i in range(len(aminoAcids)):
        aminoAcids[i].set_prev_next(
            aminoAcids[i - 1] if i > 0 else None,
            aminoAcids[i + 1] if i < len(aminoAcids) - 1 else None)

    newChain = AminoAcidChain(globalIdGenerator, chainName, "#0000FF", aminoAcids[0], aminoAcids[-1])
    globalIdGenerator += 1
    print("\tProcessing finished:", newChain.name, len(aminoAcids))
    return newChain

def process_pdb(pdb_path):
    if os.path.isfile(pdb_path):
        pdb = atomium.open(pdb_path)
    else:
        pdb = atomium.fetch(pdb_path)

    aaChains = []
    naStrands = []

    for chain in pdb.model.chains():
        residues = chain.residues()
        
        if len(residues) > 0:
            # First residue helps to determine if we are processing protein
            # or nucleic acid chain
            if(unfutils.is_protein_res(residues[0].name)):
                aaChains.append(process_aa_chain(chain.id, residues))
            elif(unfutils.is_dna_res(residues[0].name)):
                naStrands.append(process_na_strand(chain.id, residues, "DNA"))
            elif(unfutils.is_rna_res(residues[0].name)):
                naStrands.append(process_na_strand(chain.id, residues, "RNA"))

    return (pdb, aaChains, naStrands)

def convert_data_to_unf_file(pdbFile, aaChains, naStrands):
    global globalIdGenerator
    
    unf_file_data = unfutils.initialize_unf_file_data_object(pdbFile.code + ", " + pdbFile.title,
         ", ".join(pdbFile.authors) + " (converted to UNF by PDB to UNF converter)")
    
    for strand in naStrands:
        newStrObj = {}
        newStrObj["id"] = strand.id
        newStrObj["name"] = strand.name
        newStrObj["isScaffold"] = False
        newStrObj["naType"] = strand.naType
        newStrObj["color"] = strand.color
        newStrObj["fivePrimeId"] = strand.fivePrime.id
        newStrObj["threePrimeId"] = strand.threePrime.id
        newStrObj["pdbFileId"] = -1
        newStrObj["chainName"] = strand.name
        
        newStrObj["nucleotides"] = []

        currNucl = strand.fivePrime
        while True:
            newNucl = {}
            newNucl["id"] = currNucl.id
            newNucl["nbAbbrev"] = currNucl.nbName if len(currNucl.nbName) == 1 else currNucl.nbName[1]
            newNucl["pair"] = -1
            newNucl["prev"] = currNucl.prev.id if currNucl.prev != None else -1
            newNucl["next"] = currNucl.next.id if currNucl.next != None else -1
            newNucl["pdbId"] = currNucl.id

            newNuclPos = {}
            newNuclPos["nucleobaseCenter"] = currNucl.ntPos.nbCenter.tolist()
            newNuclPos["backboneCenter"] = currNucl.ntPos.bbCenter.tolist()
            newNuclPos["baseNormal"] = currNucl.ntPos.baseNormal.tolist()
            newNuclPos["hydrogenFaceDir"] = currNucl.ntPos.hydrogenFaceDir.tolist()
            
            newNucl["altPositions"] = [newNuclPos]
            newStrObj["nucleotides"].append(newNucl)

            currNucl = currNucl.next
            
            if currNucl == None:
                break

        unf_file_data["naStrands"].append(newStrObj)

    prot = {}
    prot["id"] = globalIdGenerator
    globalIdGenerator += 1
    prot["name"] = pdbFile.code
    prot["chains"] = []

    for chain in aaChains:
        newChainObj = {}
        newChainObj["id"] = chain.id
        newChainObj["color"] = chain.color
        newChainObj["nTerm"] = chain.nTermAa.id
        newChainObj["cTerm"] = chain.cTermAa.id
        newChainObj["pdbFileId"] = -1
        newChainObj["chainName"] = chain.name

        newChainObj["aminoAcids"] = []

        currAa = chain.nTermAa
        while True:
            newAa = {}
            newAa["id"] = currAa.id
            newAa["secondary"] = "NULL"
            newAa["aaAbbrev"] = currAa.aaName
            newAa["prev"] = currAa.prev.id if currAa.prev != None else -1
            newAa["next"] = currAa.next.id if currAa.next != None else -1
            newAa["pdbId"] = currAa.id
            newAa["altPositions"] = [currAa.CApos.tolist()]

            newChainObj["aminoAcids"].append(newAa)

            currAa = currAa.next
            if currAa == None:
                break

        prot["chains"].append(newChainObj)
    
    unf_file_data["proteins"].append(prot)
    unf_file_data["idCounter"] = globalIdGenerator

    with open(OUTPUT_FILE_NAME, 'w') as outfile:
        json.dump(unf_file_data, outfile)    

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        print("usage pdb_to_unf.py <pdb_path>")
        print("<pdb_path> = path to PDB/MMTF/CIF file. If the file is not available locally, it will be fetched from RCSB data bank.")
        sys.exit(1)

    convert_data_to_unf_file(*process_pdb(sys.argv[1]))

if __name__ == '__main__':
  main()
