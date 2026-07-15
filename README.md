# BlenderGPT - AI Blender Assistant

**Version 3.3** | Blender 5.1+ | DeepSeek AI

An intelligent AI agent that fully controls Blender via natural language. Powered by DeepSeek AI (OpenAI-compatible). Features auto error fixing, full scene understanding, and chat-based interaction.

---

## Features

- **Chat-Based AI Agent** - Natural conversation with full Blender control
- **Full Scene Understanding** - AI automatically detects all objects, materials, animations, collections, and scene state before responding
- **Complete Blender Control** - Modeling, animation, materials, rendering, physics, particles, compositing, VSE, and everything else
- **Auto Error Learning** - When code fails, AI apologizes, analyzes the root cause, learns from it, and provides a fix
- **3x Auto-Retry** - Up to 3 attempts with different approaches on error
- **Self-Review Protocol** - AI checks 10 common bugs before outputting code
- **DeepSeek Reasoner Support** - Uses advanced reasoning model for complex tasks by default
- **Image Upload** - Send images for AI to analyze (vision support)
- **Upload & Analyze Images** - AI can see and describe images related to 3D modeling
- **Chat Bubbles UI** - Clean chat interface with user/AI message separation
- **Thinking Indicator** - Shows when AI is processing
- **View Code** - Inspect generated Python code in Blender's Text Editor
- **Run Code** - Execute AI-generated code with one click
- **Auto-Execute Toggle** - Automatically run generated code or review first
- **Full Chat History** - AI remembers entire conversation context
- **Multi-Model** - Supports DeepSeek Chat, DeepSeek Reasoner, and any OpenAI-compatible API

---

## Quick Start

### 1. Install OpenAI Library

```bash
# Windows
"C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" -m pip install openai>=1.0.0

# macOS
/Applications/Blender.app/Contents/Resources/5.1/python/bin/python3 -m pip install openai>=1.0.0

# Linux
/path/to/blender/5.1/python/bin/python3 -m pip install openai>=1.0.0
```

### 2. Install Add-on

1. Download or clone this repository
2. Open Blender -> `Edit` -> `Preferences` -> `Add-ons`
3. Click `Install...` and select the folder as ZIP
4. Enable **"AI Blender Assistant"**

### 3. Set API Key

1. `Edit` -> `Preferences` -> `Add-ons`
2. Expand **"AI Blender Assistant"**
3. Paste your **DeepSeek API Key**
4. Get a key at: https://platform.deepseek.com

### 4. Use It

1. Press `N` in 3D Viewport to open sidebar
2. Click the **"AI"** tab
3. Type your request and click **"Send"**

---

## Examples

| Command | What Happens |
|---|---|
| "Create a 3D scene with a cube, sphere, and cylinder" | Creates objects at appropriate positions |
| "Animate all selected objects rotating" | Adds keyframes for rotation animation |
| "Add a red glossy material to the cube" | Creates and assigns material with nodes |
| "Set up a camera at 45 degrees and a sun light" | Adds and positions camera + light |
| "Switch to wireframe view" | Changes viewport shading to wireframe |
| "Render the current scene at 1080p" | Configures and renders |
| "Add a bevel modifier to all objects" | Applies modifiers programmatically |
| "What's in this scene?" | AI reads and describes all objects |
| "Parent all objects to an empty" | Creates parent-child relationships |
| "Fix: [paste error]" | AI analyzes error and provides fix |

---

## How It Works

1. **User sends a message** in the chat panel
2. **Scene context is captured** - AI receives full report of all objects, materials, collections, animations, and scene state
3. **System prompt activates** - AI follows Blender API reference and self-review protocol
4. **AI generates response** - Natural language explanation + Python code in ```python block
5. **Code is ready** - Click "Run" to execute, or "View" to inspect
6. **Auto-fix** - If code errors, AI apologizes, analyzes, learns, and fixes (up to 3 attempts)

---

## Switching AI Providers

BlenderGPT supports any OpenAI-compatible API. Edit `utilities.py`:

```python
# DeepSeek (default)
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# OpenAI
client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")

# Groq
client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# Local LLM (Ollama)
client = OpenAI(api_key="not-needed", base_url="http://localhost:11434/v1")
```

---

## Requirements

| Software | Version |
|---|---|
| Blender | 5.1 or later |
| Python | 3.11+ (bundled) |
| openai | >= 1.0.0 |
| DeepSeek API Key | Free at platform.deepseek.com |

---

## Project Structure

```
BlenderGPT-main/
├── __init__.py          # UI, operators, system prompt, scene context
├── utilities.py         # OpenAI client, API calls, image encoding
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE.md           # MIT License
└── lib/                 # Bundled Python libraries
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| OpenAI library not found | `pip install openai>=1.0.0` using Blender's Python |
| No API key detected | Set key in Edit -> Preferences -> Add-ons |
| Model not responding | Check API key validity and credits |
| Code execution error | Auto-fix handles it. Check System Console for details |
| UI not showing | Restart Blender, disable/enable add-on |

---

## License

MIT License - See [LICENSE.md](LICENSE.md)

Copyright (c) 2025 **ZylDEV**

---

## Credits

Created and maintained by [ZylDEV](https://github.com/ZylDEV)

Built with [OpenAI Python SDK](https://github.com/openai/openai-python) and [DeepSeek API](https://platform.deepseek.com/)
