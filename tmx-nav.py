import sys
import tmxlib
import math
import os
from PIL import Image, ImageDraw

class JumpCalculationData:
	
	def __init__(self, character_height, step_frequency, extra_jump_percent, walk_speed, world_gravity, max_jump_height, pixels_per_meter):
		self.character_height = character_height
		self.step_frequency = step_frequency
		self.extra_jump_percent = extra_jump_percent
		self.walk_speed = walk_speed
		self.world_gravity = world_gravity
		self.max_jump_height = max_jump_height
		self.pixels_per_meter = pixels_per_meter

	def get_step_period(self):
		return (1.0 / self.step_frequency)

	def get_step_walk(self):
		step_period = self.get_step_period()
		return step_period * self.walk_speed	

	def get_step_world_gravity(self):
		step_period = self.get_step_period()
		step_gravity = (0, step_period * step_period * self.world_gravity)
		return step_gravity


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

def print_grid(grid, tilemap, output_filename):
	image = Image.new("RGBA", get_image_size(tilemap))
	image_draw = ImageDraw.Draw(image)

	for row_index in sorted(grid.keys()):		
		for col_index in sorted(grid[row_index].keys()):
			grid_element = grid[row_index][col_index]
			
			# print "....... " + "row " + str(row_index) + " col " + str(col_index) + " Grid ->" + str(grid_element)
			if (grid_element.element_type == "navpoint"):
				print " ....... " + "row " + str(row_index) + " col " + str(col_index) + " links" + str(grid_element.links)
			grid_element.draw(image_draw, (row_index, col_index), tilemap.tile_size)

	image.save(output_filename, 'PNG', transparency=0)

def get_image_size(tilemap):
	image_width = tilemap.size[0] * tilemap.tile_size[0]
	image_height = tilemap.size[1] * tilemap.tile_size[1]
	return (image_width, image_height)


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

def add_horizontal_navpoint_links(grid, tilemap, walk_speed):
	for row_index in sorted(grid.keys()):
		last_element = None
		# for col_index in sorted(grid[row_index].keys()):
		for col_index in range(tilemap.size[0]):
			next_is_blank = not((row_index in grid) and (col_index in grid[row_index]))
			next_is_navpoint = not(next_is_blank) and (grid[row_index][col_index].element_type == "navpoint")
			next_below_is_platform = ((row_index + 1) <= tilemap.size[0]) and ((row_index + 1) in grid) and (col_index in grid[row_index + 1]) and (grid[row_index + 1][col_index].element_type == "platform")
			blank_but_walkable = next_is_blank and next_below_is_platform

			#grid_element = grid[row_index][col_index]
			#if (grid_element.element_type == "navpoint"):
			if next_is_navpoint:
				grid_element = grid[row_index][col_index]
				if (last_element != None):
					last_element.add_link(grid_element, "walk", walk_speed, 0)
					grid_element.add_link(last_element, "walk", -walk_speed, 0)
					last_element = grid_element
				else:
					last_element = grid_element
			elif not(blank_but_walkable):
				last_element = None

def get_obstacle_height_m(bottom_position_row, obstacle_position_row, tilemap, jump_calculation_data):
	obstacle_height_tiles = (bottom_position_row - obstacle_position_row)
	obstacle_height_px = obstacle_height_tiles * tilemap.tile_size[1]
	obstacle_height_m = obstacle_height_px / jump_calculation_data.pixels_per_meter
	print "... obs height m " + str(obstacle_height_m) + " ... obs height tiles " + str(obstacle_height_tiles) + " ... obs height px " + str(obstacle_height_px)
	return obstacle_height_m

def add_vertical_link_walk_up(grid, source_navpoint_position, tilemap, jump_calculation_data):
	neighbor_col_index = source_navpoint_position[1] + 1
	if (source_navpoint_position[0] - 1 >= 0):
		for row_index in range(source_navpoint_position[0] - 1, -1, -1):
			right_up_blank = not((row_index in grid) and (neighbor_col_index in grid[row_index]))
			right_up_navpoint = not(right_up_blank) and (grid[row_index][neighbor_col_index].element_type == "navpoint")	
			up_platform = (row_index in grid) and (source_navpoint_position[1] in grid[row_index]) and (grid[row_index][source_navpoint_position[1]].element_type == "platform")

			if up_platform:
				break # check my own column, if there is a platform, maybe I can't jump
			elif right_up_navpoint:	
				# obstacle_height_tiles = (source_navpoint_position[0] - row_index)
				# obstacle_height_px = obstacle_height_tiles * tilemap.tile_size[1]
				# obstacle_height = obstacle_height_px / jump_calculation_data.pixels_per_meter

				obstacle_height_m = get_obstacle_height_m(source_navpoint_position[0], row_index, tilemap, jump_calculation_data)
				jump_falling_height = get_jump_and_falling_height_for_obstacle(obstacle_height_m, jump_calculation_data.character_height, jump_calculation_data.extra_jump_percent)			
				print "####### jump falling height " + str(jump_falling_height[0])
				if (jump_falling_height[0] <= jump_calculation_data.max_jump_height):
				# if ((source_navpoint_position[0] - row_index) <= jump_calculation_data.max_jump_height):
					#jump link
					grid[source_navpoint_position[0]][source_navpoint_position[1]].add_link(grid[row_index][neighbor_col_index], "jump", 0, 3)
				grid[row_index][neighbor_col_index].add_link(grid[source_navpoint_position[0]][source_navpoint_position[1]], "fall", jump_calculation_data.walk_speed, 0)
			
					
