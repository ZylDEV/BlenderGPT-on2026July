import sys, os, bpy, bpy.props, traceback
libs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if libs_path not in sys.path: sys.path.insert(0, libs_path)
from .utilities import *

bl_info = {"name":"AI Blender Assistant","blender":(5,1,0),"category":"Object",
    "author":"ZylDEV","version":(3,3,0),"location":"View3D > Sidebar > AI Assistant",
    "description":"Ultimate Blender AI with error learning."}

system_prompt = """You are the ULTIMATE Blender 5.1 AI with COMPLETE scene understanding.

===== ERROR LEARNING SYSTEM =====
When you make a mistake and your code errors:
1. APOLOGIZE - "Sorry, I made a mistake. The error was..."
2. ANALYZE - What was the ROOT CAUSE? (wrong mode? missing check? wrong API?)
3. LEARN - "Next time I will remember to..."
4. FIX - Provide corrected code in ```python block

===== SELF-REVIEW PROTOCOL =====
Before outputting code, check ALL of these:
1. obj.animation_data AND obj.animation_data.action exists before fcurves
2. Use keyframe_insert() not manual fcurve
3. Correct mode (OBJECT/EDIT/POSE) before ops
4. Object exists before accessing
5. try/except for file/image ops
6. Correct Blender 5.1 API args
7. Check obj.type before type-specific ops
8. Parent-child relationships correct
9. Collection links correct
10. Data exists before accessing .data properties

===== BLENDER API REFERENCE =====
CREATE: bpy.ops.mesh.primitive_cube_add(size=2,location=(x,y,z))
SELECT: obj.select_set(True); bpy.context.view_layer.objects.active = obj
DELETE: bpy.ops.object.delete()
MODE: bpy.ops.object.mode_set(mode='OBJECT'|'EDIT'|'SCULPT'|'POSE')
MODIFIER: mod=obj.modifiers.new("N",'SUBSURF'|'BEVEL'|'MIRROR'|'ARRAY'|'SOLIDIFY'|'BOOLEAN'|'SCREW'|'DECIMATE'|'DISPLACE'|'WAVE'|'SIMPLE_DEFORM'|'WELD'|'WIREFRAME'|'NODES')
ANIMATE: obj.keyframe_insert(data_path="location"|"rotation_euler"|"scale",frame=N)
FCURVES: if obj.animation_data and obj.animation_data.action: for fc in obj.animation_data.action.fcurves: ...
MATERIAL: mat=bpy.data.materials.new("M"); mat.use_nodes=True; obj.data.materials.append(mat)
CAMERA: cam=bpy.context.object; cam.data.lens=50; scene.camera=cam
LIGHT: l=bpy.context.object; l.data.energy=100; l.data.color=(1,0.9,0.8)
RENDER: scene.render.engine='CYCLES'; scene.cycles.samples=128; bpy.ops.render.render(write_still=True)
PHYSICS: rb=obj.modifiers.new("RB",'RIGID_BODY'); rb.settings.type='ACTIVE'; rb.settings.mass=1
PARENT: child.parent = parent
COLLECTION: col=bpy.data.collections.new("C"); scene.collection.children.link(col)
EDIT: bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0,0,1)})
EDIT: bpy.ops.mesh.subdivide(number_cuts=2); bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1})
EDIT: bpy.ops.mesh.inset(thickness=0.1); bpy.ops.mesh.bevel(offset=0.1,segments=3)
EDIT: bpy.ops.mesh.remove_doubles(threshold=0.001); bpy.ops.mesh.normals_make_consistent()
VIEW: bpy.ops.view3d.view_all(); space.shading.type='WIREFRAME'|'SOLID'|'MATERIAL'|'RENDERED'

COMPLETE FREEDOM. Think step by step. Learn from mistakes."""

class GPT4_ChatMessage(bpy.types.PropertyGroup):
    type:bpy.props.StringProperty(); content:bpy.props.StringProperty(); image_path:bpy.props.StringProperty(default="")

