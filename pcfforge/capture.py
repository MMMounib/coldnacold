"""Captures d'aperçu UNIQUEMENT depuis Garry's Mod (aucun simulateur).

1. build de la spec ; 2. installe l'addon de l'effet + l'outil local `pcfforge_capture` ;
3. écrit garrysmod/data/pcfforge/job.json ; 4. lance GMod (gm_flatgrass, fenêtré) ;
5. attend done.json ; 6. récupère les images -> out/captures/<prefix>/ (planche + vidéo si demandée) ;
7. ferme GMod (sauf --keep-open).
"""
import os, json, time, shutil, glob, subprocess, platform, math
from PIL import Image, ImageDraw
from . import build as B, layers as SP

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, '..', 'gmod', 'pcfforge_capture')

def _cps(e):
    out = []
    for i in range(8):
        k = f'cp{i}'
        if k in e: out.append({'i': i, 'p': e[k]})
    if not any(c['i'] == 0 for c in out): out.insert(0, {'i': 0, 'p': [0, 0, 0]})
    return out

def extent(spec):
    R = 60
    for sdef in spec['systems'].values():
        for raw in (sdef['layers'] if isinstance(sdef, dict) else sdef):
            L = dict(SP.P.get(raw.get('preset'), {})); L.update(raw)
            sp = SP._pair(L.get('spread'), [0, 0])[1]; sz = SP._pair(L.get('size'), [0, 0])[1]
            R = max(R, sp, sz * (L.get('grow') or [1, 1])[1], L.get('radius', 0))
    return R

def make_job(spec, P, video):
    pv = spec.get('preview', {}); pre = spec['prefix']
    evs = []
    for e in pv.get('events', [{'t': .5, 'system': list(spec['systems'])[0]}]):
        if 'kill' in e or 'stop' in e:
            k = 'kill' if 'kill' in e else 'stop'; evs.append({'t': e['t'] + 1.0, k: f"{pre}_{e[k]}"}); continue
        ev = {'t': e['t'] + 1.0, 'system': f"{pre}_{e['system']}", 'cps': _cps(e), 'fwd': e.get('fwd', [1, 0, 0])}
        for c in ev['cps']:                              # décale aussi les trajectoires (1 s de marge au début)
            if isinstance(c['p'], dict):
                c['p'] = dict(c['p']); c['p']['t0'] = c['p'].get('t0', 0) + 1.0; c['p']['t1'] = c['p'].get('t1', 1) + 1.0
        if 'actor' in e: ev['actor'] = e['actor'] + 1       # Lua indexe à partir de 1
        evs.append(ev)
    R = extent(spec); dur = pv.get('duration', 3.0) + 1.0
    cam_w = pv.get('camera') or dict(pos=[R * .9, -R * 2.6, R * .9 + 60], look=[0, 0, min(R * .25, 80)], fov=55)
    cam_c = pv.get('camera_close') or dict(pos=[R * .5, -R * 1.3, R * .4 + 45], look=[0, 0, min(R * .2, 60)], fov=50)
    if pv.get('shots'): shots = [(n, float(t)) for n, t in pv['shots']]
    else: shots = [(n, f * (dur - 1.0)) for n, f in (('debut', .12), ('montee', .3), ('pic', .5), ('fin', .8))]
    shots = sorted(shots, key=lambda s: s[1])
    phases = [{'mode': 'shots', 'fps': 60, 'events': evs,
               'shots': [{'name': f'{i + 1}_{n}', 't': t + 1.0, 'cam': cam_c if i == 2 else cam_w} for i, (n, t) in enumerate(shots)]}]
    if video: phases.append({'mode': 'video', 'fps': 30, 'events': evs, 'duration': dur, 'cam': cam_w})
    return {'status': 'pending', 'pcf': [f"particles/{os.path.basename(P['pcf'])}"],
            'precache': [f"{pre}_{k}" for k in spec['systems']], 'actors': pv.get('actors', [[0, 0, 0]]),
            'actor_model': pv.get('actor_model', 'models/player/kleiner.mdl'), 'warmup': 4, 'phases': phases}

def _kill_gmod():
    if platform.system() == 'Windows':
        for exe in ('gmod.exe', 'hl2.exe'):
            subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)

def _running():
    if platform.system() != 'Windows': return False
    out = subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower()
    return 'gmod.exe' in out or 'hl2.exe' in out

