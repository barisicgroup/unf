import * as THREE from 'https://unpkg.com/three@0.122.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.122.0/examples/jsm/controls/OrbitControls.js';
import { parseUNF } from './unf_parser.js';

function viewerMain() {
    const canvas = document.querySelector("#mainCanvas");
    const renderer = new THREE.WebGLRenderer({ canvas });
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
        scene.fog = new THREE.Fog(0xFFFFFF, 2, 15);

        // Add objects
        scene.add(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshPhongMaterial({ color: 'red' })));
    }

    function cameraControlsInit() {
        const camTarget = new THREE.Vector3(0, 0, 0);

        camera.position.set(0, 5, 5);
        camera.up = new THREE.Vector3(0, 1, 0);
        camera.lookAt(camTarget);

        controls.target.copy(camTarget);
        controls.enableDamping = true;
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
        fileSelector.addEventListener('change', (event) => {
            fileLoaded(event.target.files);
        });
    }

    function fileLoaded(files) {
        if (files.length > 0 && files[0]) {
            const reader = new FileReader();
            reader.readAsText(files[0], "UTF-8");
            reader.onload = function (evt) {
                try {
                    parseUNF(evt.target.result);
                }
                catch (e) {
                    console.error("Parsing failed: " + files[0]);
                }
            }
            reader.onerror = function (evt) {
                console.error("Error when loading file.");
            }
        }
        else {
            console.log("No file to be loaded.");
        }
    }
}

viewerMain();