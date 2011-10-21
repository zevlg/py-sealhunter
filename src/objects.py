# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

import pygame, math
from random import randint, choice
from operator import sub
from os.path import basename

from misc import *
from constants import *

class SHobj:
    def __init__(self):
        """Object of physical world of SealHunter."""
        self.x = self.y = self.z = 0.0  # position
        self.x_speed = self.y_speed = self.z_speed = 0.0 # speeds

        # Additional friction and bouncing factor
        self.x_fric = self.y_fric = 1.0
        self.bouncing = 3

    def xx(self): return round(self.x)
    def yy(self): return round(self.y-self.z)
    def zz(self): return round(self.z)

    def apply_xfric(self):
        """Apply friction on x axis."""
        # Air has no friction
        if self.z != 0: return

        if self.x_speed < 0:
            self.x_speed += ICE_XFRIC*self.x_fric
            if self.x_speed > 0: self.x_speed = 0
        elif self.x_speed > 0:
            self.x_speed -= ICE_XFRIC*self.x_fric
            if self.x_speed < 0: self.x_speed = 0

    def apply_yfric(self):
        """Apply friction on y exis."""
        # Air has no friction
        if self.z != 0: return

        if self.y_speed < 0:
            self.y_speed += ICE_YFRIC*self.y_fric
            if self.y_speed > 0: self.y_speed = 0
        elif self.y_speed > 0:
            self.y_speed -= ICE_YFRIC*self.y_fric
            if self.y_speed < 0: self.y_speed = 0

    def apply_friction(self):
        """Apply both X and Y axis frictions."""
        self.apply_xfric()
        self.apply_yfric()

    def apply_speed(self):
        """Change object position according to its speeds."""
        self.x += self.x_speed
        self.y += self.y_speed
        self.z += self.z_speed

        if self.z > 0:
            # G acceleration
            self.z_speed -= G_ACCEL
        else:
            # Possible bounce
            self.z = 0.0
            if self.z_speed < -self.bouncing*G_ACCEL:
                self.z_speed = -(self.z_speed/2)
            else:
                self.z_speed = 0.0

    def apply_motion(self):
        """Apply speed and friction."""
        self.apply_speed()
        self.apply_friction()

    def is_quiescent(self):
        """Return True if object is in quiescent state."""
        return self.x_speed == 0 and self.y_speed == 0 \
               and self.z_speed == 0 and self.z == 0

def setobjattrs(obj, kwargs, **defaults):
    """For OBJ set ANAMES attributes that are in KWA."""
    for k in defaults:
        setattr(obj, k, defaults[k])    # default value
        if kwargs.has_key(k):
            setattr(obj, k, kwargs[k])

class WithReflection:
    """Object with reflection.
Sprite used in reflection must be in self.scs
KWARGS may contain `reflection' and `opaque' key.
WithReflection is error prone class, use with caution,
make sure your object has next attributes:
 * add  - method to add sprite to some group
 * scs  - Sprite used for reflection
 * tick - Clocked tick method
 * x, y, z - Coordinates """
    def __init__(self, **kwargs):
        setobjattrs(self, kwargs,
                    reflection=False, opaque=REFLECTION_OPAQUE)

        # Reflections cache
        self.reflections = {}

        if self.reflection:
            self.scrfs = dirty_sprite()
            self.scrfs._layer = -1
            self.add(self.scrfs)

    def update_reflection(self):
        if not self.reflection: return

        if not self.reflections.has_key(self.scs.image):
            tim = pygame.transform.flip(self.scs.image, False, True)
            tim.set_alpha(self.opaque)
            self.reflections[self.scs.image] = tim

        self.scrfs.image = self.reflections[self.scs.image]
        self.scrfs.rect = self.scs.rect.copy()
        self.scrfs.rect.y += self.scs.rect.h + self.z*1.25
        self.scrfs.dirty = 1

