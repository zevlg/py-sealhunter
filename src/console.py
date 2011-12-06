# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

# Port of pyconsole by John Schanck to SealHunter
#
# pyconsole - a simple console for pygame based applications 
#
# Copyright (C) 2006  John Schanck
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import pygame, sys 
from pygame.locals import *

import textwrap                         # Used for proper word wrapping
from itertools import ifilter
from string import ascii_letters
from code import InteractiveConsole     # Gives us access to the python interpreter

from misc import load_font, option, options, options_load, key2keycode
from constants import *

WIDTH, HEIGHT = 0, 1
OUT, IN, ERR = 0, 1, 2

options_load()
FS = option("fullscreen")
def fullscreen(c):
    """/fs - Toggle fullscreen"""
    global FS
    pygame.display.set_mode((640,480), FULLSCREEN if not FS else 0)
    FS = not FS

def windowed(c):
    """/windowed - Force windowed mode."""
    pygame.display.set_mode((640,480), HWSURFACE|DOUBLEBUF)

def bind(c, arg):
    """/bind <player> <key> <command> - Bind <key> to execute <command>
       Built-in commands: left, right, up, down, fire, reload, buy, switch"""
    sarg = arg.split(" ", 2)
    pidx, kcode = int(sarg[0]), key2keycode(sarg[1])

    plr = option("players")[pidx]
    if len(sarg) < 3:
        # print bound key
        cmd = plr["keys"].get(kcode, "unbound")
        c.message("%s: '%s' --> %s"%(plr["name"], sarg[1], cmd))
        return

    plr["keys"][kcode] = sarg[2]

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].profile["keys"][kcode] = sarg[2]

def skin(c, arg):
    """/skin <player> <color> - Set skin for the player."""
    sarg = arg.split()
    pidx = int(sarg[0])
    skin = pygame.Color(sarg[1])

    psetup = option("players")
    psetup[pidx]["skin"] = skin

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].set_skin(skin)

def alias(c, arg):
    """/alias <newname> <oldname> - Define command <newname> to execute <oldname> command"""
    global commands
    k, v = arg.split()
    commands[k] = commands[v]

def say(c, arg):
    """/say <player> <message> - Say the <message> to the public.
                                 <player> - index of the player"""
    sarg = arg.split(" ", 1)
    pidx = int(sarg[0])

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].say0(sarg[1])

def get_option(c, arg):
    """/get <optname> - Print value for <optname>"""
    if not options().has_key(arg):
        c.message("- Unknown option: %s"%arg)
        c.message("Available options: %s"%options().keys())
    else:
        c.message("%s => %s"%(arg, repr(option(arg))))

def set_option(c, arg):
    """/set <optname> <value> - Set <optname> to <value>"""
    k, v = arg.split(" ", 1)
    options()[k] = eval(v)
    get_option(c, k)

def quit(c):
    """/quit - Quit the game."""
    print "quit"
    sys.exit(0)

def screenshot(c, fn=None):
    """/screenshot [<filename>] - Take a screenshot"""
    if not fn:
        import time
        fn = "sealhunter-%s.png"%time.strftime("%Y-%m-%d--%X")

    c.message("+ Screenshot -> %s"%fn)
    pygame.image.save(pygame.display.get_surface(), fn)

def clear_field(c):
    """/clear - Clear blood and corpses from the field"""
    if 'f' in c.locals:
        c.locals['f'].clear_field('player' in c.locals)
        c.orig_screen = pygame.display.get_surface().copy()

def import_plugin(c, arg):
    """/import <plugin> - Import plugin."""
    # NOT YET
    exec "import %s"%arg

def exec_file(c, arg):
    """/exec <file> - Execute file with commands."""
    def not_comment(l):
        _, line = l
        line = line.lstrip()
        return not line or line[0] != "#"

    with open(arg, "r") as f:
        lnum = 0
        for lnum, line in ifilter(not_comment, enumerate(f)):
            line = line[:-1]            # strip \n
            try:
                if line and line[0] == "/":
                    c.send_command(line[1:])
                else:
                    c.send_python(line)
            except Exception as err:
                c.message("Error (%s) line=%d: %s"%(err.__class__, lnum, err))

##                err = c.safe_send_command(l[:-1])
##                if err:
##                    c.message("Error (%s) line=%d: %s"%(err.__class__, lnum, err))
#        map(c.safe_send_command, filter(ws_and_comments, f))

def echo(c, arg):
    """/echo <msg> - Output message to the console"""
    c.message(arg)

