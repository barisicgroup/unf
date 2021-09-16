# Unified Nanotechnology Format (UNF) documentation

## Purpose
UNF aims to allow for storing of DNA nanotechnology data (for example, DNA origami lattice designs and individual free-form single strands) together with proteins and other molecules in one file.

## Version
0.6

## Format type
JSON-based

The core of the UNF file is pure JSON, however, due to the possibility to include other files directly in the UNF file (e.g., PDB, see field *externalFiles*), the final *.unf file cannot be always considered as a valid JSON file.

## General notes
Positions are stored in [x, y, z] order, units are determined by the *lengthUnits* field.  
Rotations/orientations are stored in Euler angles ("angularUnits" field determines rads/degs), values determines how much is the object rotated around each of [x, y, z] axes.  
Zero-indexing is used.

## Conventions
IDs are unsigned integers  
To mark fields as "not used"/containing invalid value:
 - value "-1" should be used in ID-related fields (or in other fields where the meaningful values are only zero or greater)
 - empty array should be used in array-typed fields
 - empty string or "NULL" text can be used in string-based fields

## Core structure
<!--- *Note: :question: sign marks fields which are strongly "prototypical"* -->
- `string` **format:** stores the file format identification (should be always "unf")
- `number` **version:** format version number
- `string` **lengthUnits:** determines in what length units (identified by SI symbol) are position-related data stored. 
    - *Allowed values: A (for ångström), pm (for picometer), nm (for nanometer)*
    - *Default assumed value: A*
- `string` **angularUnits:** determines the units in which angular data are stored
    - *Allowed values: deg (for degrees), rad (for radians)*
    - *Default assumed value: deg*
- `string` **name:** structure name
- `string` **author:** structure author name  
- `string` **creationDate:** structure creation date (stored in ISO 8601 standard, i.e., as YYYY-MM-DDThh:mm:ss) 
- `string` **doi:** DOI of the publication related to the structure stored in the file  
- `[object]` **externalFiles:** array of files which are referenced throughout the UNF file's content
  - `number` **id:** unique number ID
  - `string` **path:** path to the file / file name
    - If the file is not included, relative path starting from the location of the UNF file may be provided to reference it
    - Otherwise, the name will be used to search for the file data inside of the UNF file 
  - `boolean` **isIncluded:** boolean determining whether the file is included in this UNF file or is provided externally
    - *Including external files inside the UNF file works as follows. First, UNF JSON is saved to a file. Then, for each included external file, line with the following content: "#INCLUDED_FILE <file_name>" is present immediately followed by the content of the inserted file starting on the next line. Finally, the resulting UNF file must end with a new line.* 
  - `string` **hash:** MD5 hash of the file's content. Serves to ensure that the content of this file is the same when reading the UNF as it was when saving it. Line endings are ignored when computing hash to avoid issues related to their representation on different OSs.
- `[object]` **lattices:** array of lattices defining constrained design space
  - `number` **id:** unique ID of this lattice
  - `string` **type:** lattice type/layout name
    - *Allowed values: square, honeycomb*
    - *Other values may result in incompatibility between applications*
  - `[number]` **position:** world position of the top-left corner (origin) of the lattice
  - `[number]` **orientation:** orientation of the lattice in space (x axis goes right from origin, y axis should face down, z axis "into" the lattice)
  - `[object]` **virtualHelices:** array of virtual helices, i.e., lattice cells determining location and orientation of a possible double helix. Lattice may contain lots of empty cells/virtual helices (theoretically infinite), which should not be part of UNF as they carry no data.
    - `number` **id:** unique ID of this virtual helix
    - `[number]` **latticePosition:** array describing the position of this virtual helix in the lattice. For example [1, 2] refers to row 1, column 2.
    - `number` **firstActiveCell:** number of the first cell containing a nucleotide
    - `number` **lastActiveCell:** number of the last cell containing a nucleotide
    - `number` **lastCell:** number of the last cell, i.e., length of the virtual helix
    - `number` **initialAngle:** initial helical twist at the beginning of the virtual helix (used for generation of DNA helix inside this virtual helix)
    - `[number]` **altPosition:** alternative world position of this particular virtual helix relative to the lattice origin; can be used to override position determined by the lattice
    - `[number]` **altOrientation:** rotation of this particular virtual helix; can be used to override position determined by the lattice
    - `[object]` **cells:** array of nucleotide locations (one cell can contain up to two complementary nucleotides). Cells (cell numbers) which are not included are considered as empty.
      - `number` **id:** unique ID of this cell
      - `number` **number:** cell number (starting with zero; higher the number, the farther the cell is from the beginning of the virtual helix)
      - `[number]` **altPosition:** this field can determine the world position of this cell in space; can be used to override position determined by lattice & cell number
      - `string` **type:** text determining the type of the cell
        - *Allowed values: n (for normal), l (for loop), s (for skip)*
      - `number` **left:** ID of the left (5'3' direction) nucleotide
      - `number` **right:** ID of the right (3'5' direction) nucleotide
