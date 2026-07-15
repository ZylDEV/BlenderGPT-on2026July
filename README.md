# BlenderGPT - AI-Powered Blender Assistant

Generate and execute Blender Python code using natural language, powered by **DeepSeek AI** (or any OpenAI-compatible API).

## Features

- **Natural Language to Blender Code** - Describe what you want in plain English, and AI writes the Python code for you
- **One-Click Execute** - Generated code runs instantly inside Blender
- **Show Code** - View, inspect, and re-run generated scripts in Blender's Text Editor
- **Chat History** - Full conversation history with delete and clear options
- **Multi-Model Support** - Works with DeepSeek Chat, DeepSeek Reasoner, and any OpenAI-compatible API
- **Secure API Key Storage** - Your API key is stored securely in Blender's add-on preferences

## Requirements

| Software | Version |
|---|---|
| Blender | 5.1 or later |
| Python | 3.11+ (bundled with Blender) |
| OpenAI Python lib | >= 1.0.0 |

## Installation

### 1. Install the OpenAI Library

BlenderGPT requires the official OpenAI Python SDK. Install it using Blender's bundled Python:

```bash
# Windows
"C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe" -m pip install openai>=1.0.0

# macOS
/Applications/Blender.app/Contents/Resources/5.1/python/bin/python3 -m pip install openai>=1.0.0

# Linux
/path/to/blender/5.1/python/bin/python3 -m pip install openai>=1.0.0
```

Alternatively, install it system-wide:
```bash
pip install openai>=1.0.0
```

### 2. Install the Add-on

1. Download or clone this repository
2. Open Blender -> `Edit` -> `Preferences` -> `Add-ons`
3. Click `Install...` and select the `BlenderGPT-main` folder as ZIP
4. Enable **"AI Blender Assistant"** by checking the checkbox

> **Tip:** If you are developing locally, you can symlink the folder to Blender's add-ons directory:
> - Windows: `%APPDATA%\Blender Foundation\Blender\5.1\scripts\addons\`
> - macOS: `~/Library/Application Support/Blender/5.1/scripts/addons/`
> - Linux: `~/.config/blender/5.1/scripts/addons/`

### 3. Set Your API Key

1. Go to `Edit` -> `Preferences` -> `Add-ons`
2. Find **"AI Blender Assistant"**
3. Click the arrow to expand preferences
4. Paste your **DeepSeek API Key** (or other provider's key)
5. You can also set the `DEEPSEEK_API_KEY` environment variable as a fallback

### 4. Usage

1. In the **3D Viewport**, press `N` to open the sidebar
2. Navigate to the **"AI Assistant"** tab
3. Select your AI model from the dropdown
4. Type your command in natural language, for example:
   - *"Create a cube at the origin"*
   - *"Add a UV sphere with 32 segments"*
   - *"Create a 3D donut with icing and sprinkles"*
   - *"Animate a cube rotating 360 degrees on the Y axis"*
5. Click **"Execute"** and watch the magic happen

## Switching to Other AI Providers

BlenderGPT supports any API that is **OpenAI-compatible** (OpenAI, Groq, Together AI, Anthropic via proxy, etc.). Here is how to customize:

### Option A: Change Provider in the Code (Permanent)

Edit `utilities.py` and change the `base_url`:

```python
# DeepSeek (default)
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# OpenAI
client = OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1"
)

# Groq
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# Together AI
client = OpenAI(
    api_key=api_key,
    base_url="https://api.together.xyz/v1"
)

# GitHub Models (free with Copilot subscription)
client = OpenAI(
    api_key=api_key,
    base_url="https://models.inference.ai.azure.com"
)

# Local LLM (Ollama, LM Studio, etc.)
client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:11434/v1"
)
```

### Option B: Add Model Selection to the UI

To add more models to the dropdown, edit `__init__.py` in the `register()` function:

```python
bpy.types.Scene.gpt4_model = bpy.props.EnumProperty(
    name="AI Model",
    description="Select the AI model",
    items=[
        ("deepseek-chat", "DeepSeek Chat", ""),
        ("deepseek-reasoner", "DeepSeek Reasoner", ""),
        # Add your custom models here
        ("gpt-4o", "GPT-4o", "OpenAI GPT-4o"),
        ("gpt-4o-mini", "GPT-4o Mini", "OpenAI GPT-4o Mini"),
        ("llama-3.3-70b", "Llama 3.3 70B", "Groq Llama 3.3"),
        ("mixtral-8x7b", "Mixtral 8x7B", "Groq Mixtral"),
    ],
    default="deepseek-chat",
)
```

> **Note:** When switching providers, make sure your API key matches the provider you selected, and the model name is supported by that provider.

## Supported Models (Default)

| Model | Description | Best For |
|---|---|---|
| DeepSeek Chat | Fast, general-purpose model | Daily Blender scripting tasks |
| DeepSeek Reasoner | Advanced reasoning model | Complex 3D math and logic |

## Project Structure

```
BlenderGPT-main/
├── __init__.py          # Add-on registration, UI panel, operators
├── utilities.py         # API client, code generation, helpers
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE.md           # License information
└── lib/                 # Bundled Python libraries (openai, httpx, etc.)
```

## Troubleshooting

| Problem | Solution |
|---|---|
| "OpenAI library not found" | Run `pip install openai>=1.0.0` using Blender's Python |
| "No API key detected" | Set your API key in Edit -> Preferences -> Add-ons -> AI Blender Assistant |
| "Permission denied" | Make sure your Python environment has write access, or use the bundled `lib/` folder |
| Model not responding | Verify your API key is valid and has credits/quota |
| Code execution error | Check the System Console (`Window` -> `Toggle System Console`) for details |

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Credits

- Original concept by [ZylDEV](https://github.com/ZylDEV)
- Adapted for DeepSeek AI & Blender 5.1+
- Built with [OpenAI Python SDK](https://github.com/openai/openai-python) and [DeepSeek API](https://platform.deepseek.com/)
