param(
    [string]$Version = "",
    [switch]$SkipDependencyInstall,
    [switch]$SkipDataPreparation,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

if (-not $Version) {
    $Version = python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
}

if (-not $SkipDependencyInstall) {
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev,windows]"
}

if (-not $SkipTests) {
    python -m pytest
}

if (-not $SkipDataPreparation) {
    python -m anatomia_app.zanatomy instalar --destino "data\zanatomy"
    python -m anatomia_app.zanatomy verificar --destino "data\zanatomy"
}

python "tools\build_content_pack.py" --version $Version --output "release"
python -m PyInstaller --noconfirm --clean "packaging\windows\anatomia-viva-3d.spec"

$IsccCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    throw "Inno Setup não encontrado. Instale-o antes de executar este script."
}

& $Iscc "/DAppVersion=$Version" "packaging\windows\installer.iss"

$Setup = Join-Path $ProjectRoot "release\AnatomiaViva3D-Setup-$Version.exe"
$Zip = Join-Path $ProjectRoot "release\AnatomiaViva3D-Windows-$Version.zip"
$StableZip = Join-Path $ProjectRoot "release\AnatomiaViva3D-Windows.zip"
if (-not (Test-Path $Setup)) {
    throw "O instalador esperado não foi criado: $Setup"
}
Compress-Archive -LiteralPath $Setup -DestinationPath $Zip -CompressionLevel Optimal -Force
Copy-Item -LiteralPath $Zip -Destination $StableZip -Force

Write-Host ""
Write-Host "Pacote Windows criado: $Zip"
Write-Host "Link estável criado: $StableZip"
