import sys
import tmxlib
import math
import os
from PIL import Image, ImageDraw

class Trajectory:
	
	def __init__(self, points, velocity):
		self.points = points
		self.hit_points = []
		self.velocity = velocity
		
	def check_collision_pos(self, character_pos, character_size_rows_cols, grid):
		for col_offset in range(character_size_rows_cols[1]):
			for row_offset in range(character_size_rows_cols[0]):
				cell_exists = ((character_pos[0] - row_offset) in grid) and ((character_pos[1] + col_offset) in grid[(character_pos[0] - row_offset)])
				cell_is_platform = cell_exists and (grid[(character_pos[0] - row_offset)][(character_pos[1] + col_offset)].element_type == "platform")
			
				#print "----------- Checking %s, %s. char size %s" % (str((character_pos[0] - row_offset)), str((character_pos[1] + col_offset)), str(character_size_rows_cols))
				if (cell_exists and cell_is_platform): 					
					#print "----- Collision at %s. %s, %s" % (str(character_pos[0] - row_offset), str(character_pos[1] + col_offset), str(character_size_rows_cols))
					return True
		
		return False
	
	def is_hit(self):
		return (len(self.hit_points) != 0)
		
	def check_collision(self, grid, character_size, tilesize):
		for point in self.points:			
			point_box = self.get_bounding_box(point, character_size)
			point_left = point_box[0][0]
			point_bottom = point_box[1][1]
			
			tile_col_index = int((point_left / tilesize[0]))
			character_width_cols = int(math.ceil(character_size[0] / tilesize[0]))
			
			tile_row_index = int((point_bottom / tilesize[1]))
			character_height_rows = int(math.ceil(character_size[1] / tilesize[1]))
				
			# print "----------- check collision for point %s" % str(point)
			if self.check_collision_pos((tile_row_index, tile_col_index), (character_height_rows, character_width_cols), grid):				
				# print "------ Added hit point %s" % str(point)
				self.hit_points.append(point)
					
	def get_bounding_box(self, point, character_size):
		box_left = point[0] - (character_size[0] / 2) 
		box_bottom = point[1]
		box_top = box_bottom - character_size[1] 
		box_right = box_left + character_size[0]
		box = [(box_left, box_top), (box_right, box_bottom)]
		return box
		
	def draw(self, image_draw, character_size):
		for point in self.points:
			navpoint_rect_size = character_size if (self.is_hit() and point in self.hit_points) else (10, 10)
			# print "- drawing NavPoint " + str(navpoint_rect_left) + " , " + str(navpoint_rect_top)
			box = self.get_bounding_box(point, navpoint_rect_size)
			image_draw.rectangle(box, outline="red")

