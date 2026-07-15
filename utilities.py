import bpy, re, os, base64

def _get_openai():
    try:
        from openai import OpenAI
        return OpenAI
    except ImportError:
        raise ImportError("pip install openai>=1.0.0")

def get_api_key(context, addon_name):
    return context.preferences.addons[addon_name].preferences.api_key or os.getenv("DEEPSEEK_API_KEY")

def encode_image(path):
    if not path or not os.path.isfile(path): return None
    ext = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}.get(os.path.splitext(path)[1].lower(),'image/png')
    with open(path,'rb') as f: return f"data:{ext};base64,{base64.b64encode(f.read()).decode()}"

def extract_code(text):
    m = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else None

def build_messages(prompt, history, sysprompt, img=None):
    msgs = [{"role":"system","content":sysprompt}]
    for m in history:
        if m.type == "assistant":
            msgs.append({"role":"assistant","content":m.content})
        elif m.type == "user":
            txt = m.content or "(Image)"
            if m.image_path and os.path.isfile(m.image_path):
                b64 = encode_image(m.image_path)
                if b64: txt = [{"type":"text","text":txt},{"type":"image_url","image_url":{"url":b64}}]
            msgs.append({"role":"user","content":txt})
    txt = prompt or "(Image)"
    if img and os.path.isfile(img):
        b64 = encode_image(img)
        if b64: txt = [{"type":"text","text":txt},{"type":"image_url","image_url":{"url":b64}}]
    msgs.append({"role":"user","content":txt})
    return msgs

def chat_with_ai(context, system_prompt, chat_history, user_text, image_path=None):
    api_key = get_api_key(context, __package__)
    if not api_key: print("No API key"); return None

    OpenAI = _get_openai()
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    msgs = build_messages(user_text, chat_history, system_prompt, image_path)

    try:
        model = context.scene.gpt4_model
        kwargs = {"model":model,"messages":msgs,"stream":True,"temperature":0.3}
        if model == "deepseek-reasoner":
            kwargs["max_completion_tokens"] = 16384
        else:
            kwargs["max_tokens"] = 16384
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"DeepSeek Error: {e}"); return None

    full = ""
    reasoning = ""
    for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta: continue
        # Capture reasoning_content for DeepSeek Reasoner
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            reasoning += delta.reasoning_content
            print(f"[REASONING] {delta.reasoning_content}", end="", flush=True)
        if delta.content:
            full += delta.content
            print(delta.content, end="", flush=True)
    print()
    # If no content but we have reasoning, use reasoning as fallback
    if not full and reasoning:
        full = reasoning
    return full

def split_area_to_text_editor(context):
    for r in context.area.regions:
        if r.type == "WINDOW":
            with context.temp_override(area=context.area, region=r):
                bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)
            break
    return context.screen.areas[-1]
