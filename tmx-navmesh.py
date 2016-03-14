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
		navpoint_center_x = (navpoint[0] * tilemap.tile_size[0]) + (tilemap.tile_size[0] / 2)
		navpoint_center_y = (navpoint[1] * tilemap.tile_size[1]) + (tilemap.tile_size[1] / 2)
		navpoint_rect_size = (20, 20)
		navpoint_rect_left = navpoint_center_x - (navpoint_rect_size[0] / 2) 
		navpoint_rect_top = navpoint_center_y - (navpoint_rect_size[1] / 2) 
		navpoint_rect_right = navpoint_rect_left + navpoint_rect_size[0]
		navpoint_rect_bottom = navpoint_rect_top + navpoint_rect_size[1]
		image_draw.rectangle([(navpoint_rect_left, navpoint_rect_top), (navpoint_rect_right, navpoint_rect_bottom)], outline="blue", fill="blue")

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
#		if ((platform.get_position()[0] <= platform_to_project.get_right_tile()) & (platform.get_size()[0] > 1) & (platform.get_top_tile() >= platform_to_project.get_position()[1]) & (platform_to_project != platform)):
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
	return navpoints

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

#print "... " + str(platforms[1])
print_platforms(platforms)
print ".... output image size " + str(get_image_size(tilemap))
navpoints = get_navpoints(tilemap, platforms)
print "..... " + str(navpoints)

print_image(platforms, tilemap, navpoints)

# platform = Platform(1, tilemap.layers['physics'].all_objects()[1])
#is_neighboring(tilemap.layers['physics'].all_objects()[0], tilemap.layers['physics'].all_objects()[1])

#print "is island " + str(platform.is_island()) + " " + str(platform.get_position()) + " " + str(platform.get_size())

