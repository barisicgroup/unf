import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import { PDBLoader } from "./PDBLoader.js";

export function getRemotePathToPdb(pdbName) {
    return "http://files.rcsb.org/download/" + pdbName;
}

export function loadPdb(pdbName, onLoaded, atomPredicate = x => true) {
    const loader = new PDBLoader();

    loader.load(
        pdbName,
        atomPredicate,
        onLoaded,
        function (xhr) { }, // Called when loading is in progresses
        function (error) {
            console.error("PDB loading failed: ", pdbName, error);
        }
    );
}

export function loadAndSpawnPdb(pdbName, position, eulerRotation, parentObject, atomPredicate = x => true) {
    loadPdb(pdbName, function (pdb) { spawnPdbData(pdb, position, eulerRotation, parentObject); }, atomPredicate);
}

export function spawnPdbData(pdbData, objPosition, eulerRotation, parentObject, atomPredicate = x => true) {
    // Modified code from https://github.com/mrdoob/three.js/blob/master/examples/webgl_loader_pdb.html

    const geometryAtoms = pdbData.geometryAtoms;
    const offset = new THREE.Vector3();
    const moleculeObject = new THREE.Object3D();

    const sphereGeometry = new THREE.IcosahedronBufferGeometry(1, 3);

    geometryAtoms.computeBoundingBox();
    geometryAtoms.boundingBox.getCenter(offset).negate();

    geometryAtoms.translate(offset.x, offset.y, offset.z);

    let positions = geometryAtoms.getAttribute("position");
    const colors = geometryAtoms.getAttribute("color");

    const position = new THREE.Vector3();
    const color = new THREE.Color();

    for (let i = 0; i < positions.count; ++i) {
        if (!atomPredicate(pdbData.json.atoms[i])) {
            continue;
        }

        position.x = positions.getX(i);
        position.y = positions.getY(i);
        position.z = positions.getZ(i);

        color.r = colors.getX(i);
        color.g = colors.getY(i);
        color.b = colors.getZ(i);

        const material = new THREE.MeshPhongMaterial({ color: color });

        const object = new THREE.Mesh(sphereGeometry, material);
        object.position.copy(position);
        moleculeObject.add(object);
    }

    moleculeObject.position.copy(objPosition);
    moleculeObject.rotation.copy(eulerRotation);
    parentObject.add(moleculeObject);
}