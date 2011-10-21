# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

import pygame, math

from random import randint
from constants import *
from misc import *
from enemies import *

class LevelSplash(pygame.sprite.DirtySprite):
    def __init__(self, num):
        pygame.sprite.DirtySprite.__init__(self)
        self.ticks = 0

        self.image = pygame.Surface((128,40))
        move_sprite(self, 300, 100)

        _sfont = load_font('trebuc.ttf', 32)
        _sfont.set_bold(True)

        _si = self.image
        _si.set_alpha(0)
        _si.blit(pygame.display.get_surface(), (0,0), self.rect)
        _lt = "Level %d"%num
        _ltf = _sfont.render(_lt, True, (255,255,255))
        for _place in [(i,j) for i in [0,2] for j in [0,2]]:
            _si.blit(_ltf, _place)
        _si.blit(_sfont.render(_lt, True, (60,60,120)), (1, 1))

    def tick(self, f):
        self.ticks += 1

        if self.ticks < 52: self.image.set_alpha(self.ticks*5)
        else: self.image.set_alpha(520-self.ticks*5)
        self.dirty = 1
        if self.ticks == 104:
            f.remove(self)
            # Actually start the level
            f.start_level()

class Level:
    def __init__(self, f, *enemies, **kwargs):
        self.f = f
        # Setup bounds
        if self.f.nplayers == 1:
            self.rr = (200,400)
        else:
            self.rr = (180,420)

        self.ticks = 0
        self.started = self.finished = False
        self.bosses = []
        self.boss_alone = False

        self.enemies = [dict(enemy=e, togo=n+int(0.85*n*(self.f.nplayers-1)),
                             ticks=-1) for (e,n) in enemies]

    def start(self):
        debug("Level %d started!"%self.num)
        self.started = True
        map(self.gen_next_enemy, self.enemies)

    def create_bsprite(self):
        self.bsprite = pygame.sprite.DirtySprite()
        _sbs = self.bsprite
        _sbs.image = pygame.Surface((640, 20))
        _sbs.rect = _sbs.image.get_rect()

        # Boss font
        self.bfont = load_font('trebuc.ttf', 14)
        self.bfont.set_bold(True)
        self.bfont.set_italic(True)

        self.render_bosses()
        self.f.add(_sbs)
        
    def born_bosses(self):
        # Subclass responsibility
        return []

    def render_bosses(self):
        _bsi = self.bsprite.image
        _bsi.fill((0,0,0))
        _bst = self.bfont.render("Boss:", True, (255,255,255))
        _bsi.blit(_bst, (3, 3))
        _bstw = _bst.get_width()
        _pbw = 640-15-_bstw
        pygame.draw.rect(_bsi, (0,0,0), (8+_bstw, 3, _pbw, 17), 1)

        _clife = sum(map(lambda x: max(x.life,0), self.bosses))
        _slife = sum(map(lambda x: x.slife, self.bosses))
        _cko = 1.0*_clife/_slife
        _cw = int(_cko*(_pbw-2))
        pygame.draw.rect(_bsi, (255,255,255), (9+_bstw, 4, _cw, 15))

        # Mark it as dirty
        self.bsprite._layer = TOP_LAYER
        self.bsprite.dirty = 1

    def gen_next_enemy(self, enemy):
        if enemy["togo"] > 0:
            ttg = max(LEVEL_TICKS - self.ticks, 0)
            bpt = int(1.5*ttg/enemy["togo"])
            enemy["ticks"] = self.ticks + randint(1, bpt+1)
            enemy["togo"] -= 1
        else:
            enemy["ticks"] = -1
        print "ENEMY gen", enemy

    def tick(self, f):
        for e in self.enemies:
            if self.ticks == e["ticks"]:
                f.add(e["enemy"](y=randint(*self.rr), field=f))
                self.gen_next_enemy(e)

##            if random.choice([1,2,3]) > 1:
##                yy = randint(200, 400)
##                f.add(Vits(x=-20, y=yy, isboss=False, field=f))
##            if random.choice([1,2,3]) > 1:
##                yy = randint(200, 400)
##                f.add(Bear(x=-40, y=yy, isboss=False, field=f))

        self.ticks += 1

        def is_dead(x): return not x.is_alive()
        if self.bosses and all(map(is_dead, self.bosses)):
            self.finished = True
            self.f.remove(self.bsprite)
            return

        creatures = self.f.creatures(*[e["enemy"] for e in self.enemies])
        if not self.bosses and self.ticks >= LEVEL_TICKS \
               and (not self.boss_alone or not creatures):
            self.bosses = self.born_bosses()
            self.create_bsprite()
            f.add(*self.bosses)

class Level1(Level):
    num = 1
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 29))

    def born_bosses(self):
        return [Knubbs(y=290, isboss=True, field=self.f)]

class Level2(Level):
    num = 2
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 29), (Aktivist, 14))
        self.boss_alone = True

    def born_bosses(self):
        """8 Pingvins as booses."""
        return [Pingvin(y=randint(*self.rr), isboss=True, field=self.f)
                for _ in range(8)]

class Level3(Level):
    num = 3
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 29), (Aktivist, 14), (Pingvin, 8))
        self.boss_alone = True

    def born_bosses(self):
        """Single or couple of bears."""
        _bys = [300] if self.f.nplayers < 2 else [250, 350]
        return [Bear(y=by, isboss=True, field=self.f) for by in _bys]

class Level4(Level):
    num = 4
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 29), (Aktivist, 14),
                       (Pingvin, 8), (Bear, 4))

    def born_bosses(self):
        """Single or couple of turtles."""
        _tys = [300] if self.f.nplayers < 2 else [250, 350]
        return [Turtle(y=ty, isboss=True, field=self.f) for ty in _tys]

class Level5(Level):
    num = 5
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 29), (Aktivist, 14),
                       (Pingvin, 8), (Bear, 4), (Turtle, 1))

    def born_bosses(self):
        return [Valross(y=300, isboss=True, field=self.f)]
