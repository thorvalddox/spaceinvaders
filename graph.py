__author__ = 'thorvald'

from collections import namedtuple, Counter
from itertools import count, cycle
from math import sqrt
from random import randrange
from enum import Enum
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
            "dead1":"sounds/Big Bomb-SoundBible.com-1219802495.wav",
            "fire1":"sounds/ray_gun-Mike_Koenig-1169060422.wav",
            "fire2":"sounds/Shotgun_Blast-Jim_Rogers-1914772763.wav",
            "damage1":"sounds/M1 Garand Single-SoundBible.com-1941178963.wav",
            "water":"sounds/Water Splash-SoundBible.com-800223477.wav"
        }

        self.sounds = {n:pygame.mixer.Sound(k) for n,k in soundlist.items()}

        for s in self.sounds.values():
            s.set_volume(0.5)
        self.sounds["fire1"].set_volume(0.2)
        self.sounds["fire2"].set_volume(0.2)

        self.music = pygame.mixer.Sound("sounds/Replicant_Police.wav")

        self.music.play(loops=-1)

    def mainloop(self,command):
        while True:
            btime = time.time()
            pygame.event.pump()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
            self.step()
            pygame.display.flip()
            self.timepassed = (time.time() - btime)*60
            command()

    def step(self):
        self.screen.blit(self.back, (0, 0))
        self.screen.fill((0, 127, 255), (0, 540, 1280, 100))
        for i in self.objectlist:
            i.step()
            i.draw(self.screen)

    def playsound(self,sound):
        try:
            self.sounds[sound].play()
        except KeyError:
            pass

def make_screenplay(iter,framelenght):
    for i in iter:
        s = time.time()
        while time.time() < s + framelenght:
            yield i



class Visual:
    def __init__(self, filename, type_="enemy",repeat=True):
        right = []
        left = []
        prefix = {"unit":"enemy","shot":"enemy_shot","explosion":"explosion"}[type_]
        for i in count():
            fname = "graphics/Battlers/sprite_{}_{}_{}.png".format(prefix, filename, i)
            if not os.path.isfile(fname):
                break
            s = pygame.image.load(fname)
            self.size = s.get_size()
            right.append(s)
            left.append(pygame.transform.flip(s, True, False))
        assert i>0,"no such file {}".format(fname)
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
        self.maingroup = filename.split("_")[0]
        self.mainsprite = Visual(filename,"unit")
        self.destroy = Visual(destroy,"explosion",False)
        self.maxhealth = mh
        self.damage = 0
        self.parts = []
        self.flipped = False
        self.cooldown = Counter()
        self.sounds = {"fire":"","dead":"dead1","damage":"damage1"}
        self.options = {"cooldown":60}
        self.xmove = 0

    def load_part(self, filename, relpos, minhealth, function):
        self.parts.append(Part(Vector2D(relpos), Visual(self.maingroup+"_"+filename,"unit"), minhealth, function))

    def attach(self, graph):
        graph.objectlist.append(self)
        self.graph = graph

    def move_by_keys(self, speed):  # Put this method in step if you want it to be controlled by keyboard.
        self.keys = pygame.key.get_pressed()
        self.xmove = self.keys[pygame.K_d] - self.keys[pygame.K_q]
        if self.xmove==-1 and self.pos.x > 50:
            self.pos = self.pos - (speed*self.timefac, 0)
            self.flipped = True
        elif self.xmove==1 and self.pos.x < 1128:
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
        w, h = self.bbox().size
        middis = (w / 2, h / 2)
        #pygame.draw.rect(screen,(255,0,0),self.bbox(),1) #show bouding box
        screen.fill((127, 127, 127), (self.pos.x - w // 2, self.pos.y + h // 2 + 5, w, 5))
        screen.fill((0, 127, 0), (self.pos.x - w // 2, self.pos.y + h // 2 + 5, w * self.health / self.maxhealth, 5))

    def step(self):
        self.cooldown.subtract({k:1 for k in self.cooldown})
        for i in self.parts:
            if self.health > i.minhealth:
                i.function()
        self.ai()

    @property
    def activeparts(self):
        return sum(self.health > i.minhealth for i in self.parts)

    def ai(self):
        pass

    @property
    def health(self):
        return self.maxhealth - self.damage

    @property
    def timefac(self):
        return self.graph.timepassed

    def launch(self, sprite, power, relpos, initspeed, gravity,flipspeed=True,
               relcooldown=1,alternate=1,cooldownslot=0):
        if randrange(alternate):
            return
        initspeed = Vector2D(initspeed)
        speed = ~initspeed if self.flipped and flipspeed else initspeed
        if self.cooldown[cooldownslot] <= 0:
            self.play("fire")
            Projectile(self.graph, sprite, power, self.origpos(relpos), speed, gravity)
            self.cooldown[cooldownslot] = self.options["cooldown"] *relcooldown

    def launch_at(self, sprite, power, relpos, target, speed, gravity,
                  relcooldown=1,alternate=1,cooldownslot=0):
        self.launch(sprite, power, relpos, (Vector2D(target) - relpos - self.pos).unit() * speed, gravity,
                    False,relcooldown,alternate,cooldownslot)

    def bbox(self):
        w, h = self.mainsprite.size
        try:
            wr = 2*max(abs(p.relpos.x+p.image.size[0]//2-w/2)+p.image.size[0]//2 for p in self.parts)
            hr = 2*max(abs(p.relpos.y+p.image.size[1]//2-h/2)+p.image.size[1]//2 for p in self.parts)
            w,h = max(w,wr), max(h,hr)
        except ValueError:
            pass
        middis = (w / 2, h / 2)
        return (pygame.Rect(self.pos - middis, (w, h)))

    def checkdead(self):
        if self.health <= 0:
            self.play("dead")
            self.graph.objectlist.remove(self)
            Effect(self.graph, self.pos, self.destroy)
            del self

    def play(self,i):
        self.graph.playsound(self.sounds[i])

    def reset_cooldown(self):
        self.cooldown = [0]*10


class Projectile:
    def __init__(self, graph, sprite, power, pos, speed, gravity):
        self.mainsprite = Visual(sprite,"shot")
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
        if self.pos.y > 550 or self.pos.y < -640:
            self.graph.playsound("water")
            try:
                self.graph.objectlist.remove(self)
            except ValueError:
                print("removed twice")
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
                        u.play("damage")
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