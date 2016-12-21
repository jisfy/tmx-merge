import sys
import tmxlib
import math
import os
from PIL import Image, ImageChops


def get_cropped_tile_image_from_image(image, tile_size, top_left, top_left_offset=(0,0)):
	boxLeft = top_left[0] + top_left_offset[0]
	boxTop = top_left[1] + top_left_offset[1]
	boxRight = top_left[0] + top_left_offset[0] + tile_size[0]
	boxBottom = top_left[1] + top_left_offset[1] + tile_size[1]

	tileBox = (boxLeft, boxTop, boxRight, boxBottom)
	croppedTile = image.crop(tileBox)

	#print "==== " + str(tile.number) + ", "  + str(tileBox) 
	return croppedTile


def get_cropped_tile_image_from_tile(tile, tile_size, top_left_offset=(0,0)):
	tileImage = Image.open(tile.image.image.source)
	return get_cropped_tile_image_from_image(tileImage, tile_size, tile.image.top_left, top_left_offset)

''' 
   This will return a tuple with the number of tiles cropped, a map holding the correspondence of tile ids from the given tileset that are the same, 
   and finally a list of tile ids that are blank in the given tileset. 
'''
def shrink_and_crop(tileset):
        tilesAlreadyCropped = []
        blank_tile_numbers = []
        tile_mapping_content_2_tile_number  = {}
        shrunk_tile_number_mapping = {} 

	for tile in tileset:
		tile_id = tile.number + 1
          #      print "_________- tile size in shrink_and_crop " + str(tileset.tile_size)
		croppedTile = get_cropped_tile_image_from_tile(tile, tileset.tile_size)

		# only save the tile if it is not blank
		if croppedTile.getbbox() :

			# only save the tile if it is not a duplicate of an already processed one 
			convertedCroppedTileString = croppedTile.convert('L').tostring()
                        if not convertedCroppedTileString in tilesAlreadyCropped:
                                tilesAlreadyCropped.append(convertedCroppedTileString)
				tile_mapping_content_2_tile_number[convertedCroppedTileString] = tile_id
			else:
				shrunk_tile_number_mapping[tile_id] = tile_mapping_content_2_tile_number[convertedCroppedTileString]
				#print "duplicate tile, skipping " + str(tile_id) 
                else:
			blank_tile_numbers.append(tile_id)
			#print "skipping tile " + str(tile_id)

	print ".... Total different tiles cropped " + str(len(tilesAlreadyCropped))
	print ".... shrunk_tile_number_mapping " + str(shrunk_tile_number_mapping)
	print ".... blank_tile_numbers " + str(blank_tile_numbers)

	return (len(tilesAlreadyCropped), shrunk_tile_number_mapping, blank_tile_numbers)

def get_texture_size_for_tileset(number_of_tiles, tile_size, tile_padding):
        tile_size_with_padding = (tile_size[0] + (tile_padding[0] * 2), tile_size[1] + (tile_padding[1] * 2))
        total_pixels_for_tiles_with_padding = number_of_tiles * tile_size_with_padding[0] * tile_size_with_padding[1]
        total_pixels_for_tiles_square = int(math.ceil(math.sqrt(total_pixels_for_tiles_with_padding)))
        # assuming tiles are square and not rectangular, so we divide by the tile_size_with_padding width
        total_pixels_for_tiles_square_corrected = int(math.ceil(total_pixels_for_tiles_square / tile_size_with_padding[0])) * tile_size_with_padding[0]
        print " -------- corrected thing  " + str(total_pixels_for_tiles_square_corrected)
	closest_pow_width = math.pow(2, int(math.ceil(math.log(total_pixels_for_tiles_square_corrected, 2))))
        number_of_tiles_per_row = int(math.floor(closest_pow_width / tile_size_with_padding[0]))
#        print " number of tiles per row " + str(tile_size_with_padding)
        number_of_rows_needed = int(math.ceil(number_of_tiles / number_of_tiles_per_row))
        closest_pow_height = math.pow(2, int(math.ceil(math.log(number_of_rows_needed * tile_size_with_padding[1], 2))))
        texture_size_pixels = (int(closest_pow_width), int(closest_pow_height))
        texture_size_tiles = (number_of_tiles_per_row, number_of_rows_needed)
	return (texture_size_tiles, texture_size_pixels)

