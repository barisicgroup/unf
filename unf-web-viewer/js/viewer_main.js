import * as THREE from "https://unpkg.com/three@0.122.0/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.122.0/examples/jsm/controls/OrbitControls.js";
import { parseUNF } from "./unf_parser.js";

function viewerMain() {
    const canvas = document.querySelector("#mainCanvas");
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, getCurrAspectRatio(), 0.1, 100);
    const controls = new OrbitControls(camera, canvas);

    fileReaderInit();
    cameraControlsInit();
    sceneInit();

    requestAnimationFrame(render);

    function render(timeSinceAppLoad) {
        update();

        if (resizeRendererToDisplaySize(renderer)) {
            camera.aspect = getCurrAspectRatio();
            camera.updateProjectionMatrix();
        }

        renderer.render(scene, camera);
        requestAnimationFrame(render);
    }

    function update() {
        controls.update();
    }

    function sceneInit() {
        // Add lights
        const ambientLight = new THREE.AmbientLight(0xFFE484, .1);
        const dirLight = new THREE.DirectionalLight(0xFFE484, 1);
        dirLight.position.set(1, 2, 4);
        dirLight.target.position.set(0, 0, 0);

        scene.add(ambientLight);
        scene.add(dirLight);
        scene.add(dirLight.target);

        // Set-up background color and fog
        scene.background = new THREE.Color(0xFFFFFF);
        scene.fog = new THREE.Fog(0xFFFFFF, 2, 30);

        // Add arrows for axes, and a grid
        scene.add(new THREE.GridHelper(100, 100, 0xcccccc, 0xdddddd));
        // y-offset of arrow helpers below is just to prevent z-fighting with a grid
        scene.add(new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0.001, 0), 1, 0x00FF00));
        scene.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0.001, 0), 1, 0xFF0000));
        scene.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0.001, 0), 1, 0x0000FF));
    }

    function cameraControlsInit() {
        const camTarget = new THREE.Vector3(0, 0, 0);

        camera.position.set(0, 5, 5);
        camera.up = new THREE.Vector3(0, 1, 0);
        camera.lookAt(camTarget);

        controls.target.copy(camTarget);
        controls.enableDamping = true;
        controls.dampingFactor = 0.07;
        controls.update();
    }

    function getCurrAspectRatio() {
        return renderer.domElement.clientWidth / renderer.domElement.clientHeight;
    }

    function resizeRendererToDisplaySize(renderer) {
        const canvas = renderer.domElement;
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        const needResize = canvas.width !== width || canvas.height !== height;
        if (needResize) {
            renderer.setSize(width, height, false);
        }
        return needResize;
    }

    function fileReaderInit() {
        const fileSelector = document.querySelector("#inputUnfFile");
        fileSelector.addEventListener("change", (event) => {
            fileLoaded(event.target.files);
        });
    }

    function fileLoaded(files) {
        const selectedFiles = Array.from(files);
        const unfFile = selectedFiles.find(x => { 
            let extension = x.name.split('.').pop();
            return extension === "unf" || extension === "json";
        });
        selectedFiles.splice(selectedFiles.indexOf(unfFile), 1);

        if (unfFile !== undefined) {
            // Only UNF file is fully read into the memory
            // Remaining files are forwared only as references
            const reader = new FileReader();
            
            reader.onload = function (evt) {
                try {
                    var parsedObjects = parseUNF(evt.target.result, selectedFiles);
                    if (parsedObjects) {
                        parsedObjects.forEach(object => scene.add(object));
                    }
                }
                catch (e) {
                    alert("Parsing failed: " + unfFile + ". ", e);
                }
            }

            reader.onerror = function (evt) {
                alert("Error when loading file: ", evt);
            }

            reader.readAsText(unfFile, "UTF-8");
        }
        else {
            console.log("No UNF file to be loaded.");
        }
    }
}

viewerMain();