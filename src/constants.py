# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>
#
# Constants used in SealHunter

from pygame.constants import *

# setting ENABLE_ACCURATE_FPS to True will cause CPU heating
ENABLE_ACCURATE_FPS = False

FPS = 50
LEVEL_TICKS = 3000                      # 1 minute per level
#LEVEL_TICKS = 200                      # 1 minute per level

# Field specifics
TOP_LAYER = 500

ICE_YOFFSET = 51
FLIMIT_WIDTH = (0, 640)
FLIMIT_HEIGHT = (185, 480-52)

BULLET_OPAQUE = 100

G_ACCEL = 0.33
REFLECTION_OPAQUE = 60
ENEMY_REFLECTION_OPAQUE = 30
PLAYER_REFLECTION_OPAQUE = 30

PLAYER_LIFE = 1000

PLAYER_XMAX = 2.0
PLAYER_YMAX = 1.3
PLAYER_XACC = 0.1
PLAYER_YACC = 0.06

ICE_FRICTION = 0.03
ICE_XFRIC = ICE_FRICTION*PLAYER_XMAX
ICE_YFRIC = ICE_FRICTION*PLAYER_YMAX

MONEY_FONT_SIZE = 9
EARNMONEY_FONT_SIZE = 10

PAUSE_KEYS = [K_p, K_BREAK, K_PAUSE]

CONSOLE_KEYS = [K_F1, K_BACKQUOTE, K_RIGHTBRACKET]
CONSOLE_HEIGHT = 300
CONSOLE_FONT_SIZE = 14
CONSOLE_BG_ALPHA = 220
CONSOLE_BG_COLOR = [0x0,0x44,0xAA]
CONSOLE_ICOLOR = [0xFF,0xFF,0xFF]
CONSOLE_OCOLOR = [0xEE,0xEE,0xEE]
CONSOLE_PS1 = "] "
CONSOLE_PS2 = ">>> "
CONSOLE_PS3 = "... "
CONSOLE_ACTIVE = False
CONSOLE_REPEAT_RATE = [500,30]
CONSOLE_MOTD = ["[SealHunter Console]"]

# if true then play random bounce sounds when shell bounds
# otherwise play it in order starting from first sound
RANDOM_BOUNCE_SOUNDS = True

WEAPON_NAMES = ["Pistol", "Magnum", "MP5", "Grenades", "Shotgun",
                "MAC10", "Flunk", "M4", "AWP", "VintageShotgun",
                "Minigun"]
