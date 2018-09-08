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
	'version': (0, 1, 0),
	'blender': (2, 79, 0),
	'location': 'Search > Make active shake',
	'warning': '',
	"wiki_url": "http://xavierloux.com/creation/view/?creation=make-object-shake",
	'tracker_url': '',
	'support': 'COMMUNITY',
	'category': '3D_interaction'}
	
import bpy
from random import randrange, uniform
from rna_prop_ui import rna_idprop_ui_prop_get

def createCustomProp(target, defaultValue, propName, description):
	target[propName]=defaultValue
	prop_ui = rna_idprop_ui_prop_get(target, propName)
	prop_ui["min"] = 0.0
	prop_ui["max"] = 1.0
	prop_ui["soft_min"] = 0.0
	prop_ui["soft_max"] = 1.0
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
	myConst.use_x = True if axe =="x" else False
	myConst.use_y = True if axe =="y" else False
	myConst.use_z = True if axe =="z" else False
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
		SpeedVar.targets[0].data_path = 'pose.bones["'+obj.name+'"]["S_Influence"]'
	else:
		SpeedVar.targets[0].data_path = '["S_Influence"]'
	
	#relative Speed driver var
	if constType == "COPY_LOCATION":
		propType = "location"
	if constType == "COPY_ROTATION":
		propType = "rotation"
	
	SpeedVar = myDriver.driver.variables.new()
	SpeedVar.name = "relative_intensity"
	SpeedVar.targets[0].id_type = 'OBJECT'
	SpeedVar.targets[0].id = varObjID

	if isPoseBone == True:
		SpeedVar.targets[0].data_path = 'pose.bones["'+obj.name+'"]["S_'+propType+'_'+axe+'"]'
	else:
		SpeedVar.targets[0].data_path = '["S_'+propType+'_'+axe+'"]'
	
	myDriver.driver.expression = "global_intensity * relative_intensity"	

def SetShakeObj(
	myTargetObj, 
	maxRandomOffset = 0,
	minScale = 1, 
	maxScale = 1):
	
	"""Trains a linear regression model.
	Creates an new Empty with a shake animation and add follow contraint to target objet.

	Args:
	myTargetObj: A `Object` or `PoseBone`, the learning rate.
	maxRandomOffset: A `int`
	minScale: A non-zero `float`, 
	maxScale: A non-zero `float`

	Returns:
	A `Object` Shake Empty with shake animation
	"""
	
	
	isPoseBone = False 
	if type(myTargetObj) == bpy.types.PoseBone:
		isPoseBone = True
	
	#Create shake empty
	myShakeEmptyName = 'ShakePoint_' + myTargetObj.name
	if isPoseBone == True:
		myShakeEmptyName = 'ShakePoint_' + myTargetObj.id_data.name + '_' + myTargetObj.name
	try:
		myShakeEmpty = bpy.data.objects[myShakeEmptyName]
	except:
		myShakeEmpty = bpy.data.objects.new(myShakeEmptyName, None)
		myShakeEmpty.location = (0.0,0.0,0.0)
		myShakeEmpty.empty_draw_size = 0.45
		bpy.context.scene.objects.link(myShakeEmpty)
		bpy.context.scene.update()
		
	#if isPoseBone == True:
		#myShakeEmpty.parent = 
	#else:
		#myShakeEmpty.parent = myTargetObj

	#Create Custom propertys 
	ShakeEmptySpeedProp = createCustomProp(myShakeEmpty, 1.0, 'S_Speed',"Global shake speed")
	createCustomProp(myTargetObj, 0.05, "S_Influence","Global shake intensity")
	createCustomProp(myTargetObj, 1.0, 'S_location_x',"Shake intensity of Location X")
	createCustomProp(myTargetObj, 1.0, 'S_location_y',"Shake intensity of Location Y")
	createCustomProp(myTargetObj, 1.0, 'S_location_z',"Shake intensity of Location Z")
	createCustomProp(myTargetObj, 1.0, 'S_rotation_x',"Shake intensity of Rotation Euler X")
	createCustomProp(myTargetObj, 1.0, 'S_rotation_y',"Shake intensity of Rotation Euler Y")
	createCustomProp(myTargetObj, 1.0, 'S_rotation_z',"Shake intensity of Rotation Euler Z")

	#Create drivers for shake animation
	myShakeEmpty.driver_add("location")
	myShakeEmpty.driver_add("rotation_euler")
	
	#Set drivers properties
	for driver in myShakeEmpty.animation_data.drivers:
		
		#Keyframes of drivers
		for key in driver.keyframe_points:
			driver.keyframe_points.remove(driver.keyframe_points[0])
		driver.keyframe_points.add()
		driver.keyframe_points.add()
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
		
		#Add Current time Driver Var
		FrameVar = driver.driver.variables.new()
		FrameVar.name = "cur_time"
		FrameVar.targets[0].id_type = 'SCENE'
		FrameVar.targets[0].id = bpy.context.scene	
		FrameVar.targets[0].data_path = "frame_current"
		
		#Add Speed Driver Var
		SpeedVar = driver.driver.variables.new()
		SpeedVar.name = "shake_speed"
		SpeedVar.targets[0].id_type = 'OBJECT'
		SpeedVar.targets[0].id = myShakeEmpty	
		SpeedVar.targets[0].data_path = ShakeEmptySpeedProp
		
		driver.driver.expression = "cur_time * shake_speed"

	
	try:
		for driver in myTargetObj.animation_data.drivers:
			#Variable on driver
			for var in driver.driver.variables:
				driver.driver.variables.remove(var)
	except:
		pass
	
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "x")
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "y")
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_LOCATION", "z")
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "x")
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "y")
	CreateShakeConstraint(myTargetObj, myShakeEmpty, "COPY_ROTATION", "z")

		
class MakesActiveObjectShake(bpy.types.Operator):
	bl_label = "Makes active object shake"
	bl_idname = "object.makesactiveshake"
	bl_description = "Set the active object shaken and add customs properties."
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		if bpy.context.object.mode == "POSE":
			ActiveObj = bpy.context.active_pose_bone
		else:
			ActiveObj = bpy.context.scene.objects.active
			
		if ActiveObj is not None:
			SetShakeObj(ActiveObj, 100, 0.95, 1.05)
			self.report({'INFO'}, "Active object is shaken, look in customs properties.")
		else:
			self.report({'WARNING'}, "WARNING: No active object, please select a object.")
		return {'FINISHED'}
		
def register():
	bpy.utils.register_module(__name__)

def unregister():
	bpy.utils.unregister_module(__name__)
