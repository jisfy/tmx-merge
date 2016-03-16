import sys
import tmxlib
import math
import os
from PIL import Image, ImageDraw

class NavLink:

	def __init__(self, target_navpoint, navtype, horizontal_speed, vertical_speed):
		self.target_navpoint = target_navpoint
		self.vertical_speed = None
		self.horizontal_speed = None
		self.navtype = navtype
		self.link_type_colors = {'fall':'red', 'jump':'blue', 'walk':'yellow'}

	def set_horizontal_speed(self, horizontal_speed):
		self.horizontal_speed = horizontal_speed

	def set_vertical_speed(self, vertical_speed):
		self.vertical_speed = vertical_speed

	def draw(self, image_draw, position, tile_size):
		navpoint_link_center_x = (self.target_navpoint.get_position()[1] * tile_size[1]) + (tile_size[1] / 2)
		navpoint_link_center_y = (self.target_navpoint.get_position()[0] * tile_size[0]) + (tile_size[0] / 2)

		color = self.link_type_colors[self.navtype]
		image_draw.line([position, (navpoint_link_center_x, navpoint_link_center_y)], fill=color)

	def __repr__(self):
		repr = "--> " + str(self.target_navpoint.id) + " speed x : " + str(self.horizontal_speed) + " speed y :" + str(self.vertical_speed)
		return repr

class GridElement:

	def __init__(self, element_type):
		self.element_type = element_type

class PlatformElement(GridElement):
	
	def __init__(self, id, mapobject):
		GridElement.__init__(self, "platform")
		self.id = id
		self.mapobject = mapobject

	def get_box(self, pos, tile_size):
		left = pos[1] * tile_size[0]
		right = ((pos[1] + 1) * tile_size[0]) - 1
        	top = pos[0] * tile_size[1]
        	bottom = ((pos[0] + 1) * tile_size[1]) - 1

		box = [(left, top), (right, bottom)]
		return box

	def draw(self, image_draw, position, tile_size):
		box = self.get_box(position, tile_size)
		image_draw.rectangle(box , fill="white", outline="blue")

	        id_text_size = image_draw.textsize(str(self.id))
		text_left = box[0][0] + ((tile_size[0] / 2) - (id_text_size[0] / 2))
		text_top = box[0][1] + ((tile_size[1] / 2) - (id_text_size[1] / 2))
		image_draw.text((text_left, text_top), str(self.id), fill="black")

class NavPoint(GridElement):

	def __init__(self, id, position_tile):
		GridElement.__init__(self, "navpoint")
		self.id = id
		self.position_tile = position_tile
		self.is_corrected = False
		self.links = {}

	def set_position(self, position):
		self.position_tile = position
		self.is_corrected = True

	def get_position(self):
		return self.position_tile

	def add_link(self, target_navpoint, navtype, horizontal_speed, vertical_speed):
		self.links[target_navpoint.id] = NavLink(target_navpoint, navtype, horizontal_speed, vertical_speed)

	def draw(self, image_draw, position, tile_size):
		navpoint_center_x = (position[1] * tile_size[0]) + (tile_size[0] / 2)
		navpoint_center_y = (position[0] * tile_size[1]) + (tile_size[1] / 2)
		navpoint_rect_size = (20, 20)
		navpoint_rect_left = navpoint_center_x - (navpoint_rect_size[0] / 2) 
		navpoint_rect_top = navpoint_center_y - (navpoint_rect_size[1] / 2) 
		navpoint_rect_right = navpoint_rect_left + navpoint_rect_size[0]
		navpoint_rect_bottom = navpoint_rect_top + navpoint_rect_size[1]
		# print "- drawing NavPoint " + str(navpoint_rect_left) + " , " + str(navpoint_rect_top)
		image_draw.rectangle([(navpoint_rect_left, navpoint_rect_top), (navpoint_rect_right, navpoint_rect_bottom)], outline="blue", fill="blue")

	        id_text_size = image_draw.textsize(str(self.id))
		text_left = navpoint_center_x - (id_text_size[0] / 2)
		text_top = navpoint_center_y - (id_text_size[1] / 2)
		image_draw.text((text_left, text_top), str(self.id), fill="white")

		for navpoint_link in self.links.values():
			navpoint_link.draw(image_draw, (navpoint_center_x, navpoint_center_y), tile_size)

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

