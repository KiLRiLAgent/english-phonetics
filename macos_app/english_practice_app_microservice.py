#!/usr/bin/env python3
"""
English Speaking Practice - macOS Menu Bar App (Microservice Client)

Lightweight UI that communicates with backend server for analysis.
No heavy ML dependencies - just recording + HTTP requests.

Version 2.1: Added call recording mode for teachers
"""

import rumps
import os
import wave
import pyaudio
import threading
import requests
import json
from pathlib import Path
from datetime import datetime
import time
import subprocess
import sys

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2  # Stereo for call recording (changed from 1)
RATE = 16000
TEMP_DIR = Path.home() / ".english_practice" / "recordings"
CALL_DIR = Path.home() / ".english_practice" / "call_recordings"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
CALL_DIR.mkdir(parents=True, exist_ok=True)

# Backend server
BACKEND_URL = "http://127.0.0.1:8780"


class EnglishPracticeApp(rumps.App):
    """Menu bar app for English speaking practice (microservice client)."""
    
    def __init__(self):
        super().__init__(
            "🎤 English Practice",
            icon=None,
            quit_button=None
        )
        
        # State
        self.recording = False
        self.call_recording = False  # NEW: call recording mode
        self.frames = []
        self.audio = None
        self.stream = None
        self.recording_start_time = None
        self.sample_width = 2  # pyaudio.paInt16 = 2 bytes
        
        # Settings
        self.enable_diarization = True
        self.target_speaker = None
        self.selected_device_index = None  # NEW: for aggregate device
        
        # Menu items
        self.menu = [
            rumps.MenuItem("🎤 Quick Practice", callback=self.start_quick_practice),
            rumps.MenuItem("📞 Start Call Recording", callback=self.start_call_recording),
            rumps.separator,
            rumps.MenuItem("📊 View Reports", callback=self.view_reports),
            rumps.MenuItem("Last Analysis", callback=self.show_last_analysis),
            rumps.MenuItem("Open Results Folder", callback=self.open_results_folder),
            rumps.separator,
            rumps.MenuItem("🎙️ Select Audio Device", callback=self.select_audio_device),
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
        
        print("✅ English Practice App initialized")
        
        # Check backend on startup
        self.check_backend()
        
        # Check for aggregate device
        self.check_aggregate_device()
    
    def check_backend(self):
        """Check if backend server is running, auto-start if not."""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend server connected (v{data.get('version', '?')})")
                return True
        except requests.exceptions.RequestException:
            pass
        
        # Backend not running - try to auto-start
        print("⚠️  Backend not running, attempting auto-start...")
        if self.auto_start_backend():
            # Wait a few seconds for backend to start
            time.sleep(3)
            try:
                response = requests.get(f"{BACKEND_URL}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend auto-started successfully!")
                    return True
            except:
                pass
        
        # Auto-start failed - show error
        self.show_backend_error()
        return False
    
    def auto_start_backend(self):
        """Try to auto-start the backend server."""
        # Look for backend in multiple locations
        possible_paths = [
            # Inside .app bundle (for DMG distribution)
            Path(sys.argv[0]).parent.parent / "Resources" / "Backend",
            # Development mode
            Path(__file__).parent.parent / "backend",
            # Installed location
            Path.home() / "Library" / "Application Support" / "EnglishPractice" / "Backend",
        ]
        
        backend_dir = None
        for path in possible_paths:
            if path.exists() and (path / "server.py").exists():
                backend_dir = path
                print(f"📁 Found backend at: {backend_dir}")
                break
        
        if not backend_dir:
            print("❌ Backend directory not found")
            return False
        
        try:
            # Start backend server in background
            server_script = backend_dir / "server.py"
            
            # Use system Python with all dependencies installed
            python_exec = "/usr/local/bin/python3"
            
            # Check if start_backend.sh wrapper exists (preferred)
            wrapper_script = backend_dir / "start_backend.sh"
            if wrapper_script.exists():
                print(f"🚀 Starting backend via wrapper: {wrapper_script}")
                command = [str(wrapper_script)]
            else:
                print(f"🚀 Starting backend: {python_exec} {server_script}")
                command = [python_exec, str(server_script)]
            
            # Start in background, redirect output to log file
            log_file = Path.home() / ".english_practice" / "backend.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, "a") as f:
                subprocess.Popen(
                    command,
                    cwd=str(backend_dir),
                    stdout=f,
                    stderr=f,
                    start_new_session=True  # Detach from parent process
                )
            
            print(f"✅ Backend started (logs: {log_file})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def show_backend_error(self):
        """Show error if backend auto-start failed."""
        rumps.alert(
            "Backend Server Failed to Start",
            "The backend server could not start automatically.\n\n"
            "Try restarting the app. If the problem persists, check:\n\n"
            f"Logs: ~/.english_practice/backend.log\n"
            f"Health check: curl {BACKEND_URL}/health\n\n"
            "You may need to reinstall the app."
        )
    
    def check_aggregate_device(self):
        """Check if Aggregate Device is configured for call recording."""
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            aggregate_found = False
            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                device_name = info.get('name', '').lower()
                
                # Check for common aggregate device names
                if 'aggregate' in device_name or 'multi-output' in device_name:
                    aggregate_found = True
                    self.selected_device_index = i
                    print(f"✅ Found aggregate device: {info.get('name')}")
                    break
            
            p.terminate()
            
            if not aggregate_found:
                print("⚠️  No aggregate device found")
                # Show warning on first launch
                threading.Timer(2.0, self.show_aggregate_warning).start()
        
        except Exception as e:
            print(f"Error checking audio devices: {e}")
    
    def show_aggregate_warning(self):
        """Show warning if aggregate device is not configured."""
        response = rumps.alert(
            "Aggregate Device Not Found",
            "To use Call Recording mode, you need to set up an Aggregate Device.\n\n"
            "This combines your microphone + system audio (via BlackHole) "
            "to record both sides of online calls.\n\n"
            "Would you like to see setup instructions?",
            ok="Show Instructions",
            cancel="Skip for now"
        )
        
        if response == 1:  # OK clicked
            # Open setup guide
            setup_file = Path(__file__).parent.parent / "CALL_RECORDING_SETUP.md"
            if setup_file.exists():
                os.system(f'open "{setup_file}"')
            else:
                rumps.alert(
                    "Setup Guide",
                    "Setup guide not found!\n\n"
                    "Check CALL_RECORDING_SETUP.md in the project folder."
                )
    
    @rumps.clicked("🎤 Quick Practice")
    def start_quick_practice(self, sender):
        """Start quick practice recording (single speaker, mono)."""
        if self.recording or self.call_recording:
            self.stop_recording()
        else:
            self.call_recording = False
            self.start_recording(mono=True)
    
    @rumps.clicked("📞 Start Call Recording")
    def start_call_recording(self, sender):
        """Start call recording (multi-speaker, stereo from aggregate device)."""
        if self.recording or self.call_recording:
            # Stop current recording
            self.stop_recording()
        else:
            # Check if aggregate device is selected
            if self.selected_device_index is None:
                response = rumps.alert(
                    "Select Audio Device",
                    "Please select your Aggregate Device first.\n\n"
                    "Click 'Select Audio Device' in the menu.",
                    ok="Select Now",
                    cancel="Cancel"
                )
                
                if response == 1:
                    self.select_audio_device(None)
                return
            
            self.call_recording = True
            self.start_recording(mono=False, device_index=self.selected_device_index)
    
    def start_recording(self, mono=True, device_index=None):
        """Start audio recording."""
        self.recording = True
        self.frames = []
        self.recording_start_time = time.time()
        
        # Update menu based on mode
        if self.call_recording:
            self.menu["📞 Start Call Recording"].title = "⏹️ Stop Call"
            self.title = "🔴 Recording 00:00"
        else:
            self.menu["🎤 Quick Practice"].title = "⏹ Stop Practice"
            self.title = "🔴 Recording..."
        
        # Notify
        mode = "Call Recording" if self.call_recording else "Quick Practice"
        rumps.notification(
            "English Practice",
            f"{mode} started",
            "Click menu to stop." if self.call_recording else "Speak in English. Click to stop."
        )
        
        # Start recording in background
        thread = threading.Thread(
            target=self._record_audio,
            args=(mono, device_index),
            daemon=True
        )
        thread.start()
        
        # Start timer update for call recording
        if self.call_recording:
            self._update_timer()
    
    def _update_timer(self):
        """Update recording timer in menu bar."""
        if self.call_recording and self.recording:
            elapsed = int(time.time() - self.recording_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.title = f"🔴 Recording {mins:02d}:{secs:02d}"
            
            # Schedule next update
            threading.Timer(1.0, self._update_timer).start()
    
    def stop_recording(self):
        """Stop recording and analyze."""
        self.recording = False
        
        # Update menu
        if self.call_recording:
            self.menu["📞 Start Call Recording"].title = "📞 Start Call Recording"
        else:
            self.menu["🎤 Quick Practice"].title = "🎤 Quick Practice"
        
        self.title = "🎤 English Practice"
        
        # Notify
        mode = "Call" if self.call_recording else "Practice"
        rumps.notification(
            "English Practice",
            f"{mode} recording stopped",
            "Analyzing your speech..."
        )
        
        # Save and analyze
        thread = threading.Thread(target=self._save_and_analyze, daemon=True)
        thread.start()
    
    def _record_audio(self, mono=True, device_index=None):
        """Record audio in background."""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Save sample width before audio is terminated
            self.sample_width = self.audio.get_sample_size(FORMAT)
            
            channels = 1 if mono else 2
            
            stream_params = {
                'format': FORMAT,
                'channels': channels,
                'rate': RATE,
                'input': True,
                'frames_per_buffer': CHUNK
            }
            
            if device_index is not None:
                stream_params['input_device_index'] = device_index
            
            self.stream = self.audio.open(**stream_params)
            
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
                f"Failed to record audio: {e}\n\n"
                "Make sure your audio device is properly configured."
            )
    
    def _save_and_analyze(self):
        """Save audio and send to backend for analysis."""
        try:
            # Determine save location and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.call_recording:
                save_dir = CALL_DIR
                audio_file = save_dir / f"call_{timestamp}.wav"
            else:
                save_dir = TEMP_DIR
                audio_file = save_dir / f"recording_{timestamp}.wav"
            
            # Determine channels
            channels = 1 if not self.call_recording else 2
            
            # Save WAV file
            with wave.open(str(audio_file), 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(self.sample_width)  # Fixed: use saved value instead of terminated audio object
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
            
            self.last_audio_file = audio_file
            print(f"✅ Saved: {audio_file}")
            
            # Analyze based on mode
            if self.call_recording:
                # Call recording: always use diarization for multi-speaker
                self._analyze_call(audio_file)
            else:
                # Quick practice: use existing logic
                if self.enable_diarization and self.target_speaker is None:
                    self._detect_speakers_then_analyze(audio_file)
                else:
                    self._analyze_audio(audio_file)
            
        except Exception as e:
            rumps.alert(
                "Analysis Error",
                f"Failed to save/analyze: {e}"
            )
    
    def _analyze_call(self, audio_file):
        """Analyze call recording with automatic multi-speaker detection."""
        try:
            print("Analyzing call recording with diarization...")
            
            # Send to backend for analysis (no target speaker = analyze all)
            with open(audio_file, 'rb') as f:
                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    files={'file': f},
                    data={'enable_diarization': 'true'},
                    timeout=180
                )
            
            if response.status_code != 200:
                rumps.alert(
                    "Backend Error",
                    f"Analysis failed: {response.text}"
                )
                return
            
            result = response.json()
            self.last_result = result
            
            # Show call results with both speakers
            self._show_call_results(result)
            self._save_call_report(result, audio_file)
            
        except requests.exceptions.RequestException as e:
            rumps.alert(
                "Backend Connection Error",
                f"Could not connect to backend server:\n{e}\n\n"
                "Make sure the backend is running."
            )
        except Exception as e:
            rumps.alert(
                "Analysis Error",
                f"Failed to analyze call: {e}"
            )
    
    def _show_call_results(self, result):
        """Show call recording results with both speakers."""
        # Get speaker info from result
        summary = result.get('summary', {})
        duration = summary.get('duration', 0)
        
        # Check if we have speaker breakdown
        speaker_breakdown = result.get('speaker_breakdown', None)
        
        if speaker_breakdown and len(speaker_breakdown) >= 2:
            # Multi-speaker analysis
            speakers = list(speaker_breakdown.values())
            
            # Assume Speaker 0 is teacher, Speaker 1 is student (can be reversed)
            teacher = speakers[0]
            student = speakers[1] if len(speakers) > 1 else speakers[0]
            
            teacher_errors = teacher.get('grammar', {}).get('total_errors', 0)
            student_errors = student.get('grammar', {}).get('total_errors', 0)
            
            teacher_score = teacher.get('overall_score', 0)
            student_score = student.get('overall_score', 0)
            
            message = (
                f"🎓 Урок завершён\n\n"
                f"Ученик (Speaker 1): {student_errors} ошибки (Grammar: {student_score}/100)\n"
                f"Преподаватель (Speaker 0): {teacher_errors} ошибка (Grammar: {teacher_score}/100)\n\n"
                f"→ Смотреть отчёт"
            )
            
            rumps.notification(
                "🎓 Урок завершён",
                f"Продолжительность: {self._format_time(duration)}",
                message,
                sound=True
            )
        else:
            # Single speaker or no diarization
            overall = result.get('overall_score', 0)
            grammar_errors = result.get('grammar', {}).get('total_errors', 0)
            
            message = (
                f"Оценка: {overall}/100\n"
                f"Ошибки: {grammar_errors}\n"
                f"Продолжительность: {self._format_time(duration)}"
            )
            
            rumps.notification(
                "Анализ завершён",
                f"Оценка: {overall}/100",
                message,
                sound=True
            )
        
        # Show detailed window
        self._show_detailed_call_window(result)
    
    def _show_detailed_call_window(self, result):
        """Show detailed call results window."""
        speaker_breakdown = result.get('speaker_breakdown', None)
        
        if speaker_breakdown and len(speaker_breakdown) >= 2:
            # Multi-speaker
            speakers = list(speaker_breakdown.values())
            
            lines = [
                "🎓 УРОК ЗАВЕРШЁН",
                ""
            ]
            
            for i, speaker in enumerate(speakers):
                speaker_name = f"Speaker {i}"
                role = "Преподаватель" if i == 0 else "Ученик"
                
                score = speaker.get('overall_score', 0)
                errors = speaker.get('grammar', {}).get('total_errors', 0)
                speaking_time = speaker.get('summary', {}).get('speaking_time', 0)
                
                lines.append(f"{role} ({speaker_name}):")
                lines.append(f"  Оценка: {score}/100")
                lines.append(f"  Ошибки: {errors}")
                lines.append(f"  Время речи: {self._format_time(speaking_time)}")
                lines.append("")
            
            lines.append("📊 Полный отчёт сохранён в папке call_recordings/")
            
            rumps.alert(
                "🎓 Анализ урока",
                "\n".join(lines)
            )
        else:
            # Single speaker - use existing logic
            self._show_detailed_window(result)
    
    def _save_call_report(self, result, audio_file):
        """Save detailed call report with both speakers."""
        report_file = audio_file.with_suffix('.txt')
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("🎓 ENGLISH LESSON CALL RECORDING ANALYSIS\n")
            f.write("="*70 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Audio: {audio_file.name}\n\n")
            
            summary = result.get('summary', {})
            f.write(f"Total Duration: {self._format_time(summary.get('duration', 0))}\n\n")
            
            # Check for speaker breakdown
            speaker_breakdown = result.get('speaker_breakdown', None)
            
            if speaker_breakdown:
                f.write("👥 MULTI-SPEAKER ANALYSIS\n")
                f.write("-"*70 + "\n\n")
                
                for speaker_id, speaker_data in speaker_breakdown.items():
                    role = "Преподаватель (Teacher)" if speaker_id == "speaker_0" else "Ученик (Student)"
                    
                    f.write(f"{'='*70}\n")
                    f.write(f"{role} - {speaker_id.upper()}\n")
                    f.write(f"{'='*70}\n\n")
                    
                    speaker_summary = speaker_data.get('summary', {})
                    f.write(f"Overall Score:      {speaker_data.get('overall_score', 0)}/100\n")
                    f.write(f"Speaking Time:      {self._format_time(speaker_summary.get('speaking_time', 0))}\n")
                    f.write(f"Speaking %:         {speaker_summary.get('speaking_percentage', 0)}%\n")
                    f.write(f"Grammar Errors:     {speaker_data.get('grammar', {}).get('total_errors', 0)}\n\n")
                    
                    # Top errors for this speaker
                    top_errors = speaker_data.get('top_errors', [])
                    if top_errors:
                        f.write(f"🔥 TOP ERRORS ({speaker_id}):\n")
                        f.write("-"*70 + "\n\n")
                        
                        for i, err in enumerate(top_errors[:3], 1):
                            cambridge = err.get('cambridge', {})
                            example = err['all_examples'][0] if err['all_examples'] else {}
                            
                            f.write(f"{i}. {cambridge.get('title', err['category'])} ({err['occurrences']}x)\n")
                            f.write(f"❌ {self._format_time(example.get('timestamp'))} \"{example.get('incorrect_text', '')}\"\n")
                            if err['replacements']:
                                f.write(f"✅ Should be: \"{err['replacements'][0]}\"\n")
                            f.write("\n")
                    
                    f.write("\n")
            else:
                # Single speaker fallback
                f.write("📊 SINGLE SPEAKER ANALYSIS\n")
                f.write("-"*70 + "\n")
                f.write(f"Overall Score: {result.get('overall_score', 0)}/100\n")
                f.write(f"Grammar Errors: {result.get('grammar', {}).get('total_errors', 0)}\n\n")
            
            f.write("="*70 + "\n")
        
        print(f"✅ Call report saved: {report_file}")
    
    def _detect_speakers_then_analyze(self, audio_file):
        """Detect speakers first, then ask user to select."""
        try:
            print("Detecting speakers...")
            
            with open(audio_file, 'rb') as f:
                response = requests.post(
                    f"{BACKEND_URL}/speakers",
                    files={'file': f},
                    timeout=60
                )
            
            if response.status_code != 200:
                # Fallback: analyze without diarization
                self._analyze_audio(audio_file, enable_diarization=False)
                return
            
            data = response.json()
            speakers = data['speakers']
            
            if speakers['total'] > 1:
                # Ask user to select speaker
                self._ask_speaker_selection(speakers, audio_file)
            else:
                # Single speaker, proceed
                self._analyze_audio(audio_file)
        
        except Exception as e:
            print(f"Speaker detection failed: {e}")
            # Fallback: analyze without diarization
            self._analyze_audio(audio_file, enable_diarization=False)
    
    def _ask_speaker_selection(self, speakers, audio_file):
        """Ask user which speaker to analyze."""
        stats = speakers['stats']
        
        # Build message
        speaker_info = []
        for s in stats:
            speaker_info.append(f"Speaker {s['id']}: {s['total_time']:.1f}s")
        
        message = (
            f"Found {speakers['total']} speakers:\n\n" +
            "\n".join(speaker_info) +
            "\n\nWhich speaker is YOU?"
        )
        
        response = rumps.Window(
            message,
            "Select Speaker",
            default_text="0",
            dimensions=(320, 100)
        ).run()
        
        if response.clicked:
            try:
                selected = int(response.text)
                self._analyze_audio(audio_file, target_speaker=selected)
            except ValueError:
                rumps.alert("Invalid Input", "Please enter a number (0, 1, 2...)")
    
    def _analyze_audio(self, audio_file, enable_diarization=None, target_speaker=None):
        """Send audio to backend for analysis."""
        try:
            if enable_diarization is None:
                enable_diarization = self.enable_diarization
            
            if target_speaker is None:
                target_speaker = self.target_speaker
            
            print(f"Analyzing with backend...")
            print(f"  Diarization: {enable_diarization}")
            print(f"  Target speaker: {target_speaker if target_speaker is not None else 'All'}")
            
            # Prepare request
            files = {'file': open(audio_file, 'rb')}
            data = {
                'enable_diarization': 'true' if enable_diarization else 'false'
            }
            
            if target_speaker is not None:
                data['target_speaker'] = str(target_speaker)
            
            # Send to backend
            response = requests.post(
                f"{BACKEND_URL}/analyze",
                files=files,
                data=data,
                timeout=120
            )
            
            files['file'].close()
            
            if response.status_code != 200:
                rumps.alert(
                    "Backend Error",
                    f"Analysis failed: {response.text}"
                )
                return
            
            result = response.json()
            self.last_result = result
            
            # Show results
            self._show_results(result)
            self._save_report(result, audio_file)
            
        except requests.exceptions.RequestException as e:
            rumps.alert(
                "Backend Connection Error",
                f"Could not connect to backend server:\n{e}\n\n"
                "Make sure the backend is running."
            )
        except Exception as e:
            rumps.alert(
                "Analysis Error",
                f"Failed to analyze: {e}"
            )
    
    def _show_results(self, result):
        """Show analysis results."""
        overall = result['overall_score']
        grammar_errors = result['grammar']['total_errors']
        duration = result['summary']['duration']
        
        emoji = "🎉" if overall >= 90 else "✅" if overall >= 75 else "⚠️"
        
        message = (
            f"{emoji} Score: {overall}/100\n"
            f"Duration: {self._format_time(duration)}\n"
            f"Errors: {grammar_errors} grammar"
        )
        
        # Use osascript for notifications (rumps.notification doesn't work in background)
        self._show_notification(
            "Analysis Complete",
            f"Overall: {overall}/100",
            message
        )
        
        # Detailed window
        self._show_detailed_window(result)
    
    def _show_detailed_window(self, result):
        """Show detailed results window."""
        overall = result['overall_score']
        summary = result['summary']
        top_errors = result.get('top_errors', [])
        
        # Summary
        lines = [
            f"📊 SUMMARY",
            f"Overall: {overall}/100",
            f"Duration: {self._format_time(summary['duration'])}",
            f"Speaking: {self._format_time(summary['speaking_time'])} ({summary['speaking_percentage']}%)",
            f"Errors: {result['grammar']['total_errors']} grammar",
            ""
        ]
        
        # Top-3
        if top_errors:
            lines.append("🔥 TOP 3 ERRORS:")
            
            for i, err in enumerate(top_errors[:3], 1):
                cambridge = err.get('cambridge', {})
                example = err['all_examples'][0] if err['all_examples'] else {}
                
                timestamp = self._format_time(example.get('timestamp'))
                incorrect = example.get('incorrect_text', '')
                correct = err['replacements'][0] if err['replacements'] else '?'
                
                lines.append(f"\n{i}. {cambridge.get('title', err['category'])} ({err['occurrences']}x)")
                lines.append(f"{timestamp} ❌ \"{incorrect}\"")
                lines.append(f"         ✅ \"{correct}\"")
        else:
            lines.append("✅ No errors found! Perfect!")
        
        # Use osascript for alert (rumps.alert doesn't work in background)
        self._show_alert(
            "📊 Analysis Results",
            "\n".join(lines)
        )
    
    def _save_report(self, result, audio_file):
        """Save detailed report as text file."""
        report_file = audio_file.with_suffix('.txt')
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("🎯 ENGLISH SPEAKING PRACTICE ANALYSIS\n")
            f.write("="*70 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Audio: {audio_file.name}\n\n")
            
            # Summary
            f.write("📊 SUMMARY\n")
            f.write("-"*70 + "\n")
            f.write(f"Overall Score:      {result['overall_score']}/100\n")
            f.write(f"Duration:           {self._format_time(result['summary']['duration'])}\n")
            f.write(f"Your speaking time: {self._format_time(result['summary']['speaking_time'])} ({result['summary']['speaking_percentage']}%)\n")
            f.write(f"Errors found:       {result['grammar']['total_errors']} grammar\n\n")
            
            # Top errors
            top_errors = result.get('top_errors', [])
            if top_errors:
                f.write("🔥 TOP 3 CRITICAL ERRORS\n")
                f.write("-"*70 + "\n\n")
                
                for i, err in enumerate(top_errors[:3], 1):
                    cambridge = err.get('cambridge', {})
                    example = err['all_examples'][0] if err['all_examples'] else {}
                    
                    f.write(f"{i}. {cambridge.get('title', err['category'])} (occurred {err['occurrences']} time(s))\n")
                    f.write(f"❌ {self._format_time(example.get('timestamp'))} \"{example.get('incorrect_text', '')}\"\n")
                    if err['replacements']:
                        f.write(f"✅ Should be: \"{err['replacements'][0]}\"\n")
                    if cambridge:
                        f.write(f"📚 {cambridge.get('explanation', '')}\n")
                        f.write(f"📕 {cambridge.get('book', '')} - {cambridge.get('unit', '')}\n")
                    f.write("\n")
            
            # All errors timeline
            all_errors = result['grammar'].get('errors', [])
            if all_errors:
                f.write("📝 ALL ERRORS (TIMELINE)\n")
                f.write("-"*70 + "\n")
                
                for err in all_errors:
                    timestamp = self._format_time(err.get('timestamp'))
                    error_type = "Grammar" if err['severity'] == 'error' else "Warning"
                    correct = err['replacements'][0] if err['replacements'] else '?'
                    
                    f.write(f"{timestamp} | {error_type} | \"{err['incorrect_text']}\" → \"{correct}\"\n")
                
                f.write("\n")
            
            f.write("="*70 + "\n")
        
        print(f"✅ Report saved: {report_file}")
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS."""
        if seconds is None:
            return "??:??"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    @rumps.clicked("📊 View Reports")
    def view_reports(self, sender):
        """Open call recordings folder."""
        os.system(f'open "{CALL_DIR}"')
    
    @rumps.clicked("Last Analysis")
    def show_last_analysis(self, sender):
        """Show last analysis results."""
        if self.last_result:
            if self.last_result.get('speaker_breakdown'):
                self._show_detailed_call_window(self.last_result)
            else:
                self._show_detailed_window(self.last_result)
        else:
            rumps.alert("No Analysis Yet", "Record something first!")
    
    @rumps.clicked("Open Results Folder")
    def open_results_folder(self, sender):
        """Open folder with recordings."""
        os.system(f'open "{TEMP_DIR}"')
    
    @rumps.clicked("🎙️ Select Audio Device")
    def select_audio_device(self, sender):
        """Let user select audio input device."""
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            devices = []
            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    devices.append((i, info.get('name', f'Device {i}')))
            
            p.terminate()
            
            if not devices:
                rumps.alert("No Audio Devices", "No input devices found!")
                return
            
            # Build selection dialog
            device_list = "\n".join([f"{i}. {name}" for i, name in devices])
            
            response = rumps.Window(
                f"Select audio input device:\n\n{device_list}\n\nEnter device number:",
                "Select Audio Device",
                default_text="0",
                dimensions=(400, 200)
            ).run()
            
            if response.clicked:
                try:
                    selected_idx = int(response.text)
                    
                    # Find matching device
                    for dev_idx, dev_name in devices:
                        if dev_idx == selected_idx:
                            self.selected_device_index = dev_idx
                            
                            rumps.notification(
                                "Audio Device Selected",
                                dev_name,
                                f"Device index: {dev_idx}"
                            )
                            
                            print(f"✅ Selected device: {dev_name} (index {dev_idx})")
                            return
                    
                    rumps.alert("Invalid Device", f"Device {selected_idx} not found!")
                
                except ValueError:
                    rumps.alert("Invalid Input", "Please enter a device number.")
        
        except Exception as e:
            rumps.alert("Error", f"Failed to list audio devices: {e}")
    
    @rumps.clicked("Speaker Diarization: ON")
    def toggle_diarization(self, sender):
        """Toggle speaker diarization."""
        self.enable_diarization = not self.enable_diarization
        
        status = "ON" if self.enable_diarization else "OFF"
        sender.title = f"Speaker Diarization: {status}"
        
        rumps.notification(
            "English Practice",
            f"Speaker Diarization {status}",
            "Will detect multiple speakers" if self.enable_diarization else "Single speaker mode"
        )
    
    def _show_notification(self, title, subtitle, message):
        """Show macOS notification using osascript (works in background)."""
        try:
            # Escape quotes in message
            message_escaped = message.replace('"', '\\"').replace("'", "\\'")
            subtitle_escaped = subtitle.replace('"', '\\"').replace("'", "\\'")
            title_escaped = title.replace('"', '\\"').replace("'", "\\'")
            
            script = f'display notification "{message_escaped}" with title "{title_escaped}" subtitle "{subtitle_escaped}" sound name "Glass"'
            subprocess.run(['osascript', '-e', script], check=False, capture_output=True)
        except Exception as e:
            print(f"Notification failed: {e}")
    
    def _show_alert(self, title, message):
        """Show macOS alert dialog using osascript (works in background)."""
        try:
            # Escape quotes
            message_escaped = message.replace('"', '\\"').replace("'", "\\'")
            title_escaped = title.replace('"', '\\"').replace("'", "\\'")
            
            script = f'display dialog "{message_escaped}" with title "{title_escaped}" buttons {{"OK"}} default button "OK"'
            subprocess.run(['osascript', '-e', script], check=False, capture_output=True)
        except Exception as e:
            print(f"Alert failed: {e}")
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS."""
        if seconds is None:
            return "?"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    @rumps.clicked("Settings")
    def show_settings(self, sender):
        """Show settings."""
        diarization_status = "ON" if self.enable_diarization else "OFF"
        device_name = "Default" if self.selected_device_index is None else f"Device {self.selected_device_index}"
        
        # Check backend status
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            backend_status = "✅ Connected" if response.status_code == 200 else "❌ Error"
        except:
            backend_status = "❌ Not running"
        
        rumps.alert(
            "Settings",
            f"Backend Server: {backend_status}\n"
            f"Audio Device: {device_name}\n"
            f"Speaker Diarization: {diarization_status}\n\n"
            f"Quick Practice folder:\n{TEMP_DIR}\n\n"
            f"Call Recordings folder:\n{CALL_DIR}"
        )
    
    @rumps.clicked("About")
    def show_about(self, sender):
        """Show about dialog."""
        rumps.alert(
            "English Speaking Practice v2.1",
            "Version 2.1 (Call Recording Mode)\n\n"
            "Features:\n"
            "• Quick practice mode\n"
            "• Call recording mode (teachers)\n"
            "• Speaker diarization (multi-speaker)\n"
            "• Timestamps for all errors\n"
            "• Cambridge Grammar explanations\n"
            "• Grammar + Fluency + Pronunciation\n\n"
            "Built with ❤️ for English learners & teachers"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, sender):
        """Quit application."""
        rumps.quit_application()


if __name__ == "__main__":
    print("🚀 Starting English Practice App (Microservice Client v2.1)...")
    app = EnglishPracticeApp()
    app.run()
