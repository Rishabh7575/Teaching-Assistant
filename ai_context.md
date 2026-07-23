# Project Context: Educator's Assistant (Stealth Code)

## Project Aim
The **Educator's Assistant** is a desktop application designed for teachers (educators) to access real-time supplemental teaching resources and answers stealthily. The UI must remain hidden from students who are viewing the shared classroom screen, but easily viewable by the teacher on their primary display or as a floating overlay.

---

## Key Features & Hotkeys
* **Draggable Floating Panel**: Sleek dark UI containing summaries, bulleted key points, and recommended resource links.
* **Region/Full Screen Capture**: Crops a selected part of the screen silently to send to visual models for analysis.
* **Voice Teaching Assistant**: Records voice inputs, converts speech to text, and retrieves answers using AI.
* **Global Hotkeys**:
  - `Ctrl + Shift + O`: Toggle floating panel visibility.
  - `Ctrl + Shift + S`: Capture screen area & analyze (Image Search).
  - `Ctrl + Shift + C`: Fast screenshot capture to memory.
  - `Ctrl + Shift + R`: Reset local buffers.
  - `Ctrl + Shift + V`: Start/Stop Voice recording.

---

## File Structure & Responsibilities
- **[main.py](file:///d:/AntiGravity%20Projects/StealthCode/main.py)**: Entry point. Listens for global hotkeys, runs background worker threads (`QThreadPool`), and manages application-wide state/signals.
- **[ui.py](file:///d:/AntiGravity%20Projects/StealthCode/ui.py)**: GUI layout and elements in PyQt6 (Floating Panel, Toast notifications, listening animations).
- **[capture.py](file:///d:/AntiGravity%20Projects/StealthCode/capture.py)**: Handles region selection using a custom rubber-band crop overlay and screenshot saving via `mss`.
- **[api_handler.py](file:///d:/AntiGravity%20Projects/StealthCode/api_handler.py)**: Houses the `AIRouter` and abstract `AIProvider` hierarchy (Gemini, OpenAI, Ollama fallbacks).
- **[speech_handler.py](file:///d:/AntiGravity%20Projects/StealthCode/speech_handler.py)**: Manages recording audio and transcribing it using `SpeechProvider` instances (Faster-Whisper, OpenAI Whisper API, Google Speech API).
- **[database.py](file:///d:/AntiGravity%20Projects/StealthCode/database.py)**: Local SQLite interface storing query history, bookmarks, and notes.

---

## State Flow for Search
1. **Screen Search**:
   - `Ctrl + Shift + S` -> `main.py` hides panel -> captures crop/full screen via `capture.py` -> calls `api_handler.py` -> shows panel with dynamic HTML content.
2. **Voice Search**:
   - `Ctrl + Shift + V` -> UI starts listening indicator -> records audio in background -> converts speech to text via `speech_handler.py` -> sends query to `api_handler.py` -> updates panel.
