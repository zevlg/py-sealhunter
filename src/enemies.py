# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

import pygame
from pygame.locals import *
from random import randint, choice, randrange

from objects import *
from misc import *

class MetaEnemy(type):
    def __init__(cls, name, bases, dict):
        type.__init__(cls, name, bases, dict)

        if name == "Aktivist":
            cls.ADIR = name
        elif name == "Vits":
            cls.ADIR = "Enemies/VitS"
        else:
            cls.ADIR = "Enemies/"+name

        setobjattrs(cls, ENEMIES[name],
                    life=(0,0), boss_life=None,
                    ticks_step=3, speed_range=(10,100),
                    bounty=0, can_press=False, boss_bonus=0,
                    headshot_bonus=0, headshot_multiplier=1,
                    spawn_sounds=[], death_sounds=[])

        snddir = {"Bruns":"brunsal", "Knubbs":"vitsal",
                  "Aktivist":"aktivist", "Bear":"isbjorn"}
        cls.pain_sounds = []
        if snddir.has_key(name):
            _sndn = snddir[name]
            setobjattrs(cls, ENEMIES[name],
                        spawn_sounds=aglob(_sndn+"/spawn*.wav"),
                        death_sounds=aglob(_sndn+"/death*.wav"),
                        pain_sounds=aglob(_sndn+"/hit*.wav"))

class Enemy(AnimateStates, Creature):
    def __init__(self, ss, **kwargs):
        dstate = 'Walking'
        # XXX
        if self.__class__.ADIR == "Aktivist": dstate = 'Running'
        AnimateStates.__init__(self, self.__class__.ADIR, dstate,
                               states_setup=ss,
                               ticks_step=self.__class__.ticks_step)
        setobjattrs(self, kwargs, isboss=False, can_leave_field=False)

        kwargs.update(reflection="enemies" in option("reflections"),
                      opaque=ENEMY_REFLECTION_OPAQUE)

        if self.isboss:
            self.bounty += self.__class__.boss_bonus

        if self.isboss and self.__class__.boss_life:
            _life = self.__class__.boss_life
        else:
            _ssl = self.__class__.life
            _life = _ssl[0] + _ssl[1]*kwargs["field"].level.num
        Creature.__init__(self, _life, **kwargs)
        if "x" not in kwargs:
            self.x -= self.scs.image.get_rect().width

        self.gibbed = False

        # Load up sounds
        self.spawn_sounds = map(load_sound, self.spawn_sounds)
        self.death_sounds = map(load_sound, self.death_sounds)
        self.pain_sounds = map(load_sound, self.pain_sounds)

        # Start the enemy
        self.apply_position()
        self.update_reflection()
        play_rnd_sound(self.spawn_sounds)

    def tick(self, f):
        Creature.tick(self, f)
        if self.gibbed:
            # Enememy has been eliminated
            return

        if self.is_alive():
            self.apply_speed()

            # Game Over, so remove enemy from the field
            if self.x > FLIMIT_WIDTH[1]:
                f.remove(self)
                if not self.can_leave_field:
                    f.game_is_over(self)
                return
        else:
            # Enemy is dead
            self.apply_motion()
            if self.is_quiescent() \
                   and self.state_idx == self.state_frames()-1:
                # Dead, quiescent and all frames are show
                f.remove(self)
                f.draw_static(self.scs.image, *self.scs.rect.topleft)
                return

        AnimateStates.tick(self, f)
        self.press_players(f)

        self.apply_position()
        self.update_reflection()

        # Update the layer
        # Changing layer is a heavy operation!
        if abs(self.y - self.scs._layer) > 2:
            f.change_layer(self.scs, self.y)

    def press_players(self, f):
        if not self.can_press: return

        def pcollides(player):
            return self.scs.rect.collidepoint(player.scs.rect.center)

        for pp in filter(pcollides, f.players):
            # Start pushing the player
            pp.state_start("Sitting")
            pp.x_speed = (pp.x_speed+self.x_speed)/3.0

    def hit(self, prj, damage, head=False):
        """Enemy has been hited."""
        if 'enemy' in option("debug"):
            debug("Enemy: %s Hit, damage=%d, totalhit=%d, head=%d, life=%d"
                  %(self, damage, self.total_hit,head, self.life))

        # Spilt a blood on hit
        if prj.is_bullet():
            zrs = min(-prj.angle * 33, 8)
            self.field.add(*blood(n=3, xrs=(-6,-3), zrs=(zrs-1, zrs+1),
                                  w=(1,6), h=(1,3),
                                  x=prj.x, y=self.y, z=self.y-prj.y))
##        if head and prj.is_bullet():
##            # Spill some blood particles
##            zv = self.y - prj.y
##            self.field.add(*blood(n=3, xrs=(-6,-5),zrs=(0,2),
##                                  w=(2,6), h=(1,3),
##                                  x=prj.x,y=self.y,z=zv))

        Creature.hit(self, prj, damage, head=head)

    def gib(self, sound=None):
        """Mark enemy as gibbed."""
        self.gibbed = True
        self.field.remove(self)
        play_sound(choice(aglob("misc/gib*.wav")))

