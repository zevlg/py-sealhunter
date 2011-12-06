# Copyright (C) 2009-2010 by Zajcev Evegny <zevlg@yandex.ru>

import pygame

from constants import *
from misc import *
from objects import setobjattrs

# Number of huds, 2 HUDS is the maximum
HUDS = 0

class DummyHud(pygame.sprite.OrderedUpdates):
    def __init__(self, player, **kwargs):
        self.player = player
        pygame.sprite.OrderedUpdates.__init__(self)

class Hud(DummyHud):
    def __init__(self, player, **kwargs):
        DummyHud.__init__(self, player, **kwargs)
        setobjattrs(self, kwargs, id=1)

        self.hname = "blue" if self.id==1 else "red"
        self.y = 23 if self.id==1 else 480-48
        self.ihud = dirty_sprite()
        self.ihud._layer = 2*TOP_LAYER
        _sihi = load_texture("Misc/%sHUD.png"%self.hname).copy()
        sprite_image(self.ihud, _sihi)

        # Blit some stuff directly to ihud sprite
        woff = 25+4
        fcol = (200,200,200)
        try:
            font = load_font('default.ttf', 10)
        except IOError:
            font = pygame.font.SysFont("Sans", 10)
        for widx in range(1, len(WEAPON_NAMES)):
            price = WEAPONS[WEAPON_NAMES[widx]]["price"]
            pimg = font.render("$%d"%price, True, fcol)
            cx = pimg.get_rect().centerx
            _sihi.blit(pimg, (woff-cx, 30))
            woff += 54

        self.mkfont = load_font('trebuc.ttf', 19)
        self.mkfont.set_bold(True)
        _mkf = self.mkfont

        _fcol = (220,220,220)
        _sihi.blit(_mkf.render("$", True, _fcol), (550, 4))
        _sihi.blit(_mkf.render("Kills:", True, _fcol), (550, 23))

        sprite_move(self.ihud, 0, self.y)

        self.hud_money = dirty_sprite()
        self.hud_money._layer = 2*TOP_LAYER+1
        self.update_money(0)

        self.hud_kills = dirty_sprite()
        self.hud_kills._layer = 2*TOP_LAYER+1
        self.update_kills(0)

        self.hud_bullets = dirty_sprite()
        self.hud_bullets._layer = 2*TOP_LAYER+1
        self.update_bullets(self.player.weapon)

        # Frame around selected weapon
        self.hud_frame = dirty_sprite()
        self.hud_frame._layer = 2*TOP_LAYER+1
        self.hud_frame.image = load_texture("Misc/HUDSelected.png")
        self.hud_frame.rect = self.hud_frame.image.get_rect()
        self.hud_frame.rect.center = (-100, self.y+25)

        # Create sprites for weapons
        self.off = 25+4                 # adhoc
        def mk_wpn_sprite(n):
            s = dirty_sprite()
            s._layer = 2*TOP_LAYER+2
            s.image = load_texture("Weapons/HUDWeapons/%s_%d.png"%(n, self.id))
            s.rect = s.image.get_rect()
            s.rect.center = (self.off, self.y+18)
            self.off += 54
            return s

        self.hud_wpns = map(mk_wpn_sprite,
                            ["magnum", "mp5", "granat", "shotgun",
                             "mac", "flunk", "colt", "awp", "farfar",
                             "minigun"])

        # Add all the sprites to HUD
        map(self.add, [self.ihud, self.hud_money, self.hud_kills,
                       self.hud_bullets, self.hud_frame]+self.hud_wpns)

    def update_km(self, s, n, yoff):
        s.image = self.mkfont.render("%d"%n, True, (220,220,220))
        s.rect = s.image.get_rect()
        s.rect.topright = (634, self.y+yoff)
        s.dirty = 1
        
    def update_money(self, money):
        self.update_km(self.hud_money, money, 4)

    def update_kills(self, kills):
        self.update_km(self.hud_kills, kills, 23)

    def update_bullets(self, wpn):
        fcol = (200,200,200)
        try:
            font = load_font('default.ttf', 10)
        except IOError:
            font = pygame.font.SysFont("Sans", 10)
        bimg = font.render("x%d"%wpn.bullets, True, (200,200,200))
        self.hud_bullets.image = bimg
        self.hud_bullets.rect = bimg.get_rect()
        widx = WEAPON_NAMES.index(wpn.__class__.__name__)
        self.hud_bullets.rect.center = 31+(widx-1)*54, 36+self.y
        self.hud_bullets.dirty = 1

    def new_weapon(self, wpn):
        widx = WEAPON_NAMES.index(wpn.__class__.__name__)
        self.ihud.image.blit(load_texture("Misc/%sBox_1.png"%self.hname),
                             (4+(widx-1)*54, 4))
        self.ihud.dirty = 1

    def select_weapon(self, wpn):
        # blit
        _shbi = self.hud_bullets.image
        _shbr = self.hud_bullets.rect
        self.ihud.image.blit(_shbi, (_shbr.x, _shbr.y-self.y))
        self.ihud.dirty = 1

        widx = WEAPON_NAMES.index(wpn.__class__.__name__)
        if widx == 0:
            self.hud_frame.rect.centerx = -100
        else:
            self.hud_frame.rect.centerx = 30 + (widx-1)*54
        self.hud_frame.dirty = 1

        self.new_weapon(wpn)
        self.update_bullets(wpn)

    def __del__(self):
        global HUDS
        HUDS -= 1

def hud(player, **kwargs):
    global HUDS
    if HUDS == 2:
        return DummyHud(player, **kwargs)
    HUDS += 1
    kwargs['id'] = HUDS
    return Hud(player, **kwargs)

def huds_reset():
    global HUDS
    HUDS = 0
