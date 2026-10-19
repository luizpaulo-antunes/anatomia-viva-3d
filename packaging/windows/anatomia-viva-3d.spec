from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).parents[1]
source_root = project_root / "src"
atlas_root = project_root / "data" / "zanatomy"

required_files = list(atlas_root.glob("*.glb"))
lightweight_files = list(atlas_root.glob("lod-v*-2000-*.glb.npz"))
if (
    len(required_files) != 7
    or len(lightweight_files) != 7
    or not (atlas_root / "TA2.csv").is_file()
):
    raise SystemExit(
        "O pacote completo exige os sete sistemas Z-Anatomy e o cache leve. "
        "Execute 'anatomia-dados instalar' e 'anatomia-dados otimizar' antes do build."
    )

datas = [
    (str(atlas_root), "data/zanatomy"),
    (
        str(source_root / "anatomia_app" / "data" / "female_reproductive_v1_5.npz"),
        "anatomia_app/data",
    ),
    (str(project_root / "README.md"), "."),
    (str(project_root / "LICENSE"), "."),
    (str(project_root / "THIRD_PARTY_LICENSES.md"), "."),
]
binaries = []
hiddenimports = []

hiddenimports.append("DracoPy")
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