WEAPONS = {"Pistol": {"price": 0,
                      "wpn_position": (10, 11),
                      "aim_position": 9,
                      "damage": 18,
                      "muzzle": "small",
                      "clip_size": 12,
                      "fire_ticks": 13,
                      "reload_ticks": 100},
           "Magnum": {"price": 500,
                      "wpn_position": (14, 11),
                      "aim_position": 10,
                      "x_recoil": 1.0,
                      "damage": 60,
                      "damage_inc": 5,
                      "muzzle": "big",
                      "clip_size": 6,
                      "fire_ticks": 20,
                      "reload_ticks": 110,
                      "pierce": 0.7},
           "MP5": {"price": 1000,
                   "wpn_position": (10, 8),
                   "aim_position": 8,
                   "x_recoil": 0.3,
                   "damage": 23,
                   "damage_inc": 2,
                   "muzzle": "small",
                   "clip_size": 30,
                   "fire_ticks": 5,
                   "reload_ticks": 80},
           "Grenades": {"price": 1500,
                        "wpn_position": (2, 8),
                        "aim_position": 10,
                        "damage": 250,
                        "clip_size": 1,
                        "fire_ticks": 8,
                        "reload_ticks": 50
                        },
           "Shotgun": {"price": 2500,
                       "wpn_position": (11, 9),
                       "aim_position": 8,
                       "cross_xoffset": 80,
                       "accuracy_angle": 7.5,
                       "x_recoil": 1.65,
                       "z_recoil": 1.9,
                       "damage": 40,
                       "muzzle": "shotgun",
                       "bullets_per_shot": 8,
                       "clip_size": 8,
                       "fire_ticks": 40,
                       "reload_ticks": 125},
           "MAC10": {"price": 3500,
                     "wpn_position": (11, 12),
                     "aim_position": 9,
                     "accuracy_angle": 4.0,
                     "x_recoil": 0.2,
                     "damage": 37,
                     "clip_size": 60,
                     "fire_ticks": 3,
                     "reload_ticks": 130},
           "Flunk": {"price": 5000,
                     "wpn_position": (16, 13),
                     "aim_position": 9,
                     "damage": 400,
                     "clip_size": 5,
                     "fire_ticks": 20,
                     "reload_ticks": 150},
           "M4": {"price": 6000,
                  "wpn_position": (18, 10),
                  "aim_position": 9,
                  "cross_xoffset": 60,
                  "damage": 40,
                  "muzzle": "big",
                  "x_recoil": 0.35,
                  "clip_size": 30,
                  "fire_ticks": 5,
                  "reload_ticks": 80,
                  "pierce": 0.8
                  },
           "AWP": {"price": 7500,
                   "wpn_position": (34, 13),
                   "aim_position": 9,
                   "cross_xoffset": 60,
                   "muzzle": "big",
                   "x_recoil": 3.2,
                   "z_recoil": 3.0,
                   "damage": 855,
                   "clip_size": 5,
                   "fire_ticks": 66,
                   "reload_ticks": 110,
                   "pierce": 0.9},
           "VintageShotgun": {"price": 10000,
                              "wpn_position": (28, 13),
                              "aim_position": 9,
                              "cross_xoffset": 80,
                              "x_recoil": 3.0,
                              "z_recoil": 3.5,
                              "damage": 125,
                              "muzzle": "shotgun",
                              "accuracy_angle": 5.25,
                              "bullets_per_shot": 15,
                              "clip_size": 2,
                              "fire_ticks": 50,
                              "reload_ticks": 50,
                              "pierce": 0.33
                              },
           "Minigun": {"price": 12500,
                       "wpn_position": (33, 15),
                       "aim_position": 4,
                       "cross_xoffset": 80,
                       "muzzle": "big",
                       "accuracy_angle": 1,
                       "damage": 65,
                       "x_recoil": 0.25,
                       "clip_size": 150,
                       "fire_ticks": 13,
                       "reload_ticks": 120,
                       "pierce": 0.5
                       }
           }

ENEMIES = {"Bruns":
           dict(life=(26, 21), ticks_step=3,
                speed_range=(0.5, 1.1),
                bounty=50, headshot_bonus=10,
                headshot_multiplier=2),

           "Knubbs":
           dict(life=(0, 250), boss_life=1250,
                ticks_step=3, speed_range=(0.7, 0.7),
                can_press=True, bounty=200,
                boss_bonus=200, headshot_multiplier=1.25),

           "Aktivist":
           dict(life=(30, 35), ticks_step=3,
                speed_range=(1.1, 2.0), bounty=100,
                headshot_bonus=15, headshot_multiplier=2),
           
           "Vits":
           dict(life=(10, 5), ticks_step=3,
                speed_range=(0.44, 0.74),
                can_press=True, bounty=25),

           "Pingvin":
           dict(life=(0, 25), ticks_step=3,
                speed_range=(0.64, 1.1), can_press=True, bounty=100,
                headshot_bonus=10, headshot_multiplier=2),

           "Bear":
           dict(life=(1700, 0), boss_life=2000,
                ticks_step=5, speed_range=(0.8, 7.4),
                can_press=True, bounty=500,
                headshot_multiplier=2),

           "Turtle":
           dict(life=(2500, 0), boss_life=2500,
                ticks_step=5, speed_range=(0.6, 0.6),
                can_press=False, bounty=500),

           # TODO: valross yet has invalid values
           "Valross":
           dict(life=(10000, 0), boss_life=10000,
                ticks_step=1, speed_range=(0.3, 8),
                can_press=True, bounty=50000,
                headshot_multiplier=2)
           }

