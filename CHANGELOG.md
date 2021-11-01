# UNF Changelog
This file contains a summary of changes in the structure of Unified Nanotechnology Format (UNF).  
While the official format repository contains also additional data, such as converters and UNF Viewer, this changelog pertains only the format itself.  
Finally, since this file was created later during the development of the format, it lists only changes since version 0.6 of the format. 

### Versioning explained
Since version 0.8.0, UNF employs MAJOR.MINOR.PATCH versioning pattern.  
MAJOR.MINOR are gradually increased when potentially compatibility-breaking changes are introduced to the UNF structure.  
PATCH is increased in case of backwards-compatible changes. For example, when a new values is allowed to be assigned to a particular field.  
Therefore, if a particular application supports UNF vX.Y.Z, it should also automatically work with any UNF version starting on X.Y. 

## Version 1.0.0
Fast-forward update. This version equals to version 0.8.0. It does not introduce any changes.  
The purpose of doing this jump in versioning is to clarify that this version offers a sufficient feature set to be usable for various nanotechnology tasks.  
Also, since 1.0.0, the core of the UNF should be more stable and without changes leading to a big overhaul of the format structure (ideally).

## Version 0.8.0
### Added
- *comments* field to root for arbitrary textual notes referencing some UNF-stored objects

### Changed
- *version* field was converted to a string type instead of a number (as it gives more freedom). Also, new MAJOR.MINOR.PATCH versioning was adopted.
- *nbAbbrev* field, for storing the nucleobase type abbreviation, now allows also *N* value for any base
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
