"""Parametric approximate foam and TPU comfort spacers in millimetres."""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import math
import json
import numpy as np
import trimesh

def validate_fit(head, pads, gap):
    if any(not math.isfinite(x) or not 30 <= x <= 500 for x in head):
        raise ValueError("Head dimensions must be 30-500 mm.")
    if not math.isfinite(gap) or not 0 <= gap <= 30:
        raise ValueError("Clearance must be 0-30 mm.")
    if any(not math.isfinite(x) or not 0 <= x <= 35 for x in pads.values()):
        raise ValueError("Padding must be 0-35 mm.")
    return np.array([
        head[0] + pads["left"] + pads["right"] + 2 * gap,
        head[1] + pads["front"] + pads["back"] + 2 * gap,
        head[2] + pads["crown"] + 2 * gap,
    ], dtype=float)

def curved_pad(rx, ry, angle, width, thickness, height):
    radius = math.hypot(rx * math.sin(angle), ry * math.cos(angle))
    spread = min(math.radians(70), width / max(radius, 1))
    vertices = []
    sections = 36
    for t in np.linspace(angle - spread / 2, angle + spread / 2, sections):
        c, s = math.cos(t), math.sin(t)
        for r, z in [(1,-height/2),(1+thickness,-height/2),(1,height/2),(1+thickness,height/2)]:
            vertices.append([(rx+r)*c,(ry+r)*s,z])
    faces = []
    def quad(a,b,c,d):
        faces.extend([(a,b,c),(a,c,d)])
    for i in range(sections-1):
        a,b = 4*i,4*(i+1)
        quad(a,b,b+1,a+1)
        quad(a+2,a+3,b+3,b+2)
        quad(a,a+2,b+2,b)
        quad(a+1,b+1,b+3,a+3)
    quad(0,1,3,2)
    end=(sections-1)*4
    quad(end,end+2,end+3,end+1)
    return trimesh.Trimesh(vertices=vertices,faces=faces,process=True)

def svg_pad(name, w, h):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w+36}mm" height="{h+46}mm" viewBox="0 0 {w+36} {h+46}"><rect x="18" y="18" width="{w}" height="{h}" rx="6" fill="none" stroke="black" stroke-width="0.5"/><text x="18" y="{h+29}" font-size="5">{name}: {w} x {h} mm</text></svg>"""

def create_kit(head, pads, gap, pad_width=65, pad_height=35, crown_width=65, crown_depth=65, material="foam"):
    if material not in ("foam","tpu"):
        raise ValueError("Material must be foam or tpu.")
    if any(not math.isfinite(v) or not 15 <= v <= 160 for v in [pad_width,pad_height,crown_width,crown_depth]):
        raise ValueError("Pad dimensions must be 15-160 mm.")
    target = validate_fit(head,pads,gap)
    angles={"right":0,"front":math.pi/2,"left":math.pi,"back":-math.pi/2}
    metadata=dict(head_mm=head, padding_mm=pads, clearance_mm=gap, target_cavity_mm=target.tolist(),
                  material=material, warning="Approximate templates only; not fitted to actual helmet cavity.")
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as archive:
        for name in ("front","back","left","right","crown"):
            thickness=pads[name]
            if thickness <= 0:
                continue
            if name=="crown":
                mesh=trimesh.creation.box(extents=(crown_width,crown_depth,thickness))
                mesh.apply_translation([0,0,head[2]/2+thickness/2])
                width,height=crown_width,crown_depth
            else:
                width,height=pad_width,pad_height
                mesh=curved_pad(head[0]/2,head[1]/2,angles[name],width,thickness,height)
            archive.writestr(f"tpu_spacers/{name}_{thickness:g}mm.stl",mesh.export(file_type="stl"))
            archive.writestr(f"foam_templates/{name}_{thickness:g}mm.svg",svg_pad(name,width,height))
        archive.writestr("FIT_PROFILE.json",json.dumps(metadata,indent=2))
        archive.writestr("READ_ME_FIRST.txt","COSTUME USE ONLY. Cut foam templates at 100% scale. STL spacers are approximations and must be manually placed. Test fit carefully; do not block breathing, vision or ventilation. Not for protective helmets.")
    out.seek(0)
    return out,metadata
