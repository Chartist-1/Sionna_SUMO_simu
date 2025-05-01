import bpy
import time 
scene = bpy.context.scene


with open('config.txt', 'r') as f:
    a = f.readline()
a = a.split(',')
for i in range(len(a)):
    a[i] = float(a[i])

bpy.context.scene.blosm.minLon,bpy.context.scene.blosm.maxLon ,bpy.context.scene.blosm.minLat , bpy.context.scene.blosm.maxLat = (38.28152,52.15014,38.29039,52.15409)

def remove_all():
    for obj in scene.objects :
        obj.select_set(True)
        bpy.ops.object.delete()


def terrain_osm():
    bpy.context.scene.blosm.dataType = 'terrain'
    bpy.ops.blosm.import_data()
    
def buildings_osm():
    bpy.context.scene.blosm.dataType = 'osm'
    bpy.context.scene.blosm.buildings = True
    bpy.context.scene.blosm.water = False
    bpy.context.scene.blosm.forests = False
    bpy.context.scene.blosm.vegetation= False
    bpy.context.scene.blosm.highways= True
    bpy.context.scene.blosm.terrainObject = "Terrain"
    bpy.ops.blosm.import_data()

def deselect_all():
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
        
def delete_all_materials():
    for material in bpy.data.materials:
        if material is not None:
            print(f"Removing material: {material.name}")
            bpy.data.materials.remove(material)
 
    
def convert2mesh():
    for obj in scene.objects:
        if (obj.name[:7] != 'profile') and (obj.type == 'CURVE'):
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.convert(target='MESH')
    except Exception as e:
        print('No objects to convert')
            


def remove_material_slots(object_name):
    obj = bpy.data.objects[object_name]
    obj.data.materials.clear()
    
def assign_material(object_name, material_name):
    obj = bpy.data.objects[object_name]
    obj.data.materials.append(bpy.data.materials.get(material_name))

if __name__ == '__main__':
    remove_all()
    terrain_osm()
    buildings_osm()
    deselect_all()
    convert2mesh()
    deselect_all()
    delete_all_materials()
    
    for obj in scene.objects:
        remove_material_slots(obj.name)
    bpy.data.materials.new('itu_brick')
    bpy.data.materials.new('itu_concrete')
    bpy.data.materials.new('itu_very_dry_ground')
    
    for obj in scene.objects:
        if (obj.name[-9:] == 'buildings') and (obj.type == 'MESH'):
            assign_material(obj.name,'itu_brick')
        elif (obj.name == 'Terrain'):
            assign_material(obj.name,'itu_very_dry_ground')
        elif (obj.type =='MESH'):
            assign_material(obj.name,'itu_concrete')
    bpy.ops.export_scene.mitsuba(filepath='new/scenario.xml',use_selection=False ,check_existing =True ,export_ids = True, axis_forward = 'Y', axis_up = 'X')
    for obj in scene.objects:
        if obj.name == 'Terrain':
            obj.select_set(True)
    bpy.ops.export_scene.mitsuba(filepath='new/terrain.xml',use_selection=True ,check_existing =True ,export_ids = True, axis_forward = 'Y', axis_up = 'X')



    # blender --background --python blender_auto.py