class JumpCalculationData:
	
	def __init__(self, character_size, step_frequency, extra_jump_percent, walk_speed, world_gravity, max_jump_height, pixels_per_meter):
		self.character_size = character_size		
		self.step_frequency = step_frequency
		self.extra_jump_percent = extra_jump_percent
		self.walk_speed = walk_speed
		self.world_gravity = world_gravity
		self.max_jump_height = max_jump_height
		self.max_jump_horizontal_tiles = 0
		self.pixels_per_meter = pixels_per_meter
		
	def get_max_jump_height_tiles(self, tilesize):
		max_jump_height_pixels = self.max_jump_height * pixels_per_meter
		max_jump_height_tiles = int(max_jump_height_pixels / tilesize[1])
		max_jump_height_remainder_px = max_jump_height_pixels % tilesize[1]
		if (max_jump_height_remainder_px != 0):
			max_jump_height_tiles += 1				
		return max_jump_height_tiles
	
	def get_character_size_px(self):
		character_size_px = (self.character_size[0] * pixels_per_meter, self.character_size[1] * pixels_per_meter)
		return character_size_px
		        
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
		self.vertical_speed = vertical_speed
		self.horizontal_speed = horizontal_speed
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
		repr = "--> " + str(self.target_navpoint.id) + ",type: " + str(self.navtype) + ",speed x : " + str(self.horizontal_speed) + " speed y :" + str(self.vertical_speed)
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
		self.correction_px = (0, 0)
		self.links = {}
		self.navpoint_colors = { True : 'green', False : 'blue'}

	def set_position(self, position):
		self.position_tile = position
		self.is_corrected = True

	def get_position(self):
		return self.position_tile

	def get_correction(self):
		return self.correction_px

	def add_correction(self, correction_px):
		self.correction_px = correction_px
		self.is_corrected = True

	def add_link(self, target_navpoint, navtype, horizontal_speed, vertical_speed):
		if (target_navpoint.id in self.links):
			self.links[target_navpoint.id].append(NavLink(target_navpoint, navtype, horizontal_speed, vertical_speed))
		else:
			self.links[target_navpoint.id] = [NavLink(target_navpoint, navtype, horizontal_speed, vertical_speed)]

	def draw(self, image_draw, position, tile_size):
		navpoint_center_x = (position[1] * tile_size[0]) + self.get_correction()[1] + (tile_size[0] / 2)
		navpoint_center_y = (position[0] * tile_size[1]) + (tile_size[1] / 2)
		navpoint_rect_size = (20, 20)
		navpoint_rect_left = navpoint_center_x - (navpoint_rect_size[0] / 2) 
		navpoint_rect_top = navpoint_center_y - (navpoint_rect_size[1] / 2) 
		navpoint_rect_right = navpoint_rect_left + navpoint_rect_size[0]
		navpoint_rect_bottom = navpoint_rect_top + navpoint_rect_size[1]

		navpoint_color = self.navpoint_colors[self.is_corrected]
		image_draw.rectangle([(navpoint_rect_left, navpoint_rect_top), (navpoint_rect_right, navpoint_rect_bottom)], outline="blue", fill=navpoint_color)

		id_text_size = image_draw.textsize(str(self.id))
		text_left = navpoint_center_x - (id_text_size[0] / 2)
		text_top = navpoint_center_y - (id_text_size[1] / 2)
		image_draw.text((text_left, text_top), str(self.id), fill="white")

		for navpoint_link_group in self.links.values():
			for navpoint_link in navpoint_link_group:
				navpoint_link.draw(image_draw, (navpoint_center_x, navpoint_center_y), tile_size)

	def __repr__(self):
		repr = "{id : " + str(self.id) + ";pos: " + str(self.position_tile) + ";links: " + str(self.links) + "}\n" 
		return repr
	
class Platform:
	
	def __init__(self, id, position):
		self.id = id
		self.position = position
		self.navpoints = []
		
	def add_navpoint(self, navpoint):
		self.navpoints.append(navpoint)

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
				
def update_tilemap_platforms(tilemap, updated_tilemap_filename):		
	objects_layer = tilemap.layers['physics']
	platform_id = 0
	for object in objects_layer.all_objects():
		object.properties['platform_id'] = str(platform_id)
		platform_id += 1
	tilemap.save(updated_tilemap_filename)

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

def print_grid(grid, tilemap, trajectories, character_size, output_filename, with_trajectories = False, with_collisions = False):
	image = Image.new("RGBA", get_image_size(tilemap))
	image_draw = ImageDraw.Draw(image)

	for row_index in sorted(grid.keys()):		
		for col_index in sorted(grid[row_index].keys()):
			grid_element = grid[row_index][col_index]
			
			# print "....... " + "row " + str(row_index) + " col " + str(col_index) + " Grid ->" + str(grid_element)
			if (grid_element.element_type == "navpoint"):
				print " ....... " + "row " + str(row_index) + " col " + str(col_index) + " links" + str(grid_element.links)
			grid_element.draw(image_draw, (row_index, col_index), tilemap.tile_size)

	if with_trajectories:
		draw_trajectories(image_draw, trajectories, character_size, with_collisions)
	
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
	## CODE DUPLICATION
	projection = None
	for row_index in range(neighbor_position[0], tilemap_size[1] + 1):
		# print "... checking for row index %s , %s" % (str(row_index), str(neighbor_position))
		cell_exists = (row_index in grid) and (neighbor_position[1] in grid[row_index])
		cell_is_platform = cell_exists and (grid[row_index][neighbor_position[1]].element_type == "platform")

		one_up_row_index = row_index - 1
		one_up_not_exists = (one_up_row_index > 0) and not((one_up_row_index in grid) and (neighbor_position[1] in grid[one_up_row_index]) and (grid[one_up_row_index][neighbor_position[1]].element_type != "navpoint"))

		# print "...finding proj nr:" + str(neighbor_position[0]) + ",nc:" + str(neighbor_position[1]) + " cip " + str(cell_is_platform) + " oneuprow " + str(one_up_not_exists) + ".. one_up_rindex " + str(one_up_row_index)
		if (cell_is_platform and one_up_not_exists):
			projection = (one_up_row_index, neighbor_position[1])
			break

	return projection