def reduce_tilesets(tilesets, target_tilemap_path, shrink_results, target_tileset_texture_size, tile_padding):
	tileset = tilesets[0]
	tile_width = tileset.tile_size[0] + (tile_padding[0] * 2)
	tile_height = tileset.tile_size[1] + (tile_padding[1] * 2)

        print "........ tile size in px  " + str(tile_width)  + " . " + str(tile_height)

        target_tileset_size_px = target_tileset_texture_size[1] 
        target_tileset_texture_size_tiles = target_tileset_texture_size[0]
	target_tilemap_image = Image.new('RGBA', target_tileset_size_px)

	first_tile_number = 1
	reduced_tileset_mappings = []
	for tileset_shrink_result in zip(tilesets, shrink_results):
		combine_tilesets_result = combine_tilesets(tileset_shrink_result[0], target_tilemap_image, tileset_shrink_result[1][1], target_tileset_texture_size_tiles, tileset_shrink_result[1][2], tile_padding, first_tile_number)
		first_tile_number = combine_tilesets_result[0]
		reduced_tileset_mappings.append(combine_tilesets_result[1])
		
	original_tileset_image_source = 'first_things_first.png'
	target_tilemap_image.save(os.path.join(target_tilemap_path, original_tileset_image_source))
	return reduced_tileset_mappings

def add_left_gutter(tile_size, tile_padding, output_image, left_tile_stripe_width=1):
        twice_tile_vertical_padding = (2 * tile_padding[1])
        new_target_tile_height = tile_size[1] + twice_tile_vertical_padding
        cropped_size = (left_tile_stripe_width, new_target_tile_height)
        left_tile_stripe = get_cropped_tile_image_from_image(output_image, cropped_size, top_left=(tile_padding[0], 0))
	for i in range(1, tile_padding[0] + 1):
              output_image.paste(left_tile_stripe, (tile_padding[0] - (left_tile_stripe_width * i), 0))

def add_right_gutter(tile_size, tile_padding, output_image, right_tile_stripe_width=1):
        twice_tile_vertical_padding = (2 * tile_padding[1])
        new_target_tile_height = tile_size[1] + twice_tile_vertical_padding
        cropped_size = (right_tile_stripe_width, new_target_tile_height)        
        top_left = (tile_size[0] + tile_padding[0] - right_tile_stripe_width, 0)
        right_tile_stripe = get_cropped_tile_image_from_image(output_image, cropped_size, top_left)
	for i in range(0, tile_padding[0]):
              output_image.paste(right_tile_stripe, (tile_size[0] + tile_padding[0] + i, 0))

def add_top_gutter(source_tile, tile_size, tile_padding, output_image, top_tile_stripe_height=1):
	top_tile_stripe = get_cropped_tile_image_from_tile(source_tile, (tile_size[0], top_tile_stripe_height))
        for i in range(1, tile_padding[1] + 1):
              output_image.paste(top_tile_stripe, (tile_padding[0], tile_padding[1] - (top_tile_stripe_height * i)))

def add_bottom_gutter(source_tile, tile_size, tile_padding, output_image, bottom_tile_stripe_height=1):
	bottom_tile_stripe = get_cropped_tile_image_from_tile(source_tile, (tile_size[0], bottom_tile_stripe_height), top_left_offset=(0, tile_size[1] - bottom_tile_stripe_height))
        for i in range(0, tile_padding[1]):
              output_image.paste(bottom_tile_stripe, (tile_padding[0], tile_size[1] + tile_padding[1] + i))

def add_gutter(source_tile, tile_size, tile_padding, output_image):
        cropped_tile_image = get_cropped_tile_image_from_tile(source_tile, tile_size)
	output_image.paste(cropped_tile_image, (tile_padding[0], tile_padding[1]))

        add_top_gutter(source_tile, tileset.tile_size, tile_padding, output_image)
        add_bottom_gutter(source_tile, tileset.tile_size, tile_padding, output_image)

        add_left_gutter(tileset.tile_size, tile_padding, output_image)
        add_right_gutter(tileset.tile_size, tile_padding, output_image)

