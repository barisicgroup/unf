import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import * as PdbUtils from "./pdb_utils.js"
import * as OxDnaUtils from "./oxdna_utils.js";

let ParserConstants = {
    SupportedFormatVersion: "1.0.0", // Intentionally exactly major.minor.patch although major.minor should be enough for a check
    AngstromsPerUnit: 256,
    VHelixRadius: 10, //A
    BasePairRise: 3.32, // A
    RotationPerBp: 34.3, // deg
    HoneycombGridName: "honeycomb",
    SquareGridName: "square"
};

let ParserUtils = {
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

    angs(val, unitString) {
        if (unitString === "pm") {
            return ParserUtils.pmToAngs(val);
        } else if (unitString === "nm") {
            return ParserUtils.nmToAngs(val);
        }
        return val;
    },

    deg(val, unitString) {
        if (unitString === "rad") {
            return THREE.MathUtils.radToDeg(val);
        }
        return val;
    },

    rad(val, unitString) {
        if (unitString === "deg") {
            return THREE.MathUtils.degToRad(val);
        }
        return val;
    },

    fileNameFromPath(path) {
        return path.replace(/^.*[\\\/]/, '');
    },

    extensionFromFileName(fileName) {
        return fileName.split('.').pop();
    },

    getStringHash(stringContent) {
        // blueimp-md5 library is used for hashing
        const strWithoutLines = stringContent.replace(/(\r\n|\n|\r)/gm, "");
        return md5(strWithoutLines);
    },

    getFileInfoText() {
        return document.getElementById("fileInfoText");
    },

    getFileContentText() {
        return document.getElementById("fileContentText");
    }
}

let UnfUtils = {
    lengthUnits: "A",
    angularUnits: "deg",

    angs(val) {
        return ParserUtils.angs(val, this.lengthUnits);
    },

    angsVec3(v3val) {
        return new THREE.Vector3(this.angs(v3val.x),
            this.angs(v3val.y),
            this.angs(v3val.z));
    },

    deg(val) {
        return ParserUtils.deg(val, this.angularUnits);
    },

    rad(val) {
        return ParserUtils.rad(val, this.angularUnits);
    }
}

