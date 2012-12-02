# Copyright (C) 2009-2011 by Zajcev Evegny <zevlg@yandex.ru>

from operator import methodcaller as method

import copy
import pygame
from pygame.sprite import LayeredDirty

import objects
from player import Player
from levels import *
from constants import *
from misc import *

class Field(LayeredDirty):
    def __init__(self, console=None):
        self.console = console
        self.players = []               # players on the field
        self.objects = []               # objects on the field
        self.deleted = []               # object to delete

        LayeredDirty.__init__(self, _update=True, _time_threshold=1000.0/FPS)
        self.game_over = False
        self.screen = pygame.display.get_surface()

        self.lockfps = FPS
        self.clock = pygame.time.Clock()

        self.bg = load_texture("Misc/backdrop.png")
        self.ice = load_texture("Misc/ice.png", True)
        self.ice_mask = pygame.mask.from_surface(self.ice)
        self.ice_rects = [pygame.Rect(FLIMIT_WIDTH[0], FLIMIT_HEIGHT[0],
                                      FLIMIT_WIDTH[1]-FLIMIT_WIDTH[0],
                                      FLIMIT_HEIGHT[1]-FLIMIT_HEIGHT[0]),
                          self.ice_mask.get_bounding_rects()[0]]
        self.ice_gap_rect = pygame.Rect(270, 0, 66, 175)

        if 'field' in option('debug'):
            debug("FIELD: ice rects: %s"%self.ice_rects)

        self.start = pygame.Surface((640,480))
        self.start.blit(self.bg, (0, 0))
        self.start.blit(self.ice, (0, ICE_YOFFSET))

        self.field = self.start.copy()
        self.ticks = 0                  # total ticks field played

        self.screen.blit(self.field, (0,0))
        # System font, for messages and FPS
        self.sfont = load_font("default.ttf", 14)

        # FPS drawer if needed
        if "fps" in option("show"):
            self.fps = pygame.sprite.GroupSingle()
            self.fps.add(pygame.sprite.DirtySprite())
#            self.fpsprite = pygame.sprite.DirtySprite()
            self.update_fpsprite()
            # show FPS rate on top of everything
            self.add(self.fps, layer=TOP_LAYER)

        # Messages
        self.messages = []
        self.show_messages = []

        self.msgs = pygame.sprite.DirtySprite()
        self.msgs.visible = 0
        self.msgs_offset = 0
        self.msgs_linesize = self.sfont.get_linesize()
        _ssh = self.msgs_linesize * option("max-messages")
        sprite_image(self.msgs, pygame.Surface((640, _ssh)))
        sprite_move(self.msgs, 0, 71)
        self.add(self.msgs, layer=0)

        # Sprite for level's progress
        self.lp_font = load_font('trebuc.ttf', 14)
        self.lp_font.set_bold(True)

        self.level_prgrs = pygame.sprite.DirtySprite()
        sprite_image(self.level_prgrs, pygame.Surface((640, 20)))
        sprite_move(self.level_prgrs, 0, 0)
        self.level_prgrs.image.blit(self.bg, (0,0), self.level_prgrs.rect)
        self.add(self.level_prgrs, layer=TOP_LAYER)

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

    def render_bosses_progress(self):
        """Render bosses life instead of level progress."""
        _bsi = self.level_prgrs.image
        _bsi.blit(self.bg, (0,0), self.level_prgrs.rect)
#        _bsi.fill((0,0,0))
        _bst = self.lp_font.render("Boss:", True, (255,255,255))
        _bsi.blit(_bst, (3, 3))
        _bstw = _bst.get_width()
        _pbw = 640-15-_bstw
        pygame.draw.rect(_bsi, (0,0,0), (8+_bstw, 3, _pbw, 17), 1)

        _bosses = filter(lambda x: x.isboss, self.creatures(Enemy))
        _clife = sum(map(lambda x: max(x.life,0), _bosses))
        _slife = sum(map(lambda x: x.slife, _bosses))
        _cko = 1.0*_clife/_slife if _slife else 0
        _cw = int(_cko*(_pbw-2))
        pygame.draw.rect(_bsi, (255,255,255), (9+_bstw, 4, _cw, 15))

        # Mark it as dirty
        self.level_prgrs.dirty = 1

    def update_fpsprite(self):
        ft = "FPS: %d, Objects: %d"% \
             (round(self.clock.get_fps()), len(self.objects))
        sprite_image(self.fps.sprite, self.sfont.render(ft, True, (0,0,0)))
        sprite_move(self.fps.sprite, 0, 480-14)
        self.fps.sprite.dirty = 1

    def add(self, *args, **kwargs):
        """Add object O to field object list."""
        LayeredDirty.add(self, *args, **kwargs)

        # Append object in-place, even if ticking
        for o in args:
            if hasattr(o, "tick"):
                self.objects.append(o)

##        if kwargs.get("append", False):
##            self.objects.extend(args)
##        else:
##            map(lambda o: self.objects.insert(0, o), args)

    def remove(self, *args):
        """Remove object O from field's object list."""
        LayeredDirty.remove(self, *args)

        # Mark as deleted, so object will be deleted on next tick
        self.deleted.extend(args)

    def has_object(self, o):
        return o in self.objects

    def tick(self):
        # 0. Tick the field
        self.ticks += 1

        if not self.players:
            # Speed-up enemies
            self.lockfps = FPS * 3

        # 1. Tick the level
        if self.level.finished:
            if self.level.num == 6:
                pass