class WithYSpeed:
    def __init__(self, ykrange):
        self.yrspee = rand_speed(*ykrange)
        self.init_speeds(apply(rand_speed, self.speed_range)())

    def init_speeds(self, speed=None, yk=None):
        if speed is not None: self.speed = speed
        if yk is None: yk = self.yrspee()

        self.y_speed = yk*self.speed
        self.x_speed = self.speed-abs(self.y_speed)

    def ykoeff(self):
        return 1.0*self.y_speed/self.speed

    def correct_position(self, f, yk=None):
        """Correct the position according to field's boundaries."""
        fhlimit = f.level.rr
        if self.y > fhlimit[1]:
            self.y = fhlimit[1]
            self.init_speeds(yk=yk)
        elif self.y < fhlimit[0]:
            self.y = fhlimit[0]
            self.init_speeds(yk=yk)

class Bruns(Enemy, WithYSpeed):
    __metaclass__ = MetaEnemy
    def __init__(self, **kwargs):
        # all numbers are VERY GOOD
        ss = {
            "Walking": {
            0:[(8,13), (7,0), (14,6)], 1:[(8,13), (6,0), (13,6)],
            2:[(7,14), (5,0), (11,6)], 3:[(9,13), (7,0), (14,6)],
            4:[(8,13), (7,0), (14,6)], 5:[(8,13), (9,0), (16,6)]},

            "StartCrawl": {
            "keep_last": True, "ticks_step": 3,
            0:[(6,14),(5,0),(11,5)], 1:[(6,14), (5,0), (11,5)],
            2:[(7,14),(8,0),(14,5)], 3:[(7,14), (11,0),(17,5)],
            4:[(8,12),(12,0),(18,5)], 5:[(8,7),(14,0),(21,5)],
            6:[(7,8),(14,3),(19,9)], 7:[(8,6),(15,1),(20,7)],
            8:[(9,5),(16,0),(21,6)], 9:[(9,5),(16,0),(21,6)],
            10:[(9,7),(14,0),(20,5)], 11:[(9,7),(14,0),(20,5)]},

            "Crawl": {
            "ticks_step": 5,
            0:[(8,7),(13,0),(19,5)], 1:[(6,7),(12,0),(17,5)],
            2:[(8,7),(13,0),(19,5)], 3:[(9,7),(14,0),(20,5)]},

            "CrawlDeath": {
            "keep_last":True, "ticks_step": 3,
            0:(12,11), 1:(16,19), 2:(20,18), 3:(19,21),
            4:(13,17), 5:(16,12), 6:(9,5), 7:(9,5)},

            "KrossatHuvud": {
            "keep_last":True, "ticks_step": 3,
            0:(8, 5), 1:(8, 7), 2:(8, 5),
            3:(8, 5), 4:(8, 4), 5:(8, 4),
            6:(8, 4)},

            "HeadKick": {
            "keep_last":True, "ticks_step": 3,
            0:(8,12), 1:(12, 17), 2:(12, 14),
            3:(8, 13), 4:(8, 13), 5:(8, 10),
            6:(9, 7), 7:(9, 7), 8:(9, 5),
            9:(9, 5), 10:(9, 5)},

            "Death1": {
            "keep_last": True, "ticks_step": 3,
            0:(19,19), 1:(29,19), 2:(43,16), 3:(56,13),
            4:(56, 5), 5:(56, 5), 6:(56, 5), 7:(56, 5)},

            "Death2": {
            "keep_last": True, "ticks_step": 3,
            0:(19,19), 1:(30,19), 2:(44,17), 3:(48,24),
            4:(56,15), 5:(57,17), 6:(57,5), 7:(57,5),
            8:(57,5)},

            "Death3": {
            "keep_last": True, "ticks_step": 3,
            0:(11,14), 1:(6,14), 2:(7, 14), 3:(7,14),
            4:(8, 12), 5:(8, 7), 6:(7,  8), 7:(8, 6),
            8:(9,  5), 9:(9, 5), 10:(9, 5)}
            }

        Enemy.__init__(self, ss, **kwargs)
        WithYSpeed.__init__(self, kwargs.get("ykrange", (-0.3, 0.3)))

        self.ticks_step = int((self.speed_range[1]+0.2)/self.speed)
        self.meat_sounds = map(load_sound, aglob("misc/meat*.wav"))

    def hit(self, prj, damage, head=False):
        Enemy.hit(self, prj, damage, head=head)

        if self.state == "Walking" and self.life <= 10 \
               and prj.is_bullet() and not head:
            # Critical wound
            self.state_start("StartCrawl")
            self.init_speeds(0, 0)

    def tick(self, f):
        if self.is_alive() and self.total_hit > self.slife/2:
            # This is painfull for brunsal
            play_rnd_sound(self.pain_sounds)

        if self.state == "Walking":
            self.correct_position(f)
            if self.ticks % randint(FPS/f.level.num, FPS) == 0:
                self.init_speeds()

        if self.state == "StartCrawl" \
               and self.state_idx == self.state_frames()-1:
            self.state_start("Crawl")
            self.init_speeds(0.2, 0)
        elif self.state == "Crawl" and \
                 self.state_ticks % randint(1, 20) == 0:
            # Draw a blood tray
            bw = randint(1,2)
            bh = 1 if bw == 1 else randint(1,3)
            bt = gen_blood(bw, bh)
            f.draw_blood(bt, self.x, self.y-bh/2)

        Enemy.tick(self, f)

    def die(self, prj):
        """Bruns dies by fatal projectile PRJ."""
        Creature.die(self, prj)
        self.x_speed = self.y_speed = 0

        # Two special deaths, headkick and krossathuvud
        if prj == "KrossatHuvud":
            self.life = 0
            self.state_start("KrossatHuvud")
            play_rnd_sound(self.meat_sounds)
            # No need for death sound, so return
            return
        elif prj == "HeadKick":
            self.life = 0
            self.state_start("HeadKick")
        elif self.life < -100:
            # GIB
            self.gib_gen(("Blood/Gib/SealHead", 18),
                         (choice(tglob("Blood/Gib/SealPart*")), 4),
                         (choice(tglob("Blood/Gib/SealTorso*")), 8))