export function parseUNF(jsonTreeView, unfFileContent, relatedFilesList) {
    let includedFileNameToContentMap = new Map();
    const unfFileJsonPart = splitJsonAndIncludedFilesFromUNF(unfFileContent, includedFileNameToContentMap);

    const parsedJson = JSON.parse(unfFileJsonPart);
    console.log("UNF JSON part: ", parsedJson);

    UnfUtils.lengthUnits = parsedJson.lengthUnits;
    UnfUtils.angularUnits = parsedJson.angularUnits;

    jsonTreeView.loadData(parsedJson);
    jsonTreeView.collapse();

    ParserUtils.getFileInfoText().value = "name: " + parsedJson.name + "; (doi " + parsedJson.doi +
        "); author: " + parsedJson.author + "; creation date: " + parsedJson.creationDate;

    if (parsedJson.version !== ParserConstants.SupportedFormatVersion) {
        alert("Unsupported format version! UNF Viewer expects v" + ParserConstants.SupportedFormatVersion +
            " but the uploaded file is stored in UNF v" + parsedJson.version + ".");
    }
    let result = [];

    var rescaledParent = new THREE.Object3D();
    rescaledParent.scale.set(
        1 / ParserConstants.AngstromsPerUnit,
        1 / ParserConstants.AngstromsPerUnit,
        1 / ParserConstants.AngstromsPerUnit);
    result.push(rescaledParent);

    // Lattices are not referring to any external files 
    // so they can be processed instantly
    const nuclToCellDict = processLattices(parsedJson, rescaledParent);

    // The rest may depend on external files which need to be first processed
    // and after this is done, UNF parsing can continue
    // ---
    // This is performed asynchronously so this function will return immediately
    // though the processing is not finished
    processExternalFiles(parsedJson, includedFileNameToContentMap, rescaledParent, relatedFilesList,
        function (fileIdToFileDataMap) {
            processStructures(parsedJson, rescaledParent, fileIdToFileDataMap, nuclToCellDict);
            processMolecules(parsedJson, rescaledParent, fileIdToFileDataMap);
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
            fileContent = includedFileNameToContentMap.get(fileRecord.path);

            if (fileContent === undefined) {
                console.error("External file not included but should be: " + fileName, fileRecord.path);
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

function processLattices(parsedJson, objectsParent) {
    const cylinderGeometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius, ParserConstants.VHelixRadius, 1, 16, 16, true);
    const cylinderGeometryCapped = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius, ParserConstants.VHelixRadius, 1, 16, 16, false);
    const cylinderTranspMaterial = new THREE.MeshPhongMaterial({ color: 0x44ff44, opacity: 0.2, transparent: true });
    const cellDeletMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000, opacity: 0.4, transparent: true, side: THREE.DoubleSide });
    const cellInsMaterial = new THREE.MeshPhongMaterial({ color: 0x0000ff, opacity: 0.4, transparent: true, side: THREE.DoubleSide });

    const lattices = parsedJson.lattices;
    const hslOffsetStep = 1 / lattices.length;
    const nuclToCellDict = {};

    lattices.forEach(lattice => {
        ParserUtils.getFileContentText().value += lattice.type + " lattice: " + lattice.name + "\n---\n";

        cylinderTranspMaterial.color.offsetHSL(hslOffsetStep, 0, 0);

        let latticeCenterOfMass = new THREE.Vector3(0, 0, 0);
        let totalActiveCellCount = 0;

        const lattOrigGeometry = new THREE.SphereGeometry(10, 2, 2);
        const lattOrigMaterial = new THREE.MeshPhongMaterial(cylinderTranspMaterial);
        lattOrigMaterial.wireframe = true;
        const lattOrigMesh = new THREE.Mesh(lattOrigGeometry, lattOrigMaterial);

        objectsParent.add(lattOrigMesh);

        // Compute lattice's center of mass during the first iteration
        // to ofset individual cells afterwards based on that
        lattice.virtualHelices.forEach(vhelix => {
            vhelix.cells.forEach(cell => {
                if (cell.fiveToThreeNts.length > 0 || cell.threeToFiveNts.length > 0) {
                    latticeCenterOfMass.add(getLatticePositionForIndex(vhelix.latticePosition[0], vhelix.latticePosition[1], cell.number, lattice));
                    ++totalActiveCellCount;
                }
            })
        });

        latticeCenterOfMass.divideScalar(totalActiveCellCount);
        lattice["unfpars_com"] = latticeCenterOfMass;

        lattice.virtualHelices.forEach(vhelix => {
            for (let i = 0; i <= vhelix.lastCell; ++i) {
                let thisMat = cylinderTranspMaterial;

                if (i < vhelix.cells.length) {
                    if (vhelix.cells[i].type === "d") {
                        thisMat = cellDeletMaterial;
                    } else if (vhelix.cells[i].type === "i") {
                        thisMat = cellInsMaterial;
                    }

                    for (let l = 0; l < vhelix.cells[i].fiveToThreeNts.length; ++l) {
                        nuclToCellDict[vhelix.cells[i].fiveToThreeNts[l]] = [lattice, vhelix, vhelix.cells[i], lattOrigMesh];
                    }

                    for (let l = 0; l < vhelix.cells[i].threeToFiveNts.length; ++l) {
                        nuclToCellDict[vhelix.cells[i].threeToFiveNts[l]] = [lattice, vhelix, vhelix.cells[i], lattOrigMesh];
                    }
                }

                const newMesh = new THREE.Mesh((i === 0 || i === vhelix.lastCell - 1) ? cylinderGeometryCapped : cylinderGeometry,
                    new THREE.MeshPhongMaterial(thisMat));
                const thisCellPos = getLatticePositionForIndex(vhelix.latticePosition[0], vhelix.latticePosition[1], i, lattice);
                newMesh.position.copy(thisCellPos);

                newMesh.scale.set(1, ParserConstants.BasePairRise, 1);
                newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
                lattOrigMesh.add(newMesh);
            }

        });

        const latPos = UnfUtils.angsVec3(new THREE.Vector3().fromArray(lattice.position, 0));

        const latRot = new THREE.Vector3(
            UnfUtils.rad(lattice.orientation[0]),
            UnfUtils.rad(lattice.orientation[1]),
            UnfUtils.rad(lattice.orientation[2]));

        lattOrigMesh.position.copy(latPos);
        lattOrigMesh.rotation.set(latRot.x, latRot.y, latRot.z);
    });

    return nuclToCellDict;
}