- `[object]` **naStrands:** array of individual nucleic acid single strands and their nucleotides
  - `number` **id:** unique ID of this strand
  - `string` **name:** name/title of this strand
  - `boolean` **isScaffold:** boolean determining whether this is a scaffold strand or a staple strand
  - `string` **naType:** nucleic acid type
    - *Allowed values: DNA, RNA, XNA*
  - `string` **color:** hex string storing the color for this strand
  - `number` **fivePrimeId:** ID of the 5' nucleotide
  - `number` **threePrimeId:** ID of the 3' nucleotide
  - `number` **pdbFileId:** ID of the relevant external PDB file (for loading atomic data)
  - `string` **chainName:** name of the chain in the referenced PDB
  - `[number]` **confFilesIds:** array of IDs referencing oxDNA configuration files used for retrieving nucleotides' positional information. By default, zeroth config file is used but it is up to an application to decide which one to use if there are more (e.g., to show dynamics animation).
  - `[object]` **nucleotides:** array of nucleotides of this strand
      - `number` **id:** unique ID of this nucleotide
      - `number` **nbAbbrev:** nucleobase type
        - *Allowed values: A, T, C, G, U*
        - *Other values may result in application incompatibility*
      - `number` **pair:** ID of the complementary nucleotide
      - `number` **prev:** ID of the preceding nucleotide in the strand
      - `number` **next:** ID of the following nucleotide in the strand
      - `number` **oxDnaConfRow:** row in the referenced oxDNA config file relevant to this nucleotide (to load position)
      - `number` **pdbId:** identification of the relevant residue in the PDB file (to load atoms)
      - `[[object]]` **altPositions:**  2D array of alternative positions of this nucleotide (if oxDNA file is not provided or the position was modified). By default, zeroth position is considered as the current one. More positions can be stored for dynamics/animation purposes.
        - `[number]` **worldOrigin:** world position of this nucleotide's helical axis
        - `[number]` **worldBaseAxisX:** x-axis goes along the short axis of the base pair (from minor groove side to major groove side)
        - `[number]` **worldBaseAxisY:** goes along the long axis of the base pair (from C1 carbon of one base to C1 carbon of other base). For each base, it goes in backbone to helical axis direction.
        - `[number]` **worldBaseAxisZ:** goes "up" and is prependicular to base plane
- `[object]` **proteins:** array of coarse-grained stored proteins
  - `number` **id:** unique ID of this protein
  - `string` **name:** name/title of this protein
  - `[object]` **chains:** array of chains of the given protein
    - `number` **id:** unique ID of this chain
    - `string` **chainName:** chain name
    - `number` **pdbFileId:** ID of the relevant external PDB file
    - `number` **nTerm:** ID of the N-terminus amino acid
    - `number` **cTerm:** ID of the C-terminus amino acid
    - `[number]` **confFilesIds:** array of IDs referencing oxDNA configuration files used for retrieving amino acids' positional information. By default, zeroth config file is used but it is up to an application to decide which one to use if there are more (e.g., to show dynamics animation).
    - `[[object]]` **aminoAcids:** array of the amino acids of this chain
      - `number` **id:** unique ID of this amino acid
      - `string` **secondary:** string determining the secondary structure this AA is part of
      - `string` **seq:** three-letter abbreviation of the AA name
      - `number` **prev:** ID of the preceding AA in the chain
      - `number` **next:** ID of the following AA in the chain
      - `number` **oxDnaConfRow:** row in the referenced oxDNA config file relevant to this AA (to load position)
      - `number` **pdbId:** identification of the relevant residue in the PDB file (to load atoms)
      - `[[number]]` **altPositions:** 2D array of alternative positions, corresponding to alpha carbon location, of this AA (if oxDNA file is not provided or the position was modified). By default, zeroth position is considered as a current one. More positions can be stored for dynamics/animation purposes.
      <!--- Note: amino acids store only position now, any orientation/backbone direction data are now omitted. -->
