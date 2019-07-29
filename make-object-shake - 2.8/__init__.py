#====================== BEGIN GPL LICENSE BLOCK ============================
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
#======================= END GPL LICENSE BLOCK =============================

# ----------------------------------------------
# This addon allows to easily make an object shake
# ----------------------------------------------

bl_info = {
	'name': 'Make Object Shake',
	'description': "This addon allows to easily make an object shake",
	'author': 'Loux Xavier (BleuRaven)',
	'version': (0, 1, 2),
	'blender': (2, 80, 0),
	'location': 'Search > Make active shake',
	'warning': '',
	"wiki_url": "http://xavierloux.com/creation/view/?creation=make-object-shake",
	'tracker_url': '',
	'support': 'COMMUNITY',
	'category': '3D_interaction'}
	
import bpy
from random import randrange, uniform
from rna_prop_ui import rna_idprop_ui_prop_get

def createCustomProp(target, defaultValue, propName, description, max = 1.0):
	target[propName]=defaultValue
	prop_ui = rna_idprop_ui_prop_get(target, propName)
	prop_ui["min"] = 0.0
	prop_ui["max"] = max
	prop_ui["soft_min"] = 0.0
	prop_ui["soft_max"] = max
	prop_ui["description"] = description
	
	DataPath = '["'+propName+'"]'
	if type(target) == bpy.types.PoseBone:
		DataPath = 'pose.bones["'+target.name+'"]'+DataPath
	return DataPath

	
def CreateShakeConstraint(obj, ShakeObj, constType, axe):

	constraintName = "Copy "+axe+" "+constType+" from Shake point"
	isPoseBone = False 
	if type(obj) == bpy.types.PoseBone:
		isPoseBone = True
		
	#Create constraints
	try:
		myConst = obj.constraints[constraintName]
	except:
		myConst = obj.constraints.new(constType)
		myConst.name = constraintName
		
	#Set constraints props
	myConst.use_x = True if axe =="X" else False
	myConst.use_y = True if axe =="Y" else False
	myConst.use_z = True if axe =="Z" else False
	myConst.use_offset = True
	myConst.target_space = 'WORLD'
	myConst.owner_space = 'LOCAL'
	myConst.target = ShakeObj
	myConst.show_expanded = False
	
	#Create drivers on constraint
	
	if isPoseBone == True:
		myDriver = bpy.context.scene.objects.active.driver_add('pose.bones["'+obj.name+'"].constraints["'+myConst.name+'"].influence')
	else:
		myDriver = obj.driver_add('constraints["'+myConst.name+'"].influence')

		
	#Prepar driver var	
	if isPoseBone == True:
		varObjID = obj.id_data
	else:
		varObjID = obj
		
	#Global Speed driver var
	SpeedVar = myDriver.driver.variables.new()
	SpeedVar.name = "global_intensity"
	SpeedVar.targets[0].id_type = 'OBJECT'
	SpeedVar.targets[0].id = varObjID
		
	if isPoseBone == True:
		SpeedVar.targets[0].data_path = 'pose.bones["'+obj.name+'"]["Shake_Influence"]'
	else:
		SpeedVar.targets[0].data_path = '["Shake_Influence"]'
	
	#relative Speed driver var
	if constType == "COPY_LOCATION":
		propType = "loc"
	if constType == "COPY_ROTATION":
		propType = "rot"
	
	SpeedVar = myDriver.driver.variables.new()
	SpeedVar.name = "relative_intensity"
	SpeedVar.targets[0].id_type = 'OBJECT'
	SpeedVar.targets[0].id = varObjID

	if isPoseBone == True:
		SpeedVar.targets[0].data_path = 'pose.bones["'+obj.name+'"]["Shake_'+propType+axe+'"]'
	else:
		SpeedVar.targets[0].data_path = '["Shake_'+propType+axe+'"]'
	
	myDriver.driver.expression = "global_intensity / 100 * relative_intensity"	