class MovingObj(pygame.sprite.OrderedUpdates, SHobj, WithReflection):
    def __init__(self, **kwargs):
        if hasattr(self, "scs"): self.scs.kill()
        else: self.scs = dirty_sprite()

        pygame.sprite.OrderedUpdates.__init__(self)
        SHobj.__init__(self)
        WithReflection.__init__(self, **kwargs)

        setobjattrs(self, kwargs, x=0, y=0, z=0,
                    x_speed=0,y_speed=0,z_speed=0,
                    bouncing=4, can_stop=False,
                    field_bound_toponly=False)

        self.scs._layer = self.y
        self.add(self.scs)

    def __getattr__(self, attr):
        if attr == "rect": return self.scs.rect
        elif attr == "image": return self.scs.image
        raise AttributeError

#     def __setattr__(self, attr, av):
#         if attr == "rect": self.scs.rect = av
#         elif attr == "image": self.scs.image = av
#         else: self.__dict__[attr] = av

    def update(self):
        move_sprite(self.scs, self.xx(), self.yy())
        self.update_reflection()

    def tick(self, f):
        self.apply_motion()
        x, y = self.rect.center
        y += self.z
        if (self.is_quiescent() and not self.can_stop) \
               or not f.is_inside(x, y, self.field_bound_toponly):
            f.remove(self)
        else:
            self.update()

class Animate(pygame.sprite.OrderedUpdates):
    def __init__(self, adir, **kwargs):
        """Animate ADIR.
Set LOOP to loop animation
if LOOP is False and KEEP_LAST is set then keep last image on screen
when animation finished.
TICKS_STEP specifies amount of ticks between images.

Does not do anything about image placement,
so you must manage scs.rect for yourself."""
        if hasattr(self, "scs"): self.scs.kill()
        else: self.scs = dirty_sprite()

        pygame.sprite.OrderedUpdates.__init__(self)
        setobjattrs(self, kwargs,
                    loop=True, keep_last=False, ticks_step=2)

        self.anim = load_animation(adir)
        self.ticks = self.state = 0

        self.scs.image = self.anim[self.state]
        self.add(self.scs)

    def update(self):
        self.scs.image = self.anim[self.state]
        self.scs.dirty = 1

    def draw_static(self, f):
        """Draw current animation at field's F static layer."""
        f.draw_static(self.scs.image, self.scs.rect[0], self.scs.rect[1])

    def tick(self, f):
        self.ticks += 1
        if self.ticks % self.ticks_step != 0:
            return

        self.state += 1
        if self.state == len(self.anim):
            if self.loop:
                self.state = 0
            else:
                self.state -= 1
                f.remove(self)
                if self.keep_last: self.draw_static(f)
                return
        self.update()

class AnimateStates(pygame.sprite.OrderedUpdates):
    """Very generic class for animated object with states."""
    def __init__(self, dir, start_state, **kwargs):
        if hasattr(self, "scs"): self.scs.kill()
        else: self.scs = dirty_sprite()

        pygame.sprite.OrderedUpdates.__init__(self)
        setobjattrs(self, kwargs,
                    states_setup={}, ticks_step=2)

        self.states = dict([(basename(dr), load_animation(dr))
                            for dr in tglob(dir+"/*")])
        self.state = start_state
        self.state_idx = self.state_ticks = 0
        self.state_baseline = self.states_setup[self.state]

        self.update()
        self.add(self.scs)

    def state_frames(self, state=None):
        if state is None: state = self.state
        return len(self.states[self.state])

    def state_start(self, state):
        if self.state != state:
            self.state = state
            self.state_idx = 0
            self.state_ticks = 0
            self.state_baseline = self.states_setup[self.state]

            # Setup ticks_step
            _sss = self.states_setup
            if _sss.has_key(self.state) and \
                   _sss[self.state].has_key("ticks_step"):
                self.ticks_step = _sss[self.state]["ticks_step"]
            self.update()
            self.apply_position()
            return True
        return False

    def state_inc(self, keep_last=False):
        self.state_idx += 1
        if self.state_idx == self.state_frames():
            _sss = self.states_setup
            if keep_last or \
                   (_sss.has_key(self.state) and \
                    _sss[self.state].has_key("keep_last") \
                    and _sss[self.state]["keep_last"]):
                self.state_idx -= 1
            else:
                self.state_idx = 0

    def state_blhb(self):
        return self.state_baseline[self.state_idx]

        _sset = self.states_setup
        _ss = self.state
        _si = self.state_idx
        if _sset.has_key(_ss) and _sset[_ss].has_key(_si):
            return _sset[_ss][_si]
