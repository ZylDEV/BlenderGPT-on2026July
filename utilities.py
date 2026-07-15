import bpy
import re
import os


def _get_openai():
    """Lazy import OpenAI (biar ga error pas add-on di-enable)."""
    try:
        from openai import OpenAI
        return OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI library tidak ditemukan. Install dengan: "
            "pip install openai>=1.0.0"
        )

def get_api_key(context, addon_name):
    # Mengambil nama package agar lebih aman
    preferences = context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return addon_prefs.api_key

def generate_blender_code(prompt, chat_history, context, system_prompt):
    # Menggunakan __package__ agar lebih akurat saat mengambil API Key
    api_key = get_api_key(context, __package__)

    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY")

    OpenAI = _get_openai()
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for message in chat_history[-10:]:
        if message.type == "assistant":
            messages.append({
                "role": "assistant",
                "content": f"```\n{message.content}\n```"
            })
        else:
            messages.append({
                "role": "user",
                "content": message.content
            })

    messages.append({
        "role": "user",
        "content":
        "Can you please write Blender Python code for the following task:\n\n"
        + prompt +
        "\n\nRespond ONLY with Python code inside triple backticks."
    })

    try:
        # DeepSeek Reasoner uses max_completion_tokens, Chat uses max_tokens
        model = context.scene.gpt4_model
        kwargs = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
        }
        if model == "deepseek-reasoner":
            kwargs["max_completion_tokens"] = 4096
        else:
            kwargs["max_tokens"] = 4096

        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"DeepSeek Error: {e}")
        return None

    completion_text = ""

    for chunk in response:
        delta = chunk.choices[0].delta

        if delta.content:
            completion_text += delta.content
            print(delta.content, end="", flush=True)

    print()

    match = re.search(r"```(?:python)?(.*?)```", completion_text, re.DOTALL)

    if match:
        code = match.group(1).strip()
    else:
        code = completion_text.strip()

    return code

def split_area_to_text_editor(context):
    area = context.area

    for region in area.regions:
        if region.type == "WINDOW":
            # Perbaikan untuk Blender 4.0+ (Menggunakan temp_override)
            with context.temp_override(area=area, region=region):
                bpy.ops.screen.area_split(
                    direction="VERTICAL",
                    factor=0.5
                )
            break

    new_area = context.screen.areas[-1]
    new_area.type = "TEXT_EDITOR"

    return new_area