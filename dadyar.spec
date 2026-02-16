# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for دادیار هوشمند (Intelligent Legal Assistant).

Build with:
    pyinstaller dadyar.spec --noconfirm

This creates a one-folder distribution in dist/dadyar/
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# ── Project root ──
PROJECT_ROOT = os.path.abspath('.')

# ── Collect heavy packages ──
streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all('streamlit')
plotly_datas = collect_data_files('plotly')
pydantic_datas = collect_data_files('pydantic')

# ── Application data files ──
app_datas = [
    # App source files (needed by streamlit run)
    (os.path.join(PROJECT_ROOT, 'app.py'), '.'),
    (os.path.join(PROJECT_ROOT, 'config'), 'config'),
    (os.path.join(PROJECT_ROOT, 'modules'), 'modules'),
    (os.path.join(PROJECT_ROOT, 'data'), 'data'),
    (os.path.join(PROJECT_ROOT, 'assets'), 'assets'),
]

all_datas = app_datas + streamlit_datas + plotly_datas + pydantic_datas

# ── Hidden imports ──
hidden_imports = streamlit_hiddenimports + [
    # Core app
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner',
    # Google Gemini
    'google.genai',
    'google.genai.types',
    'google.api_core',
    'google.api_core.exceptions',
    'google.auth',
    'httpx',
    'socksio',
    # OpenAI
    'openai',
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    # NLP
    'hazm',
    'hazm.Normalizer',
    # Data / ML
    'sklearn',
    'sklearn.feature_extraction',
    'sklearn.feature_extraction.text',
    'sklearn.metrics',
    'sklearn.metrics.pairwise',
    'numpy',
    'pandas',
    # Graph & Viz
    'networkx',
    'plotly',
    'plotly.graph_objects',
    'plotly.express',
    'kaleido',
    # Utilities
    'pydantic',
    'pydantic_settings',
    'jdatetime',
    'dotenv',
    'jsonschema',
] + collect_submodules('google.genai') + collect_submodules('hazm')


a = Analysis(
    ['launcher.py'],
    pathex=[PROJECT_ROOT],
    binaries=streamlit_binaries,
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary large packages to reduce size
        'matplotlib',
        'tkinter',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dadyar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console to show server logs
    icon=None,     # Add .ico path here for Windows builds
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dadyar',
)
