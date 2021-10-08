@ECHO OFF

ECHO Generating new example files ...

cd ..\converters

% 3UGM %
SET srcDir=..\example-files\cg_3ugm\pdb
SET destDir=..\example-files\cg_3ugm\unf

py -3 pdb_to_unf.py %srcDir%\3ugm.pdb
move output.unf %destDir%
del %destDir%\3ugm.unf
ren %destDir%\output.unf 3ugm.unf

% 6SY6 %
SET srcDir=..\example-files\cg_6sy6\pdb
SET destDir=..\example-files\cg_6sy6\unf

py -3 pdb_to_unf.py %srcDir%\6sy6.pdb
move output.unf %destDir%
del %destDir%\6sy6.unf
ren %destDir%\output.unf 6sy6.unf

% 2JYH %
SET srcDir=..\example-files\cg_rna_2jyh\pdb
SET destDir=..\example-files\cg_rna_2jyh\unf

py -3 pdb_to_unf.py %srcDir%\2jyh.pdb
move output.unf %destDir%
del %destDir%\2jyh.unf
ren %destDir%\output.unf 2jyh.unf

% HEXTUBE_CUBOID %
SET srcDir=..\example-files\hextube_cuboid\cadnano
SET destDir=..\example-files\hextube_cuboid\unf

py -3 cadnano_to_unf.py %srcDir%\hc_hextube.json:honeycomb:270,320,0 %srcDir%\sq_cuboid_hole.json:square:0,500,0
move output.unf %destDir%
del %destDir%\hextube_cuboid.unf
ren %destDir%\output.unf hextube_cuboid.unf

% SMILEY 6JI1 %
SET srcDir=..\example-files\smiley_6ji1\source_files
SET destDir=..\example-files\smiley_6ji1\unf

py -3 cadnano_to_unf.py %srcDir%\smileyFace.json:square:0,0,0
py -3 ..\other_scripts\unf_add_pdb.py output.unf %srcDir%\6ji1.pdb 6ji1 500,0,300 0,0,0
move output.unf %destDir%
del %destDir%\smiley_6ji1.unf
ren %destDir%\output.unf smiley_6ji1.unf 

PAUSE