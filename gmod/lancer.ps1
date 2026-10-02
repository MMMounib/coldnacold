# pcfforge - installer les addons generes (out/) et lancer GMod dans le Particle Editor
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
function Trouver-GMod {
    $steam = $null
    try { $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction Stop).SteamPath } catch {}
    if (-not $steam) { $steam = "C:\Program Files (x86)\Steam" }
    $libs = @($steam); $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
    if (Test-Path $vdf) { foreach ($m in (Select-String -Path $vdf -Pattern '"path"\s+"([^"]+)"')) { $libs += ($m.Matches[0].Groups[1].Value -replace '\\\\', '\') } }
    foreach ($l in ($libs | Select-Object -Unique)) { $g = Join-Path $l "steamapps\common\GarrysMod\garrysmod"; if (Test-Path $g) { return @{ Game = $g; Lib = $l } } }
    return $null
}
$gm = Trouver-GMod
if (-not $gm) { $p = Read-Host "Chemin de ...\GarrysMod\garrysmod"; $gm = @{ Game = $p; Lib = (Split-Path (Split-Path (Split-Path (Split-Path $p)))) } }
Write-Host "Garry's Mod : $($gm.Game)"
$acf = Join-Path $gm.Lib "steamapps\appmanifest_4000.acf"
if ((Test-Path $acf) -and (Select-String -Path $acf -Pattern '"BetaKey"\s+"x86-64"' -Quiet)) {
    Write-Host "ATTENTION : branche x86-64 -> le Particle Editor ne marche pas. Steam > Proprietes > Betas > Aucune." -ForegroundColor Yellow }
Write-Host "1) Installer tous les addons de out\   2) Installer + lancer l'editeur   3) Lancer l'editeur seulement   4) Retirer les addons pcfforge"
$c = Read-Host "Choix"
$addons = Get-ChildItem (Join-Path $Root "out") -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName "particles") }
if ($c -in "1", "2") {
    $pt = Join-Path $gm.Game "particles\pcfforge_test"; New-Item -ItemType Directory -Force -Path $pt | Out-Null
    foreach ($a in $addons) {
        robocopy $a.FullName (Join-Path $gm.Game "addons\$($a.Name)") /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
        Copy-Item (Join-Path $a.FullName "particles\*.pcf") $pt -Force; Write-Host "Installe : $($a.Name)" -ForegroundColor Green }
}
if ($c -eq "4") {
    foreach ($a in $addons) { $d = Join-Path $gm.Game "addons\$($a.Name)"; if (Test-Path $d) { Remove-Item $d -Recurse -Force; Write-Host "Retire : $($a.Name)" } }
    $pt = Join-Path $gm.Game "particles\pcfforge_test"; if (Test-Path $pt) { Remove-Item $pt -Recurse -Force }
}
if ($c -in "2", "3") {
    if (Get-Process -Name "hl2", "gmod" -ErrorAction SilentlyContinue) { Write-Host "Fermer Garry's Mod d'abord." -ForegroundColor Yellow; exit }
    Start-Process "steam://run/4000//-tools -nop4 -noworkshop -sv_lan 1 +sv_cheats 1 -windowed -w 1600 -h 900 +map gm_flatgrass/"
    Write-Host "Puis : Tools > Particle Editor > File > Open > garrysmod\particles\pcfforge_test\" -ForegroundColor Cyan
}