class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

def build_grid(tilemap):
	objects_layer = tilemap.layers['physics']
	grid = AutoVivification()
	platform_id = 0
	for object in objects_layer.all_objects():
		for offset_x in range(0, int(object.size[0])):
			for offset_y in range(0, int(object.size[1])):
				# print ".... row " + str(int(object.pos[1]) - offset_y) + " , col " + str(int(object.pos[0]) + offset_x)
				grid[(int(object.pos[1]) - offset_y)][(int(object.pos[0]) + offset_x)] = PlatformElement(platform_id, object)

		platform_id += 1

	return grid

def print_grid(grid, tilemap, navpoints):
	image = Image.new("RGBA", get_image_size(tilemap))
	image_draw = ImageDraw.Draw(image)

	for row_index in sorted(grid.keys()):		
		for col_index in sorted(grid[row_index].keys()):
			grid_element = grid[row_index][col_index]
			
			# print "....... " + "row " + str(row_index) + " col " + str(col_index) + " Grid ->" + str(grid_element)
			if (grid_element.element_type == "navpoint"):
				print " ....... " + "row " + str(row_index) + " col " + str(col_index) + " links" + str(grid_element.links)
			grid_element.draw(image_draw, (row_index, col_index), tilemap.tile_size)

	image.save('grabado_3.png', 'PNG', transparency=0)

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

	image.save('grabado.png', 'PNG', transparency=0)

def add_border(grid, cell_position, id):
	neighbor_row = cell_position[0] - 1
	neighbor_col = cell_position[1]
	next_navpoint_id = id
	if (not((neighbor_row in grid) and (neighbor_col in grid[neighbor_row])) and (neighbor_row > 0)):
		print "--- Adding NavPoint at " + str(neighbor_row) + " , " + str(neighbor_col) + " for .. " + str(cell_position)
		grid[neighbor_row][neighbor_col] = NavPoint(id, (neighbor_row, neighbor_col))
		next_navpoint_id = id + 1

	return next_navpoint_id

def is_last_platform_element(grid, cell_position):
	something_on_the_right = ((cell_position[1] + 1) in grid[cell_position[0]])
	is_platform = something_on_the_right and (grid[cell_position[0]][cell_position[1]].element_type == "platform")
	is_next_platform = something_on_the_right and (grid[cell_position[0]][cell_position[1] + 1].element_type == "platform")	
	same_on_the_right = is_platform and is_next_platform and (grid[cell_position[0]][cell_position[1]].id == grid[cell_position[0]][cell_position[1] + 1].id)
	return (not(same_on_the_right))

def should_have_right_projection(grid, position, tilemap_size):
	is_walkable = not(((position[0] - 1) in grid) and (position[1] in grid[position[0] - 1]) and (grid[position[0] - 1][position[1]].element_type == "platform")) and ((position[0] - 1) >= 0) 
	is_right_neighbor_taken = (position[0] in grid) and (position[1] + 1 < tilemap_size[0]) and ((position[1] + 1) in grid[position[0]])
	return not(is_right_neighbor_taken) and is_walkable

def should_have_left_projection(grid, position, tilemap_size):
	is_walkable = not(((position[0] - 1) in grid) and (position[1] in grid[position[0] - 1]) and (grid[position[0] - 1][position[1]].element_type == "platform")) and ((position[0] - 1) >= 0) 
	is_left_neighbor_taken = (position[0] in grid) and (position[1] -1 > 0) and ((position[1] - 1) in grid[position[0]])
	return not(is_left_neighbor_taken) and is_walkable

