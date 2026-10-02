"""Model analysis: what the composer and the GMod runtime need from a real .mdl.

- bounds / dimensions (hull, and vertex bounds when the .vvd is present)
- bone hierarchy and bind-pose positions
- per-bone geometry in BONE space (vertices moved with the bone's poseToBone matrix)
- main axis of that geometry (PCA) -> a segment usable as CP0 -> CP1 (e.g. a blade)
- regions: a slice [start, end] of that segment, expressed as offsets in bone space so the runtime
  can follow the animated bone with ent:GetBoneMatrix().
"""
import numpy as np

from .mdl import read, ModelError

ATTACH_TYPES = ('entity', 'bone', 'attachment', 'region', 'bounds')


def _apply34(m, p):
    m = np.asarray(m, float).reshape(3, 4)
    return m[:, :3] @ np.asarray(p, float) + m[:, 3]


def bone_geometry(model, bone):
    """Vertices whose main bone is `bone`, in that bone's space. Empty array if none / no .vvd."""
    b = model.bones[bone]
    pts = [_apply34(b.pose_to_bone, v[:3]) for v in model.vertices if v[3] == bone]
    return np.array(pts) if pts else np.zeros((0, 3))


def main_axis(points):
    """(center, unit axis, [t_min, t_max]) of a point cloud along its longest direction."""
    c = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - c, full_matrices=False)
    ax = vt[0]
    t = (points - c) @ ax
    if abs(t.min()) > abs(t.max()):                     # point the axis towards the far end (the tip)
        ax, t = -ax, -t
    return c, ax, [float(np.percentile(t, 1)), float(np.percentile(t, 99))]


def segment(model, bone, start=0.0, end=1.0):
    """Segment along the bone's geometry (or its hitbox if there is no geometry), in bone space."""
    pts = bone_geometry(model, bone)
    source = 'vertices'
    if len(pts) < 8:
        hb = [h for h in model.hitboxes if h.bone == bone]
        if not hb:
            raise ModelError(f'os {model.bones[bone].name} : ni géométrie ni hitbox pour définir un segment')
        lo, hi = np.array(hb[0].bbmin), np.array(hb[0].bbmax)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        pts, source = corners, 'hitbox'
    c, ax, (t0, t1) = main_axis(pts)
    width = (pts - c) - np.outer((pts - c) @ ax, ax)
    radius = float(np.percentile(np.linalg.norm(width, axis=1), 90)) if len(pts) else 0.0
    a, b = t0 + (t1 - t0) * start, t0 + (t1 - t0) * end
    return dict(bone=model.bones[bone].name, source=source, start=(c + ax * a).round(3).tolist(),
                end=(c + ax * b).round(3).tolist(), length=round(float(b - a), 3), radius=round(radius, 3),
                axis=ax.round(4).tolist(), profile=profile(pts, c, ax, a, b))


def _hull_at(ts, ys, x):
    """Upper convex hull of points (ts, ys), evaluated at x (linear between hull vertices, clamped at the ends)."""
    key = np.round(ts, 2)
    ux = np.unique(key)
    uy = np.array([ys[key == k].max() for k in ux])          # one point per position along the axis
    hull = []
    for p in zip(ux, uy):
        while len(hull) >= 2 and ((hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1])
                                  - (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0])) >= 0:
            hull.pop()
        hull.append(p)
    return float(np.interp(x, [h[0] for h in hull], [h[1] for h in hull]))


