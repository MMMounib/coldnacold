"""Rendu headless d'une animation Blender en PNG transparents (flipbook pour pcfforge).

Usage :
  blender -b scene.blend -P blender/flipbook.py -- --out art/nom --size 256 --frames 16
  blender -b -P blender/flipbook.py -- --demo petal --out art/petale --size 256 --frames 4
Options : --out DOSSIER  --size PX  --frames N  --demo petal|shard  --samples 32
La caméra orthographique est placée automatiquement face au sujet (axe -Y), cadrage sur la boîte englobante.
NOTE : script non testé dans l'environnement de génération (pas de Blender) — valider au 1er usage.
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
OUT = os.path.abspath(opt('--out', 'art/flipbook')); SIZE = int(opt('--size', 256))
FRAMES = int(opt('--frames', 16)); DEMO = opt('--demo'); SAMPLES = int(opt('--samples', 32))
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene

def demo(kind):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    if kind == 'shard':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        ob = bpy.context.object; ob.scale = (1, .6, .8)
    else:   # pétale : plan courbé
        bpy.ops.mesh.primitive_plane_add(size=2); ob = bpy.context.object
        bpy.ops.object.modifier_add(type='SUBSURF'); ob.modifiers[-1].levels = 3
        ob.scale = (.45, 1, 1); ob.rotation_euler = (math.radians(70), 0, 0)
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM'); ob.modifiers[-1].deform_method = 'BEND'; ob.modifiers[-1].angle = .8
    mat = bpy.data.materials.new('mat'); mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.9, .88, .9, 1)
    ob.data.materials.append(mat)
    ob.animation_data_create(); ob.rotation_mode = 'XYZ'
    ob.keyframe_insert('rotation_euler', frame=1); ob.rotation_euler[2] += math.radians(360); ob.keyframe_insert('rotation_euler', frame=FRAMES + 1)
    bpy.ops.object.light_add(type='SUN', location=(2, -3, 4)); bpy.context.object.data.energy = 3
    sc.frame_start, sc.frame_end = 1, FRAMES

if DEMO: demo(DEMO)
# cadrage : boîte englobante de tous les objets maillés sur toutes les images
pts = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    for ob in sc.objects:
        if ob.type == 'MESH': pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
ctr = (mn + mx) / 2; ext = max(mx.x - mn.x, mx.z - mn.z) * 1.15
cam_data = bpy.data.cameras.new('fb_cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = ext
cam = bpy.data.objects.new('fb_cam', cam_data); sc.collection.objects.link(cam)
cam.location = ctr + Vector((0, -10, 0)); cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam
r = sc.render; r.resolution_x = r.resolution_y = SIZE; r.film_transparent = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
try: r.engine = 'BLENDER_EEVEE_NEXT'
except Exception: r.engine = 'BLENDER_EEVEE'
try: sc.eevee.taa_render_samples = SAMPLES
except Exception: pass
step = max(1, (sc.frame_end - sc.frame_start + 1) // FRAMES)
for i in range(FRAMES):
    sc.frame_set(sc.frame_start + i * step)
    r.filepath = os.path.join(OUT, f'frame_{i:03d}.png'); bpy.ops.render.render(write_still=True)
print(f'[flipbook] {FRAMES} images -> {OUT}')
