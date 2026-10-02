"""Binary DMX v2 (PCF) writer laid out like Valve's particle editor output.

srctools writes a valid file the engine loads, but Lua PCF readers used by GMod particle tools expect the editor's
layout. Matched here (checked against references/1gonzo.pcf, written by the editor):
  - elements depth-first: root, then each system followed by its operators and its children's elements;
  - no `name` attribute (the element name lives in the header), root holds only `particleSystemDefinitions`;
  - system attributes in the editor's order; operators start with `functionName`;
  - string dictionary = element types + attribute names (uint16 count / indices), strings inline (v2).
"""
import struct
import uuid

from srctools.dmx import ValueType

HEADER = b'<!-- dmx encoding binary 2 format pcf 1 -->\n\0'
TYPE_ID = {ValueType.ELEMENT: 1, ValueType.INT: 2, ValueType.FLOAT: 3, ValueType.BOOL: 4, ValueType.STRING: 5,
           ValueType.BINARY: 6, ValueType.TIME: 7, ValueType.COLOR: 8, ValueType.VEC2: 9, ValueType.VEC3: 10,
           ValueType.VEC4: 11, ValueType.ANGLE: 12, ValueType.QUATERNION: 13, ValueType.MATRIX: 14}
SYSTEM_ORDER = ['renderers', 'operators', 'initializers', 'emitters', 'children', 'forces', 'constraints',
                'preventNameBasedLookup', 'max_particles', 'initial_particles', 'material', 'bounding_box_min',
                'bounding_box_max', 'cull_radius', 'cull_cost', 'cull_control_point', 'cull_replacement_definition',
                'radius', 'color', 'rotation', 'rotation_speed', 'normal', 'sequence_number', 'sequence_number 1',
                'group id', 'maximum time step', 'maximum sim tick rate', 'minimum sim tick rate',
                'minimum rendered frames', 'control point to disable rendering if it is the camera',
                'maximum draw distance', 'time to sleep when not drawn', 'Sort particles', 'batch particle systems',
                'view model effect', 'screen space effect']
DFS_LISTS = ('emitters', 'initializers', 'operators', 'renderers', 'forces', 'constraints', 'children')


def _attrs(el):
    """Attributes to write, in the editor's order, without `name`."""
    attrs = {a.name: a for a in el.values() if a.name.lower() != 'name'}
    if el.type == 'DmeParticleSystemDefinition':
        low = {k.lower(): k for k in attrs}
        first = [attrs[low[k.lower()]] for k in SYSTEM_ORDER if k.lower() in low]
        rest = [a for a in attrs.values() if a not in first]
        return first + rest
    if el.type == 'DmeParticleOperator':
        fn = [a for a in attrs.values() if a.name == 'functionName']
        return fn + [a for a in attrs.values() if a.name != 'functionName']
    return list(attrs.values())


def _order(root):
    """Depth-first element order: root, each system, its operators, its children (link + child system)."""
    order, seen = [], set()

    def visit(el):
        if id(el) in seen:
            return
        seen.add(id(el)); order.append(el)
        if el.type == 'DmeParticleSystemDefinition':
            for k in DFS_LISTS:
                if k in el:
                    for sub in el[k].iter_elem():
                        visit(sub)
                        if sub.type == 'DmeParticleChild' and 'child' in sub and sub['child'].val_elem is not None:
                            visit(sub['child'].val_elem)
        else:
            for a in el.values():
                if a.type == ValueType.ELEMENT:
                    for sub in (a.iter_elem() if a.is_array else [a.val_elem]):
                        if sub is not None:
                            visit(sub)
    visit(root)
    return order


def _value(a, index):
    t = a.type
    if t == ValueType.ELEMENT:
        e = a.val_elem
        return struct.pack('<i', index[id(e)] if e is not None else -1)
    if t == ValueType.INT:
        return struct.pack('<i', a.val_int)
    if t == ValueType.FLOAT:
        return struct.pack('<f', a.val_float)
    if t == ValueType.BOOL:
        return struct.pack('<B', 1 if a.val_bool else 0)
    if t == ValueType.STRING:
        return a.val_str.encode('utf-8') + b'\0'
    if t == ValueType.COLOR:
        c = a.val_color
        return struct.pack('<4B', int(c.r), int(c.g), int(c.b), int(c.a))
    if t == ValueType.VEC2:
        v = a.val_vec2
        return struct.pack('<2f', v.x, v.y)
    if t == ValueType.VEC3:
        v = a.val_vec3
        return struct.pack('<3f', v.x, v.y, v.z)
    if t == ValueType.VEC4:
        v = a.val_vec4
        return struct.pack('<4f', v.x, v.y, v.z, v.w)
    raise ValueError(f'type DMX non pris en charge : {t} ({a.name})')


def write(path, root):
    order = _order(root)
    index = {id(e): i for i, e in enumerate(order)}
    strings, sidx = [], {}

    def s(x):
        if x not in sidx:
            sidx[x] = len(strings); strings.append(x)
        return sidx[x]
    bodies = []
    for el in order:
        s(el.type)
        for a in _attrs(el):
            s(a.name)
    if len(strings) > 0xFFFF:
        raise ValueError('trop de chaînes pour DMX v2')
    out = [HEADER, struct.pack('<H', len(strings))] + [x.encode('utf-8') + b'\0' for x in strings]
    out.append(struct.pack('<i', len(order)))
    for el in order:
        out += [struct.pack('<H', s(el.type)), el.name.encode('utf-8') + b'\0', uuid.uuid4().bytes]
    for el in order:
        attrs = _attrs(el)
        body = [struct.pack('<i', len(attrs))]
        for a in attrs:
            tid = TYPE_ID[a.type]
            if a.is_array:
                if a.type != ValueType.ELEMENT:
                    raise ValueError(f'tableau non pris en charge : {a.name}')
                items = list(a.iter_elem())
                body.append(struct.pack('<HBi', s(a.name), tid + 14, len(items)))
                body += [struct.pack('<i', index[id(e)]) for e in items]
            else:
                body += [struct.pack('<HB', s(a.name), tid), _value(a, index)]
        bodies.append(b''.join(body))
    with open(path, 'wb') as f:
        f.write(b''.join(out) + b''.join(bodies))
