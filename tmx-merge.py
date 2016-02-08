import sys
import tmxlib
import math
import os
from PIL import Image, ImageChops

def get_cropped_tile_image(tile, tile_size):
	tileImage = Image.open(tile.image.image.source)

	boxLeft = tile.image.top_left[0]
	boxTop = tile.image.top_left[1]
	boxRight = tile.image.top_left[0] + tile_size[0]
	boxBottom = tile.image.top_left[1] + tile_size[1]

	tileBox = (boxLeft, boxTop, boxRight, boxBottom)
	croppedTile = tileImage.crop(tileBox)

	#print "==== " + str(tile.number) + ", "  + str(tileBox) 
	return croppedTile

def shrink_and_crop(tileset):
        tilesAlreadyCropped = []
        blank_tile_numbers = []
        tile_mapping_content_2_tile_number  = {}
        shrunk_tile_number_mapping = {} 

	for tile in tileset:
		tile_id = tile.number + 1
		croppedTile = get_cropped_tile_image(tile, tileset.tile_size)

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

	return (len(tilesAlreadyCropped), shrunk_tile_number_mapping, blank_tile_numbers)

def get_texture_size_for_tileset(number_of_tiles):
	closest_pow_two = int(math.ceil(math.log(number_of_tiles, 2)))
        width = int(closest_pow_two / 2) + int(closest_pow_two % 2)
        height = int(closest_pow_two / 2)	
	return (int(math.pow(2, width)), int(math.pow(2, height)))

def get_texture_size_for_tileset_px(tile_size, target_tileset_texture_size):
	tile_width = tile_size[0]			
	tile_height = tile_size[1]
	
	target_tileset_size_px = (tile_width * target_tileset_texture_size[0], tile_height * target_tileset_texture_size[1])	

	return target_tileset_size_px

def reduce_tilesets(tilesets, target_tilemap_path, shrink_results, target_tileset_texture_size):
	tileset = tilesets[0]
	tile_width = tileset.tile_size[0]			
	tile_height = tileset.tile_size[1]			

	target_tileset_size_px = (tile_width * target_tileset_texture_size[0], tile_height * target_tileset_texture_size[1])
	target_tilemap_image = Image.new('RGBA', target_tileset_size_px)

	first_tile_number = 1
	reduced_tileset_mappings = []
	for tileset_shrink_result in zip(tilesets, shrink_results):
		combine_tilesets_result = combine_tilesets(tileset_shrink_result[0], target_tilemap_image, tileset_shrink_result[1][1], target_tileset_texture_size, tileset_shrink_result[1][2], first_tile_number)
		first_tile_number = combine_tilesets_result[0]
		reduced_tileset_mappings.append(combine_tilesets_result[1])
		
	original_tileset_image_source = 'first_things_first.png'
	target_tilemap_image.save(os.path.join(target_tilemap_path, original_tileset_image_source))
	return reduced_tileset_mappings

def combine_tilesets(tileset, target_tilemap_image, reduced_tile_mapping, target_tileset_texture_size, blank_tile_numbers, first_tile_number):        
	target_tile_number = first_tile_number

	tile_width = tileset.tile_size[0]			
	tile_height = tileset.tile_size[1]			

	reduced_tileset_mapping = {}

	tiles_processed = []
	tiles_really_reduced = []

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
				print "non reduced tile " + str(reduced_tile_id) 
				reduced_tile = tileset[reduced_tile_id]
			
				cropped_tile_image = get_cropped_tile_image(reduced_tile, tileset.tile_size)
				### just here for debugging purposes
				### cropped_tile_image.save('output/tt_' + str(tile_id) + ".png")

				box_left = ((target_tile_number - 1) % target_tileset_texture_size[0]) * tile_width
				box_top = ((target_tile_number - 1) / target_tileset_texture_size[0]) * tile_height
		
				paste_box = (box_left, box_top)
		                
				#print "............. " + str(tile_id) + " , " + str(paste_box)
	
				target_tilemap_image.paste(cropped_tile_image, paste_box)
				reduced_tileset_mapping[tile_id] = target_tile_number
			
				target_tile_number += 1
			
			tiles_processed.append(tile_id)

			#tiles_processed.append(reduced_tile_id)	

	print "...................................." + str(tiles_processed)
	print "...................................." + str(len(tiles_processed))
	print "......................really reduced ........." + str(tiles_really_reduced)
	print "......................really reduced ........." + str(len(tiles_really_reduced))

	print "...................................." + str(reduced_tileset_mapping)
	return (target_tile_number, reduced_tileset_mapping)

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

def update_tilemaps(tilemaps, target_tilemap_filename, reduced_tileset_mappings, target_tileset_size):       
	tile_size = get_tile_size(tilemaps)
	tilemap_to_save = tmxlib.map.Map(size = get_map_size(tilemaps), tile_size=tile_size)
	tilemap_to_save.tilesets = tmxlib.tileset.TilesetList(tilemap_to_save)

	texture_size_for_tileset_px = get_texture_size_for_tileset_px(tile_size, target_tileset_size)
	
	tilemap_image = tmxlib.image_base.Image(source = 'first_things_first.png', size = texture_size_for_tileset_px)
	tilemap_to_save.tilesets.insert(0, tmxlib.tileset.ImageTileset('sometileset', tile_size, tilemap_image))
	
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

number_of_tiles = 0
for input_tilemap_filename in input_tilemap_filenames:
	print "tilemap filename " + input_tilemap_filename

	tilemap = get_tilemap(input_tilemap_filename)
	tilemaps.append(tilemap)

	tileset = get_tileset(tilemap)
	tilesets.append(tileset)

	shrink_result = shrink_and_crop(tileset)
	shrink_results.append(shrink_result)
	number_of_tiles += shrink_result[0] 
	
	

target_tileset_size = get_texture_size_for_tileset(number_of_tiles)
print "texture size " + str(target_tileset_size)

#print " ####### " + str(shrink_results)

reduced_tileset_mappings = reduce_tilesets(tilesets, output_folder, shrink_results, target_tileset_size)

#reduced_tileset_mapping = reduce_tileset(tileset, output_folder, shrink_result[1], target_tileset_size, shrink_result[2])

print "####### reduced " + str(reduced_tileset_mappings[0])
#print "####### blank " + str(shrink_result[2])

update_tilemaps(tilemaps, get_target_tilemap_filename(input_tilemap_filename, output_folder), reduced_tileset_mappings, target_tileset_size)

