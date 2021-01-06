# Unified Nanotechnology Format (UNF) documentation

## Version
0.3

## Format type
JSON-based

The core of the UNF file is pure JSON, however, due to the possibility to include other files directly
in the UNF file (e.g., PDB), the final *.unf file cannot be always considered as valid JSON file.

## General notes
Position is typically in z/x/y order (might be changed in v0.3)  
Units are picometers

## Core structure
*Note: :question: sign marks fields which are strongly "prototypical"*
- **version:** format version number
- **name:** structure name string
- **author:** structure name string  
- **creationDate:** structure creation date (stored in ISO 8601 standard, i.e., as YYYY-MM-DDThh:mm:ss) 
- **doi:** DOI of the publication related to the structure stored in the file  
- **externalFiles:** array of files which are referenced throughout the UNF file's content
  - **path:** path to the file / file name
  - **isIncluded:** boolean determining whether the file is included in this UNF file or is provided externally
    -*Including external files inside the UNF file works as follows. First, UNF JSON is saved to a file. Then, for each included external file, line with the following content: "#INCLUDED_FILE <file_name>" is present immediately followed by the content of the inserted file starting on the next line. Finally, the resulting UNF file must end with a new line.* 
  - **id:** unique number ID (no other external file should have the same)
  - **hash:** hash of the file's content (currently hashed with FNV-1a inspired algorithm, see UNF Viewer, namely *unf_parser.ParserUtils.getStringHash*, for more). Serves to ensure that the content of this file is the same when reading the UNF as it was when saving it. Line endings are ignored when computing hash to avoid issues related to their expression on different OSs.
- **virtualHelices:** array of virtual helices, i.e., cadnano-like cylindrical positions
  - **id:** unique ID of this virtual helix
  - **grid:** layout name string (e.g., "square" or "honeycomb")
  - **gridPosition:** array describing the position of this virtual helix in the grid (e.g., indices 0/1 are row/col)
  - **firstActiveCell:** number of first cell where some nucleotide is
  - **lastActiveCell:** number of last cell where some nucleotide is
  - **lastCell:** number of last cell, i.e., length of the virtual helix
  - **initialAngle:** initial angle at the beginning of the virtual helix (can be used for generation of new structures)
  - **orientation:** rotation of this particular virtual helix (in v0.3, position might be added as well as these fields might serve for positioning the helix in space when gridPosition is not set)
  - **cells:** array of possible nucleotide locations (one cell can contain two complementary nucleotides)
    - **id:** unique ID of this cell
    - **number:** cell number (higher the number, the farther the cell is from the beginning of the virtual helix)
    - **position:** if not empty, this array determines the position of this cell in space (order of axes: z/x/y)
    - **type:** number determining the type of the cell (normal/loop/skip)
    - **left:** ID of the left (5'3' direction) nucleotide
    - **right:** ID of the right (3'5' direction) nucleotide
- **singleStrands:** array of individual single strands and their nucleotides
  - **id:** unique ID of this strand
  - **isScaffold:** boolean determining whether this is a scaffold strand or a staple strand
  - **color:** hex string storing the color for this strand
  - **fivePrimeId:** ID of the 5' nucleotide
  - **threePrimeId:** ID of the 3' nucleotide
  - **pdbFileId:** ID of the relevant external PDB file
  - **chainName:** name of the chain in the referenced PDB
  - **confFilesIds:** array of IDs referencing oxDNA configuration files used for retrieving nucleotides' positional information. By default, zeroth config file is used but it is up to an application to decide which one to use if there are more (e.g., to show dynamics animation).
  - **nucleotides:** array of nucleotides of this strand
      - **id:** unique ID of this nucleotide
      - **naType:** string determining the type of nucleic acid (e.g., DNA/RNA/XNA)  
      - **nbAbbrev:** string determining the nucleobase type (A/T/C/G)
      - **pair:** ID of the complementary nucleotide
      - **prev:** ID of the preceding nucleotide in the strand
      - **next:** ID of the following nucleotide in the strand
      - **oxDnaConfRow:** row in the referenced oxDNA config file relevant to this nucleotide (to load position)
      - **pdbId:** identification of the relevant residue in the PDB file (to load atoms)
      - :question: **sidechainCenter:** --
- :question: **proteins:** array of proteins (their chains, amino acids, etc.)
  - **chains:** array of chains of the given protein
    - **id:** unique ID of this chain
    - **chainName:** chain name
    - **pdbFileId:** ID of the relevant external PDB file
    - **NTerm:** ID of the N-terminus amino acid
    - **CTerm:** ID of the C-terminus amino acid
    - **confFilesIds:** array of IDs referencing oxDNA configuration files used for retrieving amino acids' positional information. By default, zeroth config file is used but it is up to an application to decide which one to use if there are more (e.g., to show dynamics animation).
    - **aminoAcids:** array of the amino acids of this chain
      - **id:** unique ID of this amino acid
      - **secondary:** string determining the secondary structure this AA is part of
      - **seq:** abbreviation of the AA name
      - **prev:** ID of the preceding AA in the chain
      - **next:** ID of the following AA in the chain
      - **oxDnaConfRow:** row in the referenced oxDNA config file relevant to this AA (to load position)
      - **pdbId:** identification of the relevant residue in the PDB file (to load atoms)
- **molecules:** array of arbitrary molecules which have some position in space but we do not care about their modifications or individual parts (i.e., PDB is enough)
  - **pdbFileId:** ID of the relevant external PDB file
  - **orientation:** orientation in space
  - **position:** position in space
- :question: **groups:** array with user-defined groups of particular objects
  - **id:** integer ID of the group
  - **name:** string describing the name of the group
  - **includedObjects:** array with IDs of objects being part of this group
  - *Note: For this field to work, each possible included object type must have global unique ID. This also applies to groups as well. Therefore, the groups field can be used to create group hierarchy (group of groups, etc.)*
- :question: **connections:** array of connections between structures (namely, nucleotides and amino acids)
  - **id:** unique ID of this connection
  - **includedObjects:** array with IDs of objects being part of this connection
  - **interactionType:** string describing the type of interaction (e.g., "watson-crick" for pairing in helix, "hoogsteen BP" for a tertiary contacts, ...)
  - *Note: For this field to work, each "structural" object must have global unique ID probably (to be able to uniquely identify particular nucl/aa based on one value)*
- :question: **modifications:** array of modifications
  - **location:** array of nucleotide/AA IDs to be modified
  - **idtText:** string describing type of modification

# UNF Viewer documentation
The UNF Viewer is written in JavaScript and Three.js library.    
It enables to visualize UNF files by selecting a desired file from the file dialog.  
To run it, clone the repository and use e.g. live server to host the viewer application.    
Since it is written in JavaScript, it cannot search your hard drive; in other words, you need to upload not just the UNF file but also all files referenced in the "externalFiles" field. If PDB file is not uploaded, the viewer automatically tries to download it from RCSB.  
The application serves mainly for UNF development purpose, it is therefore recommended to have a dev console open to see the console logs.  

# Converters documentation
- **Cadnano to UNF converter (Python)**
  - Given a path to cadnano json file and lattice type string, it converts the cadnano file to the UNF file
  - Only the core features are converted now, i.e., virtual helices, their location in grid and nucleotide positions. Things such as loops and skips are missing.
