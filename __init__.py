import sys
import os
import bpy
import bpy.props

# Add the 'lib' folder to the Python path
libs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from .utilities import *

bl_info = {
    "name": "AI Blender Assistant",
    "blender": (5, 1, 0),
    "category": "Object",
    "author": "ZylDEV",
    "version": (2, 1, 0),
    "location": "3D View > Sidebar > AI Assistant",
    "description": "Generate Blender Python code using DeepSeek/OpenAI compatible APIs with image analysis.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

system_prompt = """You are an assistant made for the purposes of helping the user with Blender, the 3D software.
- Respond with your answers in markdown (```).
- Preferably import entire modules instead of bits.
- Do not perform destructive operations on the meshes.
- Do not use cap_ends. Do not do more than what is asked (setting up render settings, adding cameras, etc)
- Do not respond with anything that is not Python code."""

# -------------------------------------------------------------------
# PROPERTY GROUP: Chat Message
# -------------------------------------------------------------------
class GPT4_ChatMessage(bpy.types.PropertyGroup):
    type: bpy.props.StringProperty()
    content: bpy.props.StringProperty()
    image_path: bpy.props.StringProperty(default="")

# -------------------------------------------------------------------
# OPERATOR: Upload Image
# -------------------------------------------------------------------
class GPT4_OT_UploadImage(bpy.types.Operator):
    bl_idname = "gpt4.upload_image"
    bl_label = "Upload Image for Analysis"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        if not os.path.isfile(self.filepath):
            self.report({'ERROR'}, "File not found!")
            return {'CANCELLED'}
        context.scene.gpt4_uploaded_image = self.filepath
        self.report({'INFO'}, "Image loaded!")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# -------------------------------------------------------------------
# OPERATOR: Delete Message
# -------------------------------------------------------------------
class GPT4_OT_DeleteMessage(bpy.types.Operator):
    bl_idname = "gpt4.delete_message"
    bl_label = "Delete Message"
    bl_options = {'REGISTER', 'UNDO'}

    message_index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.gpt4_chat_history.remove(self.message_index)
        return {'FINISHED'}

# -------------------------------------------------------------------
# OPERATOR: Show Code
# -------------------------------------------------------------------
class GPT4_OT_ShowCode(bpy.types.Operator):
    bl_idname = "gpt4.show_code"
    bl_label = "Show Code"
    bl_options = {'REGISTER', 'UNDO'}

    code: bpy.props.StringProperty()

    def execute(self, context):
        text_name = "AI_Generated_Code.py"
        text = bpy.data.texts.get(text_name)
        if text is None:
            text = bpy.data.texts.new(text_name)
        text.clear()
        text.write(self.code)

        text_editor_area = None
        for area in context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                text_editor_area = area
                break

        if text_editor_area is None:
            text_editor_area = split_area_to_text_editor(context)

        text_editor_area.spaces.active.text = text
        return {'FINISHED'}

# -------------------------------------------------------------------
# OPERATOR: Clear Chat
# -------------------------------------------------------------------
class GPT4_OT_ClearChat(bpy.types.Operator):
    bl_idname = "gpt4.clear_chat"
    bl_label = "Clear Chat"
    bl_options = {'REGISTER', 'UNDO'}

    image_clear: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        if self.image_clear:
            context.scene.gpt4_uploaded_image = ""
        else:
            context.scene.gpt4_chat_history.clear()
            context.scene.gpt4_uploaded_image = ""
        return {'FINISHED'}

# -------------------------------------------------------------------
# OPERATOR: Send Message
# -------------------------------------------------------------------
class GPT4_OT_Execute(bpy.types.Operator):
    bl_idname = "gpt4.send_message"
    bl_label = "Send Message"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_text = context.scene.gpt4_chat_input.strip()
        image_path = context.scene.gpt4_uploaded_image

        if not user_text and not image_path:
            self.report({'ERROR'}, "Please enter a message or upload an image.")
            return {'CANCELLED'}

        # Save user message
        msg = context.scene.gpt4_chat_history.add()
        msg.type = 'user'
        msg.content = user_text if user_text else "(Image analysis)"
        if image_path:
            msg.image_path = image_path

        # Clear input
        context.scene.gpt4_chat_input = ""
        context.scene.gpt4_uploaded_image = ""

        # Set loading
        context.scene.gpt4_button_pressed = True
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # Generate code
        blender_code = generate_blender_code(
            prompt=user_text,
            chat_history=context.scene.gpt4_chat_history,
            context=context,
            system_prompt=system_prompt,
            image_path=image_path,
        )

        context.scene.gpt4_button_pressed = False

        if not blender_code:
            self.report({'ERROR'}, "No code generated. Check System Console.")
            return {'CANCELLED'}

        # Save assistant response
        msg = context.scene.gpt4_chat_history.add()
        msg.type = 'assistant'
        msg.content = blender_code

        # Execute
        if context.scene.gpt4_auto_execute:
            global_namespace = globals().copy()
            try:
                exec(blender_code, global_namespace)
            except Exception as e:
                self.report({'ERROR'}, f"Error: {e}")
                return {'CANCELLED'}

        return {'FINISHED'}

# -------------------------------------------------------------------
# PANEL
# -------------------------------------------------------------------
class GPT4_PT_Panel(bpy.types.Panel):
    bl_label = "AI Blender Assistant"
    bl_idname = "GPT4_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AI Assistant"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- Chat History Box ---
        box = layout.box()
        box.label(text="Chat History:")

        for index, message in enumerate(scene.gpt4_chat_history):
            row = box.row(align=True)

            if message.type == 'assistant':
                row.label(text="", icon='INFO')
                row.label(text=message.content[:50] + "..." if len(message.content) > 50 else message.content)
                show_op = row.operator("gpt4.show_code", text="Show Code")
                show_op.code = message.content
                del_op = row.operator("gpt4.delete_message", text="", icon='X', emboss=False)
                del_op.message_index = index

            else:
                if message.image_path:
                    row.label(text="", icon='FILE_IMAGE')
                    img_name = os.path.basename(message.image_path)
                    row.label(text=f"[IMG] {img_name[:20]}")
                else:
                    row.label(text="", icon='USER')
                    row.label(text=message.content[:50] + "..." if len(message.content) > 50 else message.content)
                del_op = row.operator("gpt4.delete_message", text="", icon='X', emboss=False)
                del_op.message_index = index

        if len(scene.gpt4_chat_history) == 0:
            box.label(text="No messages yet. Type something below!")

        # --- Uploaded Image Preview ---
        if scene.gpt4_uploaded_image:
            row = layout.row(align=True)
            row.label(text="", icon='FILE_IMAGE')
            row.label(text=os.path.basename(scene.gpt4_uploaded_image))
            op = row.operator("gpt4.clear_chat", text="", icon='X', emboss=False)
            op.image_clear = True

        # --- Model Selection ---
        layout.separator()
        col = layout.column(align=True)
        col.label(text="AI Model:")
        col.prop(scene, "gpt4_model", text="")

        # --- Toggles ---
        row = col.row(align=True)
        row.prop(scene, "gpt4_auto_execute", text="Auto-execute code")

        # --- Input ---
        layout.separator()
        col = layout.column(align=True)
        col.label(text="Message:")
        col.prop(scene, "gpt4_chat_input", text="")

        # --- Buttons ---
        row = layout.row(align=True)
        row.operator("gpt4.upload_image", text="", icon='FILE_IMAGE')
        btn_label = "Thinking..." if scene.gpt4_button_pressed else "Send"
        row.operator("gpt4.send_message", text=btn_label)

        row = layout.row(align=True)
        row.operator("gpt4.clear_chat", text="Clear Chat", icon='TRASH')

# -------------------------------------------------------------------
# ADDON PREFERENCES
# -------------------------------------------------------------------
class GPT4AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    api_key: bpy.props.StringProperty(
        name="API Key",
        subtype="PASSWORD",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "api_key")
        layout.label(text="Get your key at: https://platform.deepseek.com")

# -------------------------------------------------------------------
# MENU
# -------------------------------------------------------------------
def menu_func(self, context):
    self.layout.operator(GPT4_OT_Execute.bl_idname)

# -------------------------------------------------------------------
# REGISTRATION
# -------------------------------------------------------------------
classes = (
    GPT4_ChatMessage,
    GPT4AddonPreferences,
    GPT4_OT_UploadImage,
    GPT4_OT_DeleteMessage,
    GPT4_OT_ShowCode,
    GPT4_OT_ClearChat,
    GPT4_OT_Execute,
    GPT4_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

    bpy.types.Scene.gpt4_chat_history = bpy.props.CollectionProperty(type=GPT4_ChatMessage)
    bpy.types.Scene.gpt4_model = bpy.props.EnumProperty(
        name="AI Model",
        items=[
            ("deepseek-chat", "DeepSeek Chat", ""),
            ("deepseek-reasoner", "DeepSeek Reasoner", ""),
        ],
        default="deepseek-chat",
    )
    bpy.types.Scene.gpt4_chat_input = bpy.props.StringProperty(name="Message", default="")
    bpy.types.Scene.gpt4_button_pressed = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.gpt4_uploaded_image = bpy.props.StringProperty(default="")
    bpy.types.Scene.gpt4_auto_execute = bpy.props.BoolProperty(default=True)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    del bpy.types.Scene.gpt4_chat_history
    del bpy.types.Scene.gpt4_chat_input
    del bpy.types.Scene.gpt4_model
    del bpy.types.Scene.gpt4_button_pressed
    del bpy.types.Scene.gpt4_uploaded_image
    del bpy.types.Scene.gpt4_auto_execute

if __name__ == "__main__":
    register()
