# Unified Nanotechnology Format (UNF) documentation

## Format type
JSON

## Core structure
*Note: :question: sign marks fields which are strongly "prototypical"*
- **version:** format version number
- **name:** structure name string
- **externalFiles:** array of files which are referenced throughout the UNF file's content
- **virtualHelices:** array of virtual helices, i.e., cadnano-like cylindrical positions
- **singleStrands:** array of individual single strands and their nucleotides
- **proteins:** array of proteins (their chains, amino acids, etc.)
- **molecules:** array of arbitrary molecules which have some position in space but we do not care about their modifications or individual parts (i.e., PDB is enough)
- :question: **groups:** object with user-defined groups of particular objects (should be probably changed to array in v0.3)
-  :question: **connections:** array of connections between structures (namely, nucleotides and amino acids)
-  :question: **modifications:** array of modifications

# UNF Viewer documentation

# Converters documentation