'''
   This method combines several tileset images into a single one. The resulting tileset image is given by target_tilemap_image. 
   In order to combine several tilesets into one, the method tracks the first tile id that can be assigned to a the tiles coming from
   a new tileset in the parameter first_tile_number. 
   reduced_tile_mapping is a map holding the tiles in the given tileset which are duplicated, or the same.
   The method returns a pair with the first tile number a subsequent call could use. This is, the last tile id that was used by the 
   current method call for the target tileset. The second element of the pair is a map, containing which tiles or better tile_ids, from the
   given tileset match which from the target or destination tileset. Thus providing us with a way to math old tileset tile_id's with those
   of the new tileset
'''
def combine_tilesets(tileset, target_tilemap_image, reduced_tile_mapping, target_tileset_texture_size, blank_tile_numbers, tile_padding, first_tile_number):        
	target_tile_number = first_tile_number

        tile_horizontal_spacing = tile_padding[0]
        tile_vertical_spacing = tile_padding[1]
	tile_width = tileset.tile_size[0] 
	tile_height = tileset.tile_size[1] 

	reduced_tileset_mapping = {}

	tiles_processed = []
	tiles_really_reduced = []

        padded_target_tile_size = (tile_width + (2 * tile_padding[0]), tile_height + (2 * tile_padding[1]))  
	padded_target_tile = Image.new('RGBA', padded_target_tile_size)

	#print "..... reduced stuff " + str(reduced_tile_mapping)
	for tile in tileset:
		tile_id = tile.number + 1
		if not (tile_id in blank_tile_numbers):
			#print ",,,,,,,,,,,,,,,,,,, tile number " + str(target_tile_number)

                        reduced_tile_id = tile_id - 1
			if tile_id in reduced_tile_mapping:
				tiles_really_reduced.append(tile_id)
				reduced_tile_id = reduced_tile_mapping[tile_id]

				print "reduced tile already seen " + str(reduced_tile_id)
				reduced_tileset_mapping[tile_id] = reduced_tileset_mapping[reduced_tile_id]
			else:
				# print "non reduced tile " + str(reduced_tile_id) 
				reduced_tile = tileset[reduced_tile_id]
			
				cropped_tile_image = get_cropped_tile_image_from_tile(reduced_tile, tileset.tile_size)
				### just here for debugging purposes
                                # cropped_tile_image.save('output2/tt_' + str(tile_id) + ".png")

				box_left = (((target_tile_number - 1) % target_tileset_texture_size[0]) * (tile_width + (2 * tile_horizontal_spacing)))
                                box_top = (((target_tile_number - 1) / target_tileset_texture_size[0]) * (tile_height + (2 * tile_vertical_spacing))) 

				paste_box = (box_left, box_top)
                                add_gutter(reduced_tile, tileset.tile_size, tile_padding, padded_target_tile)
				padded_target_tile.save('output2/tt_aug_' + str(tile_id) + ".png")

				#  print "............. " + str(tile_id) + " , " + str(paste_box)
				print "............. " + str(target_tile_number) + " , " + str(paste_box)
	
				target_tilemap_image.paste(padded_target_tile, paste_box)
				reduced_tileset_mapping[tile_id] = target_tile_number
			
				target_tile_number += 1
			
			tiles_processed.append(tile_id)

	print "...................................." + str(tiles_processed)
	print "...................................." + str(len(tiles_processed))
	print "......................really reduced ........." + str(tiles_really_reduced)
	print "......................really reduced ........." + str(len(tiles_really_reduced))

	print "...................................." + str(reduced_tileset_mapping)
	return (target_tile_number, reduced_tileset_mapping)

'''
  Converts the given source_layer, which uses its own tileset, into a new layer which uses
  the new one. The mapping from the old tileset ids to the new one is given by the parameter
  reduced_tileset_mapping.
'''
def update_tilemap_layer(layer, source_layer, reduced_tileset_mapping):
	print '========== updating layer ' + layer.name
	for tile in source_layer.all_tiles():
		value = tile.gid

		if (value != 0) and (value in reduced_tileset_mapping):
			layer.set_value_at(tile.pos, reduced_tileset_mapping[value])
		else:
			layer.set_value_at(tile.pos, 0) # deleting?, setting to blank

def get_map_size(tilemaps):
	max_tilemap_height = 0
	max_tilemap_width = 0
	for tilemap in tilemaps:
		max_tilemap_height = max(max_tilemap_height, tilemap.size[0])
		max_tilemap_width = max(max_tilemap_width, tilemap.size[1])

	return (max_tilemap_height, max_tilemap_width)

