# blender modules
import bpy

# addon modules
from . import gpu_utils
from . import const
from . import ctx
from . import geom
from .. import utils

if not utils.version.IS_28:
    from . import gl_utils


draw_ctx = ctx.DrawContext()


def get_draw_joint_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_joint_limits
    else:
        return gl_utils.draw_joint_limits


def get_draw_slider_rotation_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_slider_rotation_limits
    else:
        return gl_utils.draw_slider_rotation_limits


def get_draw_slider_slide_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_slider_slide_limits
    else:
        return gl_utils.draw_slider_slide_limits


def _check_context(draw_ctx):
    has_geom = False

    for data_type, data in draw_ctx.geom.items():
        for state_type, state in data.items():

            coords = state['coords']
            lines = state['lines']
            faces = state['faces']

            if coords or lines or faces:
                has_geom = True

    return has_geom


def collect_draw_geom():
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            obj.data.xray.ondraw_postview(obj, draw_ctx, 'SHAPES')


def draw_limits():
    obj = bpy.context.active_object
    if obj and obj.type == 'ARMATURE':
        obj.data.xray.ondraw_postview(obj, draw_ctx, 'LIMITS')


def clear_draw_context():
    for data_type, data in draw_ctx.geom.items():
        for state_type, state in data.items():

            state['coords'].clear()
            state['lines'].clear()
            state['faces'].clear()


def update_draw_context():
    clear_draw_context()
    collect_draw_geom()


@bpy.app.handlers.persistent
def update_draw_ctx(scene, depsgraph):
    update_draw_context()


@bpy.app.handlers.persistent
def update_draw_ctx_27x(scene):
    update_draw_context()


@bpy.app.handlers.persistent
def clear_draw_ctx(scene, depsgraph):
    clear_draw_context()


@bpy.app.handlers.persistent
def clear_draw_ctx_27x(scene):
    clear_draw_context()


def overlay_view_3d():
    # set opengl state for limits draw
    utils.draw.reset_gl_state()
    utils.draw.set_gl_line_width(const.LINE_WIDTH)

    # collect shapes geometry
    has_geom = _check_context(draw_ctx)
    if not has_geom:
        update_draw_context()

    # draw limits
    draw_limits()

    # draw shapes
    draw_ctx.draw()
    utils.draw.reset_gl_state()


# the handle of the viewport draw handler
overlay_view_3d.__handle = None


def register():
    if overlay_view_3d.__handle is None:
        overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
            overlay_view_3d,
            (),
            'WINDOW',
            'POST_VIEW'
        )
    if utils.version.IS_281:
        utils.version.append_handler(
            bpy.app.handlers.depsgraph_update_post, update_draw_ctx
        )
        utils.version.append_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx
        )
        utils.version.append_handler(
            bpy.app.handlers.load_post, clear_draw_ctx
        )
    elif utils.version.IS_28:
        utils.version.append_handler(
            bpy.app.handlers.depsgraph_update_post, update_draw_ctx_27x
        )
        utils.version.append_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx_27x
        )
        utils.version.append_handler(
            bpy.app.handlers.load_post, clear_draw_ctx_27x
        )
    else:
        utils.version.append_handler(
            bpy.app.handlers.scene_update_post, update_draw_ctx_27x
        )
        utils.version.append_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx_27x
        )
        utils.version.append_handler(
            bpy.app.handlers.load_post, clear_draw_ctx_27x
        )


def unregister():
    if utils.version.IS_281:
        utils.version.remove_handler(
            bpy.app.handlers.load_post, clear_draw_ctx
        )
        utils.version.remove_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx
        )
        utils.version.remove_handler(
            bpy.app.handlers.depsgraph_update_post, update_draw_ctx
        )
    elif utils.version.IS_28:
        utils.version.remove_handler(
            bpy.app.handlers.load_post, clear_draw_ctx_27x
        )
        utils.version.remove_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx_27x
        )
        utils.version.remove_handler(
            bpy.app.handlers.depsgraph_update_post, update_draw_ctx_27x
        )
    else:
        utils.version.remove_handler(
            bpy.app.handlers.load_post, clear_draw_ctx_27x
        )
        utils.version.remove_handler(
            bpy.app.handlers.frame_change_post, update_draw_ctx_27x
        )
        utils.version.remove_handler(
            bpy.app.handlers.scene_update_post, update_draw_ctx_27x
        )
    if overlay_view_3d.__handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(
            overlay_view_3d.__handle,
            'WINDOW'
        )
        overlay_view_3d.__handle = None
