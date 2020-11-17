import * as THREE from 'https://unpkg.com/three@0.122.0/build/three.module.js';

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
    }
}

export function parseUNF(fileContent) {
    const parsedJson = JSON.parse(fileContent);
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
    processSingleStrands(parsedJson, rescaledParent);

    return result;
}

function processVirtualHelices(parsedJson, objectsParent) {
    const cylinderGeometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius * 0.5, ParserConstants.VHelixRadius * 0.5, 1, 32, 32);
    const cylinderTranspMaterial = new THREE.MeshBasicMaterial({ color: 0xff4444, opacity: 0.3, transparent: true });

    var vHelices = parsedJson.virtualHelices;
    vHelices.forEach(helix => {
        helix.cells.forEach(cell => {
            cylinderTranspMaterial.color.setHex(Math.random() * 0xffffff);
            const newMesh = new THREE.Mesh(cylinderGeometry, new THREE.MeshBasicMaterial(cylinderTranspMaterial));
            newMesh.position.set(
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

function processSingleStrands(parsedJson, objectsParent) {
    // TODO
}