##            self.field.add(*blood(n=10, xrs=(-7,-3),zrs=(2,4),
##                                  yrs=(-0.5,0.5), w=(2,6), h=(1,3),
##                                  x=self.x, y=self.y, z=18))

            if choice([0,1,2]) == 1 and self.life < -200:
                _pools = tglob("Blood/Splat/splat_*.png")
                _pt = load_texture(choice(_pools))
                _pt.set_alpha(randint(200, 240))
                _w, _h = _pt.get_size()
                self.field.draw_blood(_pt, self.x-_w/2, self.y-_h/2)

            return Enemy.gib(self)

        elif self.state in ["StartCrawl", "Crawl"]:
            self.state_start(choice(["CrawlDeath", "HeadKick"]))
            if self.state == "HeadKick":
                # Spill some blood
                self.field.add(*blood(n=2, xrs=(-1,1),zrs=(2,6),
                                      w=(1,3),h=(2,4),
                                      x=self.x+5,y=self.y,z=8))

        elif self.is_headshot(prj):
            self.state_start(choice(["Death1", "Death2"]))
        else:
            self.state_start("Death3")

        play_rnd_sound(self.death_sounds)

def BrunsLinear(**kwargs):
    kwargs.update(ykrange=(0,0))
    return Bruns(**kwargs)

class Knubbs(Enemy):
    __metaclass__ = MetaEnemy
    def __init__(self, **kwargs):
        # all numbers are VERY GOOD
        ss = {
            "Walking": {
            "ticks_step": 3,
            0:[(0, 20), (35,3), (41, 7)],
            1:[(-2, 23), (33,6), (39, 10)],
            2:[(-4, 24), (31,7), (37, 11)],
            3:[(-2, 23), (33,6), (39, 10)]},

            "Death1": {
            "ticks_step": 3,
            0:(0,20), 1:(0,20),
            2:(0,19), 3:(0,18), 4:(0,17),
            5:(0,17), 6:(0,16), 7:(0,16),
            8:(0,16), 9:(0,16), 10:(0,16),
            11:(0,16)},

            "Death2": {
            "ticks_step": 3,
            0:(0,21), 1:(0,27), 2:(0,31),
            3:(0,35), 4:(0,35), 5:(0,35),
            6:(0,30), 7:(1,25), 8:(3,19),
            9:(4,17), 10:(4,17)},

            "Stopped": {
            "ticks_step":8,
            0:[(0,20), (35,3), (41,7)],
            1:[(0,20), (35,3), (41,7)]}}

        Enemy.__init__(self, ss, **kwargs)
        self.x_speed = self.speed_range[0]

    def die(self, prj):
        Creature.die(self, prj)
        self.x_speed = 0
        if prj.is_bullet():
            if self.total_hit >= self.slife/2:
                self.state_start("Death2")
            else:
                self.state_start("Death1")
        else:
            self.state_start("Death1")
        play_rnd_sound(self.death_sounds)

    def tick(self, f):
        Enemy.tick(self, f)
        if self.state == "Walking" and \
           self.life < self.slife and \
           self.state_ticks % 280 == 279:
            self.state_start("Stopped")
            self.x_speed = 0
        elif self.state == "Stopped":
            if self.state_ticks == 150:
                self.state_start("Walking")
                self.x_speed = self.speed_range[0]
            elif self.life < self.slife:
                # regenerate life
                self.life += 1

