#!/usr/bin/env python3
"""
English Speaking Practice - macOS Menu Bar App

Features:
- Lives in menu bar
- Hotkey (Cmd+Shift+R) to start/stop recording
- Analyzes speech after recording
- Shows results in notification/window
"""

import rumps
import os
import sys
import wave
import pyaudio
import threading
from pathlib import Path
from datetime import datetime

# Add parent directory to path for analyzer import
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzer_mvp import EnglishPracticeAnalyzer

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
TEMP_DIR = Path.home() / ".english_practice" / "recordings"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class EnglishPracticeApp(rumps.App):
    """Menu bar app for English speaking practice."""
    
    def __init__(self):
        super().__init__(
            "🎤 English Practice",
            icon=None,  # Will use emoji as icon
            quit_button=None  # Custom quit
        )
        
        # State
        self.recording = False
        self.frames = []
        self.audio = None
        self.stream = None
        
        # Analyzer (lazy load)
        self.analyzer = None
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.toggle_recording),
            rumps.separator,
            rumps.MenuItem("Last Analysis", callback=self.show_last_analysis),
            rumps.MenuItem("Open Results Folder", callback=self.open_results_folder),
            rumps.separator,
            rumps.MenuItem("Settings", callback=self.show_settings),
            rumps.MenuItem("About", callback=self.show_about),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Last result
        self.last_result = None
        self.last_audio_file = None
        
        print("✅ English Practice App initialized")
    
    def _load_analyzer(self):
        """Lazy load analyzer (takes time)."""
        if self.analyzer is None:
            rumps.notification(
                "English Practice",
                "Loading...",
                "Loading speech analyzer, please wait..."
            )
            self.analyzer = EnglishPracticeAnalyzer()
            rumps.notification(
                "English Practice",
                "Ready!",
                "Press Cmd+Shift+R to start recording"
            )
    
    @rumps.clicked("Start Recording")
    def toggle_recording(self, sender):
        """Start or stop recording."""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start audio recording."""
        self.recording = True
        self.frames = []
        
        # Update menu
        self.menu["Start Recording"].title = "⏹ Stop Recording"
        self.title = "🔴 Recording..."
        
        # Notify
        rumps.notification(
            "English Practice",
            "Recording started",
            "Speak in English. Click menu to stop."
        )
        
        # Start recording in background thread
        thread = threading.Thread(target=self._record_audio, daemon=True)
        thread.start()
    
    def stop_recording(self):
        """Stop recording and analyze."""
        self.recording = False
        
        # Update menu
        self.menu["Start Recording"].title = "Start Recording"
        self.title = "🎤 English Practice"
        
        # Notify
        rumps.notification(
            "English Practice",
            "Recording stopped",
            "Analyzing your speech..."
        )
        
        # Save and analyze in background
        thread = threading.Thread(target=self._save_and_analyze, daemon=True)
        thread.start()
    
    def _record_audio(self):
        """Record audio in background."""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.recording:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            
            # Cleanup
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            
        except Exception as e:
            rumps.alert(
                "Recording Error",
                f"Failed to record audio: {e}"
            )
    
    def _save_and_analyze(self):
        """Save audio and run analysis."""
        try:
            # Save WAV file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = TEMP_DIR / f"recording_{timestamp}.wav"
            
            with wave.open(str(audio_file), 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
            
            self.last_audio_file = audio_file
            print(f"✅ Saved: {audio_file}")
            
            # Load analyzer if needed
            self._load_analyzer()
            
            # Analyze
            result = self.analyzer.analyze(str(audio_file), reference_text=None)
            self.last_result = result
            
            # Show results
            self._show_results(result)
            
            # Save report
            self._save_report(result, audio_file)
            
        except Exception as e:
            rumps.alert(
                "Analysis Error",
                f"Failed to analyze: {e}"
            )
    
    def _show_results(self, result):
        """Show analysis results."""
        # Summary notification
        overall = result['overall_score']
        grammar = result['grammar']['score']
        fluency_wpm = result['fluency']['wpm']
        
        emoji = "🎉" if overall >= 90 else "✅" if overall >= 75 else "⚠️"
        
        message = (
            f"{emoji} Score: {overall}/100\n"
            f"Grammar: {grammar}/100 ({result['grammar']['total_errors']} errors)\n"
            f"Fluency: {fluency_wpm} WPM"
        )
        
        rumps.notification(
            "Analysis Complete",
            f"Overall: {overall}/100",
            message,
            sound=True
        )
        
        # Detailed window (optional)
        self._show_detailed_window(result)
    
    def _show_detailed_window(self, result):
        """Show detailed results in alert."""
        grammar_errors = result['grammar']['total_errors']
        
        if grammar_errors > 0:
            errors_text = "\n\n".join([
                f"❌ {err['message']}\n   Fix: {', '.join(err['replacements'][:2])}"
                for err in result['grammar']['errors'][:3]
            ])
            
            message = (
                f"You said: \"{result['transcript']}\"\n\n"
                f"Overall Score: {result['overall_score']}/100\n"
                f"Grammar: {result['grammar']['score']}/100\n"
                f"Fluency: {result['fluency']['wpm']} WPM\n\n"
                f"Grammar Errors:\n{errors_text}"
            )
        else:
            message = (
                f"You said: \"{result['transcript']}\"\n\n"
                f"Overall Score: {result['overall_score']}/100\n"
                f"✅ Perfect grammar!\n"
                f"Fluency: {result['fluency']['wpm']} WPM"
            )
        
        rumps.alert(
            "📊 Analysis Results",
            message
        )
    
    def _save_report(self, result, audio_file):
        """Save detailed report as text file."""
        report_file = audio_file.with_suffix('.txt')
        
        with open(report_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write("ENGLISH SPEAKING PRACTICE ANALYSIS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Audio: {audio_file.name}\n\n")
            f.write(f"Overall Score: {result['overall_score']}/100\n\n")
            f.write(f"Transcript: \"{result['transcript']}\"\n\n")
            
            # Grammar
            f.write(f"GRAMMAR: {result['grammar']['score']}/100\n")
            if result['grammar']['total_errors'] > 0:
                f.write(f"Errors found: {result['grammar']['total_errors']}\n\n")
                for i, err in enumerate(result['grammar']['errors'], 1):
                    f.write(f"{i}. {err['message']}\n")
                    f.write(f"   Incorrect: '{err['incorrect_text']}'\n")
                    f.write(f"   Suggestions: {', '.join(err['replacements'][:3])}\n")
                    
                    # Cambridge
                    cambridge = err.get('cambridge', {})
                    if cambridge:
                        f.write(f"   📖 {cambridge.get('title', '')}\n")
                        f.write(f"   💡 {cambridge.get('explanation', '')}\n")
                        f.write(f"   📕 {cambridge.get('book', '')} - {cambridge.get('unit', '')}\n")
                    f.write("\n")
            else:
                f.write("✅ No grammar errors detected!\n\n")
            
            # Fluency
            f.write(f"FLUENCY:\n")
            f.write(f"  WPM: {result['fluency']['wpm']}\n")
            f.write(f"  Duration: {result['fluency']['duration']}s\n")
            f.write(f"  Pauses: {result['fluency']['pause_count']}\n")
        
        print(f"✅ Report saved: {report_file}")
    
    @rumps.clicked("Last Analysis")
    def show_last_analysis(self, sender):
        """Show last analysis results."""
        if self.last_result:
            self._show_detailed_window(self.last_result)
        else:
            rumps.alert("No Analysis Yet", "Record something first!")
    
    @rumps.clicked("Open Results Folder")
    def open_results_folder(self, sender):
        """Open folder with recordings and reports."""
        os.system(f'open "{TEMP_DIR}"')
    
    @rumps.clicked("Settings")
    def show_settings(self, sender):
        """Show settings (placeholder)."""
        rumps.alert(
            "Settings",
            "Recording folder:\n" + str(TEMP_DIR) + "\n\n"
            "Hotkey: Cmd+Shift+R (coming soon)"
        )
    
    @rumps.clicked("About")
    def show_about(self, sender):
        """Show about dialog."""
        rumps.alert(
            "English Speaking Practice",
            "Version 1.0 MVP\n\n"
            "Grammar + Fluency + Pronunciation Analysis\n"
            "with Cambridge Grammar References\n\n"
            "Built with ❤️ for English learners"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, sender):
        """Quit application."""
        rumps.quit_application()


if __name__ == "__main__":
    print("🚀 Starting English Practice App...")
    app = EnglishPracticeApp()
    app.run()
