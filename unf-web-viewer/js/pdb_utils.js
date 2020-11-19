import { PDBLoader } from "./PDBLoader.js";

export function getRemotePathToPdb(pdbName) {
    return "http://files.rcsb.org/download/" + pdbName;
}

export function loadPdb(pdbName, parentObject) {
    const loader = new PDBLoader();

    loader.load(
        pdbName,
        function(pdb) { pdbFileLoaded(pdb, parentObject); },
        function (xhr) { }, // Called when loading is in progresses
        function (error) {
            console.error("PDB loading failed: " + error);
        }
    );
}

function pdbFileLoaded(pdb, parentObject) {
    const geometryAtoms = pdb.geometryAtoms;
    const geometryBonds = pdb.geometryBonds;
    const json = pdb.json;

    console.log(parentObject.scale.x + "/" + "This molecule has " + json.atoms.length + " atoms");
}