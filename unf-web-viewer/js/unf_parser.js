import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import * as PdbUtils from "./pdb_utils.js"
import * as OxDnaUtils from "./oxdna_utils.js";

var ParserConstants = {
    SupportedFormatVersion: .1,
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

    fileNameFromPath(path) {
        return path.replace(/^.*[\\\/]/, '');
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

    processVirtualHelices(parsedJson, rescaledParent);
    processSingleStrands(parsedJson, rescaledParent, relatedFilesList);
    processMolecules(parsedJson, rescaledParent, relatedFilesList);

    return result;
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

function processSingleStrands(parsedJson, objectsParent, relatedFilesList) {
    parsedJson.singleStrands.forEach(strand => {
        var oxFile = relatedFilesList.find(x => x.name == ParserUtils.fileNameFromPath(strand.confFile[0]));
        if (oxFile !== undefined) {
            OxDnaUtils.parseOxConfFile(oxFile, x => singleStrandsOxDnaConfigLoaded(parsedJson, objectsParent, x));
        }
        else {
            console.log("No oxDNA configuration file included");
        }

    });
}

function singleStrandsOxDnaConfigLoaded(parsedJson, objectsParent, parsedData) {
    const sphereGeometry = new THREE.SphereGeometry(7, 16, 16);

    parsedJson.singleStrands.forEach(strand => {
        const material = new THREE.MeshPhongMaterial({ color: strand.color });

        strand.nucleotides.forEach(nucleotide => {
            let atoms =
                console.log(nucleotide);
        });
    });
}

function processMolecules(parsedJson, objectsParent, relatedFilesList) {
    // Right now, "molecules" field is an object, not an array (in UNF)

    const moleculePath = relatedFilesList.includes(ParserUtils.fileNameFromPath(parsedJson.molecules.pdbFile)) ?
        parsedJson.molecules.pdbFile : PdbUtils.getRemotePathToPdb(ParserUtils.fileNameFromPath(parsedJson.molecules.pdbFile));

    const position = new THREE.Vector3(
        ParserUtils.pmToAngs(parsedJson.molecules.position[1]),
        ParserUtils.pmToAngs(parsedJson.molecules.position[2]),
        ParserUtils.pmToAngs(parsedJson.molecules.position[0]));

    const rotation = new THREE.Vector3(
        parsedJson.molecules.orientation[1],
        parsedJson.molecules.orientation[2],
        parsedJson.molecules.orientation[0]
    );

    PdbUtils.loadAndSpawnPdb(moleculePath, position, rotation, objectsParent);
}