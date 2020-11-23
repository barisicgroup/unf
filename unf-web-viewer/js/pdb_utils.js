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
    // Based on code from https://github.com/mrdoob/three.js/blob/master/examples/webgl_loader_pdb.html

    const geometryAtoms = pdbData.geometryAtoms;
    const atoms = pdbData.json.atoms;
    
    const positions = geometryAtoms.getAttribute("position");
    const colors = geometryAtoms.getAttribute("color");

    const moleculeObject = new THREE.Object3D();
    const sphereGeometry = new THREE.SphereGeometry(1, 16, 16);
    const aabb = new THREE.Box3();
    
    // First, geometric center of selected atoms is computed 
    // to be able to position them at the desired location properly
    for(let i = 0; i < atoms.length; ++i) {
        if (atomPredicate(atoms[i])) {
            aabb.expandByPoint(new THREE.Vector3(
                positions.getX(i),
                positions.getY(i),
                positions.getZ(i),
            ));
        }
    }

    let offset = new THREE.Vector3();
    aabb.getCenter(offset).negate();
    geometryAtoms.translate(offset.x, offset.y, offset.z);
   
    let position = new THREE.Vector3();
    let color = new THREE.Color();

    // Second, individual atoms positions are selected and meshes are rendered
    for (let i = 0; i < positions.count; ++i) {
        if (!atomPredicate(atoms[i])) {
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
    moleculeObject.rotation.setFromVector3(eulerRotation);
    parentObject.add(moleculeObject);
}