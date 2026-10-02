--[[ pcfforge runtime (client) : attache les effets générés à une entité, un os, un attachment,
une région (segment dans le repère d'un os) ou le centre de la bounding box.

  local h = PCFForge.AttachEffect(ent, "chakra_aura" [, attachOverride])
  PCFForge.UpdateEffect(h, { [cp] = Vector(...) })     -- fixe des points de contrôle à la main
  PCFForge.DetachEffect(h [, immediate])

API Garry's Mod utilisées : CreateParticleSystem, CNewParticleEffect:SetControlPoint /
SetControlPointOrientation / StopEmission / StopEmissionAndDestroyImmediately / IsValid,
Entity:LookupBone / GetBoneMatrix / LookupAttachment / OBBCenter / LocalToWorld, LocalToWorld,
hook.Add("Think"), concommand.Add, SortedPairs, CreateClientConVar,
hook.Add("PostDrawTranslucentRenderables"), cam.IgnoreZ, render.SetColorMaterial / DrawSphere / DrawLine.  ]]
if SERVER then return end

PCFForge = PCFForge or { effects = {}, active = {} }
local P = PCFForge

function P.Register(id, def) P.effects[id] = def end

local function warn(msg) MsgC(Color(255, 150, 60), "[pcfforge] " .. msg .. "\n") end

local function place(h)
  local ent, a = h.ent, h.attach
  if a.type == "bone" or a.type == "region" then
    if not h.bone then
      h.bone = ent:LookupBone(a.bone or a.name or "")
      if not h.bone then return false, "os introuvable : " .. tostring(a.bone or a.name) end
    end
    local m = ent:GetBoneMatrix(h.bone)
    if not m then return true end                      -- os pas encore calculé cette frame : on réessaie
    local pos, ang = m:GetTranslation(), m:GetAngles()
    local s = ent:GetModelScale() or 1
    local p0 = LocalToWorld((a.from or vector_origin) * s, angle_zero, pos, ang)
    local p1 = LocalToWorld((a.to or Vector(0, 0, 1)) * s, angle_zero, pos, ang)
    h.fx:SetControlPoint(0, p0)
    h.fx:SetControlPoint(1, p1)
    h.cps = { [0] = p0, [1] = p1 }
    h.fx:SetControlPointOrientation(0, ang:Forward(), ang:Right(), ang:Up())
    if a.points then                                   -- silhouette : CP2, CP3, ... (repère de l'os)
      for i, v in ipairs(a.points) do
        local w = LocalToWorld(v * s, angle_zero, pos, ang)
        h.fx:SetControlPoint(i + 1, w)
        h.cps[i + 1] = w
      end
    end
  elseif a.type == "bounds" then
    h.fx:SetControlPoint(0, ent:LocalToWorld(ent:OBBCenter()))
  end
  return true
end

function P.AttachEffect(ent, id, override)
  local def = P.effects[id]
  if not def then warn("effet inconnu : " .. tostring(id)) return nil end
  if not IsValid(ent) then warn("entité invalide") return nil end
  local a = override or def.attach or { type = "entity" }
  local fx
  if a.type == "attachment" then
    local att = ent:LookupAttachment(a.name or "")
    if not att or att <= 0 then warn("attachment introuvable : " .. tostring(a.name)) return nil end
    fx = CreateParticleSystem(ent, def.system, PATTACH_POINT_FOLLOW, att, a.offset or vector_origin)
  elseif a.type == "entity" then
    fx = CreateParticleSystem(ent, def.system, PATTACH_ABSORIGIN_FOLLOW, 0, a.offset or vector_origin)
  else
    fx = CreateParticleSystem(ent, def.system, PATTACH_CUSTOMORIGIN, 0)
  end
  if not fx or not fx:IsValid() then warn("création impossible : " .. def.system) return nil end
  local h = { ent = ent, fx = fx, attach = a, id = id }
  local ok, err = place(h)
  if not ok then fx:StopEmissionAndDestroyImmediately() warn(err) return nil end
  P.active[h] = true
  return h
end

function P.UpdateEffect(h, cps)
  if not h or not P.active[h] or not h.fx:IsValid() then return false end
  for cp, pos in pairs(cps or {}) do h.fx:SetControlPoint(cp, pos) end
  return true
end

function P.DetachEffect(h, immediate)
  if not h or not P.active[h] then return end
  P.active[h] = nil
  if (P.effects[h.id] or {}).persistent then immediate = true end   -- persistent particles never end by themselves
  if h.fx:IsValid() then
    if immediate then h.fx:StopEmissionAndDestroyImmediately() else h.fx:StopEmission() end
  end
end

hook.Add("Think", "pcfforge_runtime", function()
  for h in pairs(P.active) do
    if not IsValid(h.ent) or not h.fx:IsValid() then
      P.DetachEffect(h, true)                          -- entité supprimée : on nettoie
    else
      local ok, err = place(h)
      if not ok then warn(err) P.DetachEffect(h, true) end
    end
  end
end)

-- pcfforge_debug 1 : dessine les points de contrôle (CP0 vert, CP1 bleu, chaînes en rouge) à travers les modèles
local dbg = CreateClientConVar("pcfforge_debug", "0", false, false, "Affiche les points de contrôle des effets pcfforge")
local C0, C1, CC = Color(60, 255, 90), Color(60, 140, 255), Color(255, 50, 50)
hook.Add("PostDrawTranslucentRenderables", "pcfforge_debug", function(_, sky)
  if sky or not dbg:GetBool() then return end
  cam.IgnoreZ(true)
  render.SetColorMaterial()
  for h in pairs(P.active) do
    local c = h.cps
    if c then
      if c[0] then render.DrawSphere(c[0], 1, 8, 8, C0) end
      if c[1] then render.DrawSphere(c[1], 1, 8, 8, C1) end
      local i = 2
      while c[i] do
        render.DrawSphere(c[i], .4, 6, 6, CC)
        if c[i + 1] then render.DrawLine(c[i], c[i + 1], CC, false) end
        i = i + 1
      end
    end
  end
  cam.IgnoreZ(false)
end)

-- outils de test (client) : pcfforge_attach <id> [bone|attachment|region|bounds|entity], pcfforge_list, pcfforge_clear
concommand.Add("pcfforge_attach", function(ply, _, args)
  local id = args[1]
  local tr = ply:GetEyeTrace()
  local ent = IsValid(tr.Entity) and tr.Entity or ply
  local override = args[2] and table.Copy((P.effects[id] or {}).attach or {}) or nil
  if override then override.type = args[2] end
  if P.AttachEffect(ent, id, override) then print("[pcfforge] " .. id .. " attaché à " .. tostring(ent)) end
end)
concommand.Add("pcfforge_list", function()
  for id, def in SortedPairs(P.effects) do
    print(string.format("  %-24s %-28s attache %s", id, def.system, (def.attach or {}).type or "entity"))
  end
end)
concommand.Add("pcfforge_clear", function()
  for h in pairs(P.active) do P.DetachEffect(h, true) end
end)
