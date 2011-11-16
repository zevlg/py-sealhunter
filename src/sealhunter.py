# Copyright (C) 2009-2011 by Zajcev Evegny <zevlg@yandex.ru>

__version__ = "0.2"
__author__ = "Zajcev Evgeny <zevlg@yandex.ru>"

import pygame
from pygame.locals import *

import menu, field, console, levels, player, hud
from misc import *
from constants import *

def start_sealhunter(config=None):
    options_load()

    # Initialize everything we need from pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(32)

    pygame.display.set_icon(pygame.image.load("textures/Misc/sh-icon.png"))
    vflags = HWSURFACE | DOUBLEBUF
    if option("fullscreen"):
        vflags |= FULLSCREEN
    pygame.display.set_mode((640, 480), vflags)
    pygame.display.set_caption('SealHunter v%s'%__version__)
    pygame.mouse.set_visible(0)

    # Exec the given config
    cons = None
    if config:
        cons = setup_console()
        cons.send_command("exec %s"%config)

#    new_game(["Clark Kent", "Peter Parker"], cons)
#    return

    menu.menu_init()
    menu.do_mainmenu(cons)
    return

    options_save()

def setup_console():
    """Initialize SealHunter console."""
    shcons = console.Console(pygame.display.get_surface(),
                             (0,0,640,CONSOLE_HEIGHT))
    return shcons

def new_game(players_names, cons=None):
    """Start game for PLAYERS."""
    hud.huds_reset()

    # Setup sealhunter console
    shcons = cons or setup_console()
    fld = field.Field(shcons)
    shcons.locals['f'] = fld

    def make_player(profile):
        return player.Player(profile, field=fld)
    def good_player(p):
        return p["name"] in players_names
    fld.add(*map(make_player, filter(good_player, option("players"))))

    # Start the game
    fld.run()

    # print players stats
    for p in fld.players:
        p.print_pstats()

##    players = filter(lambda p: p["name"] in players_names, option("players"))
##    # Field to play on
##    fld = field.Field(len(players))

##    def make_player(profile):
##        return player.Player(profile, field=fld)

##    # Create players
##    players = map(make_player, players)
##    # Start players on the field
##    map(fld.add, players)

##    # Setup sealhunter console
##    shcons = cons or setup_console()
##    shcons.locals['f'] = fld

##    fld.console = shcons

##    # xXX
###    ak = Aktivist(x=-15, y=250, field=fld)
###    fld.add(ak)

##    players[0].earn_money(100000)
##    players[0].apply_earned_money()

##    # optimization, player handles down/up, so no repeating
##    pygame.key.set_repeat()

##    while not fld.game_over:
##        kevents = pygame.event.get()
##        for event in kevents:
##            if event.type == QUIT or \
##                   (event.type == KEYUP and event.key == K_ESCAPE):
##                debug("Final FPS: %f"%fld.clock.get_fps())
##                return

##            if 'keys' in option("debug") and event.type == KEYDOWN:
##                debug("Keys: KeyDown: %d/%s"
##                      %(event.key, pygame.key.name(event.key)))

##            # Maybe console event
##            # NOTE: Use console to pause games
##            shcons.handle_event(event)

##            # Player event ?
##            for p in players:
##                p.handle_event(event)

##        fld.tick()

##    # Stop all sounds
###    pygame.mixer.stop()
