# Helmet & Mask Fit Customizer

Local FastAPI web app for resizing cosplay helmet/mask meshes to your head dimensions and generating optional removable comfort pads.

## Features
- Upload STL, OBJ, PLY, GLB, GLTF and export fitted STL.
- Uniform or independent XYZ scaling based on **interior** dimensions.
- Separate front, back, left, right and crown padding thickness settings.
- Download foam-cutting SVG templates and approximate printable TPU spacers.
- Account for comfort clearance and save a FIT_PROFILE.json in the comfort kit.

## Run (Ubuntu / Linux)

```bash
sudo apt update
sudo apt install -y python3 python3-venv
bash run.sh
```

Then visit http://localhost:8000.

## Photo calibration

The new browser-based tool accepts front and side photos and a known-size reference visible in each image. Click the reference endpoints and then the head endpoints (4 clicks per view), enter the reference length in mm, and click **Apply measured width and depth**. Enter head height separately. Photos are processed only in your browser; the app does not upload or save them. You can export or import a JSON profile of measurements and padding settings.

**Accuracy:** Use a reference in the same depth plane as your head, hold the camera level and far enough away to reduce perspective distortion, and confirm the numbers manually. This is 2D reference-based measurement, **not** automatic landmark detection, photogrammetry or a reconstructed 3D head.

## Critical limitations
The fitting engine **does not yet reconstruct a head from photographs or video**, automatically detect the helmet cavity, or align pads to mesh walls. You must measure your head and enter actual inside dimensions. If interior dimensions are omitted, it assumes 85% of the model outer dimensions as a **rough estimate only**. Inspect geometry and test-fit before committing to a full print.

**Costume / prop use only.** Do not use to modify certified protective helmets. Printed TPU parts may be too firm for direct skin contact; use soft foam and test for pressure points, vision, breathing and ventilation. Do not upload identifiable face scans to public repositories.

## Roadmap
1. ~~Manual calibrated front/profile photo measurement and reusable JSON head profile.~~ (Implemented)
2. Video photogrammetry or depth capture and manual verification.
3. Cavity detection, collision heatmap and automatic pad placement.
4. Split-part STL export for Bambu P1S build volume.

## API
- `POST /resize`: form multipart model + head dimensions, cavity dimensions, clearance, padding, scaling mode.
- `POST /comfort-kit`: thicknesses and sizes, returns ZIP with STL/SVG/JSON.
