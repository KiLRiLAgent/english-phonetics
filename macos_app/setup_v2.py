"""
Setup script to build macOS .app bundle (v2 with Speaker Diarization)

Usage:
    python setup_v2.py py2app
"""

from setuptools import setup

APP = ['english_practice_app_v2.py']
DATA_FILES = [
    ('../analyzer_diarization.py', ['../analyzer_diarization.py']),
    ('../cambridge_grammar_rules.py', ['../cambridge_grammar_rules.py']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add icon later
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
        'whisper',
        'language_tool_python',
        'numpy',
        'torch',
        'pyannote',
        'dotenv',
    ],
    'includes': [
        'analyzer_diarization',
        'cambridge_grammar_rules',
    ],
}

setup(
    name='English Practice',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
