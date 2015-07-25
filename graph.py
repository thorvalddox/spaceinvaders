__author__ = 'thorvald'

from collections import namedtuple
from itertools import count, cycle
from math import sqrt
import os.path

import pygame

import time


class Vector2D(tuple):
    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    def __add__(self, other):
        return Vector2D((self[0] + other[0], self[1] + other[1]))

    def __sub__(self, other):
        return Vector2D((self[0] - other[0], self[1] - other[1]))

    def __mul__(self, n):
        return Vector2D((n * self[0], n * self[1]))

    def __invert__(self):
        return Vector2D((-self[0],self[1]))

    def norm(self):
        return sqrt(self[0] ** 2 + self[1] ** 2)

    def unit(self):
        return self * (1.0 / self.norm())


class Graphics:
    def __init__(self):
        self.screen = pygame.display.set_mode((1280, 640))
        self.objectlist = []
        self.back = pygame.transform.scale2x(pygame.image.load("graphics/Cave.png"))
        self.timepassed = 0
        pygame.mixer.init()
        soundlist = {
            "dead":"Big Bomb-SoundBible.com-1219802495.wav",
            "fire1":"Laser Blasts-SoundBible.com-108608437.wav",
            "fire2":"Shotgun_Blast-Jim_Rogers-1914772763.wav",
            "damage":"M1 Garand Single-SoundBible.com-1941178963.mp3"
        }

        sounds = {n:pygame.mixer.Sound(k)}

    def mainloop(self):
        while True:
            btime = time.time()
            pygame.event.pump()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
            self.step()
            pygame.display.flip()
            self.timepassed = (time.time() - btime)*60

    def step(self):
        self.screen.blit(self.back, (0, 0))
        self.screen.fill((0, 127, 255), (0, 540, 1280, 100))
        for i in self.objectlist:
            i.step()
            i.draw(self.screen)

def make_screenplay(iter,framelenght):
    for i in iter:
        s = time.time()
        while time.time() < s + framelenght:
            yield i


class Visual:
    def __init__(self, filename,repeat=True):
        right = []
        left = []
        for i in count():
            fname = "graphics/Battlers/{}_{}.png".format(filename, i)
            if not os.path.isfile(fname):
                break
            s = pygame.image.load(fname)
            self.size = s.get_size()
            right.append(s)
            left.append(pygame.transform.flip(s, True, False))
        if repeat:
            self.right = make_screenplay(cycle(right),1/20)
            self.left = make_screenplay(cycle(left),1/20)
        else:
            self.right = make_screenplay(right,1/20)
            self.left = make_screenplay(left,1/20)

    def __call__(self, flipped=False):
        if not flipped:
            return (next(self.right))
        else:
            return (next(self.left))


Part = namedtuple("Part", "relpos,image,minhealth,function")


class Unit:
    def __init__(self, graph, x, y):
        self.attach(graph)
        self.pos = Vector2D(x, y)


    def origpos(self, relpos):
        relpos = Vector2D(relpos)
        if not self.flipped:
            return self.pos + relpos
        else:
            return self.pos + ~relpos

    def load_main(self, filename, destroy, mh=100):
        self.mainsprite = Visual(filename)
        self.destroy = Visual(destroy,False)
        self.maxhealth = mh
        self.damage = 0
        self.parts = []
        self.flipped = False
        self.cooldown = 0

    def load_part(self, filename, relpos, minhealth, function):
        self.parts.append(Part(Vector2D(relpos), Visual(filename), minhealth, function))

    def attach(self, graph):
        graph.objectlist.append(self)
        self.graph = graph

    def move_by_keys(self, speed):  # Put this method in step if you want it to be controlled by keyboard.
        self.keys = pygame.key.get_pressed()
        if self.keys[pygame.K_q]:
            self.pos = self.pos - (speed*self.timefac, 0)
            self.flipped = True
        elif self.keys[pygame.K_d]:
            self.pos = self.pos + (speed*self.timefac, 0)
            self.flipped = False

    def draw(self, screen):
        w, h = self.mainsprite.size
        middis = (w / 2, h / 2)
        screen.blit(self.mainsprite(self.flipped), self.pos - middis)
        for i in self.parts:
            if self.health > i.minhealth:
                normalpos = self.pos + i.relpos - middis
                flippedpos = self.pos + (w, 0) - middis + (-i.relpos.x, i.relpos.y) - (i.image.size[0], 0)
                screen.blit(i.image(self.flipped), [normalpos, flippedpos][self.flipped])

        screen.fill((127, 127, 127), (self.pos.x - w // 2, self.pos.y + h // 2 + 5, w, 5))
        screen.fill((0, 127, 0), (self.pos.x - w // 2, self.pos.y + h // 2 + 5, w * self.health / self.maxhealth, 5))

    def step(self):
        self.ai()
        self.cooldown -= self.timefac
        for i in self.parts:
            if self.health > i.minhealth:
                i.function()

    def ai(self):
        pass

    @property
    def health(self):
        return self.maxhealth - self.damage

    @property
    def timefac(self):
        return self.graph.timepassed

    def launch(self, sprite, power, relpos, initspeed, gravity,flipspeed=True):
        initspeed = Vector2D(initspeed)
        speed = ~initspeed if self.flipped and flipspeed else initspeed
        if self.cooldown < 0:
            Projectile(self.graph, sprite, power, self.origpos(relpos), speed, gravity)
            self.cooldown = 60

    def launch_at(self, sprite, power, relpos, target, speed, gravity):
        self.launch(sprite, power, relpos, (Vector2D(target) - relpos - self.pos).unit() * speed, gravity,False)

    def bbox(self):
        w, h = self.mainsprite.size
        middis = (w / 2, h / 2)
        return (pygame.Rect(self.pos - middis, (w, h)))

    def checkdead(self):
        if self.health < 0:
            self.graph.objectlist.remove(self)
            Effect(self.graph, self.pos, self.destroy)
            del self


class Projectile:
    def __init__(self, graph, sprite, power, pos, speed, gravity):
        self.mainsprite = Visual(sprite)
        self.power = power
        self.pos = pos
        self.speed = speed
        self.gravity = gravity
        self.armed = False  # prevent shooting shooter
        self.attach(graph)

    def step(self):
        self.pos = self.pos + self.speed
        self.speed = self.speed + (0, self.gravity)
        self.check_collide()
        if self.pos.y > 640 or self.pos.y < -640:
            self.graph.objectlist.remove(self)
            del self

    def attach(self, graph):
        graph.objectlist.append(self)
        self.graph = graph

    def draw(self, screen):
        w, h = self.mainsprite.size
        middis = (w / 2, h / 2)
        screen.blit(self.mainsprite(), self.pos - middis)

    def check_collide(self):

        if not self.armed:
            self.armed = not any(u.bbox().collidepoint(*self.pos) for u in self.graph.objectlist if isinstance(u, Unit))
        else:
            for u in self.graph.objectlist:
                if isinstance(u, Unit):
                    if u.bbox().collidepoint(*self.pos):
                        u.damage += self.power
                        u.checkdead()
                        self.graph.objectlist.remove(self)
                        del self
                        return

class Effect:
    def __init__(self,g,pos,visual):
        self.pos = pos
        self.mainsprite = visual
        self.attach(g)


    def attach(self, graph):
        graph.objectlist.append(self)
        self.graph = graph

    def draw(self, screen):
        w, h = self.mainsprite.size
        middis = (w / 2, h / 2)
        try:
            screen.blit(self.mainsprite(), self.pos - middis)
        except StopIteration:
            self.graph.objectlist.remove(self)
            del self

    def step(self):
        pass