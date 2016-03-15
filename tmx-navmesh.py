import sys
import tmxlib
import math
import os
from PIL import Image, ImageDraw

class Platform:

	def __init__(self, id, mapobject):
		self.bottom = None
		self.top = None
		self.left = None
		self.right = None
		self.id = id
		self.mapobject = mapobject
               
	def is_island(self):
		return ((self.bottom == None) & (self.top == None) & (self.left == None) & (self.right == None))

	def get_position(self):
		return self.mapobject.pos

	def get_size(self):
		return self.mapobject.size

	def get_map_object(self):
		return self.mapobject

	def set_left(self, platform):
		self.left = platform

	def set_right(self, platform):
		self.right = platform

	def set_top(self, platform):
		self.top = platform

	def set_bottom(self, platform): 
		self.bottom = platform

	def get_top_tile(self):
                top_tile = self.mapobject.pos[1] - self.mapobject.size[1]
		return top_tile	

	def get_right_tile(self):
		right_tile = self.mapobject.pos[0] + self.mapobject.size[0]
		return right_tile	

	def __repr__(self):
	        top_repr = "None"
		if (self.top != None):
			top_repr = str(self.top.id)

           	bottom_repr = "None"
		if (self.bottom != None):
			bottom_repr = str(self.bottom.id)

           	left_repr= "None"
		if (self.left != None):
			left_repr = str(self.left.id)

           	right_repr= "None"
		if (self.right != None):
			right_repr = str(self.right.id)

		repr = "<id : " + str(self.id) + ", top " + top_repr + ", bottom " + bottom_repr + ", left " + left_repr + ", right " + right_repr+ ">" 
		return repr
		
class NavLink:

	def __init__(self, target_navpoint, horizontal_speed, vertical_speed):
		self.target_navpoint = target_navpoint
		self.vertical_speed = None
		self.horizontal_speed = None

	def set_horizontal_speed(self, horizontal_speed):
		self.horizontal_speed = horizontal_speed

	def set_vertical_speed(self, vertical_speed):
		self.vertical_speed = vertical_speed

	def __repr__(self):
		repr = "--> " + str(self.target_navpoint.id) + " speed x : " + str(self.horizontal_speed) + " speed y :" + str(self.vertical_speed)
		return repr

class NavPoint:

	def __init__(self, id, position_tile):
		self.id = id
		self.position_tile = position_tile
		self.is_corrected = False
		self.links = {}

	def set_position(self, position):
		self.position_tile = position
		self.is_corrected = True

	def get_position(self):
		return self.position_tile

	def add_link(self, target_navpoint, horizontal_speed, vertical_speed):
		self.links[target_navpoint.id] = NavLink(target_navpoint, horizontal_speed, vertical_speed)

	def __repr__(self):
		repr = "{id : " + str(self.id) + ";pos: " + str(self.position_tile) + ";links: " + str(self.links) + "}\n" 
		return repr

def get_target_tilemap_filename(tilemap_path, target_tilemap_path):
	target_tilemap_filename = os.path.join(target_tilemap_path, os.path.basename(tilemap_path))
	return target_tilemap_filename

def get_tilemap(tilemap_path):
        tilemap = tmxlib.Map.open(tilemap_path)
	return tilemap

def print_objects(tilemap):
	objects_layer = tilemap.layers['physics']
	for object in objects_layer.all_objects():
		print ".. Object " + str(object.name) + " "  + str(object.type) + " " + str(object.pos) + " " + str(object.size)

def is_on_top(map_object_1, map_object_2):
        is_on_top = ((map_object_1.pos[1] - map_object_1.size[1]) == map_object_2.pos[1])
	return is_on_top

def is_on_left(map_object_1, map_object_2):
        is_on_left = (map_object_1.pos[0] == (map_object_2.pos[0] + map_object_2.size[0]))
	return is_on_left

def is_on_right(map_object_1, map_object_2):
        is_on_right = ((map_object_1.pos[0] + map_object_1.size[0]) == map_object_2.pos[0])
	return is_on_right

