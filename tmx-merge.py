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

	print "==== " + str(tile.number) + ", "  + str(tileBox) 
	return croppedTile


def shrink_and_crop(tilemap_path):
        tilemap = tmxlib.Map.open(tilemap_path)
	tileset = tilemap.tilesets[0]

        tilesAlreadyCropped = []
        blank_tile_numbers = []
        tile_mapping_content_2_tile_number  = {}
        shrunk_tile_number_mapping = {} 

	for tile in tileset:
		croppedTile = get_cropped_tile_image(tile, tileset.tile_size)

		# only save the tile if it is not blank
		if croppedTile.getbbox() :

			# only save the tile if it is not a duplicate of an already processed one 
			convertedCroppedTileString = croppedTile.convert('L').tostring()
                        if not convertedCroppedTileString in tilesAlreadyCropped:
                                tilesAlreadyCropped.append(convertedCroppedTileString)
				tile_mapping_content_2_tile_number[convertedCroppedTileString] = tile.number
			else:
				shrunk_tile_number_mapping[tile.number] = tile_mapping_content_2_tile_number[convertedCroppedTileString]
				print "duplicate tile, skipping " + str(tile.number) 
		else:
			blank_tile_numbers.append(tile.number)
			print "skipping tile " + str(tile.number)

	print ".... Total different tiles cropped " + str(len(tilesAlreadyCropped))

	return (len(tilesAlreadyCropped), shrunk_tile_number_mapping, blank_tile_numbers)

def get_texture_size_for_tileset(number_of_tiles):
	closest_pow_two = math.ceil(math.log(number_of_tiles, 2))
        width = (closest_pow_two / 2) + (closest_pow_two % 2)
        height = closest_pow_two / 2
	return (int(math.pow(2, width)), int(math.pow(2, height)))

def reduce_tileset(tilemap_path, target_tilemap_path, reduced_tile_mapping, target_tileset_size, blank_tile_numbers):
        tilemap = tmxlib.Map.open(tilemap_path)
	tileset = tilemap.tilesets[0]

	target_tile_number = 1

	tile_width = tileset.tile_size[0]			
	tile_height = tileset.tile_size[1]			

        target_tileset_size_px = (tile_width * target_tileset_size[0], tile_height * target_tileset_size[1])
	target_tilemap_image = Image.new('RGBA', target_tileset_size_px)

	reduced_tileset_mapping = {}

	tiles_processed = []
	for tile in tileset:
		if not (tile.number in blank_tile_numbers):
			# reduced_tile_id =  reduced_tile_mapping[tile.number] if (tile.number in reduced_tile_mapping) else tile.number
                        reduced_tile_id = tile.number
			reduced_tile = tileset[reduced_tile_id]
			
			cropped_tile_image = get_cropped_tile_image(reduced_tile, tileset.tile_size)

			box_left = (target_tile_number % target_tileset_size[1]) * tile_width
			box_top = (target_tile_number / target_tileset_size[1]) * tile_height 

			paste_box = (box_left, box_top)
                
			print ",,,,,,,,,,,,,,,,,,,,, " + str(tile.number) + " , " + str(paste_box)

			target_tilemap_image.paste(cropped_tile_image, paste_box)
			reduced_tileset_mapping[tile.number] = target_tile_number
			target_tile_number += 1
			tiles_processed.append(tile.number)

	original_tileset_image_source = tileset.image.source
	target_tilemap_image.save(os.path.join(target_tilemap_path, original_tileset_image_source))
	print "...................................." + str(tiles_processed)
	print "...................................." + str(len(tiles_processed))
	return reduced_tileset_mapping

def update_tilemap(tilemap_path, target_tilemap_path, reduced_tileset_mapping):
        tilemap = tmxlib.Map.open(tilemap_path)
	layer = tilemap.layers[0]
	
	for v in range(tilemap.size[0]):
		for h in range(tilemap.size[1]):
                        pos = (v, h)
                        print "******************** " + str(pos) 
                        value = layer.value_at(pos) 
			print " **** " + str(value)
			if (value != 0) and (value in reduced_tileset_mapping):
				layer.set_value_at(pos, reduced_tileset_mapping[value])
			else:
				layer.set_value_at(pos, 0) # deleting?, setting to blank
	target_tilemap_filename = os.path.join(target_tilemap_path, os.path.basename(tilemap_path))
	tilemap.save(target_tilemap_filename)

def print_tilemap(tile_map_path):
        tilemap = tmxlib.Map.open(tile_map_path)
	layer = tilemap.layers[0]
	tileset = tilemap.tilesets[0]
	for tile in layer.all_tiles():
		print " ... " + str(tile.number) + " , " + str(tile.pos)
	
input_tilemap_filename = 'testz.tmx'
output_folder = 'output'

print_tilemap(input_tilemap_filename)

shrink_result = shrink_and_crop(input_tilemap_filename)
number_of_tiles = shrink_result[0] 
target_tileset_size = get_texture_size_for_tileset(number_of_tiles)

print " ####### " + str(shrink_result[1])


reduced_tileset_mapping = reduce_tileset(input_tilemap_filename, output_folder, shrink_result[1], target_tileset_size, shrink_result[2])

print "####### reduced " + str(reduced_tileset_mapping)
print "####### blank " + str(shrink_result[2])

update_tilemap(input_tilemap_filename, output_folder, reduced_tileset_mapping)