# Not yet used
REFLECTION_OPAQUES = {"player": 30, "enemy": 30, "particle": 60}

# recoils
MAGNUM_XRECOIL = 1.0
MP5_XRECOIL = 0.3
SHOTGUN_XRECOIL = 1.65
SHOTGUN_ZRECOIL = 1.9
MAC10_XRECOIL = 0.2
M4_XRECOIL = 0.35
SNIPER_XRECOIL = 3.2
SNIPER_ZRECOIL = 3.0
VINTAGE_XRECOIL_PERSHELL = 1.5
VINTAGE_ZRECOIL_PERSHELL = 1.75
MINIGUN_XRECOIL = 0.25

SNIPER_SIGHT_OPAQUE = 50

# Color used in skins substitution
PLAYER_SCOLOR = (0,0x78,0xF8)
PLAYER_CHCOLOR = (0x3B, 0x6B, 0xCB)

P1_SETUP = {"name": "Clark Kent",
            "enabled": True,
            "skin": (0, 0, 180),
            "hud-position": (0, 12),
            "crosshair": True,
            "crosshair-color": (0x3B, 0x6B, 0xCB),
            "crosshair-info": True,
            "money-info": True,
            "show-earned-money": True,
            "show-hud": True,
            "start-at": (620, 220),
            "sniper-sight-color": [(255,0,0,50),(255,100,0,50)],
            "keys": {K_LEFT:'left', K_RIGHT:'right',
                     K_UP:'up', K_DOWN:'down',
                     K_SPACE:'fire', K_LSHIFT:'reload',
                     K_RETURN:"buy", K_CAPSLOCK:"switch"},
            "autokill-crawling-bruns": True,
            "autobuy-list": []}

P2_SETUP = {"name": "Peter Parker",
            "enabled": True,
            "skin": (0, 180, 0),
            "hud-position": (590, 12),
            "crosshair": True,
            "crosshair-color": (0x87, 0x2F, 0x00),
            "crosshair-info": True,
            "money-info": True,
            "show-earned-money": True,
            "show-hud": True,
            "start-at": (200,220),#(620, 350),
            "sniper-sight-color": [(150,225,0,50),(150,225,100,50)],
            "keys": {'Left': K_o, 'Right': K_u,
                     'Up': K_PERIOD, 'Down': K_e,
                     'Fire': K_TAB, 'Reload': K_RSHIFT,
                     'Buy': K_F4, 'Switch': K_F3 },
            "autokill-crawling-bruns": True,
            "autobuy-list": []}

P3_SETUP = {"name": "Max Eisenhardt",
            "enabled": True,
            "skin": (150, 0, 150),
            "crosshair": True,
            "crosshair-color": (0x87, 0x2F, 0x00),
            "crosshair-info": True,
            "money-info": True,
            "show-earned-money": True,
            "show-hud": False,
            "start-at": (300,400),#(620, 350),
            "sniper-sight-color": [(150,225,0,50),(150,225,100,50)],
            "keys": {},
            "autokill-crawling-bruns": True,
            "autobuy-list": []}

DEBUG_TYPES = ["player", "enemy", "weapon", "particle",
               "reflection", "level", "boss", "keys"]

DEFAULT_OPTIONS = {"reflections": ["player", "enemies", "weapon",
                                   "muzzle", "clips", "shells",
                                   "grenades", "particles"],
                   "accurate-fps": False,
                   "debug": (),
                   "fullscreen": False,

                   # Sounds settings
                   "sound": True,
                   "volume": 0.5,       # 0.0 - 1.0

                   # Music settings
                   "music": False,
                   "music-dir": None,
                   "music-shuffle": True,

                   # Show game particles
                   "show": ["fps", "clips", "shells", "bullets"],

                   # Misc
                   "max-messages": 4,

                   # Fun options
                   "bloody": 5,         # bloody level
                   "teamkills": True,   # enable teamkill
                   "minigun-explode": True,

                   "players": [P1_SETUP, P2_SETUP, P3_SETUP],
                   }