#        debug("- Object %s state=%s, sidx=%d does not have blhb"%(self, _ss, _si))
        return None

    def state_baselines(self):
        """Return tuple of (x-baseline, y-baseline) position."""
        blhb = self.state_blhb()
        if not blhb: return 0,0
        if type(blhb) is tuple:
            return blhb
        return blhb[0]

    def state_headrect(self):
        """Return head's rectangle, None if there is no head."""
        blhb = self.state_blhb()
        if not blhb or type(blhb) is tuple:
            return None
        _ht, _hb = blhb[1:]
        _ssr = self.scs.rect
        return pygame.Rect(_ht[0]+_ssr.x, _ht[1]+_ssr.y,
                           _hb[0]-_ht[0]+1, _hb[1]-_ht[1]+1)

    def update_reflection(self):
        """Take into account baselines, when updating reflections."""
        MovingObj.update_reflection(self)
        if self.reflection:
            _, yo = self.state_baselines()
            self.scrfs.rect.y -= 2*(self.scs.rect.h-yo-1)

    def apply_state_setup(self):
        """Apply baseline offsets to sprite's rectangle."""
        xo, yo = self.state_baselines()
        self.scs.rect.x -= xo
        self.scs.rect.y -= yo
        self.update_reflection()

    def apply_position(self):
        """Move sprite to its display position, aplying baseline offsets."""
        move_sprite(self.scs, self.xx(), self.yy())
        self.apply_state_setup()

    def update(self):
        self.scs.image = self.states[self.state][self.state_idx]

    def tick(self, f):
        self.state_ticks += 1
        _sts = self.ticks_step
        if self.state_ticks % (_sts+1) == _sts:
            self.state_inc()
            self.update()

    def is_headshot(self, prj):
        """Return True if projectile PRJ hits a HEAD."""
        # Head shot if PRJ hits either A or B segments of head boundary
        #        +-----------+
        #        |           | __/
        #        |         __*<----- hit
        #       A|      __/  |B
        #        |  ___/     |
        #        +-/---------+
        #
        #        +--/--------+
        #        | /         |
        #       A|/          |
        # hit--> *           |B
        #       /|           |
        #        +-----------+
        _hr = self.state_headrect()
        if not _hr:
            return False
        elif prj.is_bullet():
            debug("%s is_headshot: prj.x/y=%d/%d, rect=%s"%
                  (repr(self), prj.x, prj.y, repr(_hr)))
            return _hr.collidepoint(prj.x, prj.y)

        # PRJ is flunk rocket or grenade
        _exp = prj.explosion
        return _exp.distance_to_epi(_hr) <= _exp.splash_radius
##        if ht and hb and prj.is_bullet():
##            x, y = self.scs.rect.x, self.scs.rect.y
##            ht = (ht[0]+x, ht[1]+y)
##            hb = (hb[0]+x, hb[1]+y)
##            def inr(y): return y >= ht[1] and y <= hb[1]
##            return inr(prj.bully(hb[0])) and inr(prj.bully(ht[0]))
##        return False

    def is_dead_state(self):
        """Return True if object is in dead state."""
        return self.state[:5] == "Death"