def is_right_under(map_object_1, map_object_2):
        is_right_under = ((map_object_1.pos[1]) == (map_object_2.pos[1] - map_object_2.size[1]))
	return is_right_under

def parse_objects(tilemap):
	objects_layer = tilemap.layers['physics']
	object_id = 1
	platforms = {}
	for object in objects_layer.all_objects():
		platform = Platform(object_id, object)
		platforms[object_id] = platform
		object_id += 1

	for platform in platforms.values():
		for possible_neighbor in platforms.values():
			if (platform != possible_neighbor):	
				# print " platform " + str(platform.get_position()) + ", " + str(platform.get_size())
				if is_on_top(platform.get_map_object(), possible_neighbor.get_map_object()):
					platform.set_top(possible_neighbor)
				elif is_on_right(platform.get_map_object(), possible_neighbor.get_map_object()):
					platform.set_right(possible_neighbor)
				elif is_on_left(platform.get_map_object(), possible_neighbor.get_map_object()):
					platform.set_left(possible_neighbor)
				elif is_right_under(platform.get_map_object(), possible_neighbor.get_map_object()):
					platform.set_bottom(possible_neighbor)

	return platforms

def get_image_size(tilemap):
	image_width = tilemap.size[0] * tilemap.tile_size[0]
	image_height = tilemap.size[1] * tilemap.tile_size[1]
	return (image_width, image_height)

def print_image(platforms, tilemap, navpoints):
	image = Image.new("RGBA", get_image_size(tilemap))

	for platform in platforms.values():
		image_draw = ImageDraw.Draw(image)
                platform_position_left_pixels = platform.get_position()[0] * tilemap.tile_size[0]
                platform_position_bottom_pixels = platform.get_position()[1] * tilemap.tile_size[1]
                
		left = platform.get_map_object().pixel_pos[0]
                top = platform.get_map_object().pixel_pos[1] - platform.get_map_object().pixel_size[1]
                bottom = platform.get_map_object().pixel_pos[1]
		right = platform.get_map_object().pixel_pos[0] + platform.get_map_object().pixel_size[0]

		box = [(left, top), (right, bottom)]
		print "id " + str(platform.id) + ", " + str(box) 
		image_draw.rectangle(box , outline="white")

      	        id_text_size = image_draw.textsize(str(platform.id))
 		text_left = left + ((platform.get_map_object().pixel_size[0] / 2) - (id_text_size[0] / 2))
		text_top = top
		image_draw.text((text_left, text_top), str(platform.id), fill="white")

	for navpoint in navpoints:
		navpoint_center_x = (navpoint.get_position()[0] * tilemap.tile_size[0]) + (tilemap.tile_size[0] / 2)
		navpoint_center_y = (navpoint.get_position()[1] * tilemap.tile_size[1]) + (tilemap.tile_size[1] / 2)
		navpoint_rect_size = (20, 20)
		navpoint_rect_left = navpoint_center_x - (navpoint_rect_size[0] / 2) 
		navpoint_rect_top = navpoint_center_y - (navpoint_rect_size[1] / 2) 
		navpoint_rect_right = navpoint_rect_left + navpoint_rect_size[0]
		navpoint_rect_bottom = navpoint_rect_top + navpoint_rect_size[1]
		image_draw.rectangle([(navpoint_rect_left, navpoint_rect_top), (navpoint_rect_right, navpoint_rect_bottom)], outline="blue", fill="blue")
		for navpoint_link in navpoint.links.values():
			navpoint_link_target = navpoint_link.target_navpoint
			navpoint_link_center_x = (navpoint_link_target.get_position()[0] * tilemap.tile_size[0]) + (tilemap.tile_size[0] / 2)
			navpoint_link_center_y = (navpoint_link_target.get_position()[1] * tilemap.tile_size[1]) + (tilemap.tile_size[1] / 2)

			image_draw.line([(navpoint_center_x, navpoint_center_y), (navpoint_link_center_x, navpoint_link_center_y)], fill="blue")

	#for navpoint in navpoints:
	#	navpoint_center_x = (navpoint[0] * tilemap.tile_size[0]) + (tilemap.tile_size[0] / 2)
	#	navpoint_center_y = (navpoint[1] * tilemap.tile_size[1]) + (tilemap.tile_size[1] / 2)
	#	navpoint_rect_size = (20, 20)
	#	navpoint_rect_left = navpoint_center_x - (navpoint_rect_size[0] / 2) 
	#	navpoint_rect_top = navpoint_center_y - (navpoint_rect_size[1] / 2) 
	#	navpoint_rect_right = navpoint_rect_left + navpoint_rect_size[0]
	#	navpoint_rect_bottom = navpoint_rect_top + navpoint_rect_size[1]
	#	image_draw.rectangle([(navpoint_rect_left, navpoint_rect_top), (navpoint_rect_right, navpoint_rect_bottom)], outline="blue", fill="blue")

	image.save('grabado.png', 'PNG', transparency=0)

