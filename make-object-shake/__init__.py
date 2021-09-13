# ====================== BEGIN GPL LICENSE BLOCK ============================
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
# ======================= END GPL LICENSE BLOCK =============================

# ----------------------------------------------
# This addon allows to easily make an object shake
# ----------------------------------------------

import bpy
from random import randrange, uniform

bl_info = {
    'name': 'Make Object Shake',
    'description': "This addon allows to easily make an object shake",
    'author': 'Loux Xavier (BleuRaven)',
    'version': (0, 1, 4),
    'blender': (2, 91, 0),
    'location': 'VIEW_3D > OBJECT > Make active shake',
    'warning': '',
    "wiki_url":
    "https://github.com/xavier150/Make-Object-Shake",
    'tracker_url': '',
    'support': 'COMMUNITY',
    'category': '3D_interaction'}


def createCustomProp(target, default_value, property_name, description, max=1.0):

    if bpy.app.version < (3, 0, 0):
        if not target.get('_RNA_UI'):
            target['_RNA_UI'] = {}

    # set it
    target[property_name] = default_value

    # property attributes.for UI
    if bpy.app.version < (3, 0, 0):
        target['_RNA_UI'][property_name] = {
            "default": default_value,
            "min": 0.0,
            "max": max,
            "soft_min": 0.0,
            "soft_max": max,
            "description": description
            }
    else:
        target.id_properties_ui(property_name).update(
            default=default_value,
            min=0.0,
            max=max,
            soft_min=0.0,
            soft_max=max,
            description=description)

    # redraw Properties panel
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        for area in screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
                break

    DataPath = '["'+property_name+'"]'
    if type(target) == bpy.types.PoseBone:
        DataPath = 'pose.bones["'+target.name+'"]'+DataPath
    return DataPath


def CreateShakeConstraint(obj, ShakeObj, constType, axe):

    constraintName = "Copy "+axe+" "+constType+" from Shake point"
    isPoseBone = False
    if type(obj) == bpy.types.PoseBone:
        isPoseBone = True

    # Create constraints
    try:
        myConst = obj.constraints[constraintName]
    except:
        myConst = obj.constraints.new(constType)
        myConst.name = constraintName

    # Set constraints props
    myConst.use_x = True if axe == "X" else False
    myConst.use_y = True if axe == "Y" else False
    myConst.use_z = True if axe == "Z" else False
    myConst.use_offset = True
    myConst.target_space = 'WORLD'
    myConst.owner_space = 'LOCAL'
    myConst.target = ShakeObj
    myConst.show_expanded = False

    # Create drivers on constraint

    cS = 'constraints["'+myConst.name+'"].influence'
    if isPoseBone:
        DS = ('pose.bones["'+obj.name+'"].'+cS)
        myDriver = bpy.context.view_layer.objects.active.driver_add(DS)
    else:
        myDriver = obj.driver_add(cS)

    # Prepar driver var
    if isPoseBone:
        varObjID = obj.id_data
    else:
        varObjID = obj

    # Global Speed driver var
    SpeedVar = myDriver.driver.variables.new()
    SpeedVar.name = "global_intensity"
    SpeedVar.targets[0].id_type = 'OBJECT'
    SpeedVar.targets[0].id = varObjID

    if isPoseBone:
        string = 'pose.bones["'+obj.name+'"]["Shake_Influence"]'
        SpeedVar.targets[0].data_path = string
    else:
        SpeedVar.targets[0].data_path = '["Shake_Influence"]'

    # relative Speed driver var
    if constType == "COPY_LOCATION":
        propType = "loc"
    if constType == "COPY_ROTATION":
        propType = "rot"

    SpeedVar = myDriver.driver.variables.new()
    SpeedVar.name = "relative_intensity"
    SpeedVar.targets[0].id_type = 'OBJECT'
    SpeedVar.targets[0].id = varObjID

    if isPoseBone:
        s = 'pose.bones["'+obj.name+'"]["Shake_'+propType+axe+'"]'
        SpeedVar.targets[0].data_path = s
    else:
        SpeedVar.targets[0].data_path = '["Shake_'+propType+axe+'"]'

    myDriver.driver.expression = "global_intensity / 100 * relative_intensity"