class Aktivist(Enemy, WithYSpeed):
    __metaclass__ = MetaEnemy
    def __init__(self, **kwargs):
        ss = {
            "Running": {
            "ticks_step": 3,
            0:[(0,26), (11,0), (19,7)],
            1:[(0,26), (10,0), (18,7)],
            2:[(-3,26), (8,0), (16,7)],
            3:[(-3,26), (8,0), (15,7)]},

            "Death1": {
            "ticks_step": 2,
            0:(14,26), 1:(22,27), 2:(2,27), 3:(2,27),
            4:(2,27), 5:(2,27), 6:(12,25), 7:(18,20),
            8:(24,10), 9:(24,9), 10:(24,8), 11:(24,7)},

            "Death2": {
            "ticks_step": 2,
            0:(3,22), 1:(1,22), 2:(1,22), 3:(1,22),
            4:(1,22), 5:(2,20), 6:(2,20), 7:(0,27),
            8:(0,37), 9:(0,9), 10:(0,6), 11:(0,5)},

            "Death1NoSeal": {
            "ticks_step": 2,
            0:(14,26), 1:(22,27), 2:(2,27), 3:(2,27),
            4:(2,27), 5:(2,27), 6:(12,25), 7:(18,20),
            8:(24,10), 9:(24,9), 10:(24,8), 11:(24,7)},

            "Death2NoSeal": {
            "ticks_step": 2,
            0:(3,22), 1:(1,22), 2:(1,22), 3:(1,22),
            4:(1,22), 5:(2,20), 6:(2,20), 7:(0,27),
            8:(0,37), 9:(0,9), 10:(0,6), 11:(0,5)},

            "RunningNoSeal": {
            "ticks_step": 2,
            0:[(0,26),(11,0),(19,7)], 1:[(0,26),(12,0),(17,7)],
            2:[(-3,26),(8,0),(14,7)], 3:[(-5,26),(6,0),(12,7)],
            4:[(0,26),(10,0),(17,7)], 5:[(0,27),(10,0),(16,8)],
            6:[(-3,27),(7,0),(13,8)], 7:[(-5,27),(5,0),(11,8)],
            8:[(0,27),(10,0),(16,8)], 9:[(0,27),(10,0),(16,8)],
            10:[(-3,27),(7,0),(13,8)], 11:[(-5,27),(5,0),(11,8)],
            12:[(0,27),(10,0),(16,8)], 13:[(0,27),(10,0),(16,8)],
            14:[(-3,26),(7,0),(14,7)], 15:[(-5,27),(6,1),(13,8)],
            16:[(0,26),(11,0),(18,7)], 17:[(0,27),(10,0),(17,7)],
            18:[(-3,28),(6,0),(13,8)], 19:[(-6,28),(3,0),(10,8)],
            20:[(0,28),(10,0),(16,8)], 21:[(0,28),(10,0),(16,8)],
            22:[(-3,28),(7,0),(13,8)], 23:[(-6,28),(4,0),(10,8)]}
            }
        Enemy.__init__(self, ss, **kwargs)
        WithYSpeed.__init__(self, (-0.4, 0.4))
        self.ticks_step = int((self.speed_range[1]+0.4)/self.speed)

        self.has_seal = True
        self.hit_sounds = self.pain_sounds

    def tick(self, f):
        Enemy.tick(self, f)

        # Correct the position
        if self.is_alive():
            self.correct_position(f)

        if self.state is "RunningNoSeal":
            if self.state_idx == 6:
                play_sound("aktivist/panic.wav")
            elif self.state_idx == 0 and self.state_ticks > 1:
                # Cycle on 4 last positions
                self.x_speed, self.y_speed = self.speed_range[1], 0
                self.ticks_step = 1

                self.state_idx = 20
                self.update()
                self.apply_position()
                self.update_reflection()
            # spilt some blood while running w/o seal
            if self.state_ticks < 25 or randint(1,10)==10:
                self.field.add(*blood(n=1, xrs=(-0.5,0),zrs=(-1,0.2),
                                      w=(2,4), h=(1,4),
                                      x=self.x+5,y=self.y,z=12))

        if self.state is "Running" and self.ticks % FPS == 0:
            self.init_speeds()

        if not self.is_alive() and self.has_seal and self.state_idx == 5:
            # Drop the seal
            self.has_seal = False
            vits = Vits(x=self.x+4, y=self.y, field=f)
            vits.scs._layer = self.scs._layer + 1
            f.add(vits)

        if self.state == "Death2" and self.state_idx == 0:
            # Head-off death, so spilt some blood
            self.field.add(*blood(n=4, xrs=(-1,1),zrs=(2,5),
                                  w=(1,3),h=(2,4),
                                  x=self.x+5,y=self.y,z=20))

    def hit(self, prj, damage, head=False):
        has_fp = hasattr(self, "fatal_projectile")
        Enemy.hit(self, prj, damage, head=head)

        # Record the head bullet
        if 'enemy' in option("debug"):
            debug("Enemy: aktivist head=%s"%head)
        if not has_fp and hasattr(self, "fatal_projectile") \
               and prj.is_bullet() and head and damage > self.slife/2:
            if 'enemy' in option("debug"):
                debug("Enemy: HEADSHOT!")
            self.fatal_projectile.headshoted_aktivist = True

        seal_rect = Rect(self.x+4, self.y-18, 14, 7)
        if 'enemy' in option("debug"):
            debug("Enemy: Aktivist seal_rect=%s, prj=%d/%d"
                  %(seal_rect, prj.x, prj.y))

        if self.has_seal and prj.is_bullet() \
               and seal_rect.collidepoint(prj.x, prj.y):
            self.has_seal = False
            self.can_leave_field = True
            if self.is_alive():
                self.state_start("RunningNoSeal")
                play_sound("aktivist/spout.wav")
            else:
                # Start new state from same position
                self.state = self.state + "NoSeal"
                self.update()
                self.apply_position()

            # Blood from the seal
            self.field.add(*blood(n=4, xrs=(-10,-4), zrs=(-0.5,1),
                                  x=prj.x, y=self.y, z=self.y-prj.y))

    def die(self, prj):
        Creature.die(self, prj)
        # stop the creature
        self.init_speeds(0)

        if self.life < -1.5*self.slife:
            # GIB
            self.gib_gen(("Blood/Gib/AktivistHead", 26),
                         (choice(tglob("Blood/Gib/AktivistPart*")), 8),
                         (choice(tglob("Blood/Gib/AktivistTorso*")), 20))

            self.field.add(*blood(n=10, xrs=(-7,-3),zrs=(2,4),
                                  yrs=(-0.5,0.5), w=(2,6), h=(1,3),
                                  x=self.x, y=self.y, z=self.y-prj.y))
            return Enemy.gib(self)

        # Grenades and Flunk rockets always kills the seal
        if not prj.is_bullet():
            self.has_seal = False

        # State postfix
        _sps = "NoSeal" if not self.has_seal else ""
        _sts = ["Death1%s"%_sps, "Death2%s"%_sps]
        if hasattr(prj, "headshoted_aktivist"):
            self.state_start(_sts[1])
        elif self.is_headshot(prj):
            self.state_start(choice(_sts))
        else:
            self.state_start(_sts[0])

        if self.state == _sts[1]:
            self.gib_gen(("Blood/Gib/AktivistHead", 26))
        play_rnd_sound(self.death_sounds)