- `object` **molecules:** object containing molecules which have some position in space but we do not care about their modifications or individual parts (e.g., PDB is enough)
  - `[object]` **ligands:** array of ligands. If there are molecules storing both proteins and ligands in one file (e.g., as a PDB), they should be referenced in field "other molecules" instead of this one.
    - `number` **id:** unique ID
    - `string` **name:** ligand name   
    - `number` **externalFileId:** ID of the relevant external file if there is any (e.g., SDF file)
    - `[object]` **atoms:** if no external file exists, the ligand can be described also as an array of atoms
      - `string` **atomName:** unique atom name
      - `string` **elementName:** element name
      - `[[number]]` **positions:** 2D array of atom's positions. By default, zeroth position is considered as a current one. More positions can be stored for dynamics/animation purposes.
    - `[object]` **bonds:** array of bonds between atoms
      - `string` **firstAtomName:** unique name of the first atom
      - `string` **secondAtomName:** unique name of the second atom
      - `number` **bondOrder:** bond order
      - `string` **bondType:** string identifying the type of bond
    - `[[number]]` **positions:** 2D array storing positions in space (offsetting the atom positions). By default, zeroth position is considered as a current one. More positions can be stored for dynamics/animation purposes.
    - `[[number]]` **orientations:** 2D array storing orientations in space
  - `[object]` **nanostructures:** array of nanostructures (e.g., gold nanoparticles)
    - `number` **id:** unique ID
    - `string` **name:** nanostructure name 
    - `string` **externalFileId:** ID of the relevant external file
    - `[[number]]` **positions:** 2D array storing positions in space  
    - `[[number]]` **orientations:** 2D array storing orientations in space
  - `[object]` **others:** array of other arbitrary molecules
    - `number` **id:** unique ID
    - `string` **name:** molecule name
    - `string` **type:** molecule type
    - `number` **externalFileId:** ID of the relevant external file
    - `[[number]]` **positions:** 2D array storing positions in space
    - `[[number]]` **orientations:** 2D array storing orientations in space
- `[object]` **groups:** array with user-defined groups of particular objects
  - `number` **id:** unique ID of the group
  - `string` **name:** name of the group
  - `[number]` **includedObjects:** array with IDs of objects being part of this group
- `[object]` **connections:** array of connections between structures (namely, nucleotides and amino acids)
  - `number` **id:** unique ID of this connection
  - `[number]` **includedObjects:** array with IDs of objects being part of this connection
  - `string` **interactionType:** string describing the type of interaction (e.g., "watson-crick" for pairing in helix, "hoogsteen BP" for a tertiary contacts, ...)
- `[object]` **modifications:** array of modifications
  - `[number]` **location:** array of nucleotide/AA IDs to be modified
  - `[number]` **externalFileId:** ID of the relevant external structure file  
  - `[number]` **idtText:** string describing type of modification  
- `object` **misc:** object which is by default empty but should be used for storing any application-specific/domain-specific information which could not have been stored in the other fields. It can be also used for storing comments.

# UNF Viewer documentation
> :heavy_exclamation_mark: The UNF Viewer is currently outdated and supports only UNF version 0.5

The UNF Viewer is written in JavaScript and Three.js library.    
It enables to visualize the content of a UNF file by selecting a desired file from the file dialog.  
**At the moment, only a subset of UNF fields and properties is visualized. Mainly "virtuaHelices", "NAStrands" and "molecules.others". When previewing the UNF file content, keep this fact in mind.**  
To run it, clone the repository and use, e.g., live server to host the viewer application. It is recommended to refresh/reload (typically F5) the application before loading a new strucutre.    
Since it is written in JavaScript, it cannot search your hard drive; in other words, you need to upload not just the UNF file but also all files referenced in the "externalFiles" field which are not included directly in the UNF file. If a PDB file is not included nor uploaded, the viewer automatically tries to download it from RCSB.  
The application serves mainly for UNF development purposes right now, it is, therefore, recommended to have a dev console open to see the console logs.  

# Converters documentation
- **Cadnano to UNF converter (Python)**
  - Converts given cadnano files to a single UNF file
  - Only the core features are converted now, i.e., virtual helices, their location in grid and strands / nucleotides positions. **Things such as loops and skips are missing.**