def _exec(c):
    try: ns=globals().copy(); exec(c,ns); return True,None
    except Exception as e: traceback.print_exc(); return False,f"{type(e).__name__}:{e}"

def _scene_report(ctx):
    s=ctx.scene; obs=bpy.data.objects; lines=[]
    lines.append(f"Scene:{s.name} Frame:{s.frame_current}/{s.frame_end} Engine:{s.render.engine} Mode:{ctx.mode}")
    def walk(col, ind=0):
        p="  "*ind; lines.append(f"{p}[{col.name}] ({len(col.objects)} objs)")
        for o in col.objects:
            extra=""
            if o.parent: extra+=f" parent={o.parent.name}"
            if o.active_material: extra+=f" mat={o.active_material.name}"
            if o.constraints: extra+=f" constraints={len(o.constraints)}"
            if o.modifiers: extra+=f" mods={len(o.modifiers)}"
            if o.animation_data and o.animation_data.action: extra+=f" anim={o.animation_data.action.name}"
            lines.append(f"{p}  - {o.name}({o.type}){extra} loc={tuple(round(x,2) for x in o.location)}")
        for ch in col.children: walk(ch,ind+1)
    walk(s.collection)
    m=[o for o in obs if o.type=='MESH']; l=[o for o in obs if o.type=='LIGHT']
    c=[o for o in obs if o.type=='CAMERA']; a=[o for o in obs if o.type=='ARMATURE']
    lines.append(f"Total:{len(obs)} M:{len(m)} L:{len(l)} C:{len(c)} A:{len(a)}")
    return "\n".join(lines)

def _ask_ai(ctx, txt, img=None):
    ctx.scene.gpt4_button_pressed=True
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    r=chat_with_ai(ctx, system_prompt, ctx.scene.gpt4_chat_history,
        f"[SCENE]\n{_scene_report(ctx)}\n\n[USER] {txt}", img)
    ctx.scene.gpt4_button_pressed=False; return r

def _add(ctx,t,txt,i=""):
    m=ctx.scene.gpt4_chat_history.add(); m.type=t; m.content=txt
    if i: m.image_path=i; return m

class GPT4_OT_UploadImage(bpy.types.Operator):
    bl_idname="gpt4.upload_image"; bl_label="Upload Image"; bl_options={'REGISTER'}
    filepath:bpy.props.StringProperty(subtype='FILE_PATH')
    def execute(self,ctx):
        if not os.path.isfile(self.filepath): self.report({'ERROR'},"Not found!"); return {'CANCELLED'}
        ctx.scene.gpt4_uploaded_image=self.filepath; return {'FINISHED'}
    def invoke(self,ctx,event): ctx.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

class GPT4_OT_DeleteMessage(bpy.types.Operator):
    bl_idname="gpt4.delete_message"; bl_label="Delete"; bl_options={'REGISTER','UNDO'}
    idx:bpy.props.IntProperty()
    def execute(self,ctx): ctx.scene.gpt4_chat_history.remove(self.idx); return {'FINISHED'}

class GPT4_OT_ShowCode(bpy.types.Operator):
    bl_idname="gpt4.show_code"; bl_label="View Code"; bl_options={'REGISTER','UNDO'}
    code:bpy.props.StringProperty()
    def execute(self,ctx):
        t=bpy.data.texts.get("AI_Code.py")
        if t is None: t=bpy.data.texts.new("AI_Code.py")
        t.clear(); t.write(self.code)
        for a in ctx.screen.areas:
            if a.type=='TEXT_EDITOR': a.spaces.active.text=t; return {'FINISHED'}
        return {'FINISHED'}