def _hull_profile(t, w, z, c, ax, wd, th, a, b, xs, step):
    """Silhouette of low-poly geometry (few vertices per unit of length, e.g. a blade made of flat quads).

    Local windows fail there: an edge runs straight between two corner vertices that can be a whole slice apart,
    with only interior vertices (a ridge, a fuller) in between. The upper / lower edges are therefore the
    convex hull of all the region's vertices, which follows those straight edges exactly. Blades are convex in
    this sense; a concave notch would be bridged (dense models keep the per-slice method, which preserves it)."""
    lo_t, hi_t = a, b                                     # anchor on the nearest vertex column just outside
    if (t < a).any():                                     # each end, so an edge crossing the cut stays straight
        lo_t = t[t < a].max() - .3
    if (t > b).any():
        hi_t = t[t > b].min() + .3
    inside = (t >= lo_t) & (t <= hi_t)
    ts, ws, zs = t[inside], w[inside], z[inside]
    if len(ts) < 3:
        raise ModelError('silhouette : moins de 3 sommets dans la région')
    out = []
    for i, x in enumerate(xs):
        hi, lo = _hull_at(ts, ws, x), -_hull_at(ts, -ws, x)
        near = np.abs(ts - x) <= step * 1.5
        zf, zb = (float(zs[near].max()), float(zs[near].min())) if near.any() else (float(zs.max()), float(zs.min()))
        mid = (hi + lo) / 2
        pt = lambda y, zz=(zf + zb) / 2: (c + ax * x + wd * y + th * zz).round(3).tolist()
        out.append(dict(t=round((x - a) / max(b - a, 1e-6), 3), center=pt(mid), upper=pt(hi), lower=pt(lo),
                        front=pt(mid, zf), back=pt(mid, zb), half_width=round((hi - lo) / 2, 3),
                        thickness=round(zf - zb, 3), measured=True))
    return dict(width_axis=wd.round(4).tolist(), thickness_axis=th.round(4).tolist(), slices=out, method='hull')


def profile(pts, c, ax, a, b, slices=8):
    """Silhouette of the geometry between a and b along the axis, in its widest plane (e.g. a flat blade).

    Returns the plane's width axis and, per slice, the centre / upper / lower points (bone space). The
    composer scales it into an envelope and the runtime turns it into a chain of control points.
    """
    rel = pts - c
    t = rel @ ax
    flat = rel - np.outer(t, ax)
    _, _, vt = np.linalg.svd(flat, full_matrices=False)
    wd = vt[0]                                           # width direction
    th = np.cross(ax, wd)                                # thickness direction (normal of the blade's faces)
    w = rel @ wd
    z = rel @ th
    step = (b - a) / slices
    xs = [a + step * i for i in range(slices + 1)]
    inside = (t >= a) & (t <= b)
    if inside.sum() / max(b - a, 1e-6) < 8:              # low-poly (flat quads): edges are straight between
        return _hull_profile(t, w, z, c, ax, wd, th, a, b, xs, step)   # corner vertices -> local convex hull
    ext = []
    for i, x in enumerate(xs):
        # the ends only look inside the region: a guard or a handle just outside must not widen the silhouette
        lo_w = 0 if i == 0 else step * .6
        hi_w = 0 if i == slices else step * .6
        sel = (t >= x - lo_w) & (t <= x + hi_w)
        ext.append((float(w[sel].max()), float(w[sel].min()), float(z[sel].max()), float(z[sel].min()))
                   if sel.sum() >= 3 else None)
    # low-poly parts (e.g. a flat blade quad): a slice without geometry is interpolated between the nearest
    # vertex groups on each side along the axis (mesh edges are straight between vertices). Those groups may lie
    # just outside the region, but they are never merged into a slice: they only anchor the interpolation.
    known = [i for i, e in enumerate(ext) if e]
    if not any(ext) and len(t) < 3:
        raise ModelError('silhouette : aucune tranche ne contient de géométrie')
    bw = step / 3
    edges = np.arange(t.min(), t.max() + bw, bw)
    bins = []
    for k in range(len(edges) - 1):
        m = (t >= edges[k]) & (t < edges[k + 1])
        if m.sum() >= 2:
            bins.append((float(t[m].mean()), (float(w[m].max()), float(w[m].min()), float(z[m].max()), float(z[m].min()))))
    for i, e in enumerate(ext):
        if e is None:
            x = xs[i]
            left = [bn for bn in bins if bn[0] <= x]
            right = [bn for bn in bins if bn[0] > x]
            if left and right:
                (tl, el), (tr, er) = left[-1], right[0]
                f = (x - tl) / max(tr - tl, 1e-6)
                ext[i] = tuple(el[j] * (1 - f) + er[j] * f for j in range(4))
            else:
                ext[i] = (left[-1] if left else right[0])[1]
    out = []
    for i, (x, (hi, lo, zf, zb)) in enumerate(zip(xs, ext)):
        mid = (hi + lo) / 2
        pt = lambda y, zz=(zf + zb) / 2: (c + ax * x + wd * y + th * zz).round(3).tolist()
        out.append(dict(t=round((x - a) / max(b - a, 1e-6), 3), center=pt(mid), upper=pt(hi), lower=pt(lo),
                        front=pt(mid, zf), back=pt(mid, zb), half_width=round((hi - lo) / 2, 3),
                        thickness=round(zf - zb, 3), measured=i in known))
    return dict(width_axis=wd.round(4).tolist(), thickness_axis=th.round(4).tolist(), slices=out)


