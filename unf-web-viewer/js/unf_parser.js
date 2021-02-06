import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import * as PdbUtils from "./pdb_utils.js"
import * as OxDnaUtils from "./oxdna_utils.js";

var ParserConstants = {
    SupportedFormatVersion: .4,
    AngstromsPerUnit: 256,
    VHelixRadius: 20,
    BasePairRise: 3.32,
    RotationPerBp: 34.3,
    HoneycombGridName: "honeycomb",
    SquareGridName: "square",
};

var ParserUtils = {
    angsToUnits(angstroms) {
        return angstroms / ParserConstants.AngstromsPerUnit;
    },

    unitsToAngs(units) {
        return units * ParserConstants.AngstromsPerUnit;
    },

    pmToAngs(pms) {
        return pms * 0.01;
    },

    nmToAngs(nm) {
        return nm * 10;
    },

    fileNameFromPath(path) {
        return path.replace(/^.*[\\\/]/, '');
    },

    extensionFromFileName(fileName) {
        return fileName.split('.').pop();
    },

    // FNV-1a based hashing function
    getStringHash(stringContent) {
        // The string is first converted to "one-liner" to avoid
        // issues related to differently represented line endings on various OSs
        const strWithoutLines = stringContent.replace(/(\r\n|\n|\r)/gm, "");
        const fnvPrime = 0x01000193;
        let hash = 0x811c9dc5;

        for (let i = 0; i < strWithoutLines.length; ++i) {
            hash ^= strWithoutLines[i];
            hash *= fnvPrime;
        }

        return hash;
    }
}

export function parseUNF(unfFileContent, relatedFilesList) {
    let includedFileNameToContentMap = new Map();
    const unfFileJsonPart = splitJsonAndIncludedFilesFromUNF(unfFileContent, includedFileNameToContentMap);

    const parsedJson = JSON.parse(unfFileJsonPart);
    console.log(parsedJson); // Output to log for verification purposes

    if (parsedJson.version !== ParserConstants.SupportedFormatVersion) {
        alert("Unsupported format version!");
    }
    let result = [];

    var rescaledParent = new THREE.Object3D();
    rescaledParent.scale.set(
        1 / ParserConstants.AngstromsPerUnit,
        1 / ParserConstants.AngstromsPerUnit,
        1 / ParserConstants.AngstromsPerUnit);
    result.push(rescaledParent);

    // Virtual helices are not refering to any external files 
    // so they can be processed instantly
    processVirtualHelices(parsedJson, rescaledParent);

    // The rest may depend on external files so they need to be first processed
    // and after this is done, UNF parsing can continue
    // ---
    // This will be actually asynchronous so this function will return immediately
    // but not everything will be processed atm
    processExternalFiles(parsedJson, includedFileNameToContentMap, rescaledParent, relatedFilesList,
        function (fileIdToFileDataMap) {
            processSingleStrands(parsedJson, rescaledParent, fileIdToFileDataMap);
            processMolecules(parsedJson, rescaledParent, fileIdToFileDataMap);
            // TODO Proteins etc.
        });

    return result;
}

