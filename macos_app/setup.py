"""
Setup script to build macOS .app bundle

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['english_practice_app.py']
DATA_FILES = [
    ('../analyzer_mvp.py', ['../analyzer_mvp.py']),
    ('../cambridge_grammar_rules.py', ['../cambridge_grammar_rules.py']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add icon later
    'plist': {
        'CFBundleName': 'English Practice',
        'CFBundleDisplayName': 'English Speaking Practice',
        'CFBundleIdentifier': 'com.exodus.englishpractice',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'LSUIElement': True,  # Hide from Dock (menu bar only)
        'NSMicrophoneUsageDescription': 'Record your speech for pronunciation analysis',
    },
    'packages': [
        'rumps',
        'whisper',
        'language_tool_python',
        'numpy',
        'torch',
    ],
    'includes': [
        'analyzer_mvp',
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