class AnimateObj(Animate, MovingObj):
    def __init__(self, adir, **kwargs):
        Animate.__init__(self, adir, **kwargs)
        MovingObj.__init__(self, **kwargs)

        # Bouncing sounds
        self.bs_idx = 0
        setobjattrs(self, kwargs, bounce_sounds=[])

        self.update_ao()

    # This is done this way to avoid calling update on
    # Animate and MovingObj ticks
    def update(self): pass

    def update_ao(self):
        Animate.update(self)
        MovingObj.update(self)

    def tick(self, f):
        # Play bounce sound in case object is bouncing
        if self.bs_idx < len(self.bounce_sounds) and self.z+self.z_speed < 0:
            if RANDOM_BOUNCE_SOUNDS:
                play_rnd_sound(self.bounce_sounds)
            else:
                play_sound(self.bounce_sounds[self.bs_idx])
            self.bs_idx += 1

        Animate.tick(self, f)
        MovingObj.tick(self, f)
        if self.is_quiescent():
            if self.keep_last: self.draw_static(f)
            return

        self.update_ao()

class FallingClip(MovingObj):
    def __init__(self, cname, **kwargs):
        kwargs.update(reflection="clips" in option("reflections"))
        kwargs.update(can_stop=True)
        MovingObj.__init__(self, **kwargs)

        cpref = "Misc/%sClip/%sclip"%(cname,cname.lower())
        self.textures = map(load_texture, tglob("%s_*.png"%cpref))

        self.scs.image = load_texture(choice(tglob("%s_falling*.png"%cpref)))
        self.update()

    def tick(self, f):
        if self.is_quiescent():
            _ssr = self.scs.rect
            f.draw_static(choice(self.textures), _ssr[0], _ssr[1])
            f.remove(self)
            return

        MovingObj.tick(self, f)

    def update_ao(self): return self.update()

class AnimateClip(AnimateObj):
    def __init__(self, cname, **kwargs):
        kwargs.update(reflection="clips" in option("reflections"),
                      keep_last=True)
        AnimateObj.__init__(self, "Misc/%sClip"%cname, **kwargs)
        # Special for rotating clips
        setobjattrs(self, kwargs, x_fric=2.0, y_fric=2.0, bouncing=2)

class AnimateShell(AnimateObj):
    def __init__(self, adir, **kwargs):
        kwargs.update(reflection="shells" in option("reflections"),
                      keep_last=True)
        AnimateObj.__init__(self, adir, **kwargs)
        # Special for shells
        setobjattrs(self, kwargs, x_fric=2.0, y_fric=2.0, bouncing=10)

def Clip(name, **kwargs):
    if name in ["Small", "MAC"]:
        return FallingClip(name, **kwargs)
    else:
        return AnimateClip(name, **kwargs)

def Shell(name, **kwargs):
    """Create shell of NAME.
NAME can be one of:
 * small
 * normal
 * shotgun
 * awp
 * minigun"""
    name = name.capitalize()
    if not kwargs.has_key("bounce_sounds"):
        if name == "Small":
            bnc = aglob("weapons/sshell*.wav")
        elif name == "Normal" or name == "Minigun" or name == "Awp":
            bnc = aglob("weapons/shell*.wav")
        elif name == "Shotgun":
            bnc = aglob("weapons/shshell*.wav")
        else:
            bnc = []
        kwargs.update(bounce_sounds=map(load_sound, bnc))

    # Correct the name
    if name == "Normal": name = "Small"
    elif name == "Awp": name = "Minigun"
    return AnimateShell("Misc/%sShell"%name, **kwargs)

def AnimateOnce(adir, x, y, **kwargs):
    kwargs.update(loop=False)
    a = Animate(adir, **kwargs)
    move_sprite(a.scs, x, y)
    return a

class Muzzle(Animate, WithReflection):
    def __init__(self, name, weapon, xo=0, yo=0, **kwargs):
        """Create muzzle for WEAPON."""
        Animate.__init__(self, "Muzzle/"+name.capitalize(),
                         ticks_step=1, loop=False)
        kwargs.update(reflection="muzzle" in option("reflections"))
        WithReflection.__init__(self, **kwargs)

        self.weapon = weapon
        self.xo, self.yo = xo, yo

        self.update()

    def update(self):
        Animate.update(self)

        _ss = self.scs
        _ss.rect = _ss.image.get_rect()
        _swp = self.weapon.player
        _swap = self.weapon.aim_position
        mx = _swp.xx()-self.weapon.x-1+self.xo
        my = _swp.yy()-_swap+self.yo
        _ss.rect.midright = mx, my
        self.z = _swap#+_ss.rect.h/2)/1.25

        self.update_reflection()