def add_vertical_link_walk_down(grid, source_navpoint_position, tilemap, jump_calculation_data):
	neighbor_col_index = source_navpoint_position[1] + 1
	if (source_navpoint_position[0] + 1 <= tilemap.size[1]):
		for row_index in range(source_navpoint_position[0] + 1, tilemap.size[1]):
			right_down_blank = not((row_index in grid) and (neighbor_col_index in grid[row_index]))
			right_down_navpoint = not(right_down_blank) and (grid[row_index][neighbor_col_index].element_type == "navpoint")	
			right_down_platform = not(right_down_blank) and (grid[row_index][neighbor_col_index].element_type == "platform")

			if right_down_platform:
				break # check my own column, if there is a platform, maybe I can't jump
			elif right_down_navpoint:				
				if ((row_index - source_navpoint_position[0]) <= jump_calculation_data.max_jump_height):
					grid[row_index][neighbor_col_index].add_link(grid[source_navpoint_position[0]][source_navpoint_position[1]], "jump", 0, 3)
				grid[source_navpoint_position[0]][source_navpoint_position[1]].add_link(grid[row_index][neighbor_col_index], "fall", jump_calculation_data.walk_speed, 0)	

def add_vertical_link_to_neighbors(grid, source_navpoint_position, tilemap, jump_calculation_data):
	add_vertical_link_walk_up(grid, source_navpoint_position, tilemap, jump_calculation_data)
	add_vertical_link_walk_down(grid, source_navpoint_position, tilemap, jump_calculation_data)

def add_vertical_navpoint_links(grid, tilemap, jump_calculation_data):
	for col_index in range(tilemap.size[0]):
		for row_index in range(tilemap.size[1]):
			navpoint_exists = (row_index in grid) and (col_index in grid[row_index]) and (grid[row_index][col_index].element_type == "navpoint")
			if (navpoint_exists):
				add_vertical_link_to_neighbors(grid, (row_index, col_index), tilemap, jump_calculation_data)
	
####
####              JUMP VELOCITY AND HEIGHT LOGIC
####

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


####
####              JUMP VELOCITY AND HEIGHT LOGIC
####

if len(sys.argv) < 8:
	print "Usage tmx-navmesh.py tilemap.tmx walk_speed max_jump_height step_frequency character_height extra_jump_percent pixels_per_meter outputfilename"
	quit()

input_tilemap_filename = sys.argv[1]
walk_speed = int(sys.argv[2])
max_jump_height = float(sys.argv[3])
step_frequency = int(sys.argv[4])
character_height = float(sys.argv[5])
extra_jump_percent = int(sys.argv[6])
pixels_per_meter = float(sys.argv[7])
output_filename = sys.argv[8]
world_gravity_m_s_s = -9.8

jump_calculation_data = JumpCalculationData(character_height, step_frequency, extra_jump_percent, walk_speed, world_gravity_m_s_s, max_jump_height, pixels_per_meter)

tilemap = get_tilemap(input_tilemap_filename)
print "...... tilemap size in tiles " + str(tilemap.size)


### Jump height calculation stuff

step_period = 1.0/step_frequency
step_gravity = (0, step_period * step_period * world_gravity_m_s_s) # m/s/s
step_velocity_horizontal = step_period * walk_speed	

jump_and_falling_height = get_jump_and_falling_height_for_obstacle(0.5, 1.0, 20)
jump_height= jump_and_falling_height[0]
vertical_velocity_m_s = get_vertical_velocity(jump_height, step_period, step_gravity)
step_velocity = step_period * vertical_velocity_m_s
time_to_max_height = get_max_height_time(step_gravity, step_velocity)
falling_time_til_obstacle = get_falling_time_til_obstacle(step_gravity, step_velocity, jump_and_falling_height[1])
distance_traveled_horizontally = get_distance_travelled_horizontally(step_velocity_horizontal, time_to_max_height, falling_time_til_obstacle)

### Jump height calculation stuff


grid = build_grid(tilemap)
last_navpoint_id = add_navpoints(tilemap, grid)
add_projected_navpoints(tilemap, grid, last_navpoint_id)
add_horizontal_navpoint_links(grid, tilemap, walk_speed)
# add_vertical_navpoint_links(grid, tilemap, walk_speed, max_jump_height)
add_vertical_navpoint_links(grid, tilemap, jump_calculation_data)
print_grid(grid, tilemap, output_filename)
