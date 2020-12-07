# Unified Nanotechnology Format (UNF) documentation

## Version
0.2

## Format type
JSON

## Core structure
*Note: :question: sign marks fields which are strongly "prototypical"*
- **version:** format version number
- **name:** structure name string
- **externalFiles:** array of files which are referenced throughout the UNF file's content
  - **path:** path to the file / file name
  - **id:** unique number ID (no other external file should have the same)
  - **hash:** hash of the file's content (currently hashed with FNV-1a inspired algorithm, see UNF Viewer for more). Serves to ensure that the content of this file is the same when reading the UNF as it was when saving it.
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
- **proteins:** array of proteins (their chains, amino acids, etc.)
- **molecules:** array of arbitrary molecules which have some position in space but we do not care about their modifications or individual parts (i.e., PDB is enough)
- :question: **groups:** object with user-defined groups of particular objects (should be probably changed to array in v0.3)
-  :question: **connections:** array of connections between structures (namely, nucleotides and amino acids)
-  :question: **modifications:** array of modifications

# UNF Viewer documentation

# Converters documentation
