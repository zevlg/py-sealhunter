# Copyright (C) 2009-2010 by Zajcev Evegny <zevlg@yandex.ru>

import pygame
from pygame.sprite import LayeredDirty

import objects
from player import Player
from levels import *
from constants import *
from misc import *

class Field(LayeredDirty):
    def __init__(self, nplayers):
        self.nplayers = nplayers
        self.objects = []               # objects on the field
        LayeredDirty.__init__(self, _update=True, _time_threshold=1000.0/FPS)
        self.game_over = False
        self.screen = pygame.display.get_surface()

        self.clock = pygame.time.Clock()

        self.bg = load_texture("Misc/backdrop.png")
        self.ice = load_texture("Misc/ice.png", True)
        self.start = pygame.Surface((640,480))
        self.start.blit(self.bg, (0, 0))
        self.start.blit(self.ice, (0, ICE_YOFFSET))

        self.field = self.start.copy()
        self.ticks = 0                  # total ticks field played

        self.screen.blit(self.field, (0,0))
        # FPS drawer if needed
        if "fps" in option("show"):
            self.sfont = load_font("default.ttf", 14)
            self.fps = pygame.sprite.DirtySprite()
            self.update_fps()
            # show FPS rate on top of everything
            self.add(self.fps, layer=TOP_LAYER*3)

        # Messages
        self.messages = []
        self.show_messages = []

        self.msgs = pygame.sprite.DirtySprite()
        self.msgs.visible = 0
        self.msgs_offset = 0
        self.msgs_linesize = self.sfont.get_linesize()
        _ssh = self.msgs_linesize*option("max-messages")
        self.msgs.image = pygame.Surface((640, _ssh))
        move_sprite(self.msgs, 0, 71)
        self.add(self.msgs, layer=-1)

        # Levels
        self.levels = iter([Level1(self), Level2(self),
                            Level3(self), Level4(self),
                            Level5(self)])

        # Sprite for level's progress
        self.lp_font = load_font('trebuc.ttf', 14)
        self.lp_font.set_bold(True)

        self.level_prgrs = pygame.sprite.DirtySprite()
        self.level_prgrs.image = pygame.Surface((640, 20))
        move_sprite(self.level_prgrs, 0, 0)
        self.level_prgrs.image.blit(self.bg, (0,0), self.level_prgrs.rect)
        self.add(self.level_prgrs)

        # Start 1st level
        self.next_level()

    def next_level(self):
        self.level = self.levels.next()

        # NOTE: LevelSplash will call start_level after fading out
        self.add(LevelSplash(self.level.num))
#        self.level_prgrs._visible = True

    def start_level(self):
        self.level.start()
#        self.level_prgrs._visible = True

    def render_level_progress(self):
        # Render level's progress bar
        _sl = self.level
        if not _sl.finished and _sl.ticks <= LEVEL_TICKS:
            _slpi = self.level_prgrs.image
            _slpi.blit(self.bg, (0,0), self.level_prgrs.rect)
#            _slpi.fill((0,0,0))
            _ls = self.lp_font.render("Level %d:"%self.level.num,
                                      True, (0,0,0))
            _slpi.blit(_ls, (3, 3))
            _lsw = _ls.get_width()
            _pbw = 640-15-_lsw
            pygame.draw.rect(_slpi, (0,0,0), (8+_lsw, 3, _pbw, 17), 1)

            _cko = self.level.ticks*1.0/LEVEL_TICKS
            _cw = int(_cko*(_pbw-2))
            _ccol = (255,255-255*(_cko**8),255-255*(_cko**8))
            if _cw > 0:
                pygame.draw.rect(_slpi, _ccol, (9+_lsw, 4, _cw, 15))
            self.level_prgrs.dirty = 1

    def update_fps(self):
        ft = "FPS: %d, Objects: %d"% \
             (round(self.clock.get_fps()), len(self.objects))
        self.fps.image = self.sfont.render(ft, True, (0,0,0))
        move_sprite(self.fps, 0, 480-14)

    def add(self, *args, **kwargs):
        """Add object O to field object list."""
        LayeredDirty.add(self, *args, **kwargs)
        self.objects.extend(args)