function getLatticePositionForIndex(row, col, z, lattice) {
    const vHelixDiameter = ParserConstants.VHelixRadius * 2;
    let pos = new THREE.Vector3();

    if (lattice.type === ParserConstants.HoneycombGridName) {
        pos = new THREE.Vector3(
            col * ParserConstants.VHelixRadius * 1.7320508 + ParserConstants.VHelixRadius,
            -((row + Math.floor((row + 1 - col % 2) / 2)) * vHelixDiameter + vHelixDiameter * (0.5 + (col % 2) * 0.5)),
            z * ParserConstants.BasePairRise);
    }
    else if (lattice.type === ParserConstants.SquareGridName) {
        pos = new THREE.Vector3(
            col * vHelixDiameter + ParserConstants.VHelixRadius,
            -(row * vHelixDiameter + ParserConstants.VHelixRadius),
            z * ParserConstants.BasePairRise);
    } else {
        throw new Error("Invalid grid type: " + lattice.type);
    }

    if (lattice["unfpars_com"]) {
        pos.sub(lattice["unfpars_com"]);
    }

    return UnfUtils.angsVec3(pos);
}

function processStructures(parsedJson, rescaledParent, fileIdToFileDataMap, nuclToCellDict) {
    parsedJson.structures.forEach(structure => {
        ParserUtils.getFileContentText().value += "Structure " + structure.name + "\n";
        processSingleStrands(parsedJson, structure.naStrands, rescaledParent, fileIdToFileDataMap, nuclToCellDict);
        processProteins(parsedJson, structure.aaChains, rescaledParent, fileIdToFileDataMap);
    });
}