def get_tile_size(tilemaps):
	max_tile_height = 0
	max_tile_width = 0
	for tilemap in tilemaps:
		max_tile_height = max(max_tile_height, tilemap.tile_size[0])
		max_tile_width = max(max_tile_width, tilemap.tile_size[1])

	return (max_tile_height, max_tile_width)

'''
  Creates a new tilemap, combining, or merging those given by the tilemaps parameter, and using the
  the tileset. The mapping of the old tileset ids, which are used by the different tilemaps in the 
  tilemaps paremeter, to the new tile ids, is provided by reduced_tileset_mappings.
'''
def update_tilemaps(tilemaps, target_tilemap_filename, reduced_tileset_mappings, tile_size, tile_padding, target_tileset_size_px):       
	tilemap_to_save = tmxlib.map.Map(size = get_map_size(tilemaps), tile_size=tile_size)
	tilemap_to_save.tilesets = tmxlib.tileset.TilesetList(tilemap_to_save)

	tilemap_image = tmxlib.image_base.Image(source = 'first_things_first.png', size = target_tileset_size_px)
	tilemap_to_save.tilesets.insert(0, tmxlib.tileset.ImageTileset('sometileset', tile_size, tilemap_image, margin=tile_padding[0], spacing=(tile_padding[0] * 2)))
	
	for tilemap_reduced_tileset_mapping in zip(tilemaps, reduced_tileset_mappings):
		tilemap_to_update = tilemap_reduced_tileset_mapping[0]
		source_layer = tilemap_to_update.layers[0]
		source_layer_name = source_layer.name + "_up"
		tilemap_to_save.add_tile_layer(source_layer_name)
		layer_to_update = tilemap_to_save.layers[source_layer_name]
		reduced_tileset_mapping = tilemap_reduced_tileset_mapping[1]

		update_tilemap_layer(layer_to_update, source_layer, reduced_tileset_mapping)

	tilemap_to_save.save(target_tilemap_filename)

def get_target_tilemap_filename(tilemap_path, target_tilemap_path):
	target_tilemap_filename = os.path.join(target_tilemap_path, os.path.basename(tilemap_path))
	return target_tilemap_filename

def get_tilemap(tilemap_path):
        tilemap = tmxlib.Map.open(tilemap_path)
	return tilemap

def get_tileset(tilemap):        
	tileset = tilemap.tilesets[0]
	return tileset

def print_tilemap(tilemap):
	layer = tilemap.layers[0]
	tileset = tilemap.tilesets[0]
	for tile in layer.all_tiles():
		print " ... " + str(tile.gid) + " , " + str(tile.pos)

if len(sys.argv) < 2:
	print "Usage tmx-merge.py tilemap.tmx [tilemap.tmx] outputdir"
	quit()

input_tilemap_filenames = sys.argv[1:-1]
output_folder = sys.argv[-1]

tilemaps = []
tilesets = []
shrink_results = []
tile_padding = (4, 4)

total_number_unique_tiles_in_all_tilemaps = 0

for input_tilemap_filename in input_tilemap_filenames:
	print "tilemap filename " + input_tilemap_filename

	tilemap = get_tilemap(input_tilemap_filename)
	tilemaps.append(tilemap)

	tileset = get_tileset(tilemap)
	tilesets.append(tileset)

	shrink_result = shrink_and_crop(tileset)
	shrink_results.append(shrink_result)
	total_number_unique_tiles_in_all_tilemaps += shrink_result[0] 
	
print "----- total number unique tiles in all tilemaps " + str(total_number_unique_tiles_in_all_tilemaps)
target_tileset_size = get_texture_size_for_tileset(total_number_unique_tiles_in_all_tilemaps, tilemaps[0].tile_size, tile_padding)
print "----- estimated size " + str(target_tileset_size)

reduced_tileset_mappings = reduce_tilesets(tilesets, output_folder, shrink_results, target_tileset_size, tile_padding)
print "----- reduced " + str(reduced_tileset_mappings[0])

update_tilemaps(tilemaps, get_target_tilemap_filename(input_tilemap_filename, output_folder), reduced_tileset_mappings, tilemaps[0].tile_size, tile_padding, target_tileset_size[1])

