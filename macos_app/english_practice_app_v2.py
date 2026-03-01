#!/usr/bin/env python3
"""
English Speaking Practice - macOS Menu Bar App v2

NEW Features:
- Speaker diarization (separate your voice from others)
- Timestamps for all errors
- Summary + Top-3 + Timeline format
- Auto-detect when call starts (optional)
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
from analyzer_diarization import EnglishPracticeAnalyzerDiarization, format_report_new, format_timestamp

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
TEMP_DIR = Path.home() / ".english_practice" / "recordings"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class EnglishPracticeAppV2(rumps.App):
    """Menu bar app for English speaking practice with speaker diarization."""
    
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
        
        # Settings
        self.enable_diarization = True
        self.target_speaker = None  # None = analyze all speakers
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Start Recording", callback=self.toggle_recording),
            rumps.separator,
            rumps.MenuItem("Last Analysis", callback=self.show_last_analysis),
            rumps.MenuItem("Open Results Folder", callback=self.open_results_folder),
            rumps.separator,
            rumps.MenuItem("Speaker Diarization: ON", callback=self.toggle_diarization),
            rumps.separator,
            rumps.MenuItem("Settings", callback=self.show_settings),
            rumps.MenuItem("About", callback=self.show_about),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Last result
        self.last_result = None
        self.last_audio_file = None
        
        print("✅ English Practice App v2 initialized")
    
    def _load_analyzer(self):
        """Lazy load analyzer (takes time)."""
        if self.analyzer is None:
            rumps.notification(
                "English Practice",
                "Loading...",
                "Loading speech analyzer, please wait..."
            )
            self.analyzer = EnglishPracticeAnalyzerDiarization()
            rumps.notification(
                "English Practice",
                "Ready!",
                "Click menu to start recording"
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
            result = self.analyzer.analyze(
                str(audio_file), 
                reference_text=None,
                target_speaker=self.target_speaker,
                enable_diarization=self.enable_diarization
            )
            self.last_result = result
            
            # If multiple speakers detected, ask which one to analyze
            if self.enable_diarization and result['speakers']['total'] > 1:
                self._ask_speaker_selection(result, audio_file)
            else:
                # Show results immediately
                self._show_results(result)
                self._save_report(result, audio_file)
            
        except Exception as e:
            rumps.alert(
                "Analysis Error",
                f"Failed to analyze: {e}\n\n"
                f"Check ~/.english_practice/error.log for details"
            )
            
            # Log error
            with open(TEMP_DIR / "error.log", 'a') as f:
                f.write(f"\n{datetime.now()}: {e}\n")
    
    def _ask_speaker_selection(self, result, audio_file):
        """Ask user to select which speaker to analyze."""
        total_speakers = result['speakers']['total']
        
        # Build speaker info
        speaker_info = []
        for i in range(total_speakers):
            segments = [s for s in result['speakers']['segments'] if s['speaker'] == i]
            total_time = sum(s['end'] - s['start'] for s in segments)
            speaker_info.append(f"Speaker {i}: {total_time:.1f}s")
        
        message = (
            f"Found {total_speakers} speakers:\n\n" +
            "\n".join(speaker_info) +
            "\n\nWhich speaker is YOU?"
        )
        
        # Simple input dialog (rumps doesn't support complex dialogs)
        response = rumps.Window(
            message,
            "Select Speaker",
            default_text="0",
            dimensions=(320, 100)
        ).run()
        
        if response.clicked:
            try:
                selected_speaker = int(response.text)
                
                # Re-analyze with selected speaker
                result = self.analyzer.analyze(
                    str(audio_file),
                    reference_text=None,
                    target_speaker=selected_speaker,
                    enable_diarization=True
                )
                
                self.last_result = result
                self._show_results(result)
                self._save_report(result, audio_file)
                
            except ValueError:
                rumps.alert("Invalid Input", "Please enter a number (0, 1, 2...)")
    
    def _show_results(self, result):
        """Show analysis results (NEW FORMAT)."""
        # Summary notification
        overall = result['overall_score']
        grammar_errors = result['grammar']['total_errors']
        duration = result['summary']['duration']
        
        emoji = "🎉" if overall >= 90 else "✅" if overall >= 75 else "⚠️"
        
        message = (
            f"{emoji} Score: {overall}/100\n"
            f"Duration: {format_timestamp(duration)}\n"
            f"Errors: {grammar_errors} grammar"
        )
        
        rumps.notification(
            "Analysis Complete",
            f"Overall: {overall}/100",
            message,
            sound=True
        )
        
        # Detailed window with TOP-3 errors
        self._show_detailed_window(result)
    
    def _show_detailed_window(self, result):
        """Show detailed results in alert (Summary + Top-3)."""
        overall = result['overall_score']
        summary = result['summary']
        top_errors = result.get('top_errors', [])
        
        # Summary
        message_parts = [
            f"📊 SUMMARY",
            f"Overall: {overall}/100",
            f"Duration: {format_timestamp(summary['duration'])}",
            f"Speaking: {format_timestamp(summary['speaking_time'])} ({summary['speaking_percentage']}%)",
            f"Errors: {result['grammar']['total_errors']} grammar",
            ""
        ]
        
        # Top-3 errors
        if top_errors:
            message_parts.append("🔥 TOP 3 ERRORS:")
            
            for i, err in enumerate(top_errors[:3], 1):
                cambridge = err.get('cambridge', {})
                example = err['all_examples'][0] if err['all_examples'] else {}
                
                timestamp = format_timestamp(example.get('timestamp'))
                incorrect = example.get('incorrect_text', '')
                correct = err['replacements'][0] if err['replacements'] else '?'
                
                message_parts.append(
                    f"\n{i}. {cambridge.get('title', err['category'])} ({err['occurrences']}x)"
                )
                message_parts.append(f"{timestamp} ❌ \"{incorrect}\"")
                message_parts.append(f"         ✅ \"{correct}\"")
        else:
            message_parts.append("✅ No errors found! Perfect!")
        
        message = "\n".join(message_parts)
        
        rumps.alert(
            "📊 Analysis Results",
            message
        )
    
    def _save_report(self, result, audio_file):
        """Save detailed report as text file (NEW FORMAT)."""
        report_file = audio_file.with_suffix('.txt')
        
        # Use new format
        report_text = format_report_new(result)
        
        with open(report_file, 'w') as f:
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Audio: {audio_file.name}\n\n")
            f.write(report_text)
        
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
    
    @rumps.clicked("Speaker Diarization: ON")
    def toggle_diarization(self, sender):
        """Toggle speaker diarization on/off."""
        self.enable_diarization = not self.enable_diarization
        
        status = "ON" if self.enable_diarization else "OFF"
        sender.title = f"Speaker Diarization: {status}"
        
        rumps.notification(
            "English Practice",
            f"Speaker Diarization {status}",
            "Will detect multiple speakers" if self.enable_diarization else "Single speaker mode"
        )
    
    @rumps.clicked("Settings")
    def show_settings(self, sender):
        """Show settings."""
        diarization_status = "ON" if self.enable_diarization else "OFF"
        
        rumps.alert(
            "Settings",
            f"Recording folder:\n{TEMP_DIR}\n\n"
            f"Speaker Diarization: {diarization_status}\n\n"
            f"Hugging Face Token: {'✅ Set' if os.getenv('HUGGINGFACE_TOKEN') else '❌ Missing'}\n"
            f"(Required for speaker diarization)"
        )
    
    @rumps.clicked("About")
    def show_about(self, sender):
        """Show about dialog."""
        rumps.alert(
            "English Speaking Practice v2",
            "Version 2.0 MVP\n\n"
            "NEW:\n"
            "• Speaker diarization (multi-speaker)\n"
            "• Timestamps for all errors\n"
            "• Summary + Top-3 + Timeline format\n\n"
            "Features:\n"
            "• Grammar analysis (Cambridge Grammar)\n"
            "• Fluency metrics (WPM, pauses)\n"
            "• Pronunciation (WER)\n\n"
            "Built with ❤️ for English learners"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, sender):
        """Quit application."""
        rumps.quit_application()


if __name__ == "__main__":
    print("🚀 Starting English Practice App v2...")
    app = EnglishPracticeAppV2()
    app.run()
