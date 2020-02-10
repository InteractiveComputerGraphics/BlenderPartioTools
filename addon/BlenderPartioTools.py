bl_info = {
    "name": "BlenderPartioTools",
    "description": "Importer for partio files.",
    "author": "Jan Bender",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "warning": "",
	"wiki_url": "https://github.com/InteractiveComputerGraphics/BlenderPartioTools",
    "support": "COMMUNITY",
    "category": "Import-Export"
}


import bpy
import sys
import os
import re
import mathutils
import partio
from bpy_extras.io_utils import ImportHelper
from bpy.app.handlers import persistent
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator


class PartioReader:
	def __init__( self, param ):
		self.param = param

	def __call__(self, scene, depsgraph=None):
		partioFile = self.param[0]
		emitterObject = self.param[1]
		
		try:
			dummy = emitterObject.name
		except:
			# emitter does not exist anymore
			#clear the post frame handler
			bpy.app.handlers.frame_change_post.remove(self)
			return
			
		indexlist = re.findall(r'\d+', partioFile)
		self.isSequence = True
		if len(indexlist) == 0:
			self.isSequence = False
			fileName = partioFile
		else:
			frameNumber = int(indexlist[-1])
			idx = partioFile.rfind(str(frameNumber))
			l = len(str(frameNumber))
			fileName = str(partioFile[0:idx]) + str(scene.frame_current-1) + str(partioFile[idx+l:])	
		
		print("Read partio file: " + fileName)
		
		p=partio.read(fileName)

		if p != None:
			totalParticles = p.numParticles()
			print("# particles: " + str(totalParticles))
						
			emitterObject.particle_systems[0].settings.count = totalParticles
			
			if totalParticles > 10000:
				emitterObject.particle_systems[0].settings.display_method = 'DOT'

			if depsgraph is None:
				depsgraph = bpy.context.evaluated_depsgraph_get()
			particle_systems = emitterObject.evaluated_get(depsgraph).particle_systems
			particles = particle_systems[0].particles
			
			posAttr = None
			velAttr = None
			for i in range(p.numAttributes()):
				attr=p.attributeInfo(i)
				typeStr="NONE"
				if attr.name=="position": posAttr = attr
				if attr.name=="velocity": velAttr = attr

			pos = [] 
			for i in range(p.numParticles()):
				position = p.get(posAttr, i)
				x = mathutils.Vector((position[0], -position[2], position[1]))
				
				x = emitterObject.matrix_world @ x 
				pos.append(x[0])
				pos.append(x[1])
				pos.append(x[2])
			# Set the location of all particle locations to flatList
			particles.foreach_set("location", pos)


			if velAttr is not None:
				vel = []
				for i in range(p.numParticles()):
					velocity = p.get(velAttr, i)
					v = mathutils.Vector((velocity[0], -velocity[2], velocity[1]))
					v = emitterObject.matrix_world @ v - emitterObject.location
					vel.append(v[0])
					vel.append(v[1])
					vel.append(v[2])    
				particles.foreach_set("velocity", vel)  
			
			emitterObject.particle_systems[0].settings.frame_end = 0