function splitJsonAndIncludedFilesFromUNF(unfFileContent, includedFileNameToContentMap) {
    const splittedFileParts = unfFileContent.split(/#INCLUDED_FILE\s+/);

    if (splittedFileParts.length > 0) {
        const jsonPart = splittedFileParts[0]; // By the definition of the format, the JSON is the first record

        for (let i = 1; i < splittedFileParts.length; ++i) {
            const firstLineBreakIdx = splittedFileParts[i].indexOf("\n");
            const fileName = splittedFileParts[i].substring(0, firstLineBreakIdx).trim();
            const fileContent = splittedFileParts[i].substring(firstLineBreakIdx + 1);

            includedFileNameToContentMap.set(fileName, fileContent);
        }

        return jsonPart;
    }
    else {
        console.error("Cannot process file content: " + unfFileContent);
        return "{}";
    }
}

function processExternalFiles(parsedJson, includedFileNameToContentMap, rescaledParent, relatedFilesList, onProcessed) {
    // The values in the Map are actually different objects (i.e., of different data type)
    // so it is necessary to know what kind of data you are accessing
    let fileIdToFileDataMap = new Map();
    let externalFilesList = parsedJson.externalFiles;
    let promises = [];

    externalFilesList.forEach(fileRecord => {
        const fileName = ParserUtils.fileNameFromPath(fileRecord.path);
        const extension = ParserUtils.extensionFromFileName(fileName);
        const uploadedFile = relatedFilesList.find(x => x.name === fileName);
        const isIncluded = fileRecord.isIncluded;
        let fileContent = undefined;
        let necessaryToRevokeObjURL = false;
        let uploadedFileName = uploadedFile ? uploadedFile.name : undefined;

        if (isIncluded) {
            fileContent = includedFileNameToContentMap.get(fileName);
            
            if (fileContent === undefined) {
                console.error("External file not included but should be: " + fileName);
                return;
            }
        }
        else if (extension === "pdb") {
            if (uploadedFile) {
                // PDB Loader is using FileLoader class from three.js accepting 
                // URLs only (if provided with only file name, it will look for it on the server which is incorrect). 
                // For this reason, it is necessary to create unique object URL for each
                // PDB file in order to feed it into the loader.
                uploadedFileName = window.URL.createObjectURL(uploadedFile);
                necessaryToRevokeObjURL = true;
            }
            else {
                // File was not found in the user-uploaded ones so let's try to download it
                // from the protein data bank
                uploadedFileName = PdbUtils.getRemotePathToPdb(fileName);
            }
        }

        if (uploadedFileName || fileContent) {
            if (extension === "pdb") {
                promises.push(() =>
                    processPdbAndAddToMap(fileRecord.id, fileRecord.hash, fileContent,
                        uploadedFileName, fileIdToFileDataMap, necessaryToRevokeObjURL));
            }
            else if (extension === "oxdna") {
                promises.push(() =>
                    processOxCfgAndAddToMap(uploadedFile, fileRecord.id, fileContent,
                        fileRecord.hash, fileIdToFileDataMap));
            }
            else {
                console.warn("No parser for this file (unsupported extension): ", file);
            }
        } else {
            console.log("UNF-referenced file not found: ", fileName);
        }
    });

    promises.reduce(function (curr, next) {
        return curr.then(next);
    }, Promise.resolve()).then(function () {
        onProcessed(fileIdToFileDataMap);
    });

    // Helper functions
    function processPdbAndAddToMap(fileId, expectedFileHash, fileContent, pdbPath, fileIdToFileDataMap, necessaryToRevokeObjURL) {
        return new Promise(function (resolve) {
            PdbUtils.loadPdb(pdbPath, fileContent, (fileContent, pdbData) => {
                const fileHash = ParserUtils.getStringHash(fileContent);
                console.log("File id " + fileId + ": hash " + fileHash + ", expected " + expectedFileHash);
                if (fileHash !== expectedFileHash) {
                    alert("File (id " + fileId + ") hash not matching.");
                }

                fileIdToFileDataMap.set(fileId, pdbData);
                if (necessaryToRevokeObjURL) {
                    window.URL.revokeObjectURL(pdbPath);
                }
                resolve();
            })
        });
    }

    function processOxCfgAndAddToMap(oxFile, fileId, fileContent, expectedFileHash, fileIdToFileDataMap) {
        return new Promise(function (resolve) {
            OxDnaUtils.parseOxConfFile(oxFile, fileContent, (fileContent, oxData) => {
                const fileHash = ParserUtils.getStringHash(fileContent);
                console.log("File id " + fileId + ": hash " + fileHash + ", expected " + expectedFileHash);
                if (fileHash !== expectedFileHash) {
                    alert("File (id " + fileId + ") hash not matching.");
                }

                fileIdToFileDataMap.set(fileId, oxData);
                resolve();
            })
        });
    }
}

function processVirtualHelices(parsedJson, objectsParent) {
    const cylinderGeometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius, ParserConstants.VHelixRadius, 1, 32, 32);
    const cylinderTranspMaterial = new THREE.MeshBasicMaterial({ color: 0xff4444, opacity: 0.3, transparent: true });

    let vHelices = parsedJson.virtualHelices;
    let usePositionFromCells = !vHelices.some(vhelix => vhelix.cells.some(cell => cell.altPosition.length != 3));

    if (usePositionFromCells) {
        vHelices.forEach(helix => {
            helix.cells.forEach(cell => {
                cylinderTranspMaterial.color.setHex(Math.random() * 0xffffff);
                const newMesh = new THREE.Mesh(cylinderGeometry, new THREE.MeshBasicMaterial(cylinderTranspMaterial));
                newMesh.position.set(
                    ParserUtils.pmToAngs(cell.altPosition[0]),
                    ParserUtils.pmToAngs(cell.altPosition[1]),
                    ParserUtils.pmToAngs(cell.altPosition[2]));
                newMesh.scale.set(.5, ParserConstants.BasePairRise, .5); // TODO The .5 here is possibly because of invalid values in test json file?
                newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
                objectsParent.add(newMesh);
            });
        });
    }
    else {
        vHelices.forEach(helix => {
            cylinderTranspMaterial.color.setHex(Math.random() * 0xffffff);
            const newMesh = new THREE.Mesh(cylinderGeometry, new THREE.MeshBasicMaterial(cylinderTranspMaterial));
            newMesh.position.copy(getGridPositionForIndex(helix.gridPosition[0], helix.gridPosition[1], 0, helix.grid)
                .add(new THREE.Vector3(0, 0, ParserConstants.BasePairRise * helix.lastCell * 0.5)));
            newMesh.scale.set(1, ParserConstants.BasePairRise * helix.lastCell, 1);
            newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
            objectsParent.add(newMesh);
        });
    }
}

