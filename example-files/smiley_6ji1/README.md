# Smiley-6ji1 structure

Smiley DNA origami structure (taken from cadnano to PDB converter by [Aksimentiev Group](https://bionano.physics.illinois.edu/cadnano2pdb)) converted from Cadnano to UNF, "looking" at the 6JI1 peptide visualized from the UNF-appended PDB file.
The location of 6JI1 is explicitly set in the UNF file to match the desired arrangement of the scene.

**Generating UNF file from source files:**
```
cadnano_to_unf.py smileyFace.json:square:0,0,0
unf_add_pdb.py output.unf 6ji1.pdb 6ji1 500,0,300 0,0,0 
```