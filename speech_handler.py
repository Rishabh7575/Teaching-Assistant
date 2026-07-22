import os
import time
import abc
import requests
import json

# Optionally import audio libraries
try:
    import numpy as np
    import scipy.io.wavfile as wav
    HAS_AUDIO_LIBS = True
except ImportError:
    HAS_AUDIO_LIBS = False
import threading

class SpeechProvider(abc.ABC):
    @abc.abstractmethod
    def transcribe(self, audio_file_path: str) -> str:
        pass


class FasterWhisperProvider(SpeechProvider):
    """
    Uses the local faster-whisper package.
    """
    def __init__(self, model_size="tiny"):
        self.model_size = model_size
        self.model = None

    def transcribe(self, audio_file_path: str) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("faster-whisper library is not installed.")
        
        if not self.model:
            # Run model on CPU with int8 quantization for speed & memory optimization
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        
        segments, info = self.model.transcribe(audio_file_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()


class OpenAIWhisperProvider(SpeechProvider):
    """
    Uses the OpenAI Whisper API.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def transcribe(self, audio_file_path: str) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API Key is not set.")
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        files = {
            "file": (os.path.basename(audio_file_path), open(audio_file_path, "rb"), "audio/wav"),
        }
        data = {
            "model": "whisper-1"
        }
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=20)
        response.raise_for_status()
        return response.json().get("text", "").strip()


# class GoogleSpeechProvider(SpeechProvider):
#     """
#     Uses Google Cloud / SpeechRecognition API.
#     """
#     def transcribe(self, audio_file_path: str) -> str:
#         try:
#             import speech_recognition as sr
#         except ImportError:
#             raise ImportError("speech_recognition library is not installed.")
        
#         recognizer = sr.Recognizer()
#         with sr.AudioFile(audio_file_path) as source:
#             audio_data = recognizer.record(source)
#             text = recognizer.recognize_google(audio_data)
#             return text.strip()


# class SpeechRouter:
#     def __init__(self, provider_name: str = "google"):
#         self.provider_name = provider_name.lower()
#         self.providers = {
#             "faster-whisper": FasterWhisperProvider(),
#             "openai": OpenAIWhisperProvider(),
#             "google": GoogleSpeechProvider()
#         }

#     def transcribe(self, audio_file_path: str) -> str:
#         # Check active provider
#         provider = self.providers.get(self.provider_name)
#         if provider:
#             try:
#                 return provider.transcribe(audio_file_path)
#             except Exception as e:
#                 print(f"Preferred provider {self.provider_name} failed: {e}. Falling back...")
        
#         # Fallback sequence: google -> openai -> faster-whisper
#         errors = []
#         for name, prov in self.providers.items():
#             try:
#                 return prov.transcribe(audio_file_path)
#             except Exception as e:
#                 errors.append(f"{name}: {str(e)}")
        
#         raise Exception(f"All STT Providers failed. Errors: {errors}")

# # Time Duration for auto sending
# def record_audio_until_silence(output_path: str, silence_threshold=0.01, silence_duration=2.5, sample_rate=16000, max_duration=30, cancel_trigger=None) -> bool:
#     """
#     Records audio from the default microphone and saves to output_path.
#     Stops when silence is detected for silence_duration seconds, or when cancel_trigger() returns True.
#     Returns True if successfully recorded, False if cancelled or failed.
#     """
#     if not HAS_AUDIO_LIBS:
#         print("Missing numpy or scipy. Cannot record audio.")
#         return False
        
#     try:
#         import soundcard as sc
#     except ImportError:
#         print("soundcard not installed.")
#         return False
        
#     print("Recording started (Mic + System Loopback)...")
    
#     chunk_duration = 0.1  # 100ms chunks
#     chunk_samples = int(sample_rate * chunk_duration)
    
#     try:
#         mics = sc.all_microphones(include_loopback=True)
#         default_speaker_name = sc.default_speaker().name
#         speaker = None
#         for m in mics:
#             if m.isloopback and default_speaker_name in m.name:
#                 speaker = m
#                 break
#         if not speaker:
#             for m in mics:
#                 if m.isloopback:
#                     speaker = m
#                     break
                    
#         mic = sc.default_microphone()
#     except Exception as e:
#         print(f"Error getting audio devices: {e}")
#         return False

#     mic_data = []
#     speaker_data = []
    
#     stop_event = threading.Event()
    
#     def record_mic():
#         try:
#             with mic.recorder(samplerate=sample_rate, channels=1) as recorder:
#                 while not stop_event.is_set():
#                     data = recorder.record(numframes=chunk_samples)
#                     mic_data.append(data)
#         except Exception as e:
#             print("Mic error:", e)

#     def record_speaker():
#         try:
#             with speaker.recorder(samplerate=sample_rate, channels=1) as recorder:
#                 while not stop_event.is_set():
#                     data = recorder.record(numframes=chunk_samples)
#                     speaker_data.append(data)
#         except Exception as e:
#             print("Speaker loopback error:", e)
            
#     t_mic = threading.Thread(target=record_mic)
#     t_speaker = threading.Thread(target=record_speaker)
#     t_mic.start()
#     t_speaker.start()
    
#     start_time = time.time()
#     silent_chunks_required = int(silence_duration / chunk_duration)
#     silent_chunk_count = 0
    
#     try:
#         while True:
#             time.sleep(chunk_duration)
            
#             if cancel_trigger and cancel_trigger():
#                 print("Recording cancelled.")
#                 stop_event.set()
#                 return False
                
#             if (time.time() - start_time) > max_duration:
#                 print("Reached max recording duration.")
#                 stop_event.set()
#                 break
                
#             if len(mic_data) > 0:
#                 latest_mic = mic_data[-1]
#                 volume = np.sqrt(np.mean(latest_mic**2))
#                 if volume < silence_threshold:
#                     silent_chunk_count += 1
#                 else:
#                     silent_chunk_count = 0
                    
#                 if silent_chunk_count >= silent_chunks_required:
#                     print("Silence detected. Stopping recording.")
#                     stop_event.set()
#                     break
#     finally:
#         stop_event.set()
#         t_mic.join(timeout=1.0)
#         t_speaker.join(timeout=1.0)
        
#     if mic_data and speaker_data:
#         m_arr = np.concatenate(mic_data, axis=0)
#         s_arr = np.concatenate(speaker_data, axis=0)
        
#         max_len = max(len(m_arr), len(s_arr))
#         m_arr = np.pad(m_arr, ((0, max_len - len(m_arr)), (0, 0)))
#         s_arr = np.pad(s_arr, ((0, max_len - len(s_arr)), (0, 0)))
        
#         mixed = m_arr + s_arr
#         max_val = np.max(np.abs(mixed))
#         if max_val > 0:
#             mixed = (mixed / max_val * 32767).astype(np.int16)
#         else:
#             mixed = mixed.astype(np.int16)
            
#         wav.write(output_path, sample_rate, mixed)
#         return True

#     return False