function processSingleStrands(parsedJson, naStrands, objectsParent, fileIdToFileDataMap, nuclToCellDict) {
    const sphereGeometry = new THREE.SphereGeometry(2, 6, 6);

    naStrands.forEach(strand => {
        let nucleotidePositions = [];
        let nucleobasePositions = [];
        let nucleobaseNormals = [];
        let nucleobaseHydrFacesDirs = [];
        let nucleotideParents = [];
        const lineMaterial = new THREE.LineBasicMaterial({ color: strand.color });
        const sphereMaterial = new THREE.MeshPhongMaterial({ color: strand.color });

        ParserUtils.getFileContentText().value += strand.naType + " strand (" +
            (strand.isScaffold === true ? "scaf" : "stap") + ") with " + strand.nucleotides.length + " nts.\n";

        let currNucleotide = strand.nucleotides.find(x => x.id === strand.fivePrimeId);
        do {
            // If nucleotide has an alternative position defined, use it as a primary source of position
            if (currNucleotide.altPositions.length > 0) {
                nucleotidePositions.push(
                    UnfUtils.angsVec3(
                        new THREE.Vector3().fromArray(currNucleotide.altPositions[0].backboneCenter)));

                nucleobasePositions.push(
                    UnfUtils.angsVec3(
                        new THREE.Vector3().fromArray(currNucleotide.altPositions[0].nucleobaseCenter)));

                nucleobaseNormals.push(
                    UnfUtils.angsVec3(
                        new THREE.Vector3().fromArray(currNucleotide.altPositions[0].baseNormal)));

                nucleobaseHydrFacesDirs.push(
                    UnfUtils.angsVec3(
                        new THREE.Vector3().fromArray(currNucleotide.altPositions[0].hydrogenFaceDir)));
            }
            // Else, if no references to files with positions are provided, strands will be positioned
            // according to the virtual helices' cells
            // This is performed in a really unoptimized manner for simplicity and to show
            // fully separated processing of virtual helices and single strands.
            else {
                let position = null;
                const nuclRec = nuclToCellDict[currNucleotide.id];
                const lattice = nuclRec[0];
                const helix = nuclRec[1];
                const cell = nuclRec[2];
                nucleotideParents.push(nuclRec[3]);

                if (cell !== undefined) {
                    const inCellIdx = Math.max(cell.fiveToThreeNts.indexOf(currNucleotide.id), cell.threeToFiveNts.indexOf(currNucleotide.id));
                    const insertedNucleotidesVisualOffset = 3;
                    const sign = cell.fiveToThreeNts.includes(currNucleotide.id) ? 1 : -1;

                    position = getLatticePositionForIndex(helix.latticePosition[0], helix.latticePosition[1] + sign * (inCellIdx > 0 ? insertedNucleotidesVisualOffset : 0), cell.number + sign * inCellIdx, lattice);

                    const xNeighborPos = getLatticePositionForIndex(helix.latticePosition[0], helix.latticePosition[1] + 2, cell.number, lattice);
                    const zNeighborPos = getLatticePositionForIndex(helix.latticePosition[0], helix.latticePosition[1], cell.number + 1, lattice);

                    const xDir = xNeighborPos.clone().sub(position).normalize();
                    const zDir = zNeighborPos.clone().sub(position).normalize();

                    let rot = undefined;

                    if (cell.fiveToThreeNts.includes(currNucleotide.id)) {
                        rot = xDir.clone().applyAxisAngle(zDir, UnfUtils.rad(helix.initialAngle) +
                            THREE.MathUtils.degToRad(ParserConstants.RotationPerBp * cell.number));
                    } else {
                        rot = xDir.clone().applyAxisAngle(zDir, UnfUtils.rad(helix.initialAngle) +
                            THREE.MathUtils.degToRad(180) + THREE.MathUtils.degToRad(ParserConstants.RotationPerBp * cell.number));
                    }

                    position.add(rot.normalize().multiplyScalar(ParserConstants.VHelixRadius * 0.8));
                }

                if (position === null) {
                    console.error("Invalid nucleotide position: ", currNucleotide);
                }
                else {
                    nucleotidePositions.push(position);
                }
            }

            currNucleotide = strand.nucleotides.find(x => x.id === currNucleotide.next);
        }
        while (currNucleotide !== undefined);

        const strandParent = new THREE.Object3D();
        objectsParent.add(strandParent);

        if (nucleotidePositions.length > 0) {
            const geometry = new THREE.BufferGeometry().setFromPoints(nucleotidePositions);
            const strandLine = new THREE.Line(geometry, lineMaterial);
            (nucleotideParents.length > 0 ? nucleotideParents[0] : strandParent).add(strandLine);

            for (let i = 0; i < nucleotidePositions.length; ++i) {
                const nuclMesh = new THREE.Mesh(sphereGeometry, sphereMaterial);
                nuclMesh.position.copy(nucleotidePositions[i]);
                (nucleotideParents.length > i ? nucleotideParents[i] : strandParent).add(nuclMesh);
            }

            // Non-lattice-based data
            if (nucleobasePositions.length === nucleotidePositions.length) {
                for (let i = 0; i < nucleobasePositions.length; ++i) {
                    const bbToNb = nucleobasePositions[i].clone().sub(nucleotidePositions[i]);
                    const bbToNbArrow = new THREE.ArrowHelper(bbToNb.clone().normalize(), nucleotidePositions[i],
                        bbToNb.length(), strand.color);
                    strandParent.add(bbToNbArrow);

                    const baseNormArrow = new THREE.ArrowHelper(nucleobaseNormals[i].normalize(),
                        nucleobasePositions[i], 2, "#0000FF");
                    strandParent.add(baseNormArrow);

                    const baseHydrogFaceArrow = new THREE.ArrowHelper(nucleobaseHydrFacesDirs[i].normalize(),
                        nucleobasePositions[i], 2, "#00FF00");
                    strandParent.add(baseHydrogFaceArrow);
                }
            }
        }
    });
}

