import bpy
import re
import os
import base64


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
    preferences = context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return addon_prefs.api_key


def _encode_image_to_base64(image_path):
    """Read an image file and return a base64 data URI string."""
    if not image_path or not os.path.isfile(image_path):
        return None

    # Determine mime type from extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
    }
    mime = mime_map.get(ext, 'image/png')

    with open(image_path, 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    return f"data:{mime};base64,{b64_data}"


def _build_messages(prompt, chat_history, system_prompt, image_path=None):
    """Build the messages array for the API, with optional image support."""
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Add chat history (last 10 messages)
    for message in chat_history[-10:]:
        if message.type == "assistant":
            messages.append({
                "role": "assistant",
                "content": f"```\n{message.content}\n```",
            })
        elif message.type == "user":
            # Check if this message has an image
            msg_content = message.content if message.content else "(Image analysis)"

            if message.image_path and os.path.isfile(message.image_path):
                base64_img = _encode_image_to_base64(message.image_path)
                if base64_img:
                    msg_content = [
                        {"type": "text", "text": msg_content},
                        {"type": "image_url", "image_url": {"url": base64_img}},
                    ]

            messages.append({"role": "user", "content": msg_content})

    # Build current user message
    final_prompt = (
        "Can you please write Blender Python code for the following task:\n\n"
        + (prompt if prompt else "Analyze this image and describe what you see related to 3D/Blender.")
        + "\n\nRespond ONLY with Python code inside triple backticks."
    )

    # If there's an image in the current request
    if image_path and os.path.isfile(image_path):
        base64_img = _encode_image_to_base64(image_path)
        if base64_img:
            user_content = [
                {"type": "text", "text": final_prompt},
                {"type": "image_url", "image_url": {"url": base64_img}},
            ]
        else:
            user_content = final_prompt
    else:
        user_content = final_prompt

    messages.append({"role": "user", "content": user_content})

    return messages


def generate_blender_code(prompt, chat_history, context, system_prompt, image_path=None):
    api_key = get_api_key(context, __package__)

    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("DeepSeek Error: No API key found.")
        return None

    OpenAI = _get_openai()
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    messages = _build_messages(prompt, chat_history, system_prompt, image_path)

    try:
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

    # Extract code from markdown code block
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
            with context.temp_override(area=area, region=region):
                bpy.ops.screen.area_split(
                    direction="VERTICAL",
                    factor=0.5,
                )
            break

    new_area = context.screen.areas[-1]
    new_area.type = "TEXT_EDITOR"

    return new_area
