"""Minimal VTF writer/reader (ported from tools/pcfkit, validated in GMod on 28/09/2026) (uncompressed BGRA8888 with a full mip chain).

Uncompressed is larger than DXT5 but needs no external compressor and keeps the
soft gradients of energy textures free of block artefacts.

Two layouts:
  - 7.2 (plain texture): header + image data, as before;
  - 7.4 with resources, for ANIMATED SHEETS (SpriteCard sequences): a DXT1 16x16 thumbnail (0x01),
    the sheet (0x10: [uint32 size][sheet data]) and the image (0x30). Same layout as the animated
    VTFs already installed in GMod (addons/arkaia_particules: eau3, fire, doi_thinsmoke).

Sheet data (version 1, as read by Source's CSheet):
  int32 version=1, int32 sequence count, then per sequence:
    int32 number, int32 clamp (1 = play once and hold the last frame, 0 = loop), int32 frame count,
    float total time, then per frame: float duration, 4 x (float u0, v0, u1, v1) (image 0, then 3 unused).
"""
import struct

import numpy as np

IMAGE_FORMAT_BGRA8888 = 12
IMAGE_FORMAT_DXT1 = 13
FLAG_CLAMPS, FLAG_CLAMPT, FLAG_NOLOD, FLAG_EIGHTBITALPHA = 0x4, 0x8, 0x200, 0x2000
HEADER_SIZE = 80
RSRC_LOWRES, RSRC_SHEET, RSRC_HIGHRES = b'\x01\x00\x00', b'\x10\x00\x00', b'\x30\x00\x00'


