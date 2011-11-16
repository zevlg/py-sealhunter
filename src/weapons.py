# Copyright (C) 2009-2010 by Zajcev Evegny <zevlg@yandex.ru>

from operator import methodcaller as method

import pygame, random
from pygame.locals import *

from objects import *
from misc import *

class MetaWeapon(type):
    def __init__(cls, name, bases, dict):
        type.__init__(cls, name, bases, dict)

        setobjattrs(cls, WEAPONS[name], name=name,
                    price=0, wpn_position=(0,8),
                    aim_position=4, cross_xoffset=40,
                    accuracy_angle=0, bullets_per_shot=1,
                    x_recoil=0, z_recoil=0,
                    damage=0, damage_inc=0,
                    muzzle=None, clip=None, shell=None,
                    clip_size=1, fire_ticks=50,
                    reload_ticks=50, pierce=0)

        # Setup sound files
        snddir = "weapons/%d"%WEAPON_NAMES.index(name)
        setobjattrs(cls, WEAPONS[name],
                    a_fire=aglob(snddir+"/fire*.wav"),
                    a_reload=aglob(snddir+"/reload*.wav"))

        # setup textures
        hndirs = {"Pistol":"USP", "VintageShotgun":"Farfar",
                  "M4":"Colt", "Grenades":"Grenade"}
        wpn = hndirs.get(name, name)
        texdir = "Weapons/Hands/%s"%wpn
        setobjattrs(cls, WEAPONS[name],
                    s_weapon=texdir+"/%s.png"%wpn.lower(),
                    s_fire=tglob(texdir+"/fire_*.png"))
        if os.path.exists("textures/"+texdir+"/reload.png"):
            setattr(cls, "s_reload", texdir+"/reload.png")
        else:
            setattr(cls, "s_reload", None)

class Weapon(pygame.sprite.Group, WithReflection):
    def __init__(self, player):
        self.scs = dirty_sprite()

        pygame.sprite.Group.__init__(self)
        kwargs = dict(reflection="weapon" in option("reflections"),
                      opaque=PLAYER_REFLECTION_OPAQUE)
        WithReflection.__init__(self, **kwargs)

        self.player = player
        self.state = 'Idle'
        self.ticks = self.fire_state = self.reload_state = 0
        self.usage_ticks = 0

        self.x, self.y = self.wpn_position
        self.bullets = self.clip_size

        # Load sound files
        self.a_fire = map(load_sound, self.a_fire)
        self.a_reload = map(load_sound, self.a_reload)

        # Load texture files, substituting colors according to
        # player's skin
        self.s_weapon = self.load_wpn_texture(self.s_weapon)
        self.s_fire = map(self.load_wpn_texture, self.s_fire)
        if self.s_reload:
            self.s_reload = self.load_wpn_texture(self.s_reload)
        else:
            self.s_reload = self.s_weapon

        self.scs.image = self.s_weapon
        self.add(self.scs)

    def load_wpn_texture(self, w):
        return substitute_color(load_texture(w).copy(), PLAYER_SCOLOR,
                                self.player.profile["skin"])

    def weapon_tick(self, f):
        self.ticks += 1
        self.usage_ticks += 1

        if self.state == 'Fire' and self.ticks >= self.fire_ticks:
            self.state = 'Idle'
            self.ticks = 0
            self.scs.image = self.s_weapon
            if self.bullets == 0:
                self.reload(f)

        if self.state == 'Reload':
            if len(self.a_reload) > 1:
                arlen = self.reload_ticks/(len(self.a_reload) - 1)
                if self.ticks % arlen == 0:
                    sndf = self.a_reload[self.ticks/arlen]
                    play_sound(sndf)

            if self.ticks >= self.reload_ticks:
                self.state = 'Idle'
                self.bullets = self.clip_size
                self.ticks = 0
                self.scs.image = self.s_weapon
                self.x, self.y = self.wpn_position

                if self.player.profile["show-hud"]:
                    self.player.hud.update_bullets(self)

        # Move sprite to proper position
        _sp = self.player
        if _sp.state in _sp.states_with_weapon():
            wx, wy = _sp.xx()-self.x, _sp.yy()-self.y
        else:
            wx = wy = -100              # hide
        move_sprite(self.scs, wx, wy)
        # for reflection
        self.z = _sp.z + (self.y - self.scs.rect.h + 1)*1.6
        self.update_reflection()

    def can_fire(self):
        """Return True if weapon can fire right now."""
        if self.state == 'Reload':
            return False
        elif self.state == 'Fire' and self.ticks < self.fire_ticks:
            return False
        if self.bullets < 1:
            return False
        return True

    def show_muzzle(self, f):
        if self.muzzle:
            f.add(Muzzle(self.muzzle, self))

    def drop_shell(self, f):
        if self.shell and "shells" in option("show"):
            sh = Shell(self.shell)
            sh.x, sh.y, sh.z = 0, 0, 10
            sh.x_speed = 1+random.random()/2
            sh.y_speed = random.randint(-17,13)/30.0
            sh.z_speed = 1+random.random()/1.5

            if hasattr(self, "shell_attrs"):
                for k in self.shell_attrs:
                    v = self.shell_attrs[k]
                    if type(v) == type(lambda x: x):
                        v = v()
                    setattr(sh, k, v)

            sh.x += self.player.x
            sh.y += self.player.y
            sh.z += self.player.z
            sh.x_speed += self.player.x_speed/2.0
            sh.y_speed += self.player.y_speed/2.0
            sh.z_speed += self.player.z_speed/2.0

            sh.update_ao()
            f.add(sh)

    def throw_bullets(self, f):
        """Throw bullets to all the creatures."""
        # NOTE:
        #   all bullets have the same .fx and .fy at start
        #   but may have different angles

        # 1. Create a rectangle that occupy all bullets
        # 2. Find creatures that collides with that rectangle
        # 3. Calculate precise hitpoints
        _bullets = [Bullet(self, f) for _ in xrange(self.bullets_per_shot)]
        _bullys = map(lambda x: x.bully(0), _bullets)
        _ymin, _ymax = min(_bullys), max(_bullys)
        _brect = pygame.Rect(0, _ymin, _bullets[0].fx, _ymax - _ymin)
        _crts = filter(lambda x: _brect.colliderect(x.rect), f.creatures())
