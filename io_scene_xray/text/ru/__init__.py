# blender modules
import bpy

# addon modules
from . import iface
from . import error
from . import warn


def register():
    translation = {}

    translation.update(iface.translation)
    translation.update(error.translation)
    translation.update(warn.translation)

    translations = {'ru_RU': translation, }

    bpy.app.translations.register('io_scene_xray', translations)


def unregister():
    try:
        bpy.app.translations.unregister('io_scene_xray')
    except RuntimeError:
        # the translations are already unregistered
        pass
