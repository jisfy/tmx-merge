import tmxlib
import hashlib
import difflib
import math
import os
from PIL import Image, ImageChops

myMap = tmxlib.Map.open('testz.tmx')
myTileset = myMap.tilesets[0]

def get_tileset_id(tileset_path):
	tileset_filename = os.path.basename(tileset_path)
        tileset_filename_noext = os.path.splitext(tileset_filename)
        print "tileset_filename_noext " + tileset_filename_noext[0]

	return tileset_filename_noext[0]

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
        tileset_id = get_tileset_id(tilemap_path)

        tilesAlreadyCropped = []
        blank_tile_numbers = []
        tile_mapping_content_2_tile_number  = {}
        shrunk_tile_number_mapping = {} 

	for tile in tileset:
	#	tileImage = Image.open(tile.image.image.source)

#		boxLeft = tile.image.top_left[1]
#		boxTop = tile.image.top_left[0]
#		boxRight = tile.image.top_left[1] + tileset.tile_size[0]
#                boxBottom = tile.image.top_left[0] + tileset.tile_size[1]

#		tileBox = (boxLeft, boxTop, boxRight, boxBottom)
#		croppedTile = tileImage.crop(tileBox)
		croppedTile = get_cropped_tile_image(tile, tileset.tile_size)

		# only save the tile if it is not blank
		if croppedTile.getbbox() :

			# only save the tile if it is not a duplicate of an already processed one 
			convertedCroppedTileString = croppedTile.convert('L').tostring()
                        if not convertedCroppedTileString in tilesAlreadyCropped:
                                tilesAlreadyCropped.append(convertedCroppedTileString)
				tile_mapping_content_2_tile_number[convertedCroppedTileString] = tile.number
				croppedTile.save('temp/tile_' + tileset_id + "_" + str(tile.number) + '.png')
			else:
				shrunk_tile_number_mapping[tile.number] = tile_mapping_content_2_tile_number[convertedCroppedTileString]
				print "duplicate tile, skipping " + str(tile.number) 
		else:
			blank_tile_numbers.append(tile.number)
			print "skipping tile " + str(tile.number)

	print ".... Total different tiles cropped " + str(len(tilesAlreadyCropped))

	return (len(tilesAlreadyCropped), shrunk_tile_number_mapping, blank_tile_numbers)

def tileset_size(number_of_tiles):
	closest_pow_two = math.ceil(math.log(number_of_tiles, 2))
        width = (closest_pow_two / 2) + (closest_pow_two % 2)
        height = closest_pow_two / 2
	return (int(math.pow(2, width)), int(math.pow(2, height)))

def reduce_tileset(tilemap_path, target_tilemap_path, reduced_tile_mapping, target_tileset_size, blank_tile_numbers):
	tilemap_name = get_tileset_id(tilemap_path)
	target_tilemap_name = get_tileset_id(target_tilemap_path)
	
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

			# box_left = ((target_tile_number / target_tileset_size[1]) - 1) * tile_width
			# box_top = ((target_tile_number % target_tileset_size[1]) - 1) * tile_height 

			box_left = (target_tile_number % target_tileset_size[1]) * tile_width
			box_top = (target_tile_number / target_tileset_size[1]) * tile_height 

			paste_box = (box_left, box_top)
                
			print ",,,,,,,,,,,,,,,,,,,,, " + str(tile.number) + " , " + str(paste_box)

			target_tilemap_image.paste(cropped_tile_image, paste_box)
			reduced_tileset_mapping[tile.number] = target_tile_number
			target_tile_number += 1
			tiles_processed.append(tile.number)
	
	target_tilemap_image.save(target_tilemap_path)
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
        tilemap.tilesets[0].image.source = 'target.png'
	tilemap.save(target_tilemap_path)

def map_tiles(tilemap_path, target_tilemap_path, reduced_tile_mapping):
        tilemap = tmxlib.Map.open(tileset_path)
        target_tilemap = tilemap.save(target_tilemap_path)
	tileset = tilemap.tilesets[0]

def print_tilemap(tile_map_path):
        tilemap = tmxlib.Map.open(tile_map_path)
	layer = tilemap.layers[0]
	tileset = tilemap.tilesets[0]
	for tile in layer.all_tiles():
		print " ... " + str(tile.number) + " , " + str(tile.pos)
	

#for tile in myTileset:
#	print "" + str(tile.image.top_left)
#        tileImage = Image.open(tile.image.image.source)
#        tileBox = (tile.image.top_left[1], tile.image.top_left[0], tile.image.top_left[1] + 64, tile.image.top_left[0] + 64)
#        croppedTile = tileImage.crop(tileBox)
#        if croppedTile.getbbox() :
#        	croppedTile.save('temp/tile_' + str(tile.number) + '.png')
#	else:
#		print "skipping tile"

print_tilemap('testz.tmx')

shrink_result = shrink_and_crop('testz.tmx')
number_of_tiles = shrink_result[0] 
target_tileset_size = tileset_size(number_of_tiles)

print " ####### " + str(shrink_result[1])

reduced_tileset_mapping = reduce_tileset('testz.tmx', 'target.png', shrink_result[1], target_tileset_size, shrink_result[2])

print "####### reduced " + str(reduced_tileset_mapping)
print "####### blank " + str(shrink_result[2])


update_tilemap('testz.tmx', 'arsa.tmx', reduced_tileset_mapping)

#print "-----------/ " + str(target_tileset_size)