function getGridPositionForIndex(x, y, z, gridType) {
    const vHelixDiameter = ParserConstants.VHelixRadius * 2;

    if (gridType === ParserConstants.HoneycombGridName) {
        return new THREE.Vector3(
            x * ParserConstants.VHelixRadius * 1.7320508 + ParserConstants.VHelixRadius,
            (y + Math.floor((y + 1 - x % 2) / 2)) * vHelixDiameter + vHelixDiameter * (0.5 + (x % 2) * 0.5),
            z * ParserConstants.BasePairRise);

    }
    else if (ParserConstants.gridType === SquareGridName) {
        return new THREE.Vector3(
            x * vHelixDiameter + ParserConstants.VHelixRadius,
            y * vHelixDiameter + ParserConstants.VHelixRadius,
            z * ParserConstants.BasePairRise);
    }

    throw new Error("Invalid grid type!");
}

function processSingleStrands(parsedJson, objectsParent, fileIdToFileDataMap) {
    const sphereGeometry = new THREE.SphereGeometry(3.5, 16, 16);

    parsedJson.NAStrands.forEach(strand => {
        // If no references to files with positions are provided, strands will be positioned
        // according to the virtual helices' cells
        if (strand.confFilesIds.length === 0) {
            const material = new THREE.LineBasicMaterial({ color: strand.color });

            let points = [];

            let currNucleotide = strand.nucleotides.find(x => x.id === strand.fivePrimeId);
            do {
                let position = null;
                parsedJson.virtualHelices.forEach(helix => {
                    helix.cells.forEach(cell => {
                        if (cell.left === currNucleotide.id) {
                            position = getGridPositionForIndex(helix.gridPosition[0], helix.gridPosition[1], cell.number, helix.grid)
                                .add(new THREE.Vector3(0, 3, 0));
                        }
                        else if (cell.right === currNucleotide.id) {
                            position = getGridPositionForIndex(helix.gridPosition[0], helix.gridPosition[1], cell.number, helix.grid)
                                .add(new THREE.Vector3(0, -3, 0));
                        }
                    });
                });

                if (position === null) {
                    console.error("Invalid nucleotide position: ", currNucleotide);
                }
                else {
                    points.push(position);
                }

                currNucleotide = strand.nucleotides.find(x => x.id === currNucleotide.next);
            }
            while (currNucleotide !== undefined);

            if (points.length > 0) {
                const geometry = new THREE.BufferGeometry().setFromPoints(points);
                const strandLine = new THREE.Line(geometry, material);
                objectsParent.add(strandLine);
            }

            // Otherwise, they will be located at the locations retrieved from configuration file
        } else {
            const confFileId = strand.confFilesIds[0];
            const pdbFileId = strand.pdbFileId;
            const material = new THREE.MeshPhongMaterial({ color: strand.color, opacity: 0.3, transparent: true });
            if (fileIdToFileDataMap.has(confFileId)) {
                let parsedData = fileIdToFileDataMap.get(confFileId);
                strand.nucleotides.forEach(nucleotide => {
                    // Spawn sphere for each nucleotide
                    let mesh = new THREE.Mesh(sphereGeometry, material);
                    let nmPos = parsedData[nucleotide.oxdnaConfRow].position;
                    nmPos = new THREE.Vector3(
                        ParserUtils.nmToAngs(nmPos.x),
                        ParserUtils.nmToAngs(nmPos.y),
                        ParserUtils.nmToAngs(nmPos.z));
                    mesh.position.copy(nmPos);
                    objectsParent.add(mesh);

                    // Spawn individual atoms
                    if (fileIdToFileDataMap.has(pdbFileId)) {
                        PdbUtils.spawnPdbData(fileIdToFileDataMap.get(pdbFileId), nmPos, new THREE.Vector3(0, 0, 0), objectsParent, atom => {
                            return atom.chainIdentifier === strand.chainName && atom.residueSeqNum == nucleotide.pdbId;
                        });
                    }
                });
            }
            else {
                console.warn("File with id " + confFileId + " not provided. Skipping appropriate records.");
            }
        }

        // TODO Add positioning according to altPosition/altOrientation values of nucleotides
    });
}

function processMolecules(parsedJson, objectsParent, fileIdToFileDataMap) {
    // TODO parsedJson.molecules.ligands/nanostructures/...
    
    parsedJson.molecules.others.forEach(molecule => {
        const requestedPdbId = molecule.externalFileId;

        const position = new THREE.Vector3(
            ParserUtils.pmToAngs(molecule.positions[0][0]),
            ParserUtils.pmToAngs(molecule.positions[0][1]),
            ParserUtils.pmToAngs(molecule.positions[0][1]));

        const rotation = new THREE.Vector3(
            molecule.orientations[0][0],
            molecule.orientations[0][1],
            molecule.orientations[0][2]
        );

        if (fileIdToFileDataMap.has(requestedPdbId)) {
            PdbUtils.spawnPdbData(fileIdToFileDataMap.get(requestedPdbId), position, rotation, objectsParent);
        }
        else {
            console.error("Molecule PDB not found, file ID: " + requestedPdbId);
        }
    });
}