# use opencv to visualize the map
import cv2
import numpy as np


RED = 2
GREEN = 1
BLUE = 0


class Visualize:
    def __init__(self):
        self.img_num = 0

    def mark_pixel(self, img, items, color):
        for item in items:
            x, y = item.position_tuple
            img[int(x)][int(y)] = color

    async def visualize_map(self, game_info, state, units):
        height, width = game_info.map_size
        img = np.zeros((height, width, 3), np.uint8)
        self.mark_pixel(img, state.mineral_field, [255, 50, 50])
        self.mark_pixel(img, state.enemy_units, [30, 30, 255])
        self.mark_pixel(img, state.enemy_structures, [50, 50, 235])
        self.mark_pixel(img, units, [30, 255, 30])
        self.mark_pixel(img, state.structures, [50, 235, 50])
        self.img_num += 1
        print(f'{self.img_num}.png')
        cv2.imwrite(f'{self.img_num}.png', img)
        return