class GPT4_OT_ExecuteCode(bpy.types.Operator):
    bl_idname="gpt4.execute_code"; bl_label="Run"; bl_options={'REGISTER','UNDO'}
    code:bpy.props.StringProperty(); fix_count:bpy.props.IntProperty(default=0)
    def execute(self,ctx):
        if not self.code: return {'CANCELLED'}
        ok,err=_exec(self.code)
        if ok: self.report({'INFO'},"Done!"); ctx.scene.gpt4_last_error=""; ctx.scene.gpt4_last_error_code=""; return {'FINISHED'}
        ctx.scene.gpt4_last_error=err; ctx.scene.gpt4_last_error_code=self.code
        if self.fix_count>=3: self.report({'ERROR'},f"Failed 3x: {err}"); return {'CANCELLED'}
        _add(ctx,'user',f"[Fix {self.fix_count+1}/3] {err}")
        r=_ask_ai(ctx,
            f"❗ ERROR: {err}\n"
            f"YOUR CODE:\n```python\n{self.code}\n```\n\n"
            f"ERROR RECOVERY - Follow these steps:\n"
            f"1. APOLOGIZE - Say sorry and acknowledge what went wrong\n"
            f"2. ANALYZE - What was the ROOT CAUSE? (wrong mode? missing check? wrong API?)\n"
            f"3. LEARN - What will you remember next time?\n"
            f"4. FIX - Provide corrected code. Use a DIFFERENT approach this time.\n")
        if not r: return {'CANCELLED'}
        _add(ctx,'assistant',r)
        f=extract_code(r)
        if f: bpy.ops.gpt4.execute_code(code=f, fix_count=self.fix_count+1)
        return {'FINISHED'}

class GPT4_OT_ClearChat(bpy.types.Operator):
    bl_idname="gpt4.clear_chat"; bl_label="Clear"; bl_options={'REGISTER','UNDO'}
    img_only:bpy.props.BoolProperty(default=False)
    def execute(self,ctx):
        if self.img_only: ctx.scene.gpt4_uploaded_image=""
        else: ctx.scene.gpt4_chat_history.clear(); ctx.scene.gpt4_uploaded_image=""; ctx.scene.gpt4_last_error=""; ctx.scene.gpt4_last_error_code=""
        return {'FINISHED'}

class GPT4_OT_SendMessage(bpy.types.Operator):
    bl_idname="gpt4.send_message"; bl_label="Send"; bl_options={'REGISTER','UNDO'}
    def execute(self,ctx):
        txt=ctx.scene.gpt4_chat_input.strip(); img=ctx.scene.gpt4_uploaded_image
        if not txt and not img: self.report({'ERROR'},"Say something!"); return {'CANCELLED'}
        _add(ctx,'user',txt or "(Image)",img)
        ctx.scene.gpt4_chat_input=""; ctx.scene.gpt4_uploaded_image=""
        r=_ask_ai(ctx,txt,img)
        if not r: return {'CANCELLED'}
        _add(ctx,'assistant',r)
        if ctx.scene.gpt4_auto_execute:
            c=extract_code(r)
            if c: bpy.ops.gpt4.execute_code(code=c)
        return {'FINISHED'}

