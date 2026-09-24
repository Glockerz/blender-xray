import bpy
import mathutils
import io_scene_xray
import tests

from io_scene_xray import handlers
from io_scene_xray.ops import action
from io_scene_xray import utils


class XRAY_OT_test_conflicting_operator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_action_settings'
    bl_label = 'Test Operator'


class XRAY_OT_test_unique_operator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.test_unique_operator'
    bl_label = 'Test Operator'


class TestAddon(tests.utils.XRayTestCase):
    def test_blinfo(self):
        self.assertIsNotNone(io_scene_xray.bl_info)

    def test_enabled(self):
        if bpy.app.version >= (2, 80, 0):
            self.assertIn('io_scene_xray', bpy.context.preferences.addons)
        else:
            self.assertIn('io_scene_xray', bpy.context.user_preferences.addons)

    def test_is_bl_idname_registered(self):
        self.assertTrue(
            utils.version.is_bl_idname_registered(
                'io_scene_xray.copy_action_settings'
            )
        )
        self.assertFalse(
            utils.version.is_bl_idname_registered(
                'io_scene_xray.no_such_operator'
            )
        )
        self.assertFalse(
            utils.version.is_bl_idname_registered('no_such_category')
        )
        self.assertFalse(utils.version.is_bl_idname_registered(None))

        self.assertEqual(
            action.XRAY_OT_copy_action_settings,
            utils.version.get_registered_class(
                'io_scene_xray.copy_action_settings'
            )
        )
        self.assertIsNone(
            utils.version.get_registered_class(
                'io_scene_xray.no_such_operator'
            )
        )

    def test_matrix_inverted(self):
        # Blender 5.2 removed the fallback argument of Matrix.inverted(),
        # it raises ValueError for non invertible matrices
        matrix = mathutils.Matrix.Identity(4)
        self.assertEqual(matrix, utils.version.matrix_inverted(matrix))

        singular = mathutils.Matrix.Diagonal((0.0, 1.0, 1.0, 1.0))
        self.assertIsNone(utils.version.matrix_inverted(singular))
        self.assertEqual(5, utils.version.matrix_inverted(singular, 5))

    def test_make_annotations_with_non_dict_annotations(self):
        if bpy.app.version < (2, 80):
            self.skipTest('class fields are not converted to annotations '
                          'before Blender 2.80')

        # a class can have a property or a descriptor named __annotations__
        # instead of a dictionary, it must not raise
        class XRAY_TestPropertyGroup(bpy.types.PropertyGroup):
            __annotations__ = 'not a dictionary'
            prop = bpy.props.IntProperty()

        utils.version._make_annotations(XRAY_TestPropertyGroup)

        annotations = XRAY_TestPropertyGroup.__dict__['__annotations__']
        self.assertIsInstance(annotations, dict)
        self.assertIn('prop', annotations)
        self.assertNotIn('prop', XRAY_TestPropertyGroup.__dict__)

    def test_register_class_twice(self):
        # repeated registration of the same class must not raise
        # 'already registered as a subclass'
        clas = action.XRAY_OT_copy_action_settings

        utils.version.register_classes(clas)
        self.assertTrue(clas.is_registered)

        utils.version.register_classes(clas)
        self.assertTrue(clas.is_registered)

    def test_unregister_class_twice(self):
        # repeated unregistration of the same class must not raise
        clas = action.XRAY_OT_paste_action_settings

        try:
            utils.version.unregister_classes(clas)
            self.assertFalse(clas.is_registered)

            utils.version.unregister_classes(clas)
            self.assertFalse(clas.is_registered)

        finally:
            utils.version.register_classes(clas)

        self.assertTrue(clas.is_registered)

    def test_register_addon_twice(self):
        try:
            io_scene_xray.register()

            self.assertTrue(
                action.XRAY_OT_copy_action_settings.is_registered
            )
            self.assertTrue(
                hasattr(bpy.ops.io_scene_xray, 'copy_action_settings')
            )

        finally:
            io_scene_xray.unregister()

        io_scene_xray.register()

    def test_unregister_addon_twice(self):
        try:
            io_scene_xray.unregister()
            self.assertFalse(
                action.XRAY_OT_copy_action_settings.is_registered
            )

            io_scene_xray.unregister()
            self.assertFalse(
                action.XRAY_OT_copy_action_settings.is_registered
            )

        finally:
            io_scene_xray.register()

        self.assertTrue(action.XRAY_OT_copy_action_settings.is_registered)

    def test_register_class_with_conflicting_bl_idname(self):
        # another class with the same bl_idname is already registered
        # (for example, two copies of the addon are installed)
        try:
            utils.version.register_classes(XRAY_OT_test_conflicting_operator)

            # the identifier must stay available
            self.assertTrue(
                hasattr(bpy.ops.io_scene_xray, 'copy_action_settings')
            )

        finally:
            utils.version.unregister_classes(XRAY_OT_test_conflicting_operator)
            utils.version.register_classes(action.XRAY_OT_copy_action_settings)

        self.assertTrue(
            action.XRAY_OT_copy_action_settings.is_registered
        )

    def test_register_class_skips_conflicting_bl_idname(self):
        # older Blender versions raise ValueError for a class,
        # if another class with the same bl_idname is registered
        prev_register_class = bpy.utils.register_class

        def register_class_raising_value_error(clas):
            raise ValueError(
                "register_class(...): '{}' already registered as a "
                "subclass of 'Operator'".format(clas.__name__)
            )

        try:
            bpy.utils.register_class = register_class_raising_value_error

            patched = bpy.utils.register_class
            if patched is not register_class_raising_value_error:
                self.skipTest('can not patch bpy.utils.register_class')

            # the bl_idname is already registered,
            # so the class is skipped
            utils.version.register_classes(XRAY_OT_test_conflicting_operator)
            self.assertFalse(
                XRAY_OT_test_conflicting_operator.is_registered
            )

            # other ValueError-s are not skipped
            with self.assertRaises(ValueError):
                utils.version.register_classes(XRAY_OT_test_unique_operator)
            self.assertFalse(XRAY_OT_test_unique_operator.is_registered)

        finally:
            bpy.utils.register_class = prev_register_class

    def test_properties_after_reregistration(self):
        io_scene_xray.unregister()
        self.assertFalse(hasattr(bpy.types.Object, 'xray'))

        io_scene_xray.register()
        self.assertTrue(hasattr(bpy.types.Object, 'xray'))

    def test_handlers_are_not_duplicated(self):
        try:
            io_scene_xray.register()

            load_post = [
                handler
                for handler in bpy.app.handlers.load_post
                    if handler is handlers.load_post
            ]
            self.assertEqual(1, len(load_post))

            scene_update_post = [
                handler
                for handler in utils.version.get_scene_update_post()
                    if handler is handlers.scene_update_post
            ]
            self.assertEqual(1, len(scene_update_post))

        finally:
            io_scene_xray.unregister()

        io_scene_xray.register()