class Vits(Enemy):
    __metaclass__ = MetaEnemy
    def __init__(self, **kwargs):
        ss = {
            "Walking": {
            0: [(0,6),(0,0),(14,6)],
            1: [(0,6),(0,0),(14,6)],
            2: [(-2,7),(0,0),(12,7)],
            3: [(-2,8),(0,0),(12,8)],
            4: [(-3,7),(0,0),(14,7)],
            5: [(-3,6),(0,0),(14,6)]},

            "Nosa": dict([(i,[(0,6),(0,0),(14,6)]) for i in range(37)]),

            "Death1": {
            "ticks_step": 2,
            0:(0,6), 1:(0,12), 2:(0,18),
            3:(0,21), 4:(0,19), 5:(0,14),
            6:(8,3), 7:(8,3), 8:(8,3)},

            "Death2": {
            "ticks_step": 2,
            0:(44,8), 1:(71,12), 2:(87,11),
            3:(67,7), 4:(67,7), 5:(67,7)}
            }

        Enemy.__init__(self, ss, **kwargs)
        self.gibs = map(load_texture, tglob("Enemies/VitS/Gib/gib*.png"))
        self.x_speed = apply(rand_speed, self.speed_range)()
        self.ticks_step = int((self.speed_range[1]+0.50)/self.x_speed)

    def nosa(self):
        """Stop for a moment and start looking around."""
        if self.is_alive() and self.state != "Nosa":
            self.was_x_speed = self.x_speed
            self.x_speed = 0
            self.state_start("Nosa")

    def tick(self, f):
        Enemy.tick(self, f)
        if self.state == "Nosa" and self.state_idx == self.state_frames()-1:
            self.x_speed = self.was_x_speed
            self.state_start("Walking")

        if self.state == "Walking" and \
               self.state_ticks - randint(0,500) == 150:
            self.nosa()
        elif self.isboss and self.state_ticks % 100 == 99 \
                 and choice(range(3)) == 1:
            self.nosa()

    def die(self, prj):
        Creature.die(self, prj)

        if self.isboss:
            # always GIB for the boss
            self.life = -10*self.slife

        self.x_speed = 0
        if self.life < -5*self.slife:
            # GIB
            gibimg = choice(self.gibs)
            gibrect = gibimg.get_rect()
            _srect = self.scs.rect
            xoff = (_srect.width-gibrect.width)/2
            yoff = (_srect.height-gibrect.height)/2
            self.field.draw_static(gibimg, _srect.x+xoff, _srect.y+yoff)

            gparts = [("Blood/Gib/VitSealHead", 4)]
            if self.gibs.index(gibimg) in [0, 2, 3, 5, 6]:
                gparts.append((choice(["Blood/Gib/VitSealTorso1",
                                       "Blood/Gib/VitSealSpringd"]), 3))
            self.gib_gen(*gparts)
            return Enemy.gib(self)

        if prj.is_bullet():
            self.state_start(choice(["Death1", "Death2"]))
        else:
            # Non-gib grenade damage
            self.state_start("Death1")

