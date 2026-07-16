# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour Easy School 2.0.

A construire depuis la racine du projet :
    venv\\Scripts\\pyinstaller.exe packaging\\easy_school.spec --noconfirm
"""
import os

ROOT = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.dirname(ROOT)  # packaging/ -> racine du projet

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "assets"), "assets"),
    ],
    hiddenimports=[
        "psycopg2",
        "sqlalchemy.dialects.postgresql",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EasySchool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(ROOT, "packaging", "icon.ico"),
    # Garde les fichiers de support a plat a cote de l'exe (pas de sous-dossier
    # _internal cache) : le code metier resout assets/photos_eleves et
    # assets/logos relativement a __file__, il doit rester au meme niveau
    # que l'executable pour ne pas casser cette logique.
    contents_directory=".",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="EasySchool",
)