##        if kwargs.get("append", False):
##            self.objects.extend(args)
##        else:
##            map(lambda o: self.objects.insert(0, o), args)

    def remove(self, *args):
        """Remove object O from field's object list."""
        LayeredDirty.remove(self, *args)
        map(self.objects.remove, args)

    def tick(self):
        def redraw_screen():
            self.clear(self.screen, self.field)
            urects = self.draw(self.screen)
            pygame.display.update(urects)

        self.ticks += 1

        # Tick the level
        if self.level.finished:
            self.next_level()
        if self.level.started:
            self.level.tick(self)
        self.render_level_progress()

        for o in self.objects:
            if hasattr(o, "tick"):
                o.tick(self)

        # Draw FPS
        if "fps" in option("show"): self.update_fps()

        # Scroll the messages
        if self.show_messages and self.ticks - self.msg_ticks > 150:
            _msgst = (self.ticks - self.msg_ticks) % 150
            if _msgst <= self.msgs_linesize:
                if _msgst == self.msgs_linesize:
                    self.show_messages = self.show_messages[1:]
                    self.msgs_offset = 0
                else:
                    self.msgs_offset -= 1
                self.update_messages()

        redraw_screen()

        # Lock the frame rate
        if ENABLE_ACCURATE_FPS: self.clock.tick_busy_loop(FPS)
        else: self.clock.tick(FPS)

##        print
##        obs = filter(lambda o: o.__class__.__name__!="DirtySprite", self.objects)
##        print len(obs)
##        print obs

    def draw_field(self, surf, x, y):
#        return
        # Update the field as well
        self.field.blit(surf, (x, y))

        rec = (x,y)+surf.get_size()
        self.screen.blit(self.field, (x, y), rec)
        pygame.display.update(rec)

    def draw_static(self, surf, x, y):
#        return
        # Draw SURF to static objects surface at X, Y
#        self.static.blit(surf, (x, y))
        self.draw_field(surf, x, y)

    def draw_blood(self, surf, x, y):
#        return
#        self.blood.blit(surf, (x, y))
        self.draw_field(surf, x, y)

    def clear_blood(self):
        self.blood = pygame.Surface((640,480))
        make_transparent(self.blood)

        self.blood_lo.empty()

    def fade_blood(self, inc):
        # create new blood layer
        bs = pygame.sprite.Sprite(self.blood_lo)
        bs.image = self.blood
        bs.rect = bs.image.get_rect()

        self.blood = pygame.Surface((640,480))
        make_transparent(self.blood)

        # Adjust alpha for all blood layers
        for bs in self.blood_lo:
            ba = (bs.image.get_alpha() or 255) - inc
            if ba < 0:
                self.blood_lo.remove(bs)
                continue
            bs.image.set_alpha(ba)

        # display blood layers
        self.field.blit(self.start, (0,0))
        self.blood_lo.draw(self.field)
        self.field.blit(self.static, (0,0))
        self.screen.blit(self.field, (0,0))

    def is_inside(self, x, y, toponly=False):
        """Return True if X,Y is inside the field."""
        if x >= 640 or x < 0: return False
        if not toponly:
            if y > FLIMIT_HEIGHT[1]: return False

        # Hack to handle ice gap
        y -= ICE_YOFFSET
        if x > 274 and x < 336 and y < 300:
            y -= 0.3*(x-274)
        return self.ice.get_rect().collidepoint(x,y) \
               and self.ice.get_at((int(x),int(y)))[3] != 0

    def creatures(self, *classes, **kwargs):
        """Return list of alive creatures here in the field."""
        all = kwargs.get("all", False)
        def suited_creature(c):
            return isinstance(c, objects.Creature) \
                   and (not classes or isinstance(c, classes)) \
                   and (all or c.is_alive())
        return filter(suited_creature, self.objects)

    def players(self):
        """Return list of players in the field."""
        return self.creatures(Player, all=True)

    def game_is_over(self, by_enemy):
        if option("debug"):
            return
        self.game_over = True
        debug("Game Over! by %s"%by_enemy)

    def update_messages(self):
        _msgs = self.show_messages[-option("max-messages"):]
        if not _msgs:
            self.msgs.visible = False
            return

        self.msgs.visible = self.msgs.dirty = True
        _smi = self.msgs.image
        _smi.blit(self.field.subsurface(self.msgs.rect), (0,0))
        _yoff = self.msgs_offset
        _lh = self.sfont.get_linesize()
        for msg in _msgs:
            _smi.blit(self.sfont.render(msg, True, (80,0,0)), (3, _yoff))
            _yoff += _lh

    def message(self, msg, nosound=False):
        """Show message MSG."""
        if not nosound:
            play_sound("ui/saying.wav")
        self.console.output(msg)

        self.messages.append(msg)
        if not self.show_messages:
            self.msg_ticks = self.ticks
        self.show_messages.append(msg)
        self.update_messages()