def region(model, rdef):
    """rdef: {bone: name} or {hitbox_bone: name}, optional start / end fractions (0..1)."""
    name = rdef.get('bone') or rdef.get('hitbox_bone')
    if not name:
        raise ModelError('région : il faut bone ou hitbox_bone')
    idx = model.bone_index(name)
    if idx < 0:
        raise ModelError(f"os introuvable : {name!r} (os du modèle : {', '.join(b.name for b in model.bones)})")
    start, end = float(rdef.get('start', 0.0)), float(rdef.get('end', 1.0))
    if not 0 <= start < end <= 1:
        raise ModelError('région : il faut 0 <= start < end <= 1')
    return segment(model, idx, start, end)


def summary(model):
    verts = np.array([v[:3] for v in model.vertices]) if model.vertices else None
    lo, hi = (verts.min(0), verts.max(0)) if verts is not None else (np.array(model.hull_min), np.array(model.hull_max))
    return dict(path=model.path, name=model.name, version=model.version,
                bounds=dict(min=lo.round(3).tolist(), max=hi.round(3).tolist(), size=(hi - lo).round(3).tolist(),
                            center=((lo + hi) / 2).round(3).tolist(), source='vvd' if verts is not None else 'hull'),
                bones=[dict(index=b.index, name=b.name, parent=b.parent) for b in model.bones],
                attachments=[dict(name=a.name, bone=model.bones[a.bone].name if 0 <= a.bone < len(model.bones) else a.bone,
                                  origin=[round(a.matrix[3], 3), round(a.matrix[7], 3), round(a.matrix[11], 3)])
                             for a in model.attachments],
                hitboxes=[dict(set=h.set_name, bone=model.bones[h.bone].name, min=list(h.bbmin), max=list(h.bbmax))
                          for h in model.hitboxes],
                vertices=len(model.vertices))


def resolve(model_path, attachment, regions):
    """Checks an attachment against a real model and returns what the composer/runtime need."""
    m = read(model_path)
    t = attachment.get('type', 'entity')
    info = dict(model=summary(m), type=t)
    if t == 'bone':
        idx = m.bone_index(attachment['name'])
        if idx < 0:
            raise ModelError(f"os introuvable : {attachment['name']!r} (os : {', '.join(b.name for b in m.bones)})")
        info['segment'] = segment(m, idx)
    elif t == 'attachment':
        names = [a.name for a in m.attachments]
        if attachment['name'] not in names:
            raise ModelError(f"attachment introuvable : {attachment['name']!r} (attachments : {names or 'aucun'})")
    elif t == 'region':
        rname = attachment['name']
        if rname not in (regions or {}):
            raise ModelError(f'région non définie : {rname!r}')
        info['segment'] = region(m, regions[rname])
    return info