class EarnMoney(pygame.sprite.DirtySprite):
    def __init__(self, amount, x, y, **kwargs):
        pygame.sprite.DirtySprite.__init__(self)
        setobjattrs(self, kwargs,
                    font=load_font("default.ttf", EARNMONEY_FONT_SIZE),
                    font_color=(255,0,0))

        self.x, self.y = x, y
        self.ticks = 0
        self.image = self.font.render("%d$"%amount, False, self.font_color).convert()
        self.x -= self.image.get_width()/2
        self.image.set_alpha(100)
        move_sprite(self, x, y)

    def tick(self, f):
        self.ticks += 1
        if (self.ticks == 50):
            f.remove(self)
            return

        ia = self.image.get_alpha()
        self.image.set_alpha(ia-2)
        self.y -= 1
        move_sprite(self, self.x, self.y)


# Projectile stuff
class Explosion(Animate):
    def __init__(self, projectile, x, y):
        Animate.__init__(self, "Explosion", ticks_step=1,
                         loop=False, keep_last=True)
        projectile.explosion = self
        self.projectile = projectile
        self.splash_radius = projectile.weapon.splash_radius
        self.radius = 0
        self.radius_inc = self.splash_radius/8.0
        self.hited_creatures = set()    # set of already hited creatures
        self.energy = projectile.weapon.damage

        for i in range(len(self.anim)-1):
            # Max i is 16, so last frame is fully transparent
            self.anim[i].set_alpha(255-i**2+1)
        # Special for splat
        self.anim[len(self.anim)-1].set_alpha(50)

        self.scs._layer = TOP_LAYER
        self.x, self.y = x + 4, y + 6
        self.update()

        play_sound("weapons/3/explosion.wav")

    def splash_rectangles(self, radius):
        """Aproximate splash circle of RADIUS with rectangles."""
        retrects = []
        steps = 20
        for i in range(1, steps-1):
            ca = math.pi/steps
            x0 = math.cos(i*ca)
            y0 = math.sin(i*ca)
            x1 = math.cos((i+1)*ca)
            y1 = math.sin((i+1)*ca)
            w = int(abs(x1-x0)*radius)
            x,y = int(radius*min(x0, x1)), int(radius*min(y0, y1))
            retrects.append(pygame.Rect(self.x+x,self.y-y,w,y*2))
        return retrects

    def splash_collides(self, creatures):
        """Return creatures list for whom explosion splash collides."""
##        # Draw splash rectangles
##        srects = self.splash_rectangles(self.radius)
##        def draw_rect(r):
##            s = pygame.Surface(r.size)
##            s.fill((0,0,0,0))
##            self.projectile.player.field.draw_static(s, *r.topleft)
##        map(draw_rect, srects)
        _crects = map(lambda o: o.scs.rect, creatures)
        _ssrsr = self.splash_rectangles(self.radius)
        return map(lambda i: creatures[i],
                   set.union(*[set(sr.collidelistall(_crects))
                               for sr in _ssrsr]))

    def distance_to_epi(self, rect):
        """Return distance from epicentre to rect."""
        if rect.collidepoint(self.x-2, self.y-3): return 0

#        xo = abs(self.x-rect.centerx)-rect.w/2-2
#        yo = abs(self.y-rect.centery)-rect.h/2-3
        xo = self.x-2-rect.centerx
        yo = self.y-3-rect.centery
        return math.sqrt(xo**2+yo**2)

    def apply_hits(self, f):
        """Apply explosion hits to all the creatures."""
        self.radius += self.radius_inc
        nhcreatures = list(set(f.creatures())-self.hited_creatures)
        for hc in self.splash_collides(nhcreatures):
            # NOTE: dd must be positive!
            dd = abs(self.splash_radius-self.distance_to_epi(hc.scs.rect))
            dmg = int((self.energy*dd*1.0)/self.splash_radius)
            _sp = self.projectile
            _sp.hit_creature(hc, dmg)
            self.hited_creatures.add(hc)

    def update(self):
        Animate.update(self)
        _ss = self.scs
        _ss.rect = _ss.image.get_rect()
        _ss.rect.center = (self.x,self.y)

    def tick(self, f):
        if self.ticks < 8:
            self.apply_hits(f)
        elif self.ticks == 8:
            self.projectile.done_hits()

            _spp = self.projectile.player
            map(lambda cr: _spp.earn_money(cr.bounty),
                filter(lambda cr: not cr.is_alive(), self.hited_creatures))
            _spp.apply_earned_money()

        Animate.tick(self, f)

