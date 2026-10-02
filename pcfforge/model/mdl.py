"""Reader for Source .mdl (studiohdr_t, versions 44-49) and .vvd (vertex data).

Reads only what particle placement needs: name, hull bounds, bones (name, parent, bind pose,
poseToBone matrix), attachments, hitboxes, and vertex positions with their main bone.
Layouts follow Valve's public studio.h. Nothing is guessed: an unsupported file raises an error.
"""
import os
import struct
from dataclasses import dataclass, field

BONE_SIZE = 216
ATTACHMENT_SIZE = 92
HITBOX_SIZE = 68
VVD_VERTEX_SIZE = 48


class ModelError(Exception):
    pass


@dataclass
class Bone:
    index: int
    name: str
    parent: int
    pos: tuple                 # bind pose position, relative to parent
    quat: tuple                # bind pose rotation (x, y, z, w), relative to parent
    pose_to_bone: tuple        # 3x4 row-major: model space -> bone space


@dataclass
class Attachment:
    name: str
    bone: int
    matrix: tuple              # 3x4 row-major, bone space


@dataclass
class Hitbox:
    set_name: str
    bone: int
    bbmin: tuple
    bbmax: tuple


@dataclass
class Model:
    path: str
    name: str
    version: int
    hull_min: tuple
    hull_max: tuple
    bones: list = field(default_factory=list)
    attachments: list = field(default_factory=list)
    hitboxes: list = field(default_factory=list)
    vertices: list = field(default_factory=list)     # [(x, y, z, bone_index)] in model space
    vvd_found: bool = False

    def bone_index(self, name):
        for b in self.bones:
            if b.name.lower() == name.lower():
                return b.index
        return -1


def _cstr(d, off):
    end = d.index(b'\0', off)
    return d[off:end].decode('latin-1')


def read(path):
    if not os.path.exists(path):
        raise ModelError(f'modèle introuvable : {path}')
    d = open(path, 'rb').read()
    if len(d) < 408 or d[:4] != b'IDST':
        raise ModelError(f'pas un fichier MDL Source : {path}')
    i32 = lambda o: struct.unpack_from('<i', d, o)[0]
    f32 = lambda o, n: struct.unpack_from(f'<{n}f', d, o)
    version = i32(4)
    if not 44 <= version <= 49:
        raise ModelError(f'version MDL non prise en charge : {version}')
    if i32(76) != len(d):
        raise ModelError('taille déclarée incohérente : fichier tronqué ou autre format')
    m = Model(path=path, name=d[12:76].split(b'\0')[0].decode('latin-1'), version=version,
              hull_min=f32(104, 3), hull_max=f32(116, 3))
    nb, bi = i32(156), i32(160)
    for b in range(nb):
        o = bi + BONE_SIZE * b
        m.bones.append(Bone(b, _cstr(d, o + i32(o)), i32(o + 4), f32(o + 32, 3), f32(o + 44, 4), f32(o + 96, 12)))
    nsets, si = i32(172), i32(176)
    for s in range(nsets):
        o = si + 12 * s
        set_name = _cstr(d, o + i32(o))
        for h in range(i32(o + 4)):
            q = o + i32(o + 8) + HITBOX_SIZE * h
            m.hitboxes.append(Hitbox(set_name, i32(q), f32(q + 8, 3), f32(q + 20, 3)))
    na, ai = i32(240), i32(244)
    for a in range(na):
        o = ai + ATTACHMENT_SIZE * a
        m.attachments.append(Attachment(_cstr(d, o + i32(o)), i32(o + 8), f32(o + 12, 12)))
    vvd = os.path.splitext(path)[0] + '.vvd'
    if os.path.exists(vvd):
        m.vertices = read_vvd(vvd)
        m.vvd_found = True
    return m


def read_vvd(path):
    d = open(path, 'rb').read()
    if d[:4] != b'IDSV':
        raise ModelError(f'pas un fichier VVD : {path}')
    n = struct.unpack_from('<i', d, 16)[0]              # LOD 0 vertex count
    start = struct.unpack_from('<i', d, 56)[0]          # vertexDataStart
    out = []
    for k in range(n):
        o = start + VVD_VERTEX_SIZE * k
        w = struct.unpack_from('<3f', d, o)
        bones = struct.unpack_from('<3B', d, o + 12)
        x, y, z = struct.unpack_from('<3f', d, o + 16)
        main = bones[max(range(3), key=lambda i: w[i])]
        out.append((x, y, z, main))
    return out