def level(c, arg):
    """/level <num> [<ticks>] - Start player level <NUM>."""
    import levels
    import itertools

    args = arg.split()
    if len(args) > 1:
        lvl, ticks = int(args[0]), int(args[1])
    else:
        lvl, ticks = int(arg), 0

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.run_level(lvl)
    for i in range(ticks):
        fld.level.tick(fld)

def newgame(c):
    """/newgame - Start a new game."""
    import sealhunter
    psetup = option("players")
    sealhunter.new_game(psetup[0]["name"], c)

def help(c):
    """/help - Print available commands."""
    global commands
    for cmd, cfun in commands.iteritems():
        c.message("%s"%cfun.__doc__)

commands = {"fs":fullscreen, "get":get_option,
            "set":set_option, "quit":quit,
            "screenshot": screenshot,
            "wind":windowed, "bind":bind,
            "clear":clear_field,
            "skin":skin, "alias":alias,
            "say": say, "level":level,
            "exec":exec_file, "echo":echo,
            "newgame":newgame,
            "import":import_plugin,
            "help": help}

    
class Writable(list):
    line_pointer = -1
    def write(self, line):
        self.append(str(line))
    def reset(self):
        self.__init__()
    def readline(self, size=-1):
        # Python's interactive help likes to try and call
        # this, which causes the program to crash I see no
        # reason to implement interactive help.
        raise NotImplementedError

class ParseError(Exception):
    def __init__(self, token):
        self.token = token
    def at_token(self):
        return self.token