class Pingvin(Enemy, WithYSpeed):
    __metaclass__ = MetaEnemy
    dive_multiplier = 2.85
    def __init__(self, **kwargs):
        ss = {
            "Walking": {
            "ticks_step": 3,
            0:[(2, 21), (2,0), (8, 7)],
            1:[(3, 21), (3,0), (10, 7)],
            2:[(4, 21), (4,0), (12, 7)],
            3:[(3, 21), (3,0), (10, 7)]},

            "Glide": {
            "keep_last": True,
            0:[(2,21),(8,1),(14,9)],
            1:[(-2,19), (10,8),(16,8)],
            2:[(-7,13), (15,1),(22,7)],
            3:[(-7,10), (17,1),(23,7)]},

            "Death1": {
            0:(28,24), 1:(47,26), 2:(63,15),
            3:(54,6), 4:(54,6), 5:(54,5), 6:(54,6)},

            "Death2": {
            0:(2,21), 1:(3,21), 2:(5,22), 3:(7,25),
            4:(6,21), 5:(2,21), 6:(-2,17), 7:(-5,15),
            8:(-4,12), 9:(-4,10), 10:(-4,10), 11:(-4,10)},

            "GlideDeath1": {
            "keep_last": True,
            0:(-7,10)},

            "GlideDeath2": {
            "keep_last": True,
            0:(-7,10)},

            "GlideDeath3": {
            "keep_last": True,
            0:(-7,10), 1:(-7,10), 2:(-7,10),
            3:(-7,10), 4:(-7,10)},

            "GlideDeath4": {
            "keep_last": True,
            0:(-7,10), 1:(-7,10), 2:(-7,10),
            3:(-7,10), 4:(-7,10)},

            "GlideDeath5": {
            "keep_last": True,
            0:(-7,10), 1:(-7,10), 2:(-7,10),
            3:(-7,10), 4:(-7,10), 5:(-7,10)},

            "RullDeathRull": {
            0:(-11,5), 1:(-11,6), 2:(-14,8), 3:(-11,8),
            4:(-11,4), 5:(-11,5), 6:(-13,7), 7:(-12,7)},

            "RullDeathSnurr": {
            0:(-14,13), 1:(-15,11), 2:(-13,13), 3:(-14,12),
            4:(-13,13), 5:(-15,12), 6:(-15,12), 7:(-15,13)},

            "RullDeathStart": {
            0:(-7,10), 1:(-7,12), 2:(-14,11), 3:(-14,11)}
            }
        Enemy.__init__(self, ss, **kwargs)
        WithYSpeed.__init__(self, (-0.3, 0.3))

        self.glide_speeds = (1.74, 3.14)
        self.quack_sounds = aglob("pingvin/quack*.wav")
        self.quack_ticks = [randint(1,3), randint(15,25)];

    def die(self, prj):
        Creature.die(self, prj)
        if self.life < -2.0*self.slife:
            self.gib_gen(("Blood/Gib/PingvinHead", 26),
                         (choice(tglob("Blood/Gib/PingvinPart*")), 8),
                         (choice(tglob("Blood/Gib/PingvinTorso*")), 20),
                         (choice(tglob("Blood/Gib/Part*")), 8))

##            self.field.add(*blood(n=10, xrs=(-7,-3),zrs=(2,4),
##                                  yrs=(-0.5,0.5), w=(2,6), h=(1,3),
##                                  x=self.x, y=self.y, z=self.y-prj.y))
            # GIB
            return Enemy.gib(self)

        _glideaths = ["RullDeathStart"]+["GlideDeath%d"%i for i in range(1,6)]
        if self.state == "Glide":
            if self.state_idx < self.state_frames()-1:
                # Killed while prepearing to glide
                self.state_start("RullDeathStart")
            else:
                self.state_start(choice(_glideaths))
        elif self.is_headshot(prj):
            self.state_start("Death1")
        else:
            self.state_start("Death2")

    def tick(self, f):
        Enemy.tick(self, f)

        # quack on the spawn
        if self.ticks in self.quack_ticks:
            play_rnd_sound(self.quack_sounds)

        _ruldeaths = ["RullDeathRull", "RullDeathSnurr"]
        if self.state in _ruldeaths and self.is_quiescent() \
               and self.state_idx < self.state_frames()-1:
            f.remove(self)
            f.draw_static(self.scs.image, *self.scs.rect.topleft)
            return

        if self.state == "RullDeathStart" \
           and self.state_idx == self.state_frames()-1:
            self.state_start(choice(_ruldeaths))

        if self.state == "Walking" \
               and self.state_ticks > randrange(200,300):
            self.state_start("Glide")
            self.init_speeds(apply(rand_speed, self.glide_speeds)(),
                             self.ykoeff())

        if self.is_alive():
            # Bounce from the field boundaries
            self.correct_position(f, yk=-self.ykoeff())

class Bear(Enemy):
    __metaclass__ = MetaEnemy
    def __init__(self, **kwargs):
        ss = {
            "Walking": {
            0:[(0,35), (49,5), (58,22)],
            1:[(-3,34), (42,8), (55,21)],
            2:[(-4,34), (41,8), (54,21)],
            3:[(0,35), (45,9), (58,22)],
            4:[(-3,34), (42,8), (55,21)],
            5:[(-4,34), (41,8), (54,21)]},

            "Running": {
            0:[(-3,35), (42,9), (54,21)],
            1:[(-1,35), (44,8), (56,19)],
            2:[(10,35), (55,9), (67,22)],
            3:[(3,35), (47,10), (60,22)],
            4:[(-3,35), (41,9), (54,21)],
            5:[(-3,35), (41,9), (54,21)]},

            "Death": {
            "keep_last":True, "ticks_step": 1,
            0:(0,31), 1:(8,27), 2:(15,22),
            3:(12,20), 4:(12,20), 5:(12,20),
            6:(23,20)}}

        Enemy.__init__(self, ss, **kwargs)
        self.x_fric = 1.5
        self.x_speed = self.speed_range[0]

    def tick(self, f):
        # Bear can enrage when hited
        if self.is_alive() and self.total_hit > 0:
            if self.total_hit > 50:
                # This hit is painfull
                play_rnd_sound(self.pain_sounds)
            self.enrage()

        if self.state == "Death":
            _axs = abs(int(self.x_speed))
            bw = randint(1+_axs, 2+2*_axs)
            bh = randint(1, max(9-_axs,1))
            bt = gen_blood(bw, bh)
            f.draw_blood(bt, self.x+20-_axs, self.y-bh/3)

        Enemy.tick(self, f)

    def press_players(self, f):
        # Bear can butt the player or make him sit
        players = f.players
        pix = self.scs.rect.collidelistall(map(mvo_rect, players))
        pixp = [players[pi] for pi in pix]
        _bh = self.scs.rect.h
        for pl in [players[pi] for pi in pix]:
            if pl.z > _bh:
                # Player in air, do not press
                continue

            if self.is_alive():
                # Bear is butting
                pl.x_speed = self.x_speed*2
                pl.z_speed = self.x_speed
            else:
                Enemy.press_players(self, f)

    def enrage(self):
        """Enrage according to damage."""
        _ssr = self.speed_range
        _lk = (1.0*self.life)/self.slife # life left koeff
        self.x_speed = _ssr[0] + (_ssr[1]-_ssr[0])*((1-_lk)**2)

        if self.x_speed < 1:
            self.ticks_step = 4
        elif self.x_speed < 1.75:
            self.ticks_step = 3
        elif self.x_speed < 2.5:
            self.ticks_step = 2
        elif self.state != "Running":
            self.state_start("Running")
            if self.x_speed < 3.5:
                self.ticks_step = 4
            elif self.x_speed < 4.5:
                self.ticks_step = 3
            elif self.x_speed < 5.5:
                self.ticks_step = 2
            else:
                self.ticks_step = 1

        if 'enemy' in option("debug"):
            debug("Bear enraged: speed=%f, sticks=%d"
                  %(self.x_speed, self.state_ticks))

    def die(self, prj):
        Creature.die(self, prj)
        self.state_start("Death")
        self.x_speed += self.life/500.0
        play_rnd_sound(self.death_sounds)