def find_projection_for_jump(grid, neighbor_position, max_jump_height, tilemap_size):
	projection = None
	for row_index in range(neighbor_position[0], min(tilemap_size[1] + 1, neighbor_position[0] + max_jump_height + 1)):
		# print "... checking for row index %s , %s" % (str(row_index), str(neighbor_position))
		cell_exists = (row_index in grid) and (neighbor_position[1] in grid[row_index])
		cell_is_platform = cell_exists and (grid[row_index][neighbor_position[1]].element_type == "platform")

		one_up_row_index = row_index - 1
		one_up_not_exists = (one_up_row_index > 0) and not((one_up_row_index in grid) and (neighbor_position[1] in grid[one_up_row_index]) and (grid[one_up_row_index][neighbor_position[1]].element_type != "navpoint"))

		# print "...finding proj nr:" + str(neighbor_position[0]) + ",nc:" + str(neighbor_position[1]) + " cip " + str(cell_is_platform) + " oneuprow " + str(one_up_not_exists) + ".. one_up_rindex " + str(one_up_row_index)
		if (cell_is_platform and one_up_not_exists):
			projection = (one_up_row_index, neighbor_position[1])
			break

	return projection

def get_horizontal_velocity(source_position, target_position, travel_time, tilesize, pixels_per_meter):
	distance = (target_position[1] - source_position[1]) * tilesize[0] / pixels_per_meter
	horizontal_velocity = distance / travel_time
	return horizontal_velocity

def build_trajectory(grid, source_position, target_position, tilemap, jump_calculation_data):
	obstacle_height_m = get_obstacle_height_m(source_position[0], target_position[0], tilemap, jump_calculation_data)

	# Added 0 as character height, because whatever trajectory we come up with, its height will be independent from the character
	# height. The trajectory will be applied to the character, whatever its size, starting at its bottom. This means that the 
	# distance up it will need to reach, will just be that of the obstacle.
	jump_falling_height = get_jump_and_falling_height_for_obstacle(obstacle_height_m, 0, jump_calculation_data.extra_jump_percent)
	jump_velocity = get_vertical_velocity(jump_falling_height[0], jump_calculation_data.get_step_period(), jump_calculation_data.get_step_world_gravity())
	step_jump_velocity = jump_calculation_data.get_step_period() * jump_velocity
	max_height_time = get_max_height_time(jump_calculation_data.get_step_world_gravity(), step_jump_velocity)
	
	# We get the time it takes to reach the obstacle height at the estalished velocity. Solving the second grade equations, we will take 
	# the biggest of the solutions. This will mean the longest time, which is the solution for the way down. We use obstacle_height, because
	# it will give us the time it takes the character to reach the obstacle height both on the way up, and down. Notice that the obstacle
	# height on the way down, equals the total_height - extra_percentage. Extra_percentage is the distance the character will travel on the way
	# down, but the distance measured from the floor, will still be obstacle_height
	total_falling_time = get_falling_time_til_obstacle(jump_calculation_data.get_step_world_gravity(), step_jump_velocity, obstacle_height_m)
	total_time = int(math.ceil(total_falling_time)) 
	# print " ..... total time %s, v %s, %s, falling_time %s, jump_falling_height %s" % (str(total_time), str(jump_velocity), str(max_height_time), str(total_falling_time), str(jump_falling_height))

	step_n_width = 0
	step_n_height = 0
	step_horizontal_velocity = get_horizontal_velocity(source_position, target_position, total_time, tilemap.tile_size, jump_calculation_data.pixels_per_meter)
	#navpoint_position_n_px = (((source_position[1]  + 0.5) * tilemap.tile_size[0]) - step_n_width, ((source_position[0] + 0.5) * tilemap.tile_size[1]) - step_n_height)
	navpoint_position_n_px = (((source_position[1] + 0.5) * tilemap.tile_size[0]) + step_n_width, ((source_position[0] + 1) * tilemap.tile_size[1]) - 1 - step_n_height )	
	trajectory_points = [navpoint_position_n_px]
	
	#print "########  source position %s, target position %s, step_n_width %s, trajectory_pos %s" % (str(source_position), str(target_position), str(step_n_width), str(navpoint_position_n_px))	
	for n in range(total_time):
		step_n_height = step_jump_velocity * n + ((n * n) + n) * jump_calculation_data.get_step_world_gravity()[1] / 2
		step_n_width = (n * step_horizontal_velocity)
		step_n_height_px = step_n_height * jump_calculation_data.pixels_per_meter
		step_n_width_px = step_n_width * jump_calculation_data.pixels_per_meter		
		navpoint_position_n_px = (((source_position[1] + 0.5) * tilemap.tile_size[0]) + step_n_width_px, ((source_position[0] + 1) * tilemap.tile_size[1]) - 1 - step_n_height_px)
		# print "########  source position %s, target position %s, step_n_width %s, trajectory_pos %s" % (str(source_position), str(target_position), str(step_n_width), str(navpoint_position_n_px))
		trajectory_points.append(navpoint_position_n_px)
	
	trajectory = Trajectory(trajectory_points, (step_horizontal_velocity * jump_calculation_data.step_frequency, jump_velocity))
	return trajectory

