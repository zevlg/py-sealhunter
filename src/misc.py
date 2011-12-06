# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

import os, sys, pickle, math, glob
import pygame
import pygame.gfxdraw
from random import randint, choice

from constants import DEFAULT_OPTIONS

dot_sealhunter = "~/.sealhunter"
OPTIONS = {}

MEMOIZED = {}
def memoize(fun):
    def mfun(*args, **kwargs):
        mm = MEMOIZED[fun]
        if not kwargs and mm.has_key(args):
            return mm[args]

        rv = apply(fun, args, kwargs)
        if not kwargs:
            mm[args] = rv
        return rv
    MEMOIZED[fun] = {}
    return mfun

def maybe_prepend(s, pref):
    return s if s.startswith(pref) else pref+s

@memoize
def tglob(pattern):
    return sorted(glob.glob(maybe_prepend(pattern, "textures/")))

@memoize
def load_texture(path, alpha=False):
    surf = pygame.image.load(maybe_prepend(path, "textures/"))
    if alpha:
        return surf.convert_alpha()
    surf.set_colorkey((0,0,0))          # Mac OS X workaround!
    return surf.convert()

@memoize
def aglob(pattern):
    return sorted(glob.glob(maybe_prepend(pattern, "audio/")))

@memoize
def load_sound(path):
    return pygame.mixer.Sound(maybe_prepend(path, "audio/"))

@memoize
def load_font(path, size):
    if path.endswith(".ttf"):
        return pygame.font.Font(maybe_prepend(path, "fonts/"), size)
    return pygame.font.SysFont(path, size)

def substitute_color(surf, fc, tc):
    """For surface SURF substitute color FC to color TC.
Return new surface, with substituted color."""
    retsurf = surf.copy()
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            if surf.get_at((x,y)) == fc:
                retsurf.set_at((x,y), tc)
    return retsurf

@memoize
def load_animation(dr, alpha=False, subscolor=None):
    def loadit(x):
        txt = load_texture(x, alpha)
        if subscolor:
            return substitute_color(txt, *subscolor)
        else:
            return txt
    return map(loadit, tglob(dr+"/*.png"))

@memoize
def load_animation_mask(dr):
    return map(lambda x: pygame.mask.from_surface(load_texture(x)),
               tglob(dr+"/*.png"))

def make_transparent(surf, trans_color=(0,255,255)):
    """Make surface SURF to be fully transparent."""
    surf.set_colorkey(trans_color)
    surf.fill(trans_color)

def options_load():
    global OPTIONS
    OPTIONS = DEFAULT_OPTIONS
    # Load config
    try:
        ufile = open(os.path.expanduser(dot_sealhunter+"/config"), "r")
        OPTIONS = pickle.load(ufile)
        ufile.close()
    except:
        pass

def options_save():
    # Save options on config file
    dsh = os.path.expanduser(dot_sealhunter)
    if not os.path.exists(dsh):
        os.mkdir(dsh)

    ufile = open(os.path.expanduser(dot_sealhunter+"/config"), "w")
    pickle.dump(OPTIONS, ufile)
    ufile.close()

def option(name):
    return OPTIONS[name]

def options():
    return OPTIONS

def debug(str):
    if option("debug"):
        sys.stderr.write(str)
        sys.stderr.write("\n")

def sprite_image(sprite, img):
    """For SPRITE set image to IMG."""
    sprite.image = img
    sprite.rect = img.get_rect()

def sprite_update(sprite, newimg):
    sprite.image = newimg
    sprite.rect.size = newimg.get_size()
    sprite.dirty = 1

def sprite_move(sprite, x, y):
    """Move SPRITE to X,Y position."""
    if sprite.rect.topleft != (x,y):
        sprite.rect.topleft = x,y
        sprite.dirty = 1

def sprite_center(sprite, point):
    if sprite.rect.center != point:
        sprite.rect.center = point
        sprite.dirty = 1

def rand_speed(min, max):
    """Return function which return random float betwean MIX and MAX."""
    def rndspeed():
        return randint(int(min*100),int(max*100))/100.0
    return rndspeed

def dirty_sprite():
    ds = pygame.sprite.DirtySprite()
    ds.visible = 1
    return ds

def play_sound(snd, stop=False, **kwargs):
    """Play sound SND."""
    if type(snd) == str:
        return play_sound(load_sound(snd), stop, **kwargs)

    if option("sound"):
        if stop: snd.stop()
        _sc = snd.play(**kwargs)
        if _sc: _sc.set_volume(option("volume"))
        if kwargs.has_key("fadeout"):
            _sc.fadeout(kwargs['fadeout'])
        return _sc

def play_rnd_sound(sounds):
    """Play random sound from SOUNDS."""
    if sounds:
        play_sound(choice(sounds))

BLOOD_CACHE = {}
def gen_blood(w, h, color="red"):
    """Random red pixels scaled to WxH.
Intended to emulate blood."""
    # TODO: probably introduce some kind of blood particles cache
    global BLOOD_CACHE
    _bckey = (w,h)
    if not BLOOD_CACHE.has_key(_bckey):
        BLOOD_CACHE[_bckey] = []
    _cached = BLOOD_CACHE[_bckey]
    if len(_cached) > 50:
        return choice(_cached)

    bs = pygame.Surface((w, h))
    make_transparent(bs, (255,255,255))
#    bs = pygame.Surface((w, h), pygame.SRCALPHA)
#    make_transparent(bs, (250,100,100))

    rr = randint(80, 120)
    if color == "yellow":
        bc = pygame.Color(100+rr, 140+rr, rr/2)
    else:
        bc = pygame.Color(30+rr, 0, 0)
    pygame.gfxdraw.filled_ellipse(bs, w/2, h/2, w/2, h/2, bc)
#    pygame.gfxdraw.filled_ellipse(bs, w/2, h/2, w/2, h/2, bc)
#    pygame.gfxdraw.aaellipse(bs, w/2, h/2, w/2, h/2, pygame.Color(55+rr, 0,0))
#    bs = pygame.transform.smoothscale(bs, (w, h)).convert_alpha()
    bs = bs.convert()
    _cached.append(bs)
    return bs

def key2keycode(key):
    """Convert KEY string to pygame constant."""
    from pygame import constants as pyconsts
    # key in form 'up' 'a', etc
    # 1. Try K_<KEY>
    # 2. Try K_<Key>
    upk = "K_%s"%key.upper()
    if hasattr(pyconsts, upk):
        return getattr(pyconsts, upk)
    lck = "K_%s"%key.lower()
    if hasattr(pyconsts, lck):
        return getattr(pyconsts, lck)

    raise Exception, "Unknown key: %s"%key