def is_higher(platform_1, platform_2):
	if (platform_2 != None):
		return (platform_1.get_top_tile() < platform_2.get_top_tile())
	else:
		return True
	
def get_projection_right(platform_to_project, platforms): 
	projected_platform = None
	projected_point = None

	for platform in platforms.values():
		print "####### candidate " + str(platform.get_position()) + " plat_to_proj " + str(platform_to_project.get_position()) + " ptop " + str(platform.get_top_tile()) 

		if ((platform.get_position()[0] <= platform_to_project.get_right_tile()) & (platform.get_right_tile() > platform_to_project.get_right_tile()) & (platform.get_top_tile() >= platform_to_project.get_position()[1]) & (platform_to_project != platform)):
			# check if the current platform starts further to the left and is below the platform to project							  # if so, that would mean the current platform is a projection candidate
			print "............ = " + str(platform) + " ..... " + str(projected_platform)
			if is_higher(platform, projected_platform):
				projected_platform = platform			
				projected_point = (platform_to_project.get_position()[0] + platform_to_project.get_size()[0], platform.get_top_tile()) 

	return projected_point

def get_projection_left(platform_to_project, platforms): 
	projected_platform = None
	projected_point = None

	for platform in platforms.values():
		print "####### candidate " + str(platform.get_position()) + " plat_to_proj " + str(platform_to_project.get_position()) + " ptop " + str(platform.get_top_tile()) 
		if ((platform.get_position()[0] < platform_to_project.get_position()[0]) & (platform.get_size()[0] > 1) & (platform.get_top_tile() >= platform_to_project.get_position()[1]) & (platform_to_project != platform)):
			# check if the current platform starts further to the left and is below the platform to project							  # if so, that would mean the current platform is a projection candidate
			print "............ = " + str(platform) + " ..... " + str(projected_platform)
			if is_higher(platform, projected_platform):
				projected_platform = platform			
				projected_point = (platform_to_project.get_position()[0] - 1, platform.get_top_tile()) 

	return projected_point

def get_border_left(platform_for_border, platforms):
	border_point = (platform_for_border.get_map_object().pos[0], platform_for_border.get_top_tile())
	for platform in platforms.values():
		border_overlapped = ((border_point[0] <= platform.get_right_tile()) & (border_point[0] >= platform.get_position()[0]) & (border_point[1] > platform.get_top_tile()) & (border_point[1] <= platform.get_position()[1]))
		if ((platform != platform_for_border) & border_overlapped):
			print " border " + str(border_point) + ", " + str(platform.get_position()) + ", " + str(platform.get_right_tile()) + ", " + str(platform.get_top_tile())
			return None			
	return border_point

