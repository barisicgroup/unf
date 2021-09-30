import datetime

DNA_PDB_BASES = ["DA", "DG", "DT", "DC", "DU"]
RNA_PDB_BASES = ["A", "G", "T", "C", "U"]

AA_PDB_RESNAMES = ["HIS", "ARG", "LYS", "ILE", "PHE", "LEU", "TRP"
  "ALA", "MET", "PRO", "CYS", "ASN", "VAL", "GLY", "SER", "GLN", "TYR"
  "ASP", "GLU", "THR", "SEC", "PYL"]

def initialize_unf_file_data_object(name, author, lenUnits = "A", angUnits = "deg"):
    unfFileData = {}

    unfFileData['format'] = "unf"
    unfFileData['version'] = 0.6
    unfFileData['idCounter'] = 0
    unfFileData['lengthUnits'] = lenUnits
    unfFileData['angularUnits'] = angUnits
    unfFileData['name'] = name
    unfFileData['author'] = author
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

def is_dna_res(resName):
    return resName in DNA_PDB_BASES

def is_rna_res(resName):
    return resName in RNA_PDB_BASES

def is_protein_res(resName):
    return resName in AA_PDB_RESNAMES