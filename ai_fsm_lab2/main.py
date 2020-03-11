import sys
from os import path
from random import choice

import pygame as pg

from camera import Camera
from config import *
from sprites import *
from unit import Manager, Unit, Worker
from world import TerrainTypes, ResourceTypes, BuildingTypes, World


class Game:

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pg.HWSURFACE)
        pg.display.set_caption(WINDOW_CAPTION + "- Loading...")
        self.clock = pg.time.Clock()
        pg.key.set_repeat(500, 100)

        self.world = None
        self.spawn_cell = None

        self.background = None
        self.all_sprites = None
        self.fog = None
        self.non_fog = None
        self.buildings = None

        self.camera = None
        self.playing = False
        self.dt = 0

        self.load_data()

    def load_data(self):
        self.world = World.from_map(WORLD_PATH)
        self.background = pg.image.load(BACKGROUND_PATH)

    def spawn(self):
        while True:
            spawn_cell = self.world.get_random_cell()
            spawn_region = self.world.graph.neighbours(spawn_cell, False)
            spawn_region.append(spawn_cell)
            if all(self.world.graph.is_free(elem) for elem in spawn_region):
                break

        for u in range(INIT_UNITS - 1):
            rand_cell = choice(spawn_region)
            unit = Unit(self.world, rand_cell, Worker)
            UnitSprite(self, unit)
            unit.start()

        manager = Unit(self.world, spawn_cell, Manager)
        manager.start()
        UnitSprite(self, manager)

        return spawn_cell

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.fog = pg.sprite.Group()
        self.non_fog = pg.sprite.Group()
        self.buildings = pg.sprite.Group()
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

        self.world.on_buildings_changed.append(self.on_building)
        self.world.on_resources_changed.append(self.on_resource)

        self.spawn_cell = self.spawn()
        x_offset = WINDOW_WIDTH / 2 - self.spawn_cell[0] * TILE_SIZE
        y_offset = WINDOW_HEIGHT / 2 - self.spawn_cell[1] * TILE_SIZE
        self.world.reveal(self.spawn_cell)
        self.camera = Camera(x_offset, y_offset, self.world.width * TILE_SIZE, self.world.height * TILE_SIZE)

    def on_building(self, cell, building):
        if building == BuildingTypes.Camp:
            Camp(self, *cell)
        elif building == BuildingTypes.Kiln:
            Kiln(self, *cell)

    def on_resource(self, cell, resource, count):
        pass

    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            pg.display.set_caption("{} - {} FPS".format(WINDOW_CAPTION, int(self.clock.get_fps())))
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop
        self.world.step_forward(self.dt * TIME_SCALE)
        self.all_sprites.update()
        self.camera.update(self.dt)

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        for sprite in self.fog:
            fog = self.world.graph.get_fog((sprite.x, sprite.y))
            if not fog:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
        for building in self.buildings:
            self.screen.blit(building.image, self.camera.apply(building))
        for unit in self.non_fog:
            self.screen.blit(unit.image, self.camera.apply(unit))

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