def get_border_right(platform_for_border, platforms):
	border_point = (platform_for_border.get_map_object().pos[0] + platform_for_border.get_map_object().size[0] - 1, platform_for_border.get_top_tile())
	for platform in platforms.values():
		border_overlapped = ((border_point[0] <= platform.get_right_tile()) & (border_point[0] >= platform.get_position()[0]) & (border_point[1] > platform.get_top_tile()) & (border_point[1] <= platform.get_position()[1]))
		print "++++++++++++++++++++++ border " + str(border_point) + ", " + str(platform.get_position()) + ", " + str(platform.get_right_tile()) + ", " + str(platform.get_top_tile())
		if ((platform != platform_for_border) & border_overlapped):
			return None			
	return border_point
	
def get_navpoints(tilemap, platforms):
	navpoints = []
	for platform in platforms.values():
		if ((platform.left == None) & (platform.get_map_object().pos[0] != 0)):
			# check if the platform is on the left screen border
			# border_point = (platform.get_map_object().pos[0], platform.get_top_tile())
			# navpoints.append(border_point)
			border_point = get_border_left(platform, platforms)
			if border_point != None:
				navpoints.append(border_point)
			projected_point = get_projection_left(platform, platforms)
			navpoints.append(projected_point)	
			print ". appending left " + str(projected_point) + " for " + str(platform) + ", " + str(platform.get_map_object().pos)
		if ((platform.right == None) & (platform.get_map_object().pos[0] + platform.get_map_object().size[0] != tilemap.size[0])):
			# check if the platform is on the right screen border
			# border_point = (platform.get_map_object().pos[0] + platform.get_map_object().size[0] - 1, platform.get_top_tile())
			# navpoints.append(border_point)
			border_point = get_border_right(platform, platforms)
			if border_point != None:
				navpoints.append(border_point)

			projected_point = get_projection_right(platform, platforms)
			navpoints.append(projected_point)	
			print ". appending right " + str(projected_point) + " for " + str(platform) + ", " + str(platform.get_map_object().pos)
	sorted_navpoints = sorted(navpoints, key = lambda navpoint: navpoint[0])
	return sorted_navpoints

def get_vertical_velocity(desired_height, step_period, world_gravity_step):
	if (desired_height <= 0):
		return 0 # wanna go down? just let it drop
  
	#quadratic equation setup (ax^2 + bx + c = 0)
	a = 0.5 / step_gravity[1]
	b = 0.5
	c = desired_height
      
	# check both possible solutions
	quadratic_solution1 = ( -b - math.sqrt( b*b - 4*a*c ) ) / (2*a)
	quadratic_solution2 = ( -b + math.sqrt( b*b - 4*a*c ) ) / (2*a)
  
	# use the one which is positive
	v = quadratic_solution1
	if ( v < 0 ):
		v = quadratic_solution2
  
	# convert answer back to seconds
	return v * (1.0 / step_period)

def get_max_height_time(step_gravity, step_velocity):
	n = (-step_velocity / step_gravity[1]) -1
	return n

def get_jump_and_falling_height_for_obstacle(obstacle_height, character_height, extra_jump_height_percent):
	half_character_height = character_height / 2.0
	jump_height = half_character_height + obstacle_height
	extra_falling_height_til_obstacle = (jump_height * extra_jump_height_percent / 100.0)	
	jump_height_extra = extra_falling_height_til_obstacle + jump_height
	return (jump_height_extra, extra_falling_height_til_obstacle)


def get_falling_time_til_obstacle(world_gravity_step, vertical_velocity_step, falling_height):
	a = world_gravity_step[1] / 2
	b = (vertical_velocity_step + (world_gravity_step[1] / 2))
	c = -falling_height
      
	square = math.sqrt(b * b - 4 * a * c)
	quadratic_solution1 = (-b - square) / (2 * a)
	quadratic_solution2 = (-b + square) / (2 * a)	

	one_solution_negative = ((quadratic_solution1 < 0) | (quadratic_solution2 < 0))
	solution = min(quadratic_solution1, quadratic_solution2)
	if (one_solution_negative):
		solution = max(quadratic_solution1, quadratic_solution2)

	return solution

def get_distance_travelled_horizontally(step_velocity_horizontal, raising_time, falling_time):
	total_time = raising_time + falling_time
	distance_traveled_horizontally = step_velocity_horizontal * total_time

	return distance_traveled_horizontally