##                self.game_over = True       # avoid debugging
##                self.game_is_over(None)
##                return
            else:
                self.run_level(self.level.num + 1)

        if self.level.started:
            self.level.tick(self)

        # 1.5) Render level (or bosses) progress
        if self.level.seen_bosses:
            self.render_bosses_progress()
        elif self.ticks % 3 == 1:
            self.render_level_progress()

        # 2. Tick all ticking objects
        for to in copy.copy(self.objects):
            to.tick(self)

        # 3. Remove deleted (while ticking) objects
        for do in self.deleted:
            if do in self.objects:
                self.objects.remove(do)
        self.deleted = []

        # 4. Draw FPS
        if "fps" in option("show"):
            self.update_fpsprite()

        # 5. Scroll the messages
        if self.show_messages \
               and self.ticks - self.msg_ticks > option("messages-speed"):
            _msgst = (self.ticks - self.msg_ticks) % option("messages-speed")
            if _msgst <= self.msgs_linesize:
                if _msgst == self.msgs_linesize:
                    self.show_messages = self.show_messages[1:]
                    self.msgs_offset = 0
                else:
                    self.msgs_offset -= 1
                self.update_messages()

        # 6. Redraw the screen
        self.clear(self.screen, self.field)
        urects = self.draw(self.screen)
        pygame.display.update(urects)
##        self.fps.clear(self.screen, self.field)
##        self.fps.draw(self.screen)
##        pygame.display.update([pygame.Rect(0, 400, 200, 80)])#urects)

        # 7. Lock the frame rate
        if ENABLE_ACCURATE_FPS:
            self.clock.tick_busy_loop(self.lockfps)
        else:
            self.clock.tick(self.lockfps)

        # DONE

    def clear_field(self, flip_display=False):
        "Remove all static objects from the field."
        self.field.blit(self.start, (0,0))
        self.screen.blit(self.field, (0,0))

        # Mark all sprites as dirty to redraw them all
        for s in self.sprites():
            s.dirty = True

        self.draw(self.screen, self.field)
        if flip_display:
            pygame.display.flip()

    def draw_field(self, surf, x, y):
#        return
        # Update the field as well
        self.field.blit(surf, (x, y))

#         rec = (x,y)+surf.get_size()
#         self.screen.blit(self.field, (x, y), rec)
#         pygame.display.update(rec)

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
        if self.ice_rects[0].collidepoint(x,y):
            return True
        elif self.ice_gap_rect.collidepoint(x,y):
            # Hack to handle ice gap
            xoff = x - self.ice_gap_rect.left
            return y > 160 + xoff*0.272727

        return (toponly or self.ice_rects[1].collidepoint(x,y)) \
               and y < 480 \
               and self.ice_mask.get_at((int(x), int(y-ICE_YOFFSET)))

    def creatures(self, *classes, **kwargs):
        """Return list of alive creatures here in the field."""
        all = kwargs.get("all", False)
        def suited_creature(c):
            return isinstance(c, objects.Creature) \
                   and (not classes or isinstance(c, classes)) \
                   and (all or c.is_alive())
        return filter(suited_creature, self.objects)

    def allplayers(self):
        """Return list of players in the field."""
        return self.creatures(Player, all=True)

    def game_is_over(self, by_enemy, force=False):
        # Update players stats
        for p in self.players:
            p.pstats["time"] = 1.0*self.ticks/FPS
            if by_enemy:
                p.pstats["game-over-by"] = by_enemy.__class__.__name__
            _lvl = self.level
            _lvl_done = 100.0*_lvl.ticks/_lvl.level_ticks
            p.pstats["progress"] = (_lvl.num, _lvl_done)
            # Update the time in seconds, weapons has been used
            wpnstats = p.pstats["weapons"]
            for w in p.weapons:
                wpnstats[w.name]["time"] = 1.0*w.usage_ticks/FPS

        if not force and option("debug"):
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

        if len(self.show_messages) > option("max-messages"):
            self.show_messages = self.show_messages[1:]

        self.update_messages()

    def handle_event(self, event):
        """Handle EVENT on the field."""
        if 'field' in option('debug') and event.type in [KEYDOWN, KEYUP]:
            debug("Key %s %s"%(event.type, event.key))

        if event.type == QUIT or \
               (event.type == KEYUP and event.key == K_ESCAPE):
            self.game_is_over(None, force=True)
            return

        self.console.handle_event(event)

        for p in self.players:
            p.handle_event(event)

    def run_level(self, n):
        """Run the level number N."""
        # - Remove old splash if any
        for o in self.objects:
            if isinstance(o, LevelSplash):
                self.remove(o)

        self.players = self.creatures(Player, all=True)
        self.level = new_level(self, n)

    def run(self):
        """Run the field untli game is over."""
        self.run_level(1)

        while not self.game_over:
            for pyev in pygame.event.get():
                self.handle_event(pyev)

            self.tick()

        # XXX Stop all sounds
        pygame.mixer.stop()