##        _ocrts = f.creatures()
##        _ocris = _brect.collidelistall(map(lambda c: c.rect, _ocrts))
##        _crts = [_ocrts[i] for i in _ocris]

        if 'weapon' in option("debug"):
            debug("WPN: CREATURES to hit: %s"%_crts)

        # Apply bullet hits if any
        already_niceshot = False
        for bul in _bullets:
            bul.apply_hits(_crts)
            if bul.niceshot:
                already_niceshot = True

        # Earn money for killed creatures
        _deadcrts = filter(lambda c: not c.is_alive(), _crts)
        for cr in _deadcrts:
            self.player.earn_money(cr.bounty)

        self.player.apply_earned_money()

        # 3 or more kills at once is a nice shot!
        if not already_niceshot and len(_deadcrts) > 3:
            if 'weapon' in option('debug'):
                debug("WPN: %d kills by single shot!"%len(_deadcrts))
            self.player.nice_shot(len(_deadcrts)-2)

    def fire(self, f):
        if not self.can_fire(): return False

        if 'weapon' in option('debug'):
            debug("WPN: %s Fire"%self)

        self.state = 'Fire'
        self.bullets -= 1
        self.ticks = 0
        play_sound(self.a_fire[0])#maxtime=self.fire_ticks*1000/FPS)

        self.show_muzzle(f)
        if not (hasattr(self, "shell_attrs") and \
                self.shell_attrs.has_key("disabled")):
            self.drop_shell(f)

        self.throw_bullets(f)
        return True

    def drop_clip(self, f):
        """Drop clip on the field."""
        if self.clip and "clips" in option("show"):
            cl = Clip(self.clip)
            cl.x, cl.y, cl.z = -7, 0, 8
            cl.x_speed = cl.y_speed = cl.z_speed = 0

            if hasattr(self, "clip_attrs"):
                for k in self.clip_attrs:
                    v = self.clip_attrs[k]
                    if type(v) == type(lambda x: x): v = v()
                    setattr(cl, k, v)

            cl.x += self.player.x
            cl.y += self.player.y
            cl.z += self.player.z
            cl.x_speed += self.player.x_speed/2.0
            cl.y_speed += self.player.y_speed/2.0
            cl.z_speed += self.player.z_speed/2.0
            cl.update_ao()
            f.add(cl)

    def reload(self, f):
        """Reload the weapon.
Return True if weapon has been reloaded."""
        if self.state in ['Fire', 'Reload'] or \
               self.bullets == self.clip_size:
            return False

        self.state = 'Reload'
        self.ticks = 0
        play_sound(self.a_reload[0])
        self.scs.image = self.s_reload

        if not (hasattr(self, "clip_attrs") and \
                self.clip_attrs.has_key("disabled")):
            self.drop_clip(f)
        return True

