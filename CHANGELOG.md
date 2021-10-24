# UNF Changelog
This file contains a summary of changes in the structure of Unified Nanotechnology Format (UNF).  
While the official format repository contains also additional data, such as converters and UNF Viewer, this changelog pertains only the format itself.  
Finally, since this file was created later during the development of the format, it lists only changes since version 0.6 of the format. 

## Version 0.8.0
### Added
- *comments* field to root for arbitrary textual notes referencing some UNF-stored objects

### Changed
- *version* field was converted to a string type instead of a number (as it gives more freedom). Also, new MAJOR.MINOR.PATCH versioning was adopted.
- *nbAbbrev* field, for storing the nucleobase type abvbreviation, now allows also *N* value for any base
- Fixed *modifications*.*idtText* data type from [number] to [string]

### Removed
- virtual helix *altPosition* and *altOrientation* fields were removed due to no practical use

## Version 0.71
### Added
- None

### Changed
- (lattices - virtual helices -)cells' *left* and *right* attributes renamed to *fiveToThreeNts* and *threeToFiveNts*, respectively

### Removed
- None

## Version 0.7
### Added
- *simData* field added to JSON root containing *boxSize* attribute
- *structures* field added to JSON root

### Changed
- *naStrands* and *aaChains* moved under newly created *structures* field

### Removed
- *proteins* field 

## Version 0.6
Starting point in changelog.
