
from pygame.constants import *

PREFIX = "/usr/home/lg/dev/sealhunter/"

FULLSCREEN = False

REFLECTIONS = True
DRAW_SHELLS = True

PLAYERS_DISPLAY_INFO = True
PLAYERS_DISPLAY_CROSSHAIR = True
P1_KEYS = {'Left': K_LEFT, 'Right': K_RIGHT,
           'Up': K_UP, 'Down': K_DOWN,
           'Fire': K_SPACE, 'Reload': K_LSHIFT,
           'Buy': K_RETURN, 'Switch': K_F2 }
P1_START_POSITION = (620.0, 220.0)

P2_KEYS = {'Left': K_o, 'Right': K_u,
           'Up': K_PERIOD, 'Down': K_e,
           'Fire': K_TAB, 'Reload': K_RSHIFT,
           'Buy': K_F1, 'Switch': K_F3 }
P2_START_POSITION = (620.0, 350.0)

PLAY_MUSIC = False
MUSIC_SHUFFLE = True
MUSIC_DIR = PREFIX + "music/"

SHOW_FPS = True
SNIPER_SIGHT_COLORS = ((225,150,0), (255, 0, 0))
SNIPER_SIGHT_OPAQUE = 50

# SealHunter console settings
CONSOLE_KEY = K_F1               # key to enter console
CONSOLE_BG_ALPHA = 200
CONSOLE_BG_COLOR = [0x0,0x44,0xAA]

CONSOLE_FONT_SIZE = 14
CONSOLE_ICOLOR = [0xFF,0xFF,0xFF]
CONSOLE_OCOLOR = [0xEE,0xEE,0xEE]

CONSOLE_PS1 = "] "
CONSOLE_PS2 = ">>> "
CONSOLE_PS3 = "... "

CONSOLE_ACTIVE = False
CONSOLE_REPEAT_RATE = [500,30]
CONSOLE_PRESERVE_EVENTS = True

CONSOLE_PYTHON_MODE = True
CONSOLE_MOTD = ["[SealHunter Console]"]