class Projectile:
    def __init__(self, weapon):
        self.weapon = weapon
        self.player = weapon.player
        self.energy = weapon.damage
        self.given_damage = 0

    def is_grenade(self):
        """Return True if projectile is grenade or flunk rocket."""
        return isinstance(self, (Grenade, FlunkRocket))

    def is_bullet(self):
        """Return True if projectile is a bullet."""
        return not self.is_grenade()

    def hit_creature(self, hc, dmg):
        """Hit creature HC by the projectile with base damage DMG."""
        _ishs = hc.is_headshot(self)
        if _ishs:
            dmg *= hc.headshot_multiplier
            # Earn bonus money for the headshot accuracy
            self.player.earn_money(hc.headshot_bonus)

        dmg += self.weapon.damage_inc * (self.player.field.level.num-1)
        self.given_damage += dmg
        hc.hit(self, dmg, head=_ishs)

    def done_hits(self):
        """Projectile done hitting creatures."""
        if self.given_damage > self.weapon.damage*4:
            self.player.nice_shot(self)

class Grenade(Projectile, AnimateObj):
    def __init__(self, weapon, **kwargs):
        Projectile.__init__(self, weapon)

        kwargs.update(reflection="grenades" in option("reflections"),
                      can_stop=True, field_bound_toponly=True)
        AnimateObj.__init__(self, "Weapons/Granat", **kwargs)

        setobjattrs(self, kwargs,
                    bounce_sounds=map(load_sound,
                                      aglob("weapons/3/bounce*.wav")),
                    ticks_step=1, x_fric=20, y_fric=20, bouncing=1.9)

    def tick(self, f):
        AnimateObj.tick(self, f)
        if self.is_quiescent() or self.ticks == FPS:
            f.remove(self)
            exp = Explosion(self, self.xx(), self.yy())
            f.add(exp)

class FlunkRocket(Projectile, AnimateObj):
    def __init__(self, weapon, **kwargs):
        Projectile.__init__(self, weapon)

        kwargs.update(reflection="grenades" in option("reflections"),
                      can_stop=True, field_bound_toponly=True)
        AnimateObj.__init__(self, "Weapons/Granat2", **kwargs)

        setobjattrs(self, kwargs, x_fric=12, y_fric=6)

    def tick(self, f):
        if self.is_quiescent() or self.collides(f.creatures()):
            f.remove(self)
            f.add(Explosion(self, self.xx(), self.yy()))
            return
        AnimateObj.tick(self, f)

    def collides(self, creatures):
        """Return True if rocket collides with some creature."""
        crects = map(lambda o: o.scs.rect, creatures)
        return self.scs.rect.collidelist(crects) != -1