class Console:
    def __init__(self, screen, rect, locals={}):
        self.key_calls = []
        if not pygame.display.get_init():
            raise pygame.error, "Display not initialized. Initialize the display before creating a Console"

        if not pygame.font.get_init():
            pygame.font.init()

        self.parent_screen = screen
        self.rect = pygame.Rect(rect)
        self.size = self.rect.size

        self.locals = locals
        self.variables = {\
                        "bg_alpha":int,\
                        "bg_color": list,\
                        "txt_color_i": list,\
                        "txt_color_o": list,\
                        "ps1": str,\
                        "ps2": str,\
                        "ps3": str,\
                        "active": bool,\
                        "repeat_rate": list,\
                        "preserve_events":bool,\
                        "motd":list
                        }

        self.init_variables()
        self.set_interpreter()

        pygame.key.set_repeat(*self.repeat_rate)

        self.bg_layer = pygame.Surface(self.size)
        self.bg_layer.set_alpha(self.bg_alpha)

        self.txt_layer = pygame.Surface(self.size)
        self.txt_layer.set_colorkey(self.bg_color)

        try:
            self.font = load_font('default.ttf', CONSOLE_FONT_SIZE)
        except IOError:
            self.font = pygame.font.SysFont("monospace", CONSOLE_FONT_SIZE)

        self.font_height = self.font.get_linesize()
        self.max_lines = (self.size[HEIGHT] / self.font_height) - 1

        self.max_chars = (self.size[WIDTH]/(self.font.size(ascii_letters)[WIDTH]/len(ascii_letters))) - 1
        self.txt_wrapper = textwrap.TextWrapper()

        self.c_out = self.motd
        self.c_hist = [""]
        self.c_hist_pos = 0
        self.c_in = ""
        self.c_pos = 0
        self.c_draw_pos = 0
        self.c_scroll = 0

        self.changed = True


    ##################
    #-Initialization-#
    def init_variables(self):
        self.bg_alpha = CONSOLE_BG_ALPHA
        self.bg_color = CONSOLE_BG_COLOR
        self.txt_color_i = CONSOLE_ICOLOR
        self.txt_color_o = CONSOLE_OCOLOR
        self.ps1 = CONSOLE_PS1
        self.ps2 = CONSOLE_PS2
        self.ps3 = CONSOLE_PS3
        self.active = CONSOLE_ACTIVE
        self.repeat_rate = CONSOLE_REPEAT_RATE
        self.motd = CONSOLE_MOTD + ["+ Use /help to list commands"]

    def output(self, text):
        """Prepare text to be displayed
        Arguments:
            text -- Text to be displayed
        """
        if not str(text):
            return;

        try:
            self.changed = True
            if not isinstance(text,str):
                text = str(text)
            text = text.expandtabs()
            text = text.splitlines()
            self.txt_wrapper.width = self.max_chars
            for line in text:
                for w in self.txt_wrapper.wrap(line):
                    self.c_out.append(w)
        except:
            pass

    def set_active(self,b=None):
        '''\
        Activate or Deactivate the console
        Arguments:
            b -- Optional boolean argument, True=Activate False=Deactivate
        '''
        if not b:
            self.active = not self.active
        else:
            self.active = b


    def format_input_line(self):
        '''\
        Format input line to be displayed
        '''
        # The \v here is sort of a hack, it's just a character that
        # isn't recognized by the font engine
        text = self.c_in[:self.c_pos] + "\v" + self.c_in[self.c_pos+1:] 
        n_max = self.max_chars - len(self.c_ps)
        vis_range = self.c_draw_pos, self.c_draw_pos + n_max
        return self.c_ps + text[vis_range[0]:vis_range[1]]

    def draw(self):
        '''Draw the console to the parent screen'''
        if not self.active:
            return;

        if self.changed:
            self.changed = False
            # Draw Output
            self.txt_layer.fill(self.bg_color)
            lines = self.c_out[-(self.max_lines+self.c_scroll):len(self.c_out)-self.c_scroll]
            y_pos = self.size[HEIGHT]-(self.font_height*(len(lines)+1))

            for line in lines:
                tmp_surf = self.font.render(line, True, self.txt_color_o)
                self.txt_layer.blit(tmp_surf, (1, y_pos, 0, 0))
                y_pos += self.font_height
            # Draw Input
            tmp_surf = self.font.render(self.format_input_line(), True, self.txt_color_i)
            self.txt_layer.blit(tmp_surf, (1,self.size[HEIGHT]-self.font_height,0,0))
            # Clear background and blit text to it
            self.bg_layer.fill(self.bg_color)
            self.bg_layer.blit(self.txt_layer,(0,0,0,0))

        # Draw console to parent screen
        # self.parent_screen.fill(self.txt_color_i, (self.rect.x-1, self.rect.y-1, self.size[WIDTH]+2, self.size[HEIGHT]+2))
        pygame.draw.rect(self.parent_screen, self.txt_color_i,
                         (self.rect.x-1, self.rect.y-1, self.size[WIDTH]+2,
                          self.size[HEIGHT]+2), 1)
        self.parent_screen.blit(self.bg_layer,self.rect)

    #######################################################################
    # Functions to communicate with the console and the python interpreter#
    def set_interpreter(self):
        self.output("Entering Python mode")
        self.python_interpreter = InteractiveConsole(self.locals)
        self.tmp_fds = []
        self.py_fds = [Writable() for i in range(3)]
        self.c_ps = self.ps2

    def catch_output(self):
        if not self.tmp_fds:
            self.tmp_fds = [sys.stdout, sys.stdin, sys.stderr]
            sys.stdout, sys.stdin, sys.stderr = self.py_fds

    def release_output(self):
        if self.tmp_fds:
            sys.stdout, sys.stdin, sys.stderr = self.tmp_fds
            self.tmp_fds = []
            [fd.reset() for fd in self.py_fds]

    def message(self, msg):
        """Show message on the field or in the console."""
        if 'f' in self.locals and not self.active:
            fld = self.locals['f']
            fld.message(msg)
        else:
            self.output(msg)
        
    def submit_input(self, text):
        '''\
        Submit input
            1) Move input to output
            2) Evaluate input
            3) Clear input line
        '''

        self.clear_input()
        self.message(self.c_ps + text)
        self.c_scroll = 0

        if text: self.add_to_history(text)
        try:
            if text and text[0] == "/":
                self.send_command(text[1:])
            else:
                self.send_python(text)
        except Exception as err:
            self.message("- Error: %s"%err)

    def safe_send_command(self, text):
        try:
            self.send_command(text)
        except Exception as err:
            return err

    def send_command(self, text):
        def parse_command(text):
            return text.split(" ", 1)

        self.catch_output()
        cmd_arg = parse_command(text)
        cmd = cmd_arg[0]
        if len(cmd_arg) > 1: arg = (cmd_arg[1],)
        else: arg = ()
        if cmd not in commands.keys():
            self.message("Unknown command: %s"%cmd)
        else:
            # execute command and print it's output
            try:
                ret = apply(commands[cmd], (self,)+arg)
                if ret:
                    self.message("Ret: %s"%ret)
            except Exception as err:
                # Show command usage
                self.message("Error: %s"%err)
                self.message(commands[cmd].__doc__)
        self.release_output()

    def send_python(self, text):
        '''\
        Sends input the the python interpreter in effect giving the user the ability to do anything python can.
        '''
        self.c_ps = self.ps2
        self.catch_output()
        if text:
            if self.python_interpreter.push(text):
                self.c_ps = self.ps3
        else:
            code = "".join(self.py_fds[OUT])
            self.python_interpreter.push("\n")
            self.python_interpreter.runsource(code)
        for i in self.py_fds[OUT]+self.py_fds[ERR]:
            self.output(i)
        self.release_output()

    def add_to_history(self, text):
        '''\
        Add specified text to the history
        '''
        self.c_hist.insert(-1,text)
        self.c_hist_pos = len(self.c_hist)-1

    def clear_input(self):
        '''\
        Clear input line and reset cursor position
        '''
        self.c_in = ""
        self.c_pos = 0
        self.c_draw_pos = 0

    def set_pos(self, newpos):
        '''\
        Moves cursor safely
        '''
        self.c_pos = newpos
        if (self.c_pos - self.c_draw_pos) >= (self.max_chars - len(self.c_ps)):
            self.c_draw_pos = max(0, self.c_pos - (self.max_chars - len(self.c_ps)))
        elif self.c_draw_pos > self.c_pos:
            self.c_draw_pos = self.c_pos - (self.max_chars/2)
            if self.c_draw_pos < 0:
                self.c_draw_pos = 0
                self.c_pos = 0

    def str_insert(self, text, strn):
        """Insert characters at the current cursor position."""
        foo = text[:self.c_pos] + strn + text[self.c_pos:]
        self.set_pos(self.c_pos + len(strn))
        return foo

    def handle_event(self, event):
        if event.type == KEYDOWN and event.key in CONSOLE_KEYS:
            self.orig_screen = pygame.display.get_surface().copy()
            self.active = True
            while self.active:
                self.process_input()
                self.parent_screen.blit(self.orig_screen, self.rect)
                self.draw()
                pygame.display.flip()

            # restore the screen
            self.parent_screen.blit(self.orig_screen, self.rect)
            pygame.display.flip()

    def process_input(self):
        '''\
        Loop through pygame events and evaluate them
        '''
        if not self.active:
            return;

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                self.changed = True
                ## Special Character Manipulation
                if event.key == K_TAB:
                    self.c_in = self.str_insert(self.c_in, "    ")
                elif event.key == K_BACKSPACE:
                    if self.c_pos > 0:
                        self.c_in = self.c_in[:self.c_pos-1] + self.c_in[self.c_pos:]
                        self.set_pos(self.c_pos-1)
                elif event.key == K_DELETE:
                    if self.c_pos < len(self.c_in):
                        self.c_in = self.c_in[:self.c_pos] + self.c_in[self.c_pos+1:]
                elif event.key == K_RETURN or event.key == 271:
                    self.submit_input(self.c_in)
                ## Changing Cursor Position
                elif event.key == K_LEFT:
                    if self.c_pos > 0:
                        self.set_pos(self.c_pos-1)
                elif event.key == K_RIGHT:
                    if self.c_pos < len(self.c_in):
                        self.set_pos(self.c_pos+1)
                elif event.key == K_HOME:
                    self.set_pos(0)
                elif event.key == K_END:
                    self.set_pos(len(self.c_in))
                ## History Navigation
                elif event.key == K_UP:
                    if len(self.c_out):
                        if self.c_hist_pos > 0:
                            self.c_hist_pos -= 1
                        self.c_in = self.c_hist[self.c_hist_pos]
                        self.set_pos(len(self.c_in))
                elif event.key == K_DOWN:
                    if len(self.c_out):
                        if self.c_hist_pos < len(self.c_hist)-1:
                            self.c_hist_pos += 1
                        self.c_in = self.c_hist[self.c_hist_pos]
                        self.set_pos(len(self.c_in))
                ## Scrolling
                elif event.key == K_PAGEUP:
                    if self.c_scroll < len(self.c_out)-1:
                        self.c_scroll += 1
                elif event.key == K_PAGEDOWN:
                    if self.c_scroll > 0:
                        self.c_scroll -= 1
                elif event.key in CONSOLE_KEYS:
                    self.active = False
                elif event.key == K_ESCAPE:
                    self.active = False
                ## Normal character printing
                elif event.key >= 32:
                    mods = pygame.key.get_mods()
                    if mods & KMOD_CTRL:
                        if event.key in range(256) and chr(event.key) in self.key_calls:
                            self.key_calls[chr(event.key)]()
                    else:
                        char = str(event.unicode)
                        self.c_in = self.str_insert(self.c_in, char)
