import sys
from os import path

import pygame as pg

from config import *
from sprites import *
from world import World, TerrainTypes
from camera import Camera


class Game:

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pg.display.set_caption(WINDOW_CAPTION)
        self.clock = pg.time.Clock()
        pg.key.set_repeat(500, 100)

        self.background = None
        self.world = None
        self.all_sprites = None
        self.walls = None
        self.camera = None
        self.playing = False
        self.dt = 0

        self.load_data()

    def load_data(self):
        game_dir = path.dirname(__file__)
        self.world = World.from_map(path.join(game_dir, 'map/Map1.txt'))
        self.background = pg.image.load(path.join(game_dir, 'res/bg.jpg'))

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        g = self.world.graph
        for i, cell in enumerate(g.terrain):
            x = i % g.width
            y = i // g.width
            if cell[0] is TerrainTypes.Ground:
                Ground(self, x, y)
            elif cell[0] is TerrainTypes.Rock:
                Rock(self, x, y)
            elif cell[0] is TerrainTypes.Water:
                Water(self, x, y)
            elif cell[0] is TerrainTypes.Swamp:
                Swamp(self, x, y)
            elif cell[0] is TerrainTypes.Tree:
                Tree(self, x, y)

        self.camera = Camera(0, 0, 256, 256)

    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop
        self.all_sprites.update()
        self.camera.update(self.dt)

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        for sprite in self.all_sprites:
            fog = self.world.graph.get_fog((sprite.x, sprite.y))
            if not not not fog:
                self.screen.blit(sprite.image, self.camera.apply(sprite), special_flags=pg.BLEND_MULT)
        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()

# create the game object
g = Game()
while True:
    g.new()
    g.run()
