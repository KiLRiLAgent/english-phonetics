"""
Setup script to build macOS .app bundle (Microservice Client)

This is a LIGHTWEIGHT app - only UI + recording + HTTP client.
No ML dependencies (Whisper, pyannote, etc.) - those run in backend server.

Backend is bundled in .app for auto-start capability.

Usage:
    python setup_microservice.py py2app
"""

from setuptools import setup
from pathlib import Path

APP = ['english_practice_app_microservice.py']

# Bundle backend files for auto-start
backend_dir = Path(__file__).parent.parent / "backend"
backend_files = []

if backend_dir.exists():
    # Collect all backend files
    files_to_bundle = [
        backend_dir / "server.py",
        backend_dir / "analyzer_diarization.py",
        backend_dir / "cambridge_grammar_rules.py",
        backend_dir / "requirements.txt",
        backend_dir / "start_backend.sh",
    ]
    # Add .env.example if exists
    if (backend_dir / ".env.example").exists():
        files_to_bundle.append(backend_dir / ".env.example")
    
    # Format for py2app: ('destination_folder', [list of source files])
    backend_files = [
        ('Backend', [str(f) for f in files_to_bundle if f.exists()])
    ]

DATA_FILES = backend_files

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'English Practice',
        'CFBundleDisplayName': 'English Speaking Practice',
        'CFBundleIdentifier': 'com.exodus.englishpractice',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0',
        'LSUIElement': True,  # Hide from Dock (menu bar only)
        'NSMicrophoneUsageDescription': 'Record your speech for pronunciation analysis',
    },
    'packages': [
        'rumps',
        'requests',
        'pyaudio',
    ],
    'includes': [],
}

setup(
    name='English Practice',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