function processProteins(parsedJson, aaChains, objectsParent, fileIdToFileDataMap) {
    const sphereGeometry = new THREE.SphereGeometry(1, 6, 6);

    aaChains.forEach(chain => {
        let aminoAcidPositions = [];
        const pdbFileId = chain.pdbFileId;
        const lineMaterial = new THREE.LineBasicMaterial({ color: chain.color });
        const aaMaterial = new THREE.MeshPhongMaterial({ color: chain.color });

        let currAminoAcid = chain.aminoAcids.find(x => x.id === chain.nTerm);
        do {
            if (currAminoAcid.altPositions.length > 0 && currAminoAcid.altPositions[0].length >= 3) {
                const aaPos = new THREE.Vector3().fromArray(currAminoAcid.altPositions[0]);
                aminoAcidPositions.push(UnfUtils.angsVec3(aaPos));

                if (pdbFileId >= 0 && fileIdToFileDataMap.has(pdbFileId)) {
                    PdbUtils.spawnPdbData(fileIdToFileDataMap.get(pdbFileId), UnfUtils.angsVec3(aaPos), new THREE.Vector3(0, 0, 0), objectsParent, atom => {
                        return atom.chainIdentifier === chain.chainName && atom.residueSeqNum == currAminoAcid.pdbId;
                    });
                }
            }
            else {
                console.error("AA location can be retrieved only from 'altPositions' field " +
                    "at the moment. It seems to contain invalid data: ", currAminoAcid.altPositions);
            }

            currAminoAcid = chain.aminoAcids.find(x => x.id === currAminoAcid.next);
        }
        while (currAminoAcid !== undefined);

        if (aminoAcidPositions.length > 0) {
            const geometry = new THREE.BufferGeometry().setFromPoints(aminoAcidPositions);
            const chainLine = new THREE.Line(geometry, lineMaterial);
            objectsParent.add(chainLine);

            for (let i = 0; i < aminoAcidPositions.length; ++i) {
                const aaMesh = new THREE.Mesh(sphereGeometry, aaMaterial);
                aaMesh.position.copy(aminoAcidPositions[i]);
                objectsParent.add(aaMesh);
            }

            ParserUtils.getFileContentText().value += "amino acid chain " + chain.chainName + ": " +  aminoAcidPositions.length + " amino acids\n";
        }
    });
}

function processMolecules(parsedJson, objectsParent, fileIdToFileDataMap) {
    const ligAtGeometry = new THREE.BoxGeometry(1, 1, 1);
    const ligandMaterial = new THREE.MeshPhongMaterial({ color: "#00FF00" });

    parsedJson.molecules.ligands.forEach(ligand => {
        ParserUtils.getFileContentText().value += "molecule - ligand: " + ligand.name + "\n";

        const ligandObject = new THREE.Object3D();

        for (let i = 0; i < ligand.atoms.length; ++i) {
            const atomMesh = new THREE.Mesh(ligAtGeometry, ligandMaterial);

            atomMesh.position.copy(UnfUtils.angsVec3(
                new THREE.Vector3().fromArray(ligand.atoms[i].positions[0])));

            ligandObject.add(atomMesh);
        }

        ligandObject.position.copy(UnfUtils.angsVec3(
            new THREE.Vector3().fromArray(ligand.positions[0])));

        ligandObject.rotation.set(
            UnfUtils.rad(ligand.orientations[0][0]),
            UnfUtils.rad(ligand.orientations[0][1]),
            UnfUtils.rad(ligand.orientations[0][2]));

        objectsParent.add(ligandObject);
    });

    parsedJson.molecules.others.forEach(molecule => {
        ParserUtils.getFileContentText().value += "molecule - other: " + molecule.name + "\n";

        const requestedPdbId = molecule.externalFileId;

        const position = new THREE.Vector3(
            UnfUtils.angs(molecule.positions[0][0]),
            UnfUtils.angs(molecule.positions[0][1]),
            UnfUtils.angs(molecule.positions[0][2]));

        const rotation = new THREE.Vector3(
            UnfUtils.rad(molecule.orientations[0][0]),
            UnfUtils.rad(molecule.orientations[0][1]),
            UnfUtils.rad(molecule.orientations[0][2]));

        if (fileIdToFileDataMap.has(requestedPdbId)) {
            PdbUtils.spawnPdbData(fileIdToFileDataMap.get(requestedPdbId), position, rotation, objectsParent);
        }
        else {
            console.error("Molecule PDB not found, file ID: " + requestedPdbId);
        }
    });

    // TODO molecules.nanostructures
}