class PartioImporter(Operator, ImportHelper):
	bl_idname = "importer.partio" 
	bl_label = "Import partio files"

	filter_glob: StringProperty(
		default="*.bgeo",
		options={'HIDDEN'},
		maxlen=255, 
	)
	
	particleRadius: FloatProperty(
		name="Particle radius",
		description="Particle radius",
		default=0.025,
	)
	
	maxVel: FloatProperty(
		name="Max. velocity",
		description="Max. velocity",
		default=5.0,
	)

	def execute(self, context):
		self.emitterObject = None
		self.initParticleSystem()
		
		#run the function on each frame
		param = [self.filepath, self.emitterObject]
		
		self.emitterObject["partioFile"] = self.filepath
		
		bpy.app.handlers.frame_change_post.append(PartioReader(param))
		
		scn = bpy.context.scene
		scn.render.engine = 'CYCLES'
		
		indexlist = re.findall(r'\d+', self.filepath)
		self.isSequence = True
		if len(indexlist) == 0:
			self.isSequence = False
			bpy.context.scene.frame_current = 2
		else:
			frameNumber = int(indexlist[-1])
			bpy.context.scene.frame_current = frameNumber+1
		
		return {'FINISHED'}
		
	def initParticleSystem(self):
		# create emitter object
		bpy.ops.mesh.primitive_cube_add(enter_editmode=False, location=(0, 0, 0))

		self.emitterObject = bpy.context.active_object
		self.emitterObject.hide_viewport = False
		self.emitterObject.hide_render = False
		self.emitterObject.hide_select = False

		# add particle system
		bpy.ops.object.modifier_add(type='PARTICLE_SYSTEM')
		bpy.context.object.show_instancer_for_render = False
		bpy.context.object.show_instancer_for_viewport = False
		
		self.emitterObject
		self.emitterObject.particle_systems[0].settings.frame_start = 0
		self.emitterObject.particle_systems[0].settings.frame_end = 0
		self.emitterObject.particle_systems[0].settings.lifetime = 1000
		self.emitterObject.particle_systems[0].settings.particle_size = self.particleRadius
		self.emitterObject.particle_systems[0].settings.display_size = 2.0 * self.particleRadius

		# add object for rendering particles
		bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, location=(0, 0, 0))
		bpy.ops.object.shade_smooth()
		sphereObj = bpy.context.active_object
		sphereObj.hide_set(True)
		sphereObj.hide_viewport = False
		sphereObj.hide_render = True
		sphereObj.hide_select = True

		# add velocity-dependent color material
		found = True
		index = 1
		matNameBase = "ParticleMaterial"
		matName = matNameBase + str(index)
		materials = bpy.data.materials
		while (found):
			material = materials.get( matName )
			if material:
				index += 1
				matName = matNameBase + str(index)
			else:
				found = False
			
		material = materials.new( matName )


		material.use_nodes = True
		nodes = material.node_tree.nodes
		links = material.node_tree.links
		nodes.clear()
		links.clear()
		output = nodes.new( type = 'ShaderNodeOutputMaterial' )
		diffuse = nodes.new( type = 'ShaderNodeBsdfDiffuse' )
		link = links.new( diffuse.outputs['BSDF'], output.inputs['Surface'] )

		particleInfo = nodes.new( type = 'ShaderNodeParticleInfo' )

		vecMath = nodes.new( type = 'ShaderNodeVectorMath' )
		vecMath.operation = 'DOT_PRODUCT'

		math1 = nodes.new( type = 'ShaderNodeMath' )
		math1.operation = 'SQRT'
		math2 = nodes.new( type = 'ShaderNodeMath' )
		math2.operation = 'MULTIPLY'
		math2.inputs[1].default_value = 1.0/self.maxVel
		math2.use_clamp = True


		ramp = nodes.new( type = 'ShaderNodeValToRGB' )
		ramp.color_ramp.elements[0].color = (0, 0, 1, 1)

		link = links.new( particleInfo.outputs['Velocity'], vecMath.inputs[0] )
		link = links.new( particleInfo.outputs['Velocity'], vecMath.inputs[1] )

		link = links.new( vecMath.outputs['Value'], math1.inputs[0] )
		link = links.new( math1.outputs['Value'], math2.inputs[0] )
		link = links.new( math2.outputs['Value'], ramp.inputs['Fac'] )
		link = links.new( ramp.outputs['Color'], diffuse.inputs['Color'] )


		self.emitterObject.active_material = material
		sphereObj.active_material = material

		self.emitterObject.particle_systems[0].settings.render_type = 'OBJECT'
		self.emitterObject.particle_systems[0].settings.instance_object = bpy.data.objects[sphereObj.name]

@persistent
def loadPost(scene):
	for obj in bpy.data.objects:
		if "partioFile" in obj:
			param = [obj["partioFile"], obj]				
			bpy.app.handlers.frame_change_post.append(PartioReader(param))

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(PartioImporter.bl_idname, text="Partio Import")


def register():
	bpy.utils.register_class(PartioImporter)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
	bpy.app.handlers.load_post.append(loadPost)
	print(bpy.app.handlers.load_post)


def unregister():
	bpy.utils.unregister_class(PartioImporter)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
	bpy.app.handlers.load_post.remove(loadPost)


if __name__ == "__main__":
	print ("main")
	register()

	# test call
	bpy.ops.importer.partio('INVOKE_DEFAULT')
	unregister()