def SetShakeObj(
	myTargetObj, 
	maxRandomOffset = 0,
	minScale = 1, 
	maxScale = 1):
	
	isPoseBone = False 
	if type(myTargetObj) == bpy.types.PoseBone:
		isPoseBone = True
	
	#Create shake empty
	myShakeEmptyName = 'ShakePoint_' + myTargetObj.name
	if isPoseBone == True:
		myShakeEmptyName = 'ShakePoint_' + myTargetObj.id_data.name + '_' + myTargetObj.name
	if myShakeEmptyName in bpy.data.objects:
		myShakeEmpty = bpy.data.objects[myShakeEmptyName]
	else:
		myShakeEmpty = bpy.data.objects.new(myShakeEmptyName, None)
		myShakeEmpty.location = (0.0,0.0,0.0)
		myShakeEmpty.empty_display_size = 0.45
		bpy.context.scene.collection.objects.link(myShakeEmpty)
		
	#if isPoseBone == True:
		#myShakeEmpty.parent = 
	#else:
		#myShakeEmpty.parent = myTargetObj

	#Create Custom propertys 
	ShakeEmptySpeedProp = createCustomProp(myTargetObj, 1.0, 'Shake_Speed',"Global shake speed")
	createCustomProp(myTargetObj, 1.0, 'Shake_Influence',"Global shake intensity", 100.0)
	createCustomProp(myTargetObj, 1.0, 'Shake_locX',"Shake intensity of Location X")
	createCustomProp(myTargetObj, 1.0, 'Shake_locY',"Shake intensity of Location Y")
	createCustomProp(myTargetObj, 1.0, 'Shake_locZ',"Shake intensity of Location Z")
	createCustomProp(myTargetObj, 1.0, 'Shake_rotX',"Shake intensity of Rotation Euler X")
	createCustomProp(myTargetObj, 1.0, 'Shake_rotY',"Shake intensity of Rotation Euler Y")
	createCustomProp(myTargetObj, 1.0, 'Shake_rotz',"Shake intensity of Rotation Euler Z")

	#Create drivers for shake animation
	myShakeEmpty.driver_add("location")
	myShakeEmpty.driver_add("rotation_euler")
	
	#Set drivers properties
	for driver in myShakeEmpty.animation_data.drivers:
		
		#Keyframes of drivers
		for key in driver.keyframe_points:
			driver.keyframe_points.remove(driver.keyframe_points[0])
		driver.keyframe_points.add(2)
		driver.keyframe_points[0].co = (0,0)
		driver.keyframe_points[1].co = (1,0)
		
		#Modifiers of driver
		for mod in driver.modifiers:
			driver.modifiers.remove(mod)
		NoiseMod = driver.modifiers.new(type='NOISE')
		NoiseMod.offset = randrange(maxRandomOffset)
		NoiseMod.scale = uniform(minScale,maxScale)
		NoiseMod.strength = 10
		
		#Variable on driver
		for var in driver.driver.variables:
			driver.driver.variables.remove(var)
		
		#Add Speed Driver Var
		SpeedVar = driver.driver.variables.new()
		SpeedVar.name = "shake_speed"
		SpeedVar.targets[0].id_type = 'OBJECT'
		SpeedVar.targets[0].id = myTargetObj	
		SpeedVar.targets[0].data_path = ShakeEmptySpeedProp
		
		driver.driver.expression = "shake_speed * 100 * frame"

	
	try:
		for driver in myTargetObj.animation_data.drivers:
			#Variable on driver
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

		
class MOS_OT_MakesActiveObjectShake(bpy.types.Operator):
	bl_label = "Makes active object shake"
	bl_idname = "object.makesactiveshake"
	bl_description = "Set the active object shaken and add customs properties."
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		if bpy.context.object.mode == "POSE":
			ActiveObj = bpy.context.active_pose_bone
		else:
			ActiveObj = bpy.context.view_layer.objects.active
			
		if ActiveObj is not None:
			SetShakeObj(ActiveObj, 10000, 95, 105)
			self.report({'INFO'}, "Active object is shaken, look in customs properties.")
		else:
			self.report({'WARNING'}, "WARNING: No active object, please select a object.")
		return {'FINISHED'}
		
#############################[...]#############################

classes = (
	MOS_OT_MakesActiveObjectShake,
)

register, unregister = bpy.utils.register_classes_factory(classes)