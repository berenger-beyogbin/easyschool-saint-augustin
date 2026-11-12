# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
from pathlib import Path


def _postgresql_client_binaries():
    """Embarque pg_dump et ses DLL afin que la sauvegarde fonctionne sur un poste client."""
    candidates = []
    configured = os.environ.get("PG_DUMP_PATH")
    if configured:
        candidates.append(Path(configured))
    on_path = shutil.which("pg_dump")
    if on_path:
        candidates.append(Path(on_path))
    postgres_roots = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(env_name)
        if root:
            postgres_roots.append(Path(root) / "PostgreSQL")
    postgres_roots.append(Path(f"{os.environ.get('SystemDrive', 'C:')}\\PostgreSQL"))
    for root in postgres_roots:
        candidates.extend(root.glob("*/bin/pg_dump.exe"))
        candidates.extend(root.glob("*/pgAdmin 4/runtime/pg_dump.exe"))

    def version_key(path):
        for parent in path.parents:
            if parent.name.isdigit():
                return int(parent.name)
        return 0

    pg_dump = max((path for path in candidates if path.is_file()), key=version_key, default=None)
    if pg_dump is None:
        raise RuntimeError(
            "pg_dump introuvable : installez les outils client PostgreSQL "
            "ou definissez PG_DUMP_PATH avant de construire l'application."
        )

    runtime_dir = pg_dump.parent
    files = [pg_dump, *runtime_dir.glob("*.dll")]
    print(f"Client PostgreSQL embarque depuis {runtime_dir}")
    install_root = next((parent for parent in pg_dump.parents if parent.name.isdigit()), runtime_dir.parent)
    license_files = [
        install_root / "server_license.txt",
        install_root / "commandlinetools_3rd_party_licenses.txt",
    ]
    binaries = [(str(path), "postgresql") for path in files]
    datas = [(str(path), "postgresql") for path in license_files if path.is_file()]
    return binaries, datas


postgresql_binaries, postgresql_datas = _postgresql_client_binaries()


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=postgresql_binaries,
    datas=[
        ('assets', 'assets'),
        ('migrations', 'migrations'),
        ('alembic.ini', '.'),
        *postgresql_datas,
    ],
    # migrations/env.py est embarque comme donnee et n'est donc pas analyse
    # par PyInstaller. Declarer explicitement ses imports de bibliotheque
    # standard necessaires a l'execution de `EasySchool.exe --migrate`.
    hiddenimports=['logging.config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EasySchool',
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
    icon=['assets\\icon.ico'],
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EasySchool',
)
