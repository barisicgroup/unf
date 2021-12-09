import datetime
import numpy as np

DNA_PDB_BASES = ["DA", "DG", "DT", "DC", "DU"]

RNA_PDB_BASES = ["A", "G", "T", "C", "U"]

AA_PDB_RESNAMES = ["HIS", "ARG", "LYS", "ILE", "PHE", "LEU", "TRP"
  "ALA", "MET", "PRO", "CYS", "ASN", "VAL", "GLY", "SER", "GLN", "TYR"
  "ASP", "GLU", "THR", "SEC", "PYL"]

NUCLEOBASE_RING_COMMON_ATOMS = ["C2", "C4", "C5", "C6", "N1", "N3"]

def initialize_unf_file_data_object(name, author, lenUnits = "A", angUnits = "deg"):
    unfFileData = {}

    unfFileData['format'] = "unf"
    unfFileData['version'] = "1.0.0"
    unfFileData['idCounter'] = 0
    unfFileData['lengthUnits'] = lenUnits
    unfFileData['angularUnits'] = angUnits
    unfFileData['name'] = name
    unfFileData['author'] = author
    unfFileData['creationDate'] = datetime.datetime.now().replace(microsecond=0).isoformat()
    unfFileData['doi'] = "NULL"
    unfFileData['simData'] = {}
    unfFileData['simData']['boxSize'] = []
    unfFileData['externalFiles'] = []
    unfFileData['lattices'] = []
    unfFileData['structures'] = []
    unfFileData['groups'] = []
    unfFileData['connections'] = []
    unfFileData['modifications'] = []
    unfFileData['comments'] = []
    unfFileData['misc'] = {}
    unfFileData['molecules'] = {}
    unfFileData['molecules']['ligands'] = []
    unfFileData['molecules']['nanostructures'] = []
    unfFileData['molecules']['others'] = []

    return unfFileData

def is_dna_res(resName):
    return resName in DNA_PDB_BASES

def is_rna_res(resName):
    return resName in RNA_PDB_BASES

def is_protein_res(resName):
    return resName in AA_PDB_RESNAMES

def is_drna_backbone(atomName):
    return "P" in atomName or "'" in atomName

def normalize(np_vector):
    return np_vector / np.sqrt(np.sum(np_vector**2))

def dec_color_to_hex(decimalColor):
    result = "#"
    hexRes = hex(decimalColor).replace("0x", "")
    for i in range(0, 6 - len(hexRes)):
        result += "0"
    result += hexRes
    return result

# Expects hex string of form #RRGGBB
def hex_color_to_dec(hexColor):
    if len(hexColor) != 7:
        return int("00FF00", 16)
    return int(hexColor[1:], 16)
    