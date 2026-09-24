# Fetch the image checkpoint for the LYGO Image Engine.
#
#   powershell -ExecutionPolicy Bypass -File get_model.ps1 -List
#   powershell -ExecutionPolicy Bypass -File get_model.ps1                 # sdxl-turbo, 6.9 GB
#   powershell -ExecutionPolicy Bypass -File get_model.ps1 -Model sd15     # 4.3 GB, lighter
#   powershell -ExecutionPolicy Bypass -File get_model.ps1 -From <url>     # anything you already host
#
# Resumable: curl -C - continues a part file, so a dropped line costs nothing. The digest is checked
# when the file is complete, and a file that fails the check is NOT kept.
#
# Licences are the model authors', not ours: sdxl-turbo is Stability AI's non-commercial research
# licence, SD 1.5 is CreativeML Open RAIL-M. Read them before you ship a picture commercially.

param(
  [ValidateSet("sdxl-turbo", "sd15")][string]$Model = "sdxl-turbo",
  [string]$From = "",
  [string]$Dest = "",
  [switch]$List
)

$ErrorActionPreference = "Stop"

$catalog = @{
  "sdxl-turbo" = @{
    Name  = "SDXL Turbo 1.0 fp16 (fast: 4 steps, cfg 1.0)"
    Url   = "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors"
    File  = "sd_xl_turbo_1.0_fp16.safetensors"
    Bytes = 6938081905
    Sha   = ""
    Note  = "Stability AI Non-Commercial Research Community Licence"
  }
  "sd15" = @{
    Name  = "Stable Diffusion 1.5 (pruned emaonly, 20 steps, cfg 7)"
    Url   = "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
    File  = "v1-5-pruned-emaonly.safetensors"
    Bytes = 4265146304
    Sha   = ""
    Note  = "CreativeML Open RAIL-M (commercial use allowed with restrictions)"
  }
}

if ($List) {
  Write-Host "Checkpoints this fetcher knows:" -ForegroundColor Cyan
  foreach ($k in $catalog.Keys) {
    $c = $catalog[$k]
    Write-Host ("  {0,-11} {1}" -f $k, $c.Name)
    Write-Host ("              {0:N0} bytes  -  {1}" -f $c.Bytes, $c.Note)
    Write-Host ("              {0}" -f $c.Url)
  }
  Write-Host ""
  Write-Host "Run without -List to fetch the default (sdxl-turbo)."
  exit 0
}

$entry = $catalog[$Model]
if ($From) { $entry.Url = $From; $entry.File = [System.IO.Path]::GetFileName(([Uri]$From).AbsolutePath) }

$root = if ($Dest) { $Dest } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$dir = Join-Path $root "models\sd"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$target = Join-Path $dir $entry.File

Write-Host "Target : $target"
Write-Host "Source : $($entry.Url)"
Write-Host "Licence: $($entry.Note)"
if ($entry.Bytes) { Write-Host ("Size   : {0:N0} bytes  (about {1:N1} GB)" -f $entry.Bytes, ($entry.Bytes / 1GB)) }
Write-Host ""

if ((Test-Path $target) -and $entry.Bytes -and ((Get-Item $target).Length -eq $entry.Bytes)) {
  Write-Host "Already complete - nothing to do." -ForegroundColor Green
} else {
  Write-Host "Fetching. This resumes if it is interrupted; run this script again to continue." -ForegroundColor Yellow
  & curl.exe -L -C - --retry 5 --retry-delay 3 -o $target $entry.Url
  if ($LASTEXITCODE -ne 0) { Write-Host "curl returned $LASTEXITCODE - run the script again to resume." -ForegroundColor Red; exit 1 }
}

$len = (Get-Item $target).Length
Write-Host ("On disk: {0:N0} bytes" -f $len)

if ($entry.Bytes -and $len -ne $entry.Bytes) {
  Write-Host ("Size mismatch: expected {0:N0}. The download is incomplete - run again to resume." -f $entry.Bytes) -ForegroundColor Red
  exit 1
}
if ($entry.Sha) {
  $sha = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLower()
  if ($sha -ne $entry.Sha.ToLower()) {
    Write-Host "SHA-256 does NOT match - removing the file rather than keeping a bad one." -ForegroundColor Red
    Remove-Item $target
    exit 1
  }
  Write-Host "SHA-256 ok: $sha" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next: run LYGO_IMAGE_ENGINE.bat - it points the console at this folder and starts the gateway." -ForegroundColor Cyan