class Bullet(Projectile):
    def __init__(self, weapon, field):
        Projectile.__init__(self, weapon)
        self.field = field

        # Get random angle according to accuracy_angle
        waa = int(1000.0*self.weapon.accuracy_angle)
        adeg = randint(-waa, waa)/1000.0
        self.angle = math.sin(adeg*math.pi/180)

        # Fire starts here
        self.fx = int(self.player.xx() - self.weapon.wpn_position[0])
        self.fy = int(self.player.yy() - self.weapon.aim_position)

        # Draw bullet tray
        if "bullets" in option("show"):
            _sb = self.bully
            x0, x1 = randint(0,self.fx), randint(0,self.fx)
            field.add(BulletTray((x0,_sb(x0)), (x1,_sb(x1))))

    def bully(self, bx):
        """Calculate bullet's y according to bullet's x BX."""
        return self.fy + int((self.fx-bx)*self.angle)

    def collide(self, creature):
        """Return tuple of creature and hitpoint
if bullet collides CREATURE."""
        def crpos(rp):
            if rp[1] > self.bully(rp[0]): return 1
            else: return -1

        _cr = creature.scs.rect
        if _cr.left > self.fx: return False
        crcorns = [_cr.topleft,_cr.topright,_cr.bottomright,_cr.bottomleft]
        if abs(sum(map(crpos, crcorns))) == 4:
            return False

        # Check precisely using creature's mask
        cm = pygame.mask.from_surface(creature.scs.image)
        xoff, yoff = _cr.topleft
        sx = min(_cr.right, self.fx)
        while sx > xoff:
            sy = self.bully(sx)
            if _cr.collidepoint(sx, sy) and cm.get_at((sx-xoff,sy-yoff)):
                return (creature, (sx,sy))
            sx -= 1 
        return False

    def apply_hits(self, creatures):
        """Apply bullet's damage energy to hitted creatures."""
        _hitcols = filter(None, map(self.collide, creatures))
        _hitcrts = sorted(_hitcols, key=lambda hro: hro[1][0], reverse=True)
        for hc, hp in _hitcrts:
            if self.energy < 1:
                break

            self.x, self.y = hp
            # randomize hit position a little
            self.x -= randint(0, 2)

            self.hit_creature(hc, self.energy)

            # Decrease bullet's energy according to pierce
            self.energy *= self.weapon.pierce
        self.done_hits()

class BulletTray(pygame.sprite.DirtySprite):
    """Class for momentary bullet trays.
Bullet tray is simply momentary yellow line on the screen."""
    def __init__(self, start, end, color=(255,255,0)):
        pygame.sprite.DirtySprite.__init__(self)
        self.image = pygame.Surface((abs(end[0]-start[0]),
                                     abs(end[1]-start[1])+1))

        ck = (0,0,0)
        self.image.fill(ck)
        self.image.set_colorkey(ck)
        self.image.set_alpha(BULLET_OPAQUE)

        x, y = map(min, zip(end, start))
        pygame.draw.line(self.image, color, (start[0]-x,start[1]-y),
                         (end[0]-x,end[1]-y))
        move_sprite(self, x, y)

    def tick(self, f):
        f.remove(self)

class Creature(MovingObj):
    """Generic class for creatures."""
    def __init__(self, life, **kwargs):
        MovingObj.__init__(self, **kwargs)
        setobjattrs(self, kwargs, field=None)

        self.slife = self.life = life
        self.ticks = self.total_hit = 0

        self.hs_sounds = map(load_sound, aglob("misc/headshot*.wav"))
        self.hit_sounds = map(load_sound, aglob("misc/genhit*.wav"))

        self.is_dying = False

    def is_alive(self):
        """Return True if creature is alive."""
        return self.life > 0

    def update(self, f):
        """Overrides MovingObj update method."""
        # Subclass responsibility
        pass

    def tick(self, f):
        """Overrides MovingObj tick method.
So you must define you own tick if inheriting Creature."""
        self.ticks += 1
        if not self.is_alive() and not self.is_dying:
            self.die(self.fatal_projectile)
        else:
            self.total_hit = 0

    def hit(self, prj, damage, head=False):
        """Creature has been hitted by projectile PRJ by DAMAGE.
If HEAD is True, then creature has been headshoted."""
        self.total_hit += damage
        self.life -= damage

        # Cause the hit
        if prj.is_bullet():
            play_rnd_sound(self.hs_sounds if head else self.hit_sounds)
            hframes = 1 + min(int(damage/25), 2)
            self.field.add(Hit(prj.x, prj.y, frames=hframes))

        if not self.is_alive():
            from copy import copy
            self.fatal_projectile = copy(prj)

    def die(self, prj):
        self.is_dying = True

        # NOTE: prj can be a string in some cases
        if hasattr(prj, "player"):
            prj.player.kills(self, prj)

    def is_headshot(self, prj):
        # Subclass responsibility
        return False


