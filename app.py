from pathlib import Path
from io import BytesIO
import json
import numpy as np
import trimesh
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from comfort import validate_fit, create_kit

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Helmet & Mask Fit Customizer")

@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "index.html").read_text(encoding="utf-8")

@app.post("/resize")
async def resize(
    model: UploadFile = File(...),
    head_width: float = Form(...), head_depth: float = Form(...), head_height: float = Form(...),
    clearance: float = Form(2),
    interior_width: float = Form(0), interior_depth: float = Form(0), interior_height: float = Form(0),
    mode: str = Form("uniform"),
    pad_front: float = Form(0), pad_back: float = Form(0),
    pad_left: float = Form(0), pad_right: float = Form(0), pad_crown: float = Form(0),
):
    if not (model.filename or "").lower().endswith((".stl", ".obj", ".ply", ".glb", ".gltf")):
        raise HTTPException(400, "Upload STL, OBJ, PLY, GLB or GLTF.")
    raw = await model.read()
    if len(raw) > 70_000_000:
        raise HTTPException(413, "Model must be below 70 MB.")
    try:
        scene = trimesh.load(BytesIO(raw), file_type=model.filename.rsplit(".", 1)[-1].lower(), force="scene")
        meshes = [g.copy() for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("No polygon mesh found")
        mesh = trimesh.util.concatenate(meshes)
    except Exception as exc:
        raise HTTPException(400, f"Unable to load model: {exc}") from exc
    if mesh.is_empty or np.any(mesh.extents < 0.001):
        raise HTTPException(400, "Model has no usable 3D dimensions.")
    pads = dict(front=pad_front, back=pad_back, left=pad_left, right=pad_right, crown=pad_crown)
    try:
        target = validate_fit((head_width, head_depth, head_height), pads, clearance)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    interior = np.array([interior_width, interior_depth, interior_height], dtype=float)
    if np.any(~np.isfinite(interior)) or np.any(interior < 0):
        raise HTTPException(400, "Invalid interior dimensions.")
    estimated = interior <= 0
    interior = np.where(estimated, mesh.extents * 0.85, interior)
    scale = target / interior
    if mode == "uniform":
        scale[:] = max(scale)
    elif mode != "xyz":
        raise HTTPException(400, "Unknown scaling mode.")
    if np.any(scale < 0.2) or np.any(scale > 5):
        raise HTTPException(400, "Scale outside 20%-500%. Check dimensions and units.")
    mesh.apply_transform(np.diag([*scale, 1]))
    data = mesh.export(file_type="stl")
    info = dict(target_cavity_mm=target.tolist(), scale_xyz=scale.tolist(), estimated_interior=bool(np.any(estimated)))
    return StreamingResponse(BytesIO(data), media_type="model/stl", headers={
        "Content-Disposition": 'attachment; filename="helmet_fitted.stl"',
        "X-Fit-Info": json.dumps(info, separators=(",", ":")),
        "Access-Control-Expose-Headers": "X-Fit-Info",
    })

@app.post("/comfort-kit")
async def comfort_kit(
    head_width: float = Form(...), head_depth: float = Form(...), head_height: float = Form(...),
    clearance: float = Form(2),
    pad_front: float = Form(8), pad_back: float = Form(8),
    pad_left: float = Form(8), pad_right: float = Form(8), pad_crown: float = Form(8),
    pad_width: float = Form(65), pad_height: float = Form(35),
    crown_width: float = Form(65), crown_depth: float = Form(65), material: str = Form("foam")
):
    pads = dict(front=pad_front, back=pad_back, left=pad_left, right=pad_right, crown=pad_crown)
    try:
        archive, _ = create_kit([head_width, head_depth, head_height], pads, clearance,
                                pad_width, pad_height, crown_width, crown_depth, material)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return StreamingResponse(archive, media_type="application/zip", headers={
        "Content-Disposition": 'attachment; filename="comfort_fit_kit.zip"'
    })
