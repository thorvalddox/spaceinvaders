__author__ = 'thorvald'

from graph import Unit,Graphics, Vector2D
import pygame


class PlayerShip(Unit):
    def __init__(self,g):
        self.pos = Vector2D((640,540))
        self.load_main("sprite_enemy_mediumboat_main","sprite_explosion_medium")
        self.load_part("sprite_enemy_mediumboat_frontturret",(65,-10),0,lambda:0)
        self.attach(g)

    def ai(self):
        self.move_by_keys(4)
        if self.keys[pygame.K_s]:
            self.launch("sprite_enemy_shot_rotating",20,(40,-20),(12,-12),0.2)
        elif self.keys[pygame.K_z]:
            self.launch("sprite_enemy_shot_rotating",20,(40,-20),(0,-12),0.2)
        #elif self.keys[pygame.K_a]:
        #    self.launch("sprite_enemy_shot_rotating",20,(40,-20),(0,-5),0.1)


class EnemySimple(Unit):
    def __init__(self,g,player):
        self.load_main("sprite_enemy_sphereprobe","sprite_explosion_medium",30)
        self.hspeed = 0
        self.attach(g)
        self.target = player
        self.pos = Vector2D((320,200))
        self.hspeed = 2
    def ai(self):
        self.pos = self.pos + (self.hspeed*self.timefac,0)
        if self.pos.x < 100:
            self.hspeed = 2
        elif self.pos.x > 1180:
            self.hspeed -= 2
        self.launch_at("sprite_enemy_shot_pulse",10,(0,20),self.target.pos,6,0)


if __name__ == "__main__":
    g = Graphics()
    m = PlayerShip(g)
    EnemySimple(g,m)
    g.mainloop()
