from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).parents[1]
source_root = project_root / "src"
cache_root = project_root / "data" / "bodyparts3d" / "cache"

cache_files = list(cache_root.glob("*.vtp"))
if len(cache_files) < 443:
    raise SystemExit(
        "O pacote completo exige 443 arquivos VTP. Execute "
        "'anatomia-dados instalar' e 'anatomia-dados otimizar' antes do build."
    )

datas = [
    (str(cache_root), "data/bodyparts3d/cache"),
    (str(project_root / "data" / "bodyparts3d" / "content.json"), "data/bodyparts3d"),
    (str(project_root / "README.md"), "."),
    (str(project_root / "LICENSE"), "."),
    (str(project_root / "THIRD_PARTY_LICENSES.md"), "."),
]
binaries = []
hiddenimports = []

for package in ("pyvista", "pyvistaqt", "vtkmodules"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [str(project_root / "packaging" / "windows" / "launcher.py")],
    pathex=[str(source_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "jupyter", "notebook"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AnatomiaViva3D",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AnatomiaViva3D",
)
