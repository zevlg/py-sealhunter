# Copyright (C) 2009-2010 by Zajcev Evegny <zevlg@yandex.ru>

import pygame, math

from random import randint
from constants import *
from misc import *
from enemies import *

class LevelSplash(pygame.sprite.DirtySprite):
    def __init__(self, lname):
        pygame.sprite.DirtySprite.__init__(self)
        self.ticks = 0

        _sfont = load_font('trebuc.ttf', 32)
        _sfont.set_bold(True)

        _srsrect = _sfont.render(lname, True, (255,255,255)).get_rect()
        sprite_image(self, pygame.Surface((_srsrect.w+2,_srsrect.h+2)))
        sprite_center(self, (320, 100))

        _si = self.image
        _si.set_alpha(0)
        _si.blit(load_texture("Misc/backdrop.png"), (0,0), self.rect)
        _ltf = _sfont.render(lname, True, (255,255,255))
        for _place in [(i,j) for i in [0,2] for j in [0,2]]:
            _si.blit(_ltf, _place)
        _si.blit(_sfont.render(lname, True, (60,60,120)), (1, 1))

    def tick(self, f):
        self.ticks += 1

        if self.ticks < 52: self.image.set_alpha(self.ticks*5)
        else: self.image.set_alpha(520-self.ticks*5)
        self.dirty = 1
        if self.ticks == 104:
            f.remove(self)
            # Actually start the level
            f.level.start()

class Level:
    def __init__(self, f, num, **kwargs):
        self.f = f
        self.num = num

        # Field bounds for this level
        self.rr = (200,400) if len(f.players) < 2 else (180,420)

        setobjattrs(self, kwargs, name="Level %d"%self.num,
                    level_ticks=LEVEL_TICKS, no_splash=False,
                    start_enemies=[], start_boss=[],
                    boss_alone=False, gen_cheap_enemies=False)

        self.ticks = 0
        self.started = self.finished = False
        self.seen_bosses = False
        
        self.enemies = [dict(enemy=e, togo=n+int(0.85*n*(len(f.players)-1)),
                             ticks=-1) for (e,n) in self.start_enemies]

        if self.no_splash:
            self.start()
        else:
            f.add(LevelSplash(self.name), layer=TOP_LAYER)

    def start(self):
        if 'level' in option("debug"):
            debug("Level: Level %d started!"%self.num)
        self.started = True
        for enemy in self.enemies:
            enemy["origtogo"] = enemy["togo"]
            self.gen_next_enemy(enemy)

    def born_bosses(self):
        """Start the boss for this level."""
        def bboss((bclas, bparams)):
            bparams.update(field=self.f, isboss=True)
            return bclas(**bparams)
        self.seen_bosses = True
        return map(bboss, self.start_boss)

    def gen_next_enemy(self, enemy):
        if enemy["togo"] > 0:
            ttg = max(self.level_ticks - self.ticks, 0)
            bpt = int(1.0*ttg/enemy["togo"])
            enemy["ticks"] = self.ticks + 1 + randint(bpt/2, bpt)
            enemy["togo"] -= 1
        else:
            if self.gen_cheap_enemies:
                # Level with turtle
                bpt = self.level_ticks/enemy["origtogo"]
                enemy["ticks"] = self.ticks + 1 + randint(bpt, bpt+bpt/2)
            else:
                enemy["ticks"] = -1

        if 'level' in option("debug"):
            debug("Level: enemy gen %s"%enemy)

    def tick(self, f):
        for e in self.enemies:
            if self.ticks == e["ticks"]:
                enemy = e["enemy"](y=randint(*self.rr), field=f)
                if self.seen_bosses and self.gen_cheap_enemies:
                    # Level with turtles, constantly generate cheap
                    # enemies when turtles are creaping
                    enemy.bounty /= 10
                    enemy.headshot_bonus /= 10

                f.add(enemy)
                self.gen_next_enemy(e)

        self.ticks += 1

        if not self.seen_bosses and self.ticks >= self.level_ticks:
            # Time to born the bosses ?
            if not self.boss_alone or not self.f.creatures(Enemy, all=True):
                f.add(*self.born_bosses())
        elif self.seen_bosses:
            # Check all bosses are dead to finish the level
            bosses = filter(lambda e: e.isboss,
                            self.f.creatures(Enemy, all=True))
            if not bosses:
                self.finished = True

def new_level(f, num, empty=False):
    """Create new standard level."""
    kwargs = {}
    if not empty:
        enemies = [[(BrunsLinear, 29)],
                   [(Bruns, 16), (Aktivist, 9)],
                   [(Bruns, 20), (Aktivist, 13), (Pingvin, 12)],
                   [(Bruns, 25), (Aktivist, 15), (Pingvin, 13),
                    (Knubbs, 3)],
                   [(Bruns, 30), (Aktivist, 16), (Pingvin, 15),
                    (Knubbs, 4), (Bear, 2)],
                   []]
        kwargs["start_enemies"] = enemies[num-1]
        kwargs["boss_alone"] = num in [2,3,5]

        # bosses
        _rr = (200,400) if len(f.players) < 2 else (180,420) # XXX
        _bys = [300] if len(f.players) < 2 else [250, 350]
        boss = [[(Knubbs, {"y":290})],
                [(Pingvin, {"y":randint(*_rr)}) for _ in range(9)],
                [(Bear, {"y":by}) for by in _bys],
                [(Turtle, {"y":by}) for by in _bys],
                [(Valross, {"y":300})],
                [(Vits, {"y":300})]]
        kwargs["start_boss"] = boss[num-1]

    # Level's specifics
    if num == 4:
        kwargs.update(gen_cheap_enemies=True)
    elif num == 6:
        kwargs.update(name="Last seal on the planet", level_ticks=1)

    return Level(f, num, **kwargs)

class Level1(Level):
    num = 1
    def __init__(self, f):
        Level.__init__(self, f, (BrunsLinear, 29))

    def born_bosses(self):
        return [Knubbs(y=290, isboss=True, field=self.f)]

class Level2(Level):
    num = 2
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 16), (Aktivist, 9))
        self.boss_alone = True

    def born_bosses(self):
        """8 Pingvins as booses."""
        return [Pingvin(y=randint(*self.rr), isboss=True, field=self.f)
                for _ in range(9)]

class Level3(Level):
    num = 3
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 20), (Aktivist, 13), (Pingvin, 12))
        self.boss_alone = True

    def born_bosses(self):
        """Single or couple of bears."""
        _bys = [300] if len(self.f.players) < 2 else [250, 350]
        return [Bear(y=by, isboss=True, field=self.f) for by in _bys]

class Level4(Level):
    num = 4
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 25), (Aktivist, 15),
                       (Pingvin, 13), (Knubbs, 3))

    def born_bosses(self):
        """Single or couple of turtles."""
        _tys = [300] if len(self.f.players) < 2 else [250, 350]
        return [Turtle(y=ty, isboss=True, field=self.f) for ty in _tys]

class Level5(Level):
    num = 5
    def __init__(self, f):
        Level.__init__(self, f, (Bruns, 30), (Aktivist, 16),
                       (Pingvin, 15), (Knubbs, 4), (Bear, 2))
        self.boss_alone = True

    def born_bosses(self):
        return [Valross(y=300, isboss=True, field=self.f)]

class LevelFinal(Level):
    num = 6
    def __init__(self, f):
        Level.__init__(self, f)
        self.level_ticks = 100

    def born_bosses(self):
        return [Vits(y=300, isboss=True, field=self.f)]