# Blood
class GenHit(Animate):
    def __init__(self, name, x, y, frames=3):
        Animate.__init__(self, name, loop=False, ticks_step=2)
        self.anim = self.anim[:frames]
        self.x, self.y = x, y
        self.scs._layer = TOP_LAYER
        self.update()

    def update(self):
        Animate.update(self)
        move_center(self.scs, self.x, self.y)

def Hit(x, y, frames):
    return GenHit("Blood/Hit", x, y, frames)

def Ric(x, y, frames):
    return GenHit("ShellHit", x, y, frames)

class Particle(AnimateObj):
    def __init__(self, pname, **kwargs):
        kwargs.update(reflection="particles" in option("reflections"))
        kwargs.update(keep_last=True)
        AnimateObj.__init__(self, pname, **kwargs)

        self.x_fric = self.y_fric = 10
        self.bouncing = 20

class BloodParticle(MovingObj):
    def __init__(self, w, h, **kwargs):
        kwargs.update(reflection="blood" in option("reflections"))
        kwargs.update(keep_last=True)
        MovingObj.__init__(self, **kwargs)

#        self.drip_sounds = map(load_sound, aglob("misc/drip*.wav"))

        # can't slide and bounce
        self.x_fric = self.y_fric = 100
        self.bouncing = 100

        self.scs.image = gen_blood(w, h)
        move_sprite(self.scs, self.x, self.y)

    def tick(self, f):
        MovingObj.tick(self, f)
        if self.is_quiescent():
#            play_rnd_sound(self.drip_sounds)
            _ss = self.scs
            f.draw_blood(_ss.image, _ss.rect.x, _ss.rect.y)

class ObjectsGroup(pygame.sprite.DirtySprite):
    def __init__(self, **kwargs):
        pygame.sprite.DirtySprite.__init__(self)
        self.objects = []

    def add(self, o):
        self.objects.extend(o)

    def remove(self, *o):
        map(self.objects.remove, o)

    def render(self):
        """Render all the objects."""
        # determine size
        minxy, maxxy = (640,480), (0, 0)
        for o in self.objects:
            _osr = o.scs.rect
            minxy = map(min, _osr.topleft, minxy)
            maxxy = map(max, _osr.bottomright, maxxy)

        debug("OG: minxy=%s, maxxy=%s"%(repr(minxy), repr(maxxy)))
        self.image = pygame.Surface(map(sub, maxxy, minxy))
        for o in self.objects:
            _os = o.scs
            debug("OG: topleft = %s"%(repr(_os.rect.topleft)))
            self.image.blit(_os.image, map(sub, _os.rect.topleft, minxy))

        move_sprite(self, *minxy)

    def tick(self, f):
        map(lambda o: o.tick(f), self.objects)
        self.render()
#        print "qqq = %s"%map(lambda o: o.is_quiescent(), self.objects)
        if all(map(lambda o: o.is_quiescent(), self.objects)):
            f.remove(self)

def blood_particles(**args):
    """Generate bunch of blood particles."""
    _xrs = apply(rand_speed, args.get("xrs", (-1,1)))
    _yrs = apply(rand_speed, args.get("yrs", (-0.3, 0.3)))
    _zrs = apply(rand_speed, args.get("zrs", (2, 6)))
    _bw, _bh = args.get("w", (2,4)), args.get("h", (1,3))
    _n = args.get("n", 10)*option("bloody")
    bps = [BloodParticle(apply(randint, _bw), apply(randint, _bh),
                         x_speed=_xrs(), y_speed=_yrs(), z_speed=_zrs(),
                         **dict([(k,args[k]) for k in ["x", "y", "z"]]))
           for _ in xrange(_n)]
    return bps
    og = ObjectsGroup()
    og.add(bps)
    og.render()
    return og

blood = blood_particles # short name alias