def find_jump_candidates(grid, source_position, tilemap, jump_calculation_data, left_candidates):
	projections_found = []
	candidate_sign = -1 if left_candidates else 1
	for horizontal_distance in range(1, jump_calculation_data.max_jump_horizontal_tiles):
		horizontal_nth_neighbor_col_index = source_position[1] + (candidate_sign * horizontal_distance)
				
		projection_found = find_projection_for_jump(grid, (source_position[0], horizontal_nth_neighbor_col_index + (candidate_sign * 1)), jump_calculation_data.get_max_jump_height_tiles(tilemap.tile_size), tilemap.size)
		if (projection_found != None):
				projections_found.append(projection_found)
				
	return projections_found
	
def add_projected_jump_navpoints(tilemap, grid, first_navpoint_id, jump_calculation_data):
	navpoint_id = first_navpoint_id
	candidate_trajectories = []
	for col_index in range(tilemap.size[0]):
		left_projection_added = False
		right_projection_added = False
		for row_index in range(tilemap.size[1]):
			cell_exists = (row_index in grid) and (col_index in grid[row_index])
			cell_is_platform = cell_exists and (grid[row_index][col_index].element_type == "platform")
		
			if (cell_is_platform) and (should_have_left_projection(grid, (row_index, col_index), tilemap.size)):
				projection_found = find_jump_candidates(grid, (row_index, col_index), tilemap, jump_calculation_data, True)
				# print " should have left r:" + str(row_index) + ", c:" + str(col_index) + ",p:" + str(projection_found)
				for projection_candidate in projection_found:					
						navpoint_candidate = NavPoint(navpoint_id, projection_candidate)
						candidate_trajectory = build_trajectory(grid, projection_candidate, (row_index - 1, col_index), tilemap, jump_calculation_data)
						candidate_trajectory.check_collision(grid, jump_calculation_data.get_character_size_px(), tilemap.tile_size)
						candidate_trajectories.append(candidate_trajectory)						
						
						if not(candidate_trajectory.is_hit()):
							navpoint_candidate.is_corrected = True
							if not((projection_candidate[0] in grid) and (projection_candidate[1] in grid[projection_candidate[0]]) and (grid[projection_candidate[0]][projection_candidate[1]].element_type == "navpoint")):
								grid[projection_candidate[0]][projection_candidate[1]] = navpoint_candidate
								navpoint_id +=1
							grid[projection_candidate[0]][projection_candidate[1]].add_link(grid[row_index - 1][col_index], "jump", candidate_trajectory.velocity[0], candidate_trajectory.velocity[1])
						left_projection_added = True

			if (cell_is_platform) and (should_have_right_projection(grid, (row_index, col_index), tilemap.size)):	
				projection_found = find_jump_candidates(grid, (row_index, col_index), tilemap, jump_calculation_data, False)
				# print " should have right r:" + str(row_index) + ", c:" + str(col_index) + ",p:" + str(projection_found)				
				for projection_candidate in projection_found:					
						navpoint_candidate = NavPoint(navpoint_id, projection_candidate)
						candidate_trajectory = build_trajectory(grid, projection_candidate, (row_index - 1, col_index), tilemap, jump_calculation_data)
						candidate_trajectory.check_collision(grid, jump_calculation_data.get_character_size_px(), tilemap.tile_size)
						candidate_trajectories.append(candidate_trajectory)
						
						if not(candidate_trajectory.is_hit()):
							navpoint_candidate.is_corrected = True
							if not((projection_candidate[0] in grid) and (projection_candidate[1] in grid[projection_candidate[0]]) and (grid[projection_candidate[0]][projection_candidate[1]].element_type == "navpoint")):
								grid[projection_candidate[0]][projection_candidate[1]] = navpoint_candidate
								navpoint_id +=1
							grid[projection_candidate[0]][projection_candidate[1]].add_link(grid[row_index - 1][col_index], "jump", candidate_trajectory.velocity[0], candidate_trajectory.velocity[1])							
						right_projection_added = True

			if (left_projection_added and right_projection_added):
				break

	return (navpoint_id, candidate_trajectories)


