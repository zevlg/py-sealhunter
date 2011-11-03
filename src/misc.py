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
    def mfun(*args):
        mm = MEMOIZED[fun]
        if mm.has_key(args):
            return mm[args]

        rv = apply(fun, args)
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

@memoize
def load_animation(dr, alpha=False):
    return map(lambda x: load_texture(x, alpha), tglob(dr+"/*.png"))

def make_transparent(surf, trans_color=(0,255,255)):
    """Make surface SURF to be fully transparent."""
    surf.set_colorkey(trans_color)
    surf.fill(trans_color)

def substitute_color(surf, fc, tc):
    """For surface SURF substitute color FC to color TC.
Substitution is done destructively."""
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            if surf.get_at((x,y)) == fc:
                surf.set_at((x,y), tc)
    return surf

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
        import sys
        sys.stderr.write(str+"\n")

def move_sprite(sprite, x, y):
    """Move SPRITE to X,Y position."""
    sprite.rect = sprite.image.get_rect().move(x, y)
    sprite.dirty = 1

def move_center(sprite, x, y):
    sprite.rect = sprite.image.get_rect()
    sprite.rect.center = x,y
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
    if type(snd) == str:
        return play_sound(load_sound(snd), stop, **kwargs)

    if option("sound"):
        if stop: snd.stop()
        _sc = snd.play(**kwargs)
        if _sc: _sc.set_volume(option("volume"))
        return _sc

def play_rnd_sound(sounds):
    if sounds:
        play_sound(choice(sounds))

def gen_blood(w, h):
    # TODO: probably introduce some kind of blood particles cache
    bs = pygame.Surface((2*w,2*h)).convert_alpha()
    bs.fill((255,255,255,0))
    rr = randint(0,60)
    pygame.gfxdraw.filled_ellipse(bs, w, h, w, h,
                                  pygame.Color(140+rr,rr/2,rr/2,255))
    return pygame.transform.smoothscale(bs, (w, h))

def key2keycode(key):
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
