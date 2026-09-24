# blender modules
import bpy

# addon modules
from .. import ui
from .. import ops
from .. import utils


class XRAY_PT_edit_helper(ui.base.XRayPanel):
    bl_context = 'object'
    bl_label = ui.base.build_label('Edit Helper')

    @classmethod
    def poll(cls, context):
        return ops.edit_helpers.base.get_object_helper(context)

    def draw(self, context):
        helper = ops.edit_helpers.base.get_object_helper(context)
        helper.draw(self.layout, context)


def register():
    utils.version.register_classes(XRAY_PT_edit_helper)


def unregister():
    utils.version.unregister_class(XRAY_PT_edit_helper)