class Turtle(Enemy):
    __metaclass__ = MetaEnemy
    KRIPER_TICKS = FPS * 2
    HURT_DAMAGE = 300
    def __init__(self, **kwargs):
        ss = {
            "Walking": {
            "ticks_step": 3,
            0:[(0,25),(40,11),(52,21)],
            1:[(-1,25),(40,11),(51,21)],
            2:[(-2,25),(39,11),(51,21)],
            3:[(-1,25),(40,11),(51,21)]},

            "Death1": {
            0:(0,27), 1:(0,33), 2:(1,39),
            3:(2,44), 4:(2,52), 5:(2,27),
            6:(2,24), 7:(2,24), 8:(2,24)},

            "SpringDeath": {
            0:(8,25), 1:(21,25), 2:(21,25),
            3:(21,25), 4:(21,25), 5:(21,25),
            6:(21,25)},

            "KrypaIn": {0:(-2,25)},

            "KryperUt": {
            0:[(-2,25),(38,14),(40,19)],
            1:[(0,25),(41,13),(46,20)],
            2:[(-2,25),(38,12),(47,20)],
            3:[(0,25),(40,11),(52,21)]}
            }
        Enemy.__init__(self, ss, **kwargs)
        self.x_fric = 2.5
        self.x_speed = self.speed_range[0]

        self.hide_damage = self.HURT_DAMAGE

    def hit(self, prj, damage, head=False):
        """Turtle has been hitted by projectile PRJ by DAMAGE.
If HEAD is True, then creature has been headshoted."""
        if "enemy" in option("debug"):
            debug("Enemy: TURTLE hit, prj=%s dmg=%d head=%s"
                  %(prj, damage, head))

        if self.state == "KrypaIn" \
               or (not head and self.y - prj.y > 5):
            if prj.is_bullet():
                prjenergy = prj.energy
                prj.energy = 0
                play_rnd_sound(aglob("padda/*.wav"))
                hframes = 1 + min(int(damage/25), 2)
                self.field.add(Ric(prj.x-1, prj.y, frames=hframes))

                # Create ricocheted bullet with half energy of origin
                if 'bullet' in option('debug'):
                    debug("Bullet: ricco: y=%d, turtle=%s"
                          %(prj.y, self.scs.rect))

                _sry = self.scs.rect.top
                if self.y - prj.y > 10:
                    adeg = (_sry - prj.y)*3 + randint(-5,5)
                    fy = _sry - 1
                else:
                    adeg = (self.y - prj.y)*3 + randint(-5,5)
                    fy = self.y + 1
                if adeg == 0:
                    adeg = 1
                fx = prj.x - int((fy-prj.y)/math.tan(adeg*math.pi/180))
                rbul = Bullet(prj.weapon, self.field, adeg=adeg,
                              fx=fx, fy=fy, ric=True)
                rbul.energy = 1 + prjenergy / 2
                prj.weapon.throw_bullets(self.field, [rbul])

            # Push the turtle back
            if self.state == "KrypaIn":
                if self.x_speed > -2:
                    self.x_speed -= damage/150.0
            return

        self.hide_damage -= damage
        Enemy.hit(self, prj, damage, head)

    def krypain(self):
        self.x_speed = 0
        self.state_start("KrypaIn")
        self.hide_damage = Turtle.HURT_DAMAGE
        self.kryperut_ticks = self.ticks + Turtle.KRIPER_TICKS

    def tick(self, f):
        Enemy.tick(self, f)

        if self.state == "KrypaIn":
            if self.ticks == self.kryperut_ticks:
                # Check that no player is aiming at the turtle
                def player_aiming(p):
                    ay = p.yy() - p.weapon.aim_position
                    return ay > self.scs.rect.top and \
                           ay < self.scs.rect.bottom

                if any(filter(player_aiming, f.players)):
                    self.kryperut_ticks += Turtle.KRIPER_TICKS
                else:
                    self.state_start("KryperUt")
            else:
                self.apply_friction()
        elif self.state == "KryperUt" \
             and self.state_ticks == self.state_frames()-1:
            self.x_speed = self.speed_range[0]
            self.state_start("Walking")

        if self.is_alive() and self.hide_damage <= 0:
            self.krypain()

    def die(self, prj):
        Creature.die(self, prj)
        self.x_speed = 0
        self.state_start("Death1" if prj.is_bullet() else "SpringDeath")