def add_projected_fall_navpoints(tilemap, grid, first_navpoint_id, jump_calculation_data):
	navpoint_id = first_navpoint_id
	for col_index in range(tilemap.size[0]):
		left_projection_added = False
		right_projection_added = False
		for row_index in range(tilemap.size[1]):
			cell_exists = (row_index in grid) and (col_index in grid[row_index])
			cell_is_platform = cell_exists and (grid[row_index][col_index].element_type == "platform")
		
			if (cell_is_platform) and (should_have_left_projection(grid, (row_index, col_index), tilemap.size)):				
				# print " should have left r:" + str(row_index) + ", c:" + str(col_index) + ",p:" + str(projection_found)
				projection_candidate = find_projection(grid, (row_index, col_index - 1), tilemap.size)				
				projection_is_navpoint = (projection_candidate != None) and (projection_candidate[0] in grid) and (projection_candidate[1] in grid[projection_candidate[0]]) and (grid[projection_candidate[0]][projection_candidate[1]].element_type == "navpoint")
				projection_is_blank = (projection_candidate != None) and not(projection_is_navpoint)
				one_up_navpoint = ((row_index - 1) in grid) and (col_index in grid[row_index - 1]) and (grid[row_index - 1][col_index].element_type == "navpoint") and ((row_index - 1) >= 0) 
				
				if one_up_navpoint and projection_is_navpoint:
					grid[row_index - 1][col_index].add_link(grid[projection_candidate[0]][projection_candidate[1]], "fall", -jump_calculation_data.walk_speed, 0)	
				elif one_up_navpoint and projection_is_blank:
					navpoint_candidate = NavPoint(navpoint_id, projection_candidate)
					grid[projection_candidate[0]][projection_candidate[1]] = navpoint_candidate
					navpoint_id +=1
					grid[row_index - 1][col_index].add_link(grid[projection_candidate[0]][projection_candidate[1]], "fall", -jump_calculation_data.walk_speed, 0)
					left_projection_added = True
									
			if (cell_is_platform) and (should_have_right_projection(grid, (row_index, col_index), tilemap.size)):	
				projection_candidate = find_projection(grid, (row_index, col_index + 1), tilemap.size)				
				projection_is_navpoint = (projection_candidate != None) and (projection_candidate[0] in grid) and (projection_candidate[1] in grid[projection_candidate[0]]) and (grid[projection_candidate[0]][projection_candidate[1]].element_type == "navpoint")
				projection_is_blank = (projection_candidate != None) and not(projection_is_navpoint)
				one_up_navpoint = ((row_index - 1) in grid) and (col_index in grid[row_index - 1]) and (grid[row_index - 1][col_index].element_type == "navpoint") and ((row_index - 1) >= 0) 
				
				if one_up_navpoint and projection_is_navpoint:
					grid[row_index - 1][col_index].add_link(grid[projection_candidate[0]][projection_candidate[1]], "fall", jump_calculation_data.walk_speed, 0)	
				elif one_up_navpoint and projection_is_blank:
					navpoint_candidate = NavPoint(navpoint_id, projection_candidate)
					grid[projection_candidate[0]][projection_candidate[1]] = navpoint_candidate
					navpoint_id += 1
					grid[row_index - 1][col_index].add_link(grid[projection_candidate[0]][projection_candidate[1]], "fall", jump_calculation_data.walk_speed, 0)
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

		for col_index in range(tilemap.size[0]):
			next_is_blank = not((row_index in grid) and (col_index in grid[row_index]))
			next_is_navpoint = not(next_is_blank) and (grid[row_index][col_index].element_type == "navpoint")
			next_below_is_platform = ((row_index + 1) <= tilemap.size[0]) and ((row_index + 1) in grid) and (col_index in grid[row_index + 1]) and (grid[row_index + 1][col_index].element_type == "platform")
			blank_but_walkable = next_is_blank and next_below_is_platform

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
								