def capture(spec_path, gmod=None, video=False, keep_open=False, timeout=300, map_name='gm_flatgrass'):
    from .__main__ import find_gmod
    spec, P, tex, rep = B.build(spec_path)
    print(B.summary(rep))
    if rep['errors']: return None
    gm = gmod or find_gmod()
    if not gm:
        print('Garry\'s Mod introuvable : relancer avec --gmod "<...>/GarrysMod/garrysmod". Aucune image produite '
              '(les aperçus ne viennent QUE du moteur).')
        return None
    # 1. installation effet + outil de capture
    dst = os.path.join(gm, 'addons', os.path.basename(P['addon']))
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(P['addon'], dst)
    hdst = os.path.join(gm, 'addons', 'pcfforge_capture')
    shutil.rmtree(hdst, ignore_errors=True); shutil.copytree(HARNESS, hdst)
    # 2. job
    data = os.path.join(gm, 'data', 'pcfforge'); os.makedirs(data, exist_ok=True)
    for f in ('done.json',): 
        if os.path.exists(os.path.join(data, f)): os.remove(os.path.join(data, f))
    shutil.rmtree(os.path.join(data, 'out'), ignore_errors=True)
    json.dump(make_job(spec, P, video), open(os.path.join(data, 'job.json'), 'w'), indent=1)
    # 3. lancement (Steam doit être ouvert ; il demande de confirmer les options)
    if _running():
        print('Garry\'s Mod est déjà ouvert : il faut le fermer (le PCF n\'est rechargé qu\'au démarrage).'); _kill_gmod(); time.sleep(3)
    args = f'-windowed -w 1280 -h 720 -novid -noworkshop +sv_cheats 1 +map {map_name}'
    if platform.system() == 'Windows': os.startfile(f'steam://run/4000//{args}/')
    else: subprocess.Popen(['xdg-open', f'steam://run/4000//{args}/'])
    print(f'GMod lancé ({args}). Accepter la fenêtre Steam des options de lancement si elle apparaît. Attente des captures…')
    t_end = time.time() + timeout
    while time.time() < t_end and not os.path.exists(os.path.join(data, 'done.json')): time.sleep(2)
    if not os.path.exists(os.path.join(data, 'done.json')):
        log = open(os.path.join(data, 'log.txt'), errors='ignore').read() if os.path.exists(os.path.join(data, 'log.txt')) else '(pas de log)'
        print(f'Délai dépassé ({timeout} s). Journal GMod :\n{log[-1500:]}\nVérifier que GMod est fermé avant la capture, puis relancer.')
        return None
    time.sleep(1); report = json.load(open(os.path.join(data, 'done.json'), encoding='utf-8', errors='ignore'))
    if not keep_open: _kill_gmod()
    # 4. récupération
    os.makedirs(P['prev'], exist_ok=True)
    shots = sorted(glob.glob(os.path.join(data, 'out', '*.jpg')))
    for f in shots: shutil.copy(f, P['prev'])
    res = {'shots': [os.path.join(P['prev'], os.path.basename(f)) for f in shots], 'engine_report': report}
    if shots:
        ims = [Image.open(f) for f in shots]; tw, th = 640, 360; cols = 2; rows = (len(ims) + 1) // 2
        sheet = Image.new('RGB', (tw * cols, th * rows)); d = ImageDraw.Draw(sheet)
        for i, (im, f) in enumerate(zip(ims, shots)):
            x, y = (i % cols) * tw, (i // cols) * th; sheet.paste(im.resize((tw, th)), (x, y))
            d.rectangle([x, y, x + 220, y + 20], fill=(0, 0, 0)); d.text((x + 5, y + 4), os.path.basename(f)[:-4], fill=(255, 255, 255))
        sheet.save(os.path.join(P['prev'], 'planche.jpg'), quality=90)
        sheet.resize((tw, th * rows // 2)).save(os.path.join(P['prev'], 'planche_small.jpg'), quality=85)
        res['sheet_small'] = os.path.join(P['prev'], 'planche_small.jpg')
    frames = sorted(glob.glob(os.path.join(data, 'out', 'frames', '*.jpg')))
    if frames and shutil.which('ffmpeg'):
        mp4 = os.path.join(P['prev'], spec['prefix'] + '.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', os.path.join(data, 'out', 'frames', '%05d.jpg'),
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', mp4])
        res['video'] = mp4
    return res

def remove_harness(gmod=None):
    from .__main__ import find_gmod
    gm = gmod or find_gmod()
    if gm:
        shutil.rmtree(os.path.join(gm, 'addons', 'pcfforge_capture'), ignore_errors=True)
        print('Outil de capture retiré de', gm)