class Valross(Enemy):
    __metaclass__ = MetaEnemy
    NORMAL = 1
    FLIPPED = -1
    def __init__(self, **kwargs):
        ss = {
            "Walking": {
            "ticks_step": 3,
            0:[(0,37),(33,0),(54,15)],
            1:[(0,37),(30,0),(51,15)],
            2:[(0,37),(26,0),(46,15)],
            3:[(0,37),(31,0),(51,15)]},

            "Death": {
            "ticks_step": 10,
            0:(0,37), 1:(0,37), 2:(0,37),
            3:(0,37), 4:(2,37), 5:(2,37),
            6:(2,37), 7:(2,37), 8:(2,37),
            9:(2,37), 10:(9,32), 11:(9,26),
            12:(8,18), 13:(8,18), 14:(8,18),
            15:(9,18), 16:(8,18)},

            "Charge": {0:[(0,32),(42,0),(64,18)]},
            "Rush":{0:[(0,37),(27,0),(52,19)]}
            }
        Enemy.__init__(self, ss, **kwargs)

        self.orient = Valross.NORMAL
        # spawn sound
        play_rnd_sound(aglob("valross/morr*.wav"))
#        self.x_speed = self.speed_range[0]

    def die(self, prj):
        Creature.die(self, prj)
        self.state_start("Death")
        play_sound("valross/death1.wav")

    def hit(self, prj, damage, head=True):
        if damage > 50:
            play_rnd_sound(aglob("valross/hit*.wav"))
        Enemy.hit(self, prj, damage, head)

    def tick(self, f):
        # Can't use Enemy.tick() directly because of check for
        # FLIMIT_WIDTH
        Creature.tick(self, f)
        if self.is_alive():
            self.apply_speed()
            debug("Valross: x=%d (lim=%d)"%(self.x, FLIMIT_WIDTH[1]))
            if self.x > FLIMIT_WIDTH[1]:
                # flip the valross
                debug("Valross: NEED FLIP")
                self.orient = Valross.FLIPPED
                self.x_speed = self.speed_range[0]
                self.state_start("Walking")
            elif self.x < 0:
                debug("Valross: NEED FLIP")
                self.orient = Valross.NORMAL
                self.x_speed = self.speed_range[0]
                self.state_start("Walking")
        else:
            self.apply_motion()
            if self.is_quiescent() \
                   and self.state_idx == self.state_frames()-1:
                # Dead, quiescent and all frames are show
                f.remove(self)
                f.draw_static(self.scs.image, *self.scs.rect.topleft)

        AnimateStates.tick(self, f)
        self.press_players(f)

        self.apply_position()
        self.update_reflection()

        if self.state == "Walking":
            if (self.orient == Valross.NORMAL and self.x > 100) \
               or (self.orient == Valross.FLIPPED \
                   and self.x < FLIMIT_WIDTH[1]-100):
                self.state_start("Charge")
                play_sound("valross/charge.wav")
            elif self.state_idx == 1:
                self.x += self.orient*3.0/self.ticks_step
            elif self.state_idx == 2:
                self.x += self.orient*5.0/self.ticks_step
        elif self.state == "Charge":
            if self.state_ticks == int(1.2*FPS):
                self.state_start("Rush")
                # XXX
                self.x_speed = 12
            else:
                # Drop some sparks from the front
                _xrs = apply(rand_speed, sorted((-self.orient*4, -self.orient*2)))
                _zrs = apply(rand_speed, (2, 3))
                bps = [SparkParticle(randint(1,4), randint(1,4),
                                     x_speed=_xrs(),z_speed=_zrs(),
                                     x=self.x+randint(46,50),
                                     y=self.y+randint(2,6), z=0)
                       for _ in range(3)]
                self.field.add(bps)
##class Valross(Enemy):
##    __metaclass__ = MetaEnemy
##    def __init__(self, **kwargs):
##        ss = {
##            "Walking": {
##            "ticks_step": 3,
##            0:[(0,37),(33,0),(54,15)],
##            1:[(0,37),(30,0),(51,15)],
##            2:[(0,37),(26,0),(46,15)],
##            3:[(0,37),(31,0),(51,15)]},

##            "Death1": {
##            0:(0,37), 1:(0,37), 2:(0,37),
##            3:(0,37), 4:(2,37), 5:(2,37),
##            6:(2,37), 7:(2,37), 8:(2,37),
##            9:(2,37), 10:(9,32), 11:(9,26),
##            12:(8,18), 13:(8,18), 14:(8,18),
##            15:(9,18), 16:(8,18)}
##            }
##        #TODO

