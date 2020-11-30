import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";

export function parseOxConfFile(oxFile, onFileParsed) {
    const reader = new FileReader();

    reader.onload = function (evt) {
        try {
            onFileParsed(evt.target.result, processOxConfFileContent(evt.target.result));
        }
        catch (e) {
            alert("Parsing failed: " + oxFile.name + ".", e);
        }
    }

    reader.onerror = function (evt) {
        parsedData = [];
        alert("Error when loading oxDNA configuration file: ", evt);
    }

    reader.readAsText(oxFile, "UTF-8");
}

function processOxConfFileContent(content) {
    let resultData = [];

    const allLines = content.split(/\r\n|\n/);
    
    // First three lines contain some general information so we may skip them
    for(let i = 3; i < allLines.length; ++i) {
        var splittedLine = allLines[i].split(/[ ,]+/);

        if(splittedLine.length < 15) {
            console.warn("Ignored line in oxdna conf file: '" + splittedLine + "'");
            continue;
        }

        var newNucleotideData = {
            position: new THREE.Vector3(
                parseFloat(splittedLine[0]),
                parseFloat(splittedLine[1]),
                parseFloat(splittedLine[2]),
            ),
            bbVersor: new THREE.Vector3(
                parseFloat(splittedLine[3]),
                parseFloat(splittedLine[4]),
                parseFloat(splittedLine[5]),
            ),
            normalVersor: new THREE.Vector3(
                parseFloat(splittedLine[6]),
                parseFloat(splittedLine[7]),
                parseFloat(splittedLine[8]),
            ),
            velocity: new THREE.Vector3(
                parseFloat(splittedLine[9]),
                parseFloat(splittedLine[10]),
                parseFloat(splittedLine[11]),
            ),
            angularVelocity: new THREE.Vector3(
                parseFloat(splittedLine[12]),
                parseFloat(splittedLine[13]),
                parseFloat(splittedLine[14]),
            ),

        };

        resultData.push(newNucleotideData);
    }

    return resultData;
}