def draw_trajectories(image_draw, trajectories, character_size, draw_collisions=True):
		for trajectory in trajectories:
			if (trajectory.is_hit() and draw_collisions):
					trajectory.draw(image_draw, character_size)
			elif not(trajectory.is_hit()):
				trajectory.draw(image_draw, character_size)
	
####
####              JUMP VELOCITY AND HEIGHT LOGIC
####

def get_vertical_velocity(desired_height, step_period, step_gravity):
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

	print "================== qs1 %s, qs2 %s" % (str(quadratic_solution1), str(quadratic_solution2))
	solution = max(quadratic_solution1, quadratic_solution2)

	return solution

def get_distance_travelled_horizontally(step_velocity_horizontal, raising_time, falling_time):
	total_time = raising_time + falling_time
	distance_traveled_horizontally = step_velocity_horizontal * total_time

	return distance_traveled_horizontally

def get_maximum_distance_horizontal(max_jump_height, step_period, step_walk_speed, step_world_gravity):
 	velocity_to_maximum_height = get_vertical_velocity(max_jump_height, step_period, step_world_gravity)
	step_velocity = step_period * velocity_to_maximum_height
	time_to_maximum_height = get_max_height_time(step_world_gravity, step_velocity)
	maximum_horizontal_distance = step_walk_speed * time_to_maximum_height
	
	return maximum_horizontal_distance

def get_maximum_tiles_horizontal(max_jump_height, step_period, step_walk_speed, step_world_gravity, tilesize, pixels_per_meter):
    maximum_horizontal_distance = get_maximum_distance_horizontal(max_jump_height, step_period, step_walk_speed, step_world_gravity)
    maximum_full_tiles = int(maximum_horizontal_distance * pixels_per_meter / tilesize[0])
    total_tiles = maximum_full_tiles
    partial_tile_pixels = maximum_horizontal_distance * pixels_per_meter % tilesize[0]
   
    if (partial_tile_pixels != 0):
        total_tiles += 1
    
    return total_tiles

####
####              JUMP VELOCITY AND HEIGHT LOGIC
####



####              MAIN
####              sample line : python tmx-nav.py navmesh/background4.tmx 3 2 60 1 20 108 output.png

if len(sys.argv) < 9:
	print "Usage tmx-navmesh.py tilemap.tmx walk_speed max_jump_height step_frequency character_width character_height extra_jump_percent pixels_per_meter outputfilename"
	quit()

input_tilemap_filename = sys.argv[1]
walk_speed = int(sys.argv[2])
max_jump_height = float(sys.argv[3])
step_frequency = int(sys.argv[4])
character_size = (float(sys.argv[5]), float(sys.argv[6]))
extra_jump_percent = int(sys.argv[7])
pixels_per_meter = float(sys.argv[8])
output_bitmap_filename = sys.argv[9]
output_updated_tilemap = sys.argv[10]
world_gravity_m_s_s = -9.8

tilemap = get_tilemap(input_tilemap_filename)
print "...... tilemap size in tiles " + str(tilemap.size)
                                                       
jump_calculation_data = JumpCalculationData(character_size, step_frequency, extra_jump_percent, walk_speed, world_gravity_m_s_s, max_jump_height, pixels_per_meter)

jump_calculation_data.max_jump_horizontal_tiles = get_maximum_tiles_horizontal(max_jump_height, jump_calculation_data.get_step_period(), jump_calculation_data.get_step_walk(), jump_calculation_data.get_step_world_gravity(), tilemap.tile_size, jump_calculation_data.pixels_per_meter)

grid = build_grid(tilemap)

update_tilemap_platforms(tilemap, output_updated_tilemap)

last_navpoint_id = add_navpoints(tilemap, grid)
last_navpoint_id_trajectories = add_projected_jump_navpoints(tilemap, grid, last_navpoint_id, jump_calculation_data)
last_navpoint_id_fall_paths = add_projected_fall_navpoints(tilemap, grid, last_navpoint_id_trajectories[0], jump_calculation_data)
add_horizontal_navpoint_links(grid, tilemap, walk_speed)

#add_projected_navpoints(tilemap, grid, last_navpoint_id)
#add_horizontal_navpoint_links(grid, tilemap, walk_speed)
#add_vertical_navpoint_links(grid, tilemap, jump_calculation_data)
#print_grid(grid, tilemap, output_filename)
character_size_px = (character_size[0] * pixels_per_meter, character_size[1] * pixels_per_meter)
print_grid(grid, tilemap, last_navpoint_id_trajectories[1], character_size_px, output_bitmap_filename, with_trajectories=True)