class Pistol(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.clip = self.shell = "Small"

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks == 0: self.x -= 1; self.y += 1
            elif self.ticks == 2: self.x += 1; self.y -= 1

        Weapon.weapon_tick(self, f)

class Magnum(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.shell = "Normal"
        self.shell_attrs = {"disabled": True, "z": 12,
                            "x_speed": rand_speed(1, 1.5),
                            "z_speed": rand_speed(0.5, 1)}

        self.s_reload = pygame.transform.rotate(self.s_fire[1], 90)

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks == 0:
                self.scs.image = self.s_fire[0]
            elif self.ticks == 4:
                self.scs.image = self.s_fire[1]
                self.x, self.y = 8, 15
            elif self.ticks == 8:
                self.scs.image = self.s_fire[2]
                self.x, self.y = 1, 17
            elif self.ticks == 12:
                self.scs.image = self.s_fire[1]
                self.x, self.y = 8, 15
            elif self.ticks == 16:
                self.scs.image = self.s_fire[0]
                self.x, self.y = self.wpn_position
            elif self.ticks == 20:
                self.scs.image = self.s_weapon
                self.x, self.y = self.wpn_position

        Weapon.weapon_tick(self, f)

        if self.state == 'Reload':
            if self.ticks < 2:
                self.x, self.y = 12, 9
            elif self.ticks > 200:
                self.scs.image = self.s_weapon
                self.x, self.y = self.wpn_position

    def reload(self, f):
        reloaded = Weapon.reload(self, f)
        if reloaded:
            # Drop bunch of shells
            for i in range(self.clip_size):
                self.drop_shell(f)
        return reloaded

class MP5(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.clip = "MP5"
        self.shell = "Small"
        self.shell_attrs = {"x_speed": rand_speed(2,2.5)}

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks == 0:
                self.scs.image = self.s_fire[0]
                self.x -= 1; self.y += 1
            elif self.ticks == 1:
                self.scs.image = self.s_fire[1]
                self.x -= 1; self.y += 1
            elif self.ticks == 3:
                self.scs.image = self.s_fire[2]
                self.x += 1; self.y -= 1
            elif self.ticks == self.fire_ticks-1:
                self.x, self.y = self.wpn_position

        Weapon.weapon_tick(self, f)

class Grenades(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.splash_radius = 95
        self.s_fire.append(self.s_weapon)

    def weapon_tick(self, f):
        if self.state == 'Fire':
            self.scs.image = self.s_fire[self.ticks/2]
            if self.ticks < 4:
                self.x -= 2; self.y += 2
            else:
                self.x += 2; self.y += 2

            # Actually launch grenade
            if self.ticks == self.fire_ticks - 1:
                _sp = self.player
                f.add(Grenade(self, x=_sp.x-self.x, y=_sp.y, z=_sp.z+20,
                              x_speed=_sp.x_speed-4, y_speed=_sp.y_speed,
                              z_speed=_sp.z_speed+4))
        else:
            self.x, self.y = self.wpn_position

        Weapon.weapon_tick(self, f)

    def throw_bullets(self, f):
        # Grenade is not a bullet
        pass

class Shotgun(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.shell = "Shotgun"
        self.shell_attrs = {"disabled": True,
                            "x_speed": rand_speed(2,2.67),
                            "z_speed": rand_speed(2,3)}

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks == 3:
                self.scs.image = self.s_fire[0]
                self.x, self.y = self.wpn_position[0]+2, 17
            elif self.ticks == 21:
                self.scs.image = self.s_fire[1]
                self.drop_shell(f)
            elif self.ticks == 35:
                self.scs.image = self.s_fire[2]
            elif self.ticks == self.fire_ticks-1:
                self.scs.image = self.s_weapon
                self.x, self.y = self.wpn_position

        Weapon.weapon_tick(self, f)

        if self.state == 'Reload':
            if self.ticks % 20 == 0:
                play_sound(self.a_reload[0], True)

class MAC10(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.shell = "Small"
        self.shell_attrs = {"x_speed": rand_speed(2,2.5),
                            "z_speed": rand_speed(2,2.5)}
        self.clip = "MAC"
        self.clip_attrs = {"disabled": True,
                           "x_speed": rand_speed(-1,1),
                           "y_speed": rand_speed(-0.2, 0.5)}

        self.s_reload = pygame.transform.rotate(self.s_weapon, 45)

    def reload(self, f):
        reloaded = Weapon.reload(self, f)
        if reloaded:
            # Drop couple of clips
            for xo,yo in [(-4,4),(-6,7)]:
                self.clip_attrs["x"], self.clip_attrs["y"] = xo, yo
                self.drop_clip(f)
        return reloaded

    def fire(self, f):
        fired = Weapon.fire(self, f)
        if fired:
            # Draw muzzles
            for xo,yo in [(0,-2),(2,1)]:
                f.add(Muzzle("small", self,xo=xo,yo=yo))
        return fired

class Flunk(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.splash_radius = 100

        self.a_reload_grenade = self.a_reload[1]
        del self.a_reload[1]

    def weapon_tick(self, f):
        if self.state == 'Fire':
            self.scs.image = self.s_fire[self.ticks/2]

        Weapon.weapon_tick(self, f)

        if self.state == 'Reload' and self.ticks % 30 == 0:
            play_sound(self.a_reload_grenade, True)

    def throw_bullets(self, f):
        """Launch the flunk grenade."""
        _sp = self.player
        f.add(FlunkRocket(self, x=_sp.x-self.x-7, y=_sp.y, z=_sp.z+12,
                          x_speed=_sp.x_speed/2-7.7, y_speed=_sp.y_speed*2,
                          z_speed=_sp.z_speed))

class M4(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.clip = "MP5"
        self.clip_attrs = {"x": -7}
        self.shell = "Normal"
        self.shell_attrs = {"x_speed": rand_speed(2,2.5)}

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks == 0:
                self.scs.image = self.s_fire[0]
                self.x = self.wpn_position[0] + 3
                self.y = self.wpn_position[1] + 2
            elif self.ticks == self.fire_ticks/2:
                self.scs.image = self.s_fire[1]
                self.x = self.wpn_position[0] + 2
        elif self.state == 'Reload':
            self.scs.image = self.s_reload
            self.x, self.y = self.wpn_position[0], 19
        else:
            self.scs.image = self.s_weapon
            self.x, self.y = self.wpn_position

        Weapon.weapon_tick(self, f)

class AWP(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.clip = "AWP"
        self.clip_attrs = {"x": -10}
        self.shell = "AWP"
        self.shell_attrs = {"z_speed": rand_speed(4,6),
                            "x_speed": rand_speed(3,5)}

        self.a_reload.insert(0, load_sound("weapons/8/boltpull.wav"))

        # Create sight sprite
        self.sight = dirty_sprite()
        self.sight._layer = TOP_LAYER
        sscol = self.player.profile["sniper-sight-color"]
        wwsight = pygame.Surface((666, len(sscol))).convert_alpha()
        wwsight.fill((0,0,0,0))
        for i in range(len(sscol)):
            pygame.draw.line(wwsight, sscol[i], (0, i), (666, i))
        self.sight.image = wwsight
        self.add(self.sight)

    def weapon_tick(self, f):
        Weapon.weapon_tick(self, f)

        if self.state in ['Fire', 'Reload']:
            move_sprite(self.sight, -100, -100)
        else:
            _ssr = self.scs.rect
            move_sprite(self.sight, _ssr.x-666, _ssr.y+3)

        if self.state == 'Fire':
            self.x = self.wpn_position[0]
            if self.ticks < 20:
                self.x -= 3

class VintageShotgun(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.shell = "Shotgun"
        self.shell_attrs = {"z_speed":rand_speed(2,3),
                            "x_speed":rand_speed(2,3)}

        self.s_load = map(self.load_wpn_texture,
                          tglob("Weapons/Hands/Farfar/reload_*.png"))
        self.a_load = map(load_sound, aglob("weapons/9/load*.wav"))

    def weapon_tick(self, f):
        if self.state == 'Fire':
            if self.ticks < 30:
                if self.ticks == 0:
                    play_sound(self.a_load[0])
                elif self.ticks == 15:
                    play_sound(self.a_load[1])

                if self.ticks % 3 == 0:
                    self.scs.image = self.s_load[self.ticks/3]

            if self.ticks == 35:
                # Real fire
                self.scs.image = self.s_weapon

                self.bullets -= 2
                play_sound(self.a_fire[0])

                # Apply recoil to player
                self.player.x_speed += self.x_recoil
                self.player.z_speed += self.z_recoil
                if self.player.profile["show-hud"]:
                    self.player.hud.update_bullets(self)

                # Draw muzzle if any
                self.show_muzzle(f)

                # Drop couple of shells
                self.drop_shell(f)
                self.drop_shell(f)

                # Finally throw the bullets
                self.throw_bullets(f)

        Weapon.weapon_tick(self, f)

    def fire(self, f):
        if not self.can_fire(): return False

        self.state = 'Fire'
        self.ticks = 0

        # Avoid recoil
        return False

class Minigun(Weapon):
    __metaclass__ = MetaWeapon
    def __init__(self, *args):
        Weapon.__init__(self, *args)
        self.shell = "Minigun"
        self.shell_attrs = {"z_speed": rand_speed(2, 4),
                            "x_speed": rand_speed(2.5, 4.5)}

        self.s_fire = map(self.load_wpn_texture,
                          tglob("Weapons/Hands/Minigun/heat_*.png"))

        self.a_fire_playing = []
        self.a_winddown = load_sound("weapons/10/winddown.wav")

        self.heatidx = 0

    def inc_heat(self, inc):
        """Increase minigun's heat.
INC can be negative in order to decrease heating."""
        self.heatidx += inc
        if self.heatidx < 0: self.heatidx = 0
        elif self.heatidx > 20: self.heatidx = 20

        # Change fire_ticks according to minigun hastle
        self.fire_ticks = 13-self.heatidx/2

    def play_fire(self, si):
        if si in self.a_fire_playing: return
        self.a_fire_playing.append(si)
        play_sound(self.a_fire[si], loops=-1)
#        self.a_fire[si].play(-1)

    def stop_fire(self, si):
        if si in self.a_fire_playing:
            self.a_fire[si].stop()
            self.a_fire_playing.remove(si)

    def weapon_tick(self, f):
        if self.state in ['Idle', 'Reload']:
            self.x, self.y = self.wpn_position

            # stop fire sounds
            for si in range(len(self.a_fire)):
                self.stop_fire(si)

            if self.ticks == 0 and self.heatidx == 20:
                play_sound(self.a_winddown)

            if self.ticks % 5 == 4:
                self.inc_heat(-1)
        elif self.state == 'Fire':
            if self.ticks == self.fire_ticks/2:
                self.x -= 1
            elif self.ticks == self.fire_ticks-1:
                self.x += 1

            # Compose sounds
            if self.fire_ticks == 6:
                self.play_fire(1)
            elif self.fire_ticks == 4:
                self.play_fire(2)

            if self.ticks % 3 == 2 or self.ticks == self.fire_ticks-1:
                self.inc_heat(1)

            # At maximum heating, minigun can explode!
            if option("minigun-explode") and self.bullets < 50 \
               and self.heatidx == 20 and random.randint(1,100) == 13:
                # Throw all the bullets
                self.fire_ticks = 0
                while self.bullets > 0:
                    self.player.tick(f)

        Weapon.weapon_tick(self, f)
        self.scs.image = self.s_fire[self.heatidx]
