--[[ pcfforge_capture — OUTIL LOCAL DE PRÉVISUALISATION (ne JAMAIS mettre sur un serveur de jeu)
Lit garrysmod/data/pcfforge/job.json (écrit par `python -m pcfforge capture`), joue les effets dans le vrai
moteur, place la caméra, capture des images (render.Capture) dans garrysmod/data/pcfforge/out/, puis écrit done.json.
Coordonnées du job : relatives au sol sous le point d'apparition du joueur.
Ne fait rien si aucun job "pending" n'existe.  ]]
AddCSLuaFile()
local JOBF = "pcfforge/job.json"
local job = file.Exists(JOBF, "DATA") and util.JSONToTable(file.Read(JOBF, "DATA") or "") or nil
if not job or job.status ~= "pending" then return end
for _, p in ipairs(job.pcf or {}) do game.AddParticles(p) end
for _, s in ipairs(job.precache or {}) do PrecacheParticleSystem(s) end
if SERVER then return end

local function log(m) file.Append("pcfforge/log.txt", os.date("%H:%M:%S ") .. tostring(m) .. "\n") end
local function V(t) return Vector(t[1] or 0, t[2] or 0, t[3] or 0) end
file.CreateDir("pcfforge/out"); file.CreateDir("pcfforge/out/frames")
file.Write("pcfforge/log.txt", "")

local base, phase, phaseIdx, t0, effects, actors, shotIdx, frame, cam, capturePath
local phases = job.phases or {}
local done = false
local report = { shots = {}, frames = 0, fps_min = 999, fps_sum = 0, fps_n = 0, errors = {} }

local function cpPos(cp, t)
  if cp.from then
    local u = math.Clamp((t - (cp.t0 or 0)) / math.max((cp.t1 or 1) - (cp.t0 or 0), 0.001), 0, 1)
    local p = LerpVector(u, V(cp.from), V(cp.to)); p.z = p.z + (cp.arc or 0) * math.sin(math.pi * u)
    return base + p
  end
  return base + V(cp)
end

local function clearScene()
  for _, e in pairs(effects or {}) do if IsValid(e.fx) then e.fx:StopEmissionAndDestroyImmediately() end end
  effects = {}
end

local function spawnActors()
  for _, a in ipairs(actors or {}) do if IsValid(a) then a:Remove() end end
  actors = {}
  for i, a in ipairs(job.actors or {}) do
    local m = ClientsideModel(job.actor_model or "models/player/kleiner.mdl")
    if IsValid(m) then
      m:SetPos(base + V(a)); m:SetAngles(Angle(0, (a[4] or 90), 0))
      local seq = m:LookupSequence("idle_all_01"); if seq and seq > 0 then m:ResetSequence(seq) end
      actors[i] = m
    end
  end
end

local function startPhase(i)
  phaseIdx = i; phase = phases[i]
  if not phase then
    done = true; RunConsoleCommand("host_framerate", "0")
    report.fps_avg = report.fps_n > 0 and report.fps_sum / report.fps_n or 0
    file.Write("pcfforge/done.json", util.TableToJSON(report, true))
    job.status = "done"; file.Write(JOBF, util.TableToJSON(job, true)); log("terminé")
    return
  end
  clearScene(); spawnActors()
  RunConsoleCommand("host_framerate", tostring(1 / (phase.fps or 30)))
  t0 = nil; shotIdx = 1; frame = 0; log("phase " .. i .. " : " .. (phase.mode or "?"))
end

local function camFor(c)
  local pos, look = base + V(c.pos), base + V(c.look)
  return { origin = pos, angles = (look - pos):Angle(), fov = c.fov or 55 }
end

-- démarrage : attendre que le joueur soit prêt, puis 3 s de chargement
hook.Add("InitPostEntity", "pcfforge_capture", function()
  timer.Simple(job.warmup or 3, function()
    local ply = LocalPlayer()
    local tr = util.TraceLine({ start = ply:GetPos() + Vector(0, 0, 10), endpos = ply:GetPos() - Vector(0, 0, 500), filter = ply })
    base = tr.HitPos; log("origine : " .. tostring(base))
    startPhase(1)
  end)
end)

hook.Add("Think", "pcfforge_capture", function()
  if done or not phase or not base then return end
  if not t0 then t0 = CurTime() end
  local t = CurTime() - t0
  for k, ev in ipairs(phase.events or job.events or {}) do
    local key = phaseIdx .. ":" .. k
    if not effects[key] and t >= ev.t then
      if ev.system then
        local fx
        local c0 = { 0, 0, 0 }
        for _, c in ipairs(ev.cps or {}) do if c.i == 0 then c0 = c.p end end
        local p0 = cpPos(c0, t)
        if ev.actor and actors[ev.actor] then
          fx = CreateParticleSystem(actors[ev.actor], ev.system, PATTACH_ABSORIGIN_FOLLOW, 0, Vector(0, 0, 0))
        else
          fx = CreateParticleSystemNoEntity(ev.system, p0, V(ev.fwd or { 1, 0, 0 }):Angle())
        end
        if IsValid(fx) then effects[key] = { fx = fx, ev = ev } else
          table.insert(report.errors, "échec création " .. ev.system); effects[key] = { ev = ev } end
      elseif ev.kill or ev.stop then
        for _, e in pairs(effects) do
          if e.ev.system == (ev.kill or ev.stop) and IsValid(e.fx) then
            if ev.kill then e.fx:StopEmissionAndDestroyImmediately() else e.fx:StopEmission() end
          end
        end
        effects[key] = { ev = ev }
      end
    end
  end
  for _, e in pairs(effects) do          -- points de contrôle mobiles
    if IsValid(e.fx) and e.ev.cps and not e.ev.actor then
      for _, c in ipairs(e.ev.cps) do e.fx:SetControlPoint(c.i, cpPos(c.p, t)) end
    end
  end
  local rft = RealFrameTime(); if rft > 0 then local f = 1 / rft
    report.fps_min = math.min(report.fps_min, f); report.fps_sum = report.fps_sum + f; report.fps_n = report.fps_n + 1 end
  -- que capturer à ce rendu ?
  capturePath = nil
  if phase.mode == "shots" then
    local s = phase.shots[shotIdx]
    if s then cam = camFor(s.cam); if t >= s.t then capturePath = "pcfforge/out/" .. s.name .. ".jpg" end
    else startPhase(phaseIdx + 1) end
  elseif phase.mode == "video" then
    cam = camFor(phase.cam)
    if t <= phase.duration then capturePath = string.format("pcfforge/out/frames/%05d.jpg", frame) else startPhase(phaseIdx + 1) end
  end
end)

hook.Add("CalcView", "pcfforge_capture", function(ply, pos, ang, fov)
  if done or not cam then return end
  return { origin = cam.origin, angles = cam.angles, fov = cam.fov, drawviewer = false }
end)
hook.Add("HUDShouldDraw", "pcfforge_capture", function() if not done then return false end end)
hook.Add("PreDrawViewModel", "pcfforge_capture", function() if not done then return true end end)
hook.Add("PostRender", "pcfforge_capture", function()
  if done or not capturePath then return end
  local data = render.Capture({ format = "jpg", x = 0, y = 0, w = ScrW(), h = ScrH(), quality = 92 })
  if not data then table.insert(report.errors, "capture vide (menu ouvert ?)"); return end
  file.Write(capturePath, data)
  if phase.mode == "shots" then table.insert(report.shots, phase.shots[shotIdx].name); shotIdx = shotIdx + 1
  else frame = frame + 1; report.frames = frame end
  capturePath = nil
end)
