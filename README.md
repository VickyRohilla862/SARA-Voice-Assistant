<div align="center">
<br><br>
   <img src="https://readme-typing-svg.demolab.com?font=IBM+Plex+Sans&size=40&pause=1300&color=0088ff&center=true&vCenter=true&width=700&lines=SARA+Voice+Assistant;Smart+Automated+Response+Assistant" alt="SARA Animated Title" />
<br>
<br>
  <p>Smart Automated Response Assistant for Windows with voice, GUI, automation, realtime search, and image generation.</p>

  <p>
    <img src="https://img.shields.io/badge/Platform-Windows-0078D6" alt="Windows" />
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB" alt="Python" />
    <img src="https://img.shields.io/badge/UI-PyQt5-41CD52" alt="PyQt5" />
    <img src="https://img.shields.io/badge/Status-Active-2ea44f" alt="Status" />
  </p>

</div>

---

## Overview
SARA is a Windows-first voice assistant that blends real-time speech recognition, text-to-speech, system automation, and AI responses with a polished PyQt5 interface. It supports conversational chat, live web search, content creation, and on-demand image generation.

## Highlights
- Wake word detection with interrupt-aware speech handling
- Live GUI with mic status and assistant feedback
- System automation (apps, volume, screenshots, screen recording)
- Realtime web search and conversational responses
- Content creation and presentation generation
- Image generation via Hugging Face models

## Project Structure
- `Main.py` - main entry point and orchestration
- `Backend/` - speech, model routing, automation, and search
- `Frontend/` - PyQt5 GUI and assets
- `Data/` - runtime data and generated files
- `requirements.txt` - Python dependencies

## Prerequisites
- Windows 10/11
- Python 3.10+ (recommended)
- Working microphone and speakers

## VS Code Setup
1. Install VS Code and the Python extension (Microsoft).
2. Open this folder in VS Code.
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Select the interpreter:
   - `Ctrl+Shift+P` -> `Python: Select Interpreter` -> `.venv`
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Create a `.env` file in the project root.

## Environment Variables
Create a `.env` file next to `Main.py`.

Example:
```env
CohereAPIKey=Your_Cohere_API_KEY_Here
Username=Your_Name
AssistantName=Sara
GroqAPIKey=Your_Groq_API_KEY_Here
InputLanguage=en
AssistantVoice = en-IN-NeerjaNeural
HUGGINGFACE_API_KEY=Your_Huggingface_API_KEY_Here

```

Note:
- `InputLanguage` controls speech recognition (for example: `en-IN`, `hi-IN`).

## Run
```powershell
python Main.py
```

## Troubleshooting
- If audio input/output is not working, verify Windows microphone permissions and default devices.
- If `PyAudio` fails to install, upgrade pip and retry: `python -m pip install --upgrade pip`.
- If the GUI does not appear, confirm `PyQt5` is installed correctly.
- If image generation fails, check your Hugging Face token and internet access.
