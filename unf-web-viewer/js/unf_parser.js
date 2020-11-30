import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import * as PdbUtils from "./pdb_utils.js"
import * as OxDnaUtils from "./oxdna_utils.js";

var ParserConstants = {
    SupportedFormatVersion: .2,
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
        const fnvPrime = 0x01000193;
        let hash = 0x811c9dc5;

        for (let i = 0; i < stringContent.length; ++i) {
            hash ^= stringContent[i];
            hash *= fnvPrime;
        }

        return hash;
    }
}

export function parseUNF(unfFileContent, relatedFilesList) {
    const parsedJson = JSON.parse(unfFileContent);
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
    processExternalFiles(parsedJson, rescaledParent, relatedFilesList,
        function (fileIdToFileDataMap) {
            processSingleStrands(parsedJson, rescaledParent, fileIdToFileDataMap);
            processMolecules(parsedJson, rescaledParent, fileIdToFileDataMap);
        });

    return result;
}

function processExternalFiles(parsedJson, rescaledParent, relatedFilesList, onProcessed) {
    // The values in the Map are actually different objects (i.e., of different data type)
    // so it is necessary to know what kind of data you are accessing
    let fileIdToFileDataMap = new Map();
    let externalFilesList = parsedJson.externalFiles;
    let promises = [];

    externalFilesList.forEach(fileRecord => {
        const fileName = ParserUtils.fileNameFromPath(fileRecord.path);
        const uploadedFile = relatedFilesList.find(x => x.name === fileName);
        const extension = ParserUtils.extensionFromFileName(fileName);
        let necessaryToRevokeObjURL = false;
        let uploadedFileName = uploadedFile ? uploadedFile.name : undefined;

        if (extension === "pdb") {
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

        if (uploadedFileName) {
            if (extension === "pdb") {
                promises.push(() => processPdbAndAddToMap(fileRecord.id, uploadedFileName, fileIdToFileDataMap, necessaryToRevokeObjURL));
            }
            else if (extension === "oxdna") {
                promises.push(() => processOxCfgAndAddToMap(uploadedFile, fileRecord.id, fileIdToFileDataMap));
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
    function processPdbAndAddToMap(fileId, pdbPath, fileIdToFileDataMap, necessaryToRevokeObjURL) {
        return new Promise(function (resolve) {
            PdbUtils.loadPdb(pdbPath, (fileContent, pdbData) => {
                console.log(fileId + ": " + ParserUtils.getStringHash(fileContent));
                fileIdToFileDataMap.set(fileId, pdbData);
                if (necessaryToRevokeObjURL) {
                    window.URL.revokeObjectURL(pdbPath);
                }
                resolve();
            })
        });
    }

    function processOxCfgAndAddToMap(oxFile, fileId, fileIdToFileDataMap) {
        return new Promise(function (resolve) {
            OxDnaUtils.parseOxConfFile(oxFile, (fileContent, oxData) => {
                console.log(fileId + ": " + ParserUtils.getStringHash(fileContent));
                fileIdToFileDataMap.set(fileId, oxData);
                resolve();
            })
        });
    }
}

function processVirtualHelices(parsedJson, objectsParent) {
    // At the moment, this functions processes all virtualHelices.cells records
    // and draws a single cylinder at the cell.position
    const cylinderGeometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius * 0.5, ParserConstants.VHelixRadius * 0.5, 1, 32, 32);
    const cylinderTranspMaterial = new THREE.MeshBasicMaterial({ color: 0xff4444, opacity: 0.3, transparent: true });

    var vHelices = parsedJson.virtualHelices;
    vHelices.forEach(helix => {
        helix.cells.forEach(cell => {
            cylinderTranspMaterial.color.setHex(Math.random() * 0xffffff);
            const newMesh = new THREE.Mesh(cylinderGeometry, new THREE.MeshBasicMaterial(cylinderTranspMaterial));
            newMesh.position.set(
                // UNF now stores positions as z/x/y
                ParserUtils.pmToAngs(cell.position[1]),
                ParserUtils.pmToAngs(cell.position[2]),
                ParserUtils.pmToAngs(cell.position[0]));
            newMesh.scale.set(1, ParserConstants.BasePairRise, 1);
            newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
            objectsParent.add(newMesh);
        });
    });

    function getPositionForIndex(x, y, gridType) {
        const vHelixDiameter = ParserConstants.VHelixRadius * 2;

        if (gridType === ParserConstants.HoneycombGridName) {
            return new THREE.Vector3(
                x * ParserConstants.VHelixRadius * 1.7320508 + ParserConstants.VHelixRadius,
                (y + Math.floor((y + 1 - x % 2) / 2)) * vHelixDiameter + vHelixDiameter * (0.5 + (x % 2) * 0.5),
                0);

        }
        else if (ParserConstants.gridType === SquareGridName) {
            return new THREE.Vector3(
                x * vHelixDiameter + ParserConstants.VHelixRadius,
                y * vHelixDiameter + ParserConstants.VHelixRadius,
                0);
        }

        throw new Error("Invalid grid type!");
    }
}

function processSingleStrands(parsedJson, objectsParent, fileIdToFileDataMap) {
    const sphereGeometry = new THREE.SphereGeometry(3.5, 16, 16);

    parsedJson.singleStrands.forEach(strand => {
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
    });
}

function processMolecules(parsedJson, objectsParent, fileIdToFileDataMap) {
    parsedJson.molecules.forEach(molecule => {
        const requestedPdbId = molecule.pdbFileId;

        const position = new THREE.Vector3(
            ParserUtils.pmToAngs(molecule.position[1]),
            ParserUtils.pmToAngs(molecule.position[2]),
            ParserUtils.pmToAngs(molecule.position[0]));

        const rotation = new THREE.Vector3(
            molecule.orientation[1],
            molecule.orientation[2],
            molecule.orientation[0]
        );

        if (fileIdToFileDataMap.has(requestedPdbId)) {
            PdbUtils.spawnPdbData(fileIdToFileDataMap.get(requestedPdbId), position, rotation, objectsParent);
        }
        else {
            console.error("Molecule PDB not found, file ID: " + requestedPdbId);
        }
    });
}