def find_projection(grid, neighbor_position, tilemap_size):
	projection = None
	for row_index in range(neighbor_position[0], tilemap_size[1]):
		cell_exists = (row_index in grid) and (neighbor_position[1] in grid[row_index])
		cell_is_platform = cell_exists and (grid[row_index][neighbor_position[1]].element_type == "platform")

		one_up_row_index = row_index - 1
		one_up_not_exists = (one_up_row_index > 0) and not((one_up_row_index in grid) and (neighbor_position[1] in grid[one_up_row_index]) and (grid[one_up_row_index][neighbor_position[1]].element_type != "navpoint"))

		# print "...finding proj nr:" + str(neighbor_position[0]) + ",nc:" + str(neighbor_position[1]) + " cip " + str(cell_is_platform) + " oneuprow " + str(one_up_not_exists) + ".. one_up_rindex " + str(one_up_row_index)
		if (cell_is_platform and one_up_not_exists):
			projection = (one_up_row_index, neighbor_position[1])
			break

	return projection

def find_left_projection(grid, position, tilemap_size):
	left_neighbor_position = (position[0], position[1] - 1)
	return find_projection(grid, left_neighbor_position, tilemap_size)

def find_right_projection(grid, position, tilemap_size):
	right_neighbor_position = (position[0], position[1] + 1)
	return find_projection(grid, right_neighbor_position, tilemap_size)

def add_projected_navpoints(tilemap, grid, first_navpoint_id):
	navpoint_id = first_navpoint_id
	for col_index in range(tilemap.size[0]):
		left_projection_added = False
		right_projection_added = False
		for row_index in range(tilemap.size[1]):
			cell_exists = (row_index in grid) and (col_index in grid[row_index])
			cell_is_platform = cell_exists and (grid[row_index][col_index].element_type == "platform")
		
			if (cell_is_platform) and (should_have_left_projection(grid, (row_index, col_index), tilemap.size)):
				projection_found = find_left_projection(grid, (row_index, col_index), tilemap.size)
				# print " should have left r:" + str(row_index) + ", c:" + str(col_index) + ",p:" + str(projection_found)
				if projection_found != None:
					grid[projection_found[0]][projection_found[1]] = NavPoint(navpoint_id, projection_found)
					navpoint_id +=1 
					left_projection_added = True

			if (cell_is_platform) and (should_have_right_projection(grid, (row_index, col_index), tilemap.size)):	
				projection_found = find_right_projection(grid, (row_index, col_index), tilemap.size)
				# print " should have right r:" + str(row_index) + ", c:" + str(col_index) + ",p:" + str(projection_found)
				if projection_found != None:
					grid[projection_found[0]][projection_found[1]] = NavPoint(navpoint_id, projection_found)
					navpoint_id +=1
					right_projection_added = True

			if (left_projection_added and right_projection_added):
				break

	return navpoint_id

def add_navpoints(tilemap, grid):
	navpoint_id = 0
	for row_index in sorted(grid.keys()):
		current_cell_platform_id = None
		for col_index in sorted(grid[row_index].keys()):
			if (row_index > 0):
					grid_element = grid[row_index][col_index]
					is_platform = (grid_element.element_type == "platform")				
					if (is_platform):
						still_same_platform = (grid_element.id == current_cell_platform_id)

						if (not still_same_platform):
							# new platform started							
							current_cell_platform_id = grid_element.id
							navpoint_id = add_border(grid, (row_index, col_index), navpoint_id)
						elif is_last_platform_element(grid, (row_index, col_index)):
							navpoint_id = add_border(grid, (row_index, col_index), navpoint_id)

	return navpoint_id

def add_horizontal_navpoint_links(grid):
	for row_index in sorted(grid.keys()):
		last_element = None
		for col_index in sorted(grid[row_index].keys()):
			grid_element = grid[row_index][col_index]
			if (grid_element.element_type == "navpoint"):
				if (last_element != None):
					last_element.add_link(grid_element, "walk", 3, 0)
					grid_element.add_link(last_element, "walk", -3, 0)
					last_element = grid_element
				else:
					last_element = grid_element
			else:
				last_element = None