def SetShakeObj(myTargetObj, maxRandomOffset=0, minScale=1, maxScale=1):

    isPoseBone = False
    if type(myTargetObj) == bpy.types.PoseBone:
        isPoseBone = True

    # Create shake empty
    myShakeEmptyName = 'ShakePoint_' + myTargetObj.name
    if isPoseBone:
        myShakeEmptyName = ('ShakePoint_' + myTargetObj.id_data.name + '_' + myTargetObj.name)
    if myShakeEmptyName in bpy.data.objects:
        myShakeEmpty = bpy.data.objects[myShakeEmptyName]
    else:
        myShakeEmpty = bpy.data.objects.new(myShakeEmptyName, None)
        myShakeEmpty.location = (0.0, 0.0, 0.0)
        myShakeEmpty.empty_display_size = 0.45
        bpy.context.scene.collection.objects.link(myShakeEmpty)

    # Create Custom propertys
    ShakeEmptySpeedProp = createCustomProp(myTargetObj, 1.0, 'Shake_Speed', "Global shake speed")
    createCustomProp(myTargetObj, 1.0, 'Shake_Influence', "Global shake intensity", 100.0)
    createCustomProp(myTargetObj, 1.0, 'Shake_locX', "Shake intensity of Location X")
    createCustomProp(myTargetObj, 1.0, 'Shake_locY', "Shake intensity of Location Y")
    createCustomProp(myTargetObj, 1.0, 'Shake_locZ', "Shake intensity of Location Z")
    createCustomProp(myTargetObj, 1.0, 'Shake_rotX', "Shake intensity of Rotation Euler X")
    createCustomProp(myTargetObj, 1.0, 'Shake_rotY', "Shake intensity of Rotation Euler Y")
    createCustomProp(myTargetObj, 1.0, 'Shake_rotz', "Shake intensity of Rotation Euler Z")

    # Create drivers for shake animation
    myShakeEmpty.driver_add("location")
    myShakeEmpty.driver_add("rotation_euler")

    # Set drivers properties
    for driver in myShakeEmpty.animation_data.drivers:

        # Keyframes of drivers
        for key in driver.keyframe_points:
            driver.keyframe_points.remove(driver.keyframe_points[0])
        driver.keyframe_points.add(2)
        driver.keyframe_points[0].co = (0, 0)
        driver.keyframe_points[1].co = (1, 0)

        # Modifiers of driver
        for mod in driver.modifiers:
            driver.modifiers.remove(mod)
        NoiseMod = driver.modifiers.new(type='NOISE')
        NoiseMod.offset = randrange(maxRandomOffset)
        NoiseMod.scale = uniform(minScale, maxScale)
        NoiseMod.strength = 10

        # Variable on driver
        for var in driver.driver.variables:
            driver.driver.variables.remove(var)

        # Add Speed Driver Var
        SpeedVar = driver.driver.variables.new()
        SpeedVar.name = "shake_speed"
        SpeedVar.targets[0].id_type = 'OBJECT'
        if isPoseBone:
            # SpeedVar.targets[0].id_type = 'ARMATURE'
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            print(myTargetObj.id_data)
            SpeedVar.targets[0].id = myTargetObj.id_data
            SpeedVar.targets[0].data_path = 'bones["'+myTargetObj.name+'"]'
        else:
            SpeedVar.targets[0].id = myTargetObj
        SpeedVar.targets[0].data_path = ShakeEmptySpeedProp

        driver.driver.expression = "shake_speed * 100 * frame"

    try:
        for driver in myTargetObj.animation_data.drivers:
            # Variable on driver
            for var in driver.driver.variables:
                driver.driver.variables.remove(var)
    except:
        pass

    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "X")
    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "Y")
    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "Z")
    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "X")
    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "Y")
    CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "Z")


class MOS_PT_MakeObjectShake(bpy.types.Panel):

    bl_idname = "MOS_PT_ObjectShake"
    bl_label = "ObjectShake"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_category = "Make Object Shake"

    class MOS_OT_MakeActiveObjectShake(bpy.types.Operator):
        bl_label = "Make active object shake"
        bl_idname = "object.make_active_object_shake"
        bl_description = "Set the active object shaken and add customs properties."
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            if bpy.context.object.mode == "POSE":
                ActiveObj = bpy.context.active_pose_bone
            else:
                ActiveObj = bpy.context.view_layer.objects.active

            if ActiveObj is not None:
                SetShakeObj(ActiveObj, 10000, 95, 105)
                self.report({'INFO'}, "Active object is shaken, "
                            "look in customs properties.")
            else:
                self.report({'WARNING'}, "WARNING: No active object, "
                            "please select a object.")
            return {'FINISHED'}

    class MOS_OT_MakeActiveBoneShake(bpy.types.Operator):
        bl_label = "Make active bone shake"
        bl_idname = "object.make_active_bone_shake"
        bl_description = "Set the active bone shaken and add customs properties."
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            if bpy.context.object.mode == "POSE":
                ActiveObj = bpy.context.active_pose_bone
            else:
                ActiveObj = bpy.context.view_layer.objects.active

            if ActiveObj is not None:
                SetShakeObj(ActiveObj, 10000, 95, 105)
                self.report({'INFO'}, "Active bone is shaken, "
                            "look in customs properties.")
            else:
                self.report({'WARNING'}, "WARNING: No active object, "
                            "please select a bone in PoseBone.")
            return {'FINISHED'}

# ############################[...]#############################


classes = (
    MOS_PT_MakeObjectShake.MOS_OT_MakeActiveObjectShake,
    MOS_PT_MakeObjectShake.MOS_OT_MakeActiveBoneShake,
)


def menu_func_object(self, context):
    layout = self.layout
    col = layout.column()
    col.separator(factor=1.0)
    col.operator(MOS_PT_MakeObjectShake.MOS_OT_MakeActiveObjectShake.bl_idname)


def menu_func_bone(self, context):
    layout = self.layout
    col = layout.column()
    col.separator(factor=1.0)
    col.operator(MOS_PT_MakeObjectShake.MOS_OT_MakeActiveBoneShake.bl_idname)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(menu_func_object)
    bpy.types.VIEW3D_MT_pose.append(menu_func_bone)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    bpy.types.VIEW3D_MT_object.remove(menu_func_object)
    bpy.types.VIEW3D_MT_pose.remove(menu_func_bone)
