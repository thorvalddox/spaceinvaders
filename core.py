__author__ = 'thorvald'

from random import randrange,random
from functools import partial
from graph import Unit,Graphics, Vector2D, cycle
import pygame

import json


class PlayerShip(Unit):
    def __init__(self,g):
        self.pos = Vector2D((640,540))
        self.load_main("sprite_enemy_mediumboat_main","sprite_explosion_medium")
        self.load_part("sprite_enemy_mediumboat_frontturret",(65,-10),0,lambda:0)
        self.attach(g)
        self.sounds.update(fire="fire2")
        self.exp = 0
        self.level = 1

    def ai(self):
        self.move_by_keys(4)
        self.levelup()

        if self.keys[pygame.K_s]:
            self.launch("sprite_enemy_shot_rotating",20,(40,-20),(12+abs(self.xmove*4),-12),0.2)
        elif self.keys[pygame.K_z] and self.level >= 2:
            self.launch("sprite_enemy_shot_rotating",20,(40,-20),(abs(self.xmove*4),-17),0.2)
        elif self.keys[pygame.K_p]:
            for e in self.graph.objectlist:
                if isinstance(e,EnemySimple):
                    e.damage = e.maxhealth
                    e.checkdead()
        #elif self.keys[pygame.K_a]:
        #    self.launch("sprite_enemy_shot_rotating",20,(40,-20),(0,-5),0.1)

    def draw(self,screen):
        Unit.draw(self,screen)
        w,h = self.mainsprite.size
        screen.fill((127, 127, 127), (self.pos.x - w // 2, self.pos.y + h // 2 + 10, w, 5))
        screen.fill((0, 0, 255), (self.pos.x - w // 2, self.pos.y + h // 2 + 10, w * self.exp / 100, 5))
        for i in range(self.level):
            screen.fill((255, 0, 0), (self.pos.x - w // 2+7*i, self.pos.y + h // 2 + 16, 5, 5))

    def levelup(self):
        if self.exp > 100:
            self.exp -= 100
            self.level += 1
            if self.level == 3:
                self.load_part("sprite_enemy_mediumboat_rearturret",(10,-10),0,lambda:0)

class EnemySimple(Unit):
    def __init__(self,g,player,data):
        self.load_main("sprite_enemy_" + data.get("image","largeboat_bridge"),"sprite_explosion_medium",
                       data.get("life",30))
        self.attach(g)
        self.target = player
        self.pos = Vector2D((randrange(-1000,100),randrange(200,350)))
        self.hspeed = data.get("speed",2) + random()
        self.sounds.update(data.get("sounds",{}))
        self.options.update(data.get("options",{}))
        self.firespeed = data.get("firespeed",10)
        self.bullet = "sprite_enemy_" + data.get("bullet","shot_pulse")
        self.strenght = data.get("strength",10)

        parts = data.get("parts",[])
        for p in parts:
            self.load_part(p["sprite"],p["pos"],p["minhealth"],partial(self.runpart,p))


    def ai(self):
        self.pos = self.pos + (self.hspeed*self.timefac,0)
        if self.pos.x < 100:
            self.hspeed = abs(self.hspeed)
        elif self.pos.x > 1180:
            self.hspeed = -abs(self.hspeed)
        if self.pos.x > 0:
            self.launch_at(self.bullet,self.strenght,(0,0),self.target.pos,self.firespeed,0)

    def runpart(self,data):
        func = data.get("func","none")
        if func == "none":
            return
        elif func == "fire":
            self.launch_at(data.get("bullet",self.bullet),
                           data.get("strenght",self.strenght),
                           data.get("relpos",(0,0)),
                           self.target.pos,
                           data.get("firespeed",self.firespeed),
                           0,cooldownslot=data.get("slot",1))

class EnemyStalk(EnemySimple):
    def ai(self):
        self.pos = self.pos + (self.hspeed*self.timefac,0)
        if self.pos.x < self.target.pos.x:
            self.hspeed = abs(self.hspeed)
        elif self.pos.x > self.target.pos.x:
            self.hspeed = -abs(self.hspeed)
        if self.pos.x > 0:
            self.launch_at(self.bullet,self.strenght,(0,0),self.target.pos,self.firespeed,0)

class jsonLoader:
    def __init__(self):
        self.data = json.load(open("Enemies.json"))
        self.endict = self.data["Enemies"]
        self.waves = self.data["Waves"]

    def spawn_enemy(self, graph, player, name):
        data = self.endict[name]
        type_ = {"simple":EnemySimple,"stalk":EnemyStalk}
        type_[data["type"]](graph, player, data)
        player.exp += 12//player.level

    def wave_generator(self, graph, player):
        for wave in cycle(self.waves):
            player.damage = 0
            for n in wave:
                self.spawn_enemy(graph,player,n)
            yield



def checkWaveDefeated(graph):
    return not any(isinstance(u,Unit) and not isinstance(u,PlayerShip) for u in graph.objectlist)

def spawn_wave(generator,graph):
    if checkWaveDefeated(graph):
        next(generator)

if __name__ == "__main__":
    g = Graphics()
    m = PlayerShip(g)
    w = jsonLoader().wave_generator(g,m)

    g.mainloop(partial(spawn_wave,w,g))