def add_vertical_link_to_neighbors(grid, source_navpoint_position, tilemap, max_jump_height):
	source_navpoint_position[0]
	neighbor_col_index = source_navpoint_position[1] + 1
	for row_index in range(tilemap.size[1]):
		navpoint_exists = (row_index in grid) and (neighbor_col_index in grid[row_index]) and (grid[row_index][neighbor_col_index].element_type == "navpoint")

		if navpoint_exists:
			if (source_navpoint_position[0] > row_index):
				if ((source_navpoint_position[0] - row_index) <= max_jump_height):
					#jump link
					grid[source_navpoint_position[0]][source_navpoint_position[1]].add_link(grid[row_index][neighbor_col_index], "jump", 0, 3)
				grid[row_index][neighbor_col_index].add_link(grid[source_navpoint_position[0]][source_navpoint_position[1]], "fall", 3, 0)
			elif (source_navpoint_position[0] < row_index):
					# fall link
				if ((row_index - source_navpoint_position[0]) <= max_jump_height):
					grid[row_index][neighbor_col_index].add_link(grid[source_navpoint_position[0]][source_navpoint_position[1]], "jump", 0, 3)
				grid[source_navpoint_position[0]][source_navpoint_position[1]].add_link(grid[row_index][neighbor_col_index], "fall", 3, 0)	

def add_vertical_navpoint_links(grid, tilemap):
	for col_index in range(tilemap.size[0]):
		for row_index in range(tilemap.size[1]):
			navpoint_exists = (row_index in grid) and (col_index in grid[row_index]) and (grid[row_index][col_index].element_type == "navpoint")
			if (navpoint_exists):
				add_vertical_link_to_neighbors(grid, (row_index, col_index), tilemap, 2)
	
def get_navpoints_new(tilemap, platforms):
	navpoints = {}
	index = 0
	for platform in platforms.values():
		added_border = 0
		navpoint_border_left = None
		navpoint_border_right = None
		if ((platform.left == None) & (platform.get_map_object().pos[0] != 0)):
			# check if the platform is on the left screen border

			projected_point = get_projection_left(platform, platforms)
			navpoint_projected = NavPoint(index, projected_point)
			navpoints[index] = navpoint_projected
			index +=1

			border_point = get_border_left(platform, platforms)
			if border_point != None:
				navpoint_border_left = NavPoint(index, border_point)
				navpoints[index] = navpoint_border_left
				navpoint_border_left.add_link(navpoint_projected, "walk", -3, 0)
				index +=1
				added_border +=1


		if ((platform.right == None) & (platform.get_map_object().pos[0] + platform.get_map_object().size[0] != tilemap.size[0])):
			# check if the platform is on the right screen border

			projected_point = get_projection_right(platform, platforms)
			navpoint_projected = NavPoint(index, projected_point)
			navpoints[index] = navpoint_projected
			index +=1
			
			border_point = get_border_right(platform, platforms)
			if border_point != None:
				navpoint_border_right = NavPoint(index, border_point)
				navpoints[index] = navpoint_border_right
				navpoint_border_right.add_link(navpoint_projected, "walk", 3, 0)
				index +=1
				added_border +=1

		if (added_border == 2):
			navpoint_border_left.add_link(navpoint_border_right, "walk", 3, 0)
			navpoint_border_right.add_link(navpoint_border_left, "walk", -3, 0)

	return navpoints

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

#navpoint_graph = get_navpoints_new(tilemap, platforms)
#print_image(platforms, tilemap, navpoint_graph.values())
#print "Navpoint Graph " + str(navpoint_graph)

grid = build_grid(tilemap)
last_navpoint_id = add_navpoints(tilemap, grid)
add_projected_navpoints(tilemap, grid, last_navpoint_id)
add_horizontal_navpoint_links(grid)
add_vertical_navpoint_links(grid, tilemap)
print_grid(grid, tilemap, None)