def get_navpoint_graph(navpoints, max_jump_height):
	navpoint_graph = {}
	index = 0
	for navpoint in navpoints:

		if index in navpoint_graph:
			current_navpoint = navpoint_graph[index]
		else:
			print ".... Adding Navpoint " + str(index)
			current_navpoint = NavPoint(index, navpoint)
			navpoint_graph[index] = current_navpoint

		for next_index in range(index + 1, len(navpoints)):
			next_further_right = (navpoint[0] == (navpoints[next_index][0] - 1))
			distance_up_next = navpoint[1] - navpoints[next_index][1]
			next_further_up_reachable = ((distance_up_next > 0) & (distance_up_next <= max_jump_height))
			next_further_down = navpoint[1] > navpoints[next_index][1]
			next_same_height = (distance_up_next == 0)

			if next_further_right & next_further_up_reachable:
				next_navpoint = NavPoint(next_index, navpoints[next_index])
				navpoint_graph[next_index] = next_navpoint
				current_navpoint.add_link(next_navpoint, 0, 0)				
			elif next_further_right & next_further_down:
				pass
			elif next_same_height:
				next_navpoint = NavPoint(next_index, navpoints[next_index])
				navpoint_graph[next_index] = next_navpoint
				current_navpoint.add_link(next_navpoint, 0, 0)

		index +=1

	return navpoint_graph
		

def print_platforms(platforms):
	for platform in platforms.values():
		print ".. " + str(platform)

if len(sys.argv) < 2:
	print "Usage tmx-navmesh.py tilemap.tmx outputdir"
	quit()

input_tilemap_filenames = sys.argv[-1]
output_folder = sys.argv[-1]

tilemap = get_tilemap(input_tilemap_filenames)
print "...... tilemap size in tiles " + str(tilemap.size)
print_objects(tilemap)

platforms = parse_objects(tilemap)

#print_image(platforms, tilemap, navpoints)

print_platforms(platforms)
print ".... output image size " + str(get_image_size(tilemap))

navpoints = get_navpoints(tilemap, platforms)
print "..... " + str(navpoints)

jump_and_falling_height = get_jump_and_falling_height_for_obstacle(0.5, 1.0, 20)
jump_height= jump_and_falling_height[0]

MAXIMUM_JUMP_HEIGHT = 3
horizontal_velocity_m_s = 2.0
world_gravity_m_s_s = -9.8
step_period = 1.0/60.0
step_gravity = (0, step_period * step_period * world_gravity_m_s_s) # m/s/s
step_velocity_horizontal = step_period * horizontal_velocity_m_s	

vertical_velocity_m_s = get_vertical_velocity(jump_height, step_period, step_gravity)
step_velocity = step_period * vertical_velocity_m_s
time_to_max_height = get_max_height_time(step_gravity, step_velocity)
falling_time_til_obstacle = get_falling_time_til_obstacle(step_gravity, step_velocity, jump_and_falling_height[1])
distance_traveled_horizontally = get_distance_travelled_horizontally(step_velocity_horizontal, time_to_max_height, falling_time_til_obstacle)

print "-----  vertical velocity for height " + str(jump_height) + ", " + str(vertical_velocity_m_s) + " raising time " + str(time_to_max_height) + " falling time " + str(falling_time_til_obstacle) + " ... " + str(distance_traveled_horizontally)

navpoint_graph = get_navpoint_graph(navpoints, MAXIMUM_JUMP_HEIGHT)
print_image(platforms, tilemap, navpoint_graph.values())
print "Navpoint Graph " + str(navpoint_graph)
# platform = Platform(1, tilemap.layers['physics'].all_objects()[1])
#is_neighboring(tilemap.layers['physics'].all_objects()[0], tilemap.layers['physics'].all_objects()[1])

#print "is island " + str(platform.is_island()) + " " + str(platform.get_position()) + " " + str(platform.get_size())

