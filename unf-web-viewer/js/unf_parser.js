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

    return result;
}

function processVirtualHelices(parsedJson, objectsParent) {
    const geometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius, ParserConstants.VHelixRadius, 1, 32, 32);
    const material = new THREE.MeshPhongMaterial({ color: 0xff4444 });

    var vHelices = parsedJson.virtualHelices;
    for (const [key, value] of Object.entries(vHelices)) {
        const newMesh = new THREE.Mesh(geometry, material);
        newMesh.position.copy(getPositionForIndex(value.gridPosition[0], value.gridPosition[1], parsedJson.grid));
        newMesh.position.z -= value.lastActiveCell * ParserConstants.BasePairRise * 0.5;
        newMesh.scale.set(1, value.lastActiveCell * ParserConstants.BasePairRise, 1);
        newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
        objectsParent.add(newMesh);
    }
   
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