class GPT4_PT_Panel(bpy.types.Panel):
    bl_label="AI Assistant"; bl_idname="GPT4_PT_Panel"
    bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category="AI"
    @classmethod
    def poll(cls,ctx): return ctx.area.type=='VIEW_3D'
    def draw(self,ctx):
        layout=self.layout; s=ctx.scene; col=layout.column(align=True)
        if len(s.gpt4_chat_history)==0:
            box=col.box(); c=box.column(align=True); c.scale_y=1.1
            c.label(text="AI Blender Agent v3.3")
            c.separator()
            for t in ['"describe this scene"','"create a full 3D scene"','"animate all objects"','"add materials to everything"','"set up render and camera"']:
                c.label(text=t)
        for i,msg in enumerate(s.gpt4_chat_history):
            if msg.type=='assistant':
                box=col.box(); box.scale_y=0.85
                r=box.row(align=True); r.label(text="",icon='INFO'); r.label(text="AI")
                d=r.operator("gpt4.delete_message",text="",icon='X',emboss=False); d.idx=i
                for line in msg.content.split('\n'):
                    if line.strip(): box.column(align=True).label(text=line)
                code=extract_code(msg.content)
                if code:
                    r=box.row(align=True)
                    op=r.operator("gpt4.execute_code",text="Run",icon='PLAY'); op.code=code; op.fix_count=0
                    sv=r.operator("gpt4.show_code",text="View",icon='TEXT'); sv.code=code
            else:
                box=col.box(); box.scale_y=0.85
                r=box.row(align=True); r.label(text="",icon='USER')
                if msg.image_path: r.label(text=f"[IMG] {os.path.basename(msg.image_path)[:25]}")
                else: r.label(text="You")
                d=r.operator("gpt4.delete_message",text="",icon='X',emboss=False); d.idx=i
                if msg.content: box.column(align=True).label(text=msg.content)
        if s.gpt4_button_pressed:
            box=col.box(); box.scale_y=0.85; box.column(align=True).label(text="Thinking...")
        layout.separator()
        if s.gpt4_uploaded_image:
            r=layout.row(align=True); r.label(text="",icon='FILE_IMAGE')
            r.label(text=os.path.basename(s.gpt4_uploaded_image)[:30])
            o=r.operator("gpt4.clear_chat",text="",icon='X',emboss=False); o.img_only=True
        r=layout.row(align=True); r.prop(s,"gpt4_model",text=""); r.prop(s,"gpt4_auto_execute",text="Auto",icon='PLAY')
        layout.prop(s,"gpt4_chat_input",text="")
        r=layout.row(align=True); r.operator("gpt4.upload_image",text="",icon='FILE_IMAGE')
        r.operator("gpt4.send_message",text="Thinking..." if s.gpt4_button_pressed else "Send")
        layout.operator("gpt4.clear_chat",text="Clear",icon='TRASH')

class GPT4AddonPreferences(bpy.types.AddonPreferences):
    bl_idname=__package__; api_key:bpy.props.StringProperty(name="API Key",subtype="PASSWORD",default="")
    def draw(self,ctx): self.layout.prop(self,"api_key"); self.layout.label(text="https://platform.deepseek.com")

classes=(GPT4_ChatMessage,GPT4AddonPreferences,GPT4_OT_UploadImage,GPT4_OT_DeleteMessage,
    GPT4_OT_ShowCode,GPT4_OT_ExecuteCode,GPT4_OT_ClearChat,GPT4_OT_SendMessage,GPT4_PT_Panel)

def register():
    for c in classes: bpy.utils.register_class(c)
    S=bpy.types.Scene
    S.gpt4_chat_history=bpy.props.CollectionProperty(type=GPT4_ChatMessage)
    S.gpt4_model=bpy.props.EnumProperty(name="Model",items=[("deepseek-reasoner","DeepSeek Reasoner",""),("deepseek-chat","DeepSeek Chat","")],default="deepseek-reasoner")
    S.gpt4_chat_input=bpy.props.StringProperty(name="",description="Ask about Blender...")
    S.gpt4_button_pressed=bpy.props.BoolProperty(default=False); S.gpt4_uploaded_image=bpy.props.StringProperty(default="")
    S.gpt4_auto_execute=bpy.props.BoolProperty(default=False); S.gpt4_last_error=bpy.props.StringProperty(default="")
    S.gpt4_last_error_code=bpy.props.StringProperty(default="")

def unregister():
    for c in reversed(classes): bpy.utils.unregister_class(c)
    for p in ('gpt4_chat_history','gpt4_chat_input','gpt4_model','gpt4_button_pressed','gpt4_uploaded_image','gpt4_auto_execute','gpt4_last_error','gpt4_last_error_code'):
        delattr(bpy.types.Scene,p)

if __name__=="__main__": register()
