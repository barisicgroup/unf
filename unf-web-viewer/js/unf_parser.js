import * as THREE from 'https://unpkg.com/three@0.122.0/build/three.module.js';

var ParserConstants = {
    SupportedFormatVersion: .1,
    HoneycombGridName: "honeycomb",
    SquareGridName: "square",
    VHelixRadius: .1,
    BasePairRise: .017
};

export function parseUNF(fileContent) {
    let parsedJson = JSON.parse(fileContent);
    console.log(parsedJson); // Output to log for verification purposes

    if(parsedJson.version !== ParserConstants.SupportedFormatVersion) {
        alert("Unsupported format version!");
    }

    let result = [];
    const geometry = new THREE.CylinderBufferGeometry(
        ParserConstants.VHelixRadius, ParserConstants.VHelixRadius, 1, 32, 32);
    const material = new THREE.MeshPhongMaterial({ color: 0xff4444 });

    var vHelices = parsedJson.virtualHelices; // Not an array but an object!
    for (const [key, value] of Object.entries(vHelices)) {
        const newMesh = new THREE.Mesh(geometry, material);
        newMesh.position.copy(getPositionForIndex(value.gridPosition[0], value.gridPosition[1], parsedJson.grid));
        newMesh.position.z -= value.lastActiveCell * ParserConstants.BasePairRise * 0.5;
        newMesh.scale.set(1, value.lastActiveCell * ParserConstants.BasePairRise, 1);
        newMesh.rotation.set(THREE.MathUtils.degToRad(90), 0, 0);
        result.push(newMesh);
    }

    return result;
}

function getPositionForIndex(x, y, gridType) {
    // This is really ugly hardcoded stuff taken from Vivern
    // but good enough for testing purposes.
    if (gridType === ParserConstants.HoneycombGridName) {
        return new THREE.Vector3(
            x * ParserConstants.VHelixRadius * 2 * 0.8660254 + ParserConstants.VHelixRadius,
            (y + Math.floor((y + 1 - x % 2) / 2)) * ParserConstants.VHelixRadius * 2 + ParserConstants.VHelixRadius * 2 * (0.5 + (x % 2) * 0.5),
            0);

    }
    else if (ParserConstants.gridType === SquareGridName) {
        return new THREE.Vector3(
            x * ParserConstants.VHelixRadius * 2 + ParserConstants.VHelixRadius,
            y * ParserConstants.VHelixRadius * 2 + ParserConstants.VHelixRadius,
            0);
    }

    throw new Error("Invalid grid type!");
}