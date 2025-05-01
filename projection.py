import mitsuba as mi
from sionna.rt import load_scene

# scene = load_scene(f'scenarios/test_scenario/scenario.xml')

scene = mi.load_file('scenarios/test_scenario/terrain.xml')


ray = mi.Ray3f(
    o=mi.Point3f([86.435, -73.34, 1000]),  # Ray origin: (x=0, y=1, z=0)
    d=mi.Vector3f([0, 0, -1])  # Ray direction: pointing downward along the Y-axis
)

intersection = scene.ray_intersect(ray).p[2]

print(intersection)