def _mips(rgba):
    levels = [rgba.astype(np.float32)]
    while levels[-1].shape[0] > 1 or levels[-1].shape[1] > 1:
        a = levels[-1]
        h, w = max(1, a.shape[0] // 2), max(1, a.shape[1] // 2)
        a = a[:h * 2 if a.shape[0] > 1 else 1, :w * 2 if a.shape[1] > 1 else 1]
        a = a.reshape(h, a.shape[0] // h, w, a.shape[1] // w, 4).mean(axis=(1, 3))
        levels.append(a)
    return levels


def _header(version, w, h, flags, levels, lowres=(0xFFFFFFFF, 0, 0), header_size=HEADER_SIZE, resources=0):
    avg = levels[-1][0, 0, :3] / 255.0
    hdr = struct.pack('<4s2II2HI2H4x3f4xfIBIBBH', b'VTF\0', 7, version, header_size, w, h, flags, 1, 0,
                      float(avg[0]), float(avg[1]), float(avg[2]), 1.0, IMAGE_FORMAT_BGRA8888,
                      len(levels), lowres[0], lowres[1], lowres[2], 1)
    if version >= 3:
        hdr += b'\0' * 3 + struct.pack('<I', resources)
    return hdr + b'\0' * (HEADER_SIZE - len(hdr))


def _body(levels):
    body = b''
    for lvl in reversed(levels):  # smallest mip first
        px = np.clip(np.round(lvl), 0, 255).astype(np.uint8)
        body += px[..., [2, 1, 0, 3]].tobytes()
    return body


def _check_pow2(h, w):
    for n in (h, w):
        if n & (n - 1):
            raise ValueError('VTF dimensions must be powers of two')


def _flags(clamp_s, clamp_t):
    return FLAG_EIGHTBITALPHA | FLAG_NOLOD | (FLAG_CLAMPS if clamp_s else 0) | (FLAG_CLAMPT if clamp_t else 0)


def write(path, rgba, clamp_s=True, clamp_t=True):
    """rgba: uint8 array (H, W, 4), H and W powers of two."""
    h, w = rgba.shape[:2]
    _check_pow2(h, w)
    levels = _mips(rgba)
    with open(path, 'wb') as fh:
        fh.write(_header(2, w, h, _flags(clamp_s, clamp_t), levels) + _body(levels))


def _dxt1_thumbnail(levels):
    """16x16 (or smaller) DXT1 thumbnail: every 4x4 block is the flat average colour (RGB565)."""
    lvl = next(l for l in levels if max(l.shape[:2]) <= 16)
    th, tw = lvl.shape[:2]
    bh, bw = max(1, th // 4), max(1, tw // 4)
    out = b''
    for by in range(bh):
        for bx in range(bw):
            c = lvl[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4, :3].reshape(-1, 3).mean(0)
            r, g, b = (int(round(c[0] * 31 / 255)), int(round(c[1] * 63 / 255)), int(round(c[2] * 31 / 255)))
            c565 = (r << 11) | (g << 5) | b
            out += struct.pack('<HHI', c565, c565, 0)
    return (IMAGE_FORMAT_DXT1, bw * 4, bh * 4), out


def sheet_bytes(sequences):
    """sequences: list of (frames, clamp) with frames = list of (u0, v0, u1, v1) rects, 1 time unit each."""
    out = struct.pack('<2i', 1, len(sequences))
    for n, (rects, clamp) in enumerate(sequences):
        out += struct.pack('<3if', n, int(bool(clamp)), len(rects), float(len(rects)))
        for r in rects:
            out += struct.pack('<f4f', 1.0, *r) + b'\0' * 48
    return out


def write_sheet(path, rgba, sequences, clamp_s=True, clamp_t=True):
    """Animated sheet VTF (7.4 + resources). sequences: see sheet_bytes."""
    h, w = rgba.shape[:2]
    _check_pow2(h, w)
    levels = _mips(rgba)
    lowres, thumb = _dxt1_thumbnail(levels)
    sheet = sheet_bytes(sequences)
    hsize = HEADER_SIZE + 3 * 8
    off_thumb = hsize
    off_sheet = off_thumb + len(thumb)
    off_image = off_sheet + 4 + len(sheet)
    hdr = _header(4, w, h, _flags(clamp_s, clamp_t), levels, lowres, hsize, 3)
    hdr += RSRC_LOWRES + b'\0' + struct.pack('<I', off_thumb)
    hdr += RSRC_SHEET + b'\0' + struct.pack('<I', off_sheet)
    hdr += RSRC_HIGHRES + b'\0' + struct.pack('<I', off_image)
    with open(path, 'wb') as fh:
        fh.write(hdr + thumb + struct.pack('<I', len(sheet)) + sheet + _body(levels))


def parse_sheet(data):
    """Sheet resource data -> list of (clamp, [(duration, (u0, v0, u1, v1)), ...])."""
    ver, count = struct.unpack_from('<2i', data, 0)
    per = 4 if ver else 1
    pos, seqs = 8, []
    for _ in range(count):
        _n, clamp, frames, _total = struct.unpack_from('<3if', data, pos)
        pos += 16
        fr = []
        for _f in range(frames):
            dur = struct.unpack_from('<f', data, pos)[0]
            fr.append((dur, struct.unpack_from('<4f', data, pos + 4)))
            pos += 4 + 16 * per
        seqs.append((clamp, fr))
    if pos != len(data):
        raise ValueError(f'sheet: parsed {pos} of {len(data)} bytes')
    return seqs


def read(path):
    """Return (rgba uint8 array of the top mip, info dict). Only BGRA8888 is supported.
    info['sheet'] holds the parsed sheet of an animated VTF (None otherwise)."""
    data = open(path, 'rb').read()
    sig, vmaj, vmin, hsize, w, h, flags, frames, _first = struct.unpack_from('<4s2II2HI2H', data, 0)
    if sig != b'VTF\0':
        raise ValueError(f'{path}: not a VTF')
    (fmt, mips, lowfmt) = struct.unpack_from('<IBI', data, 52)
    if fmt != IMAGE_FORMAT_BGRA8888:
        raise ValueError(f'{path}: format {fmt} not supported by this reader')
    size = sum(max(1, w >> i) * max(1, h >> i) * 4 for i in range(mips))
    sheet = None
    if vmin >= 3:
        nres = struct.unpack_from('<I', data, 68)[0]
        res = {data[80 + 8 * i:83 + 8 * i]: struct.unpack_from('<I', data, 84 + 8 * i)[0] for i in range(nres)}
        if RSRC_HIGHRES not in res:
            raise ValueError(f'{path}: no image resource')
        end = res[RSRC_HIGHRES] + size
        if RSRC_SHEET in res:
            o = res[RSRC_SHEET]
            n = struct.unpack_from('<I', data, o)[0]
            sheet = parse_sheet(data[o + 4:o + 4 + n])
    else:
        end = hsize + size
    if len(data) != end:
        raise ValueError(f'{path}: size mismatch ({len(data)} != {end})')
    top = np.frombuffer(data[end - w * h * 4:end], np.uint8).reshape(h, w, 4)[..., [2, 1, 0, 3]]
    return top.copy(), {'version': f'{vmaj}.{vmin}', 'width': w, 'height': h, 'flags': flags,
                        'mips': mips, 'bytes': len(data), 'sheet': sheet}
