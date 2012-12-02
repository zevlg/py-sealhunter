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
from itertools import ifilter, izip_longest, takewhile
from string import ascii_letters
from code import InteractiveConsole     # Gives us access to the python interpreter

from misc import load_font, option, options, options_load, key2keycode
from misc import play_sound
from constants import *

WIDTH, HEIGHT = 0, 1
OUT, IN, ERR = 0, 1, 2

options_load()
FS = option("fullscreen")
def fullscreen(c):
    u"""\u2022 /fs - Toggle fullscreen mode."""
    global FS
    pygame.display.set_mode((640,480), FULLSCREEN if not FS else 0)
    FS = not FS

def bind(c, arg):
    u"""\u2022 /bind <player> <key> <command>
    Bind <key> to execute <command>.
    Built-in commands: left, right, up, down, fire, reload, buy, switch
    Command also could be any console command if prefixed with '/',
    f.i. /bind 0 F2 /echo hello there"""
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
    u"""\u2022 /skin <player> <color>
    Set skin for the player.
    <player> - index of the player."""
    sarg = arg.split()
    pidx = int(sarg[0])
    skin = pygame.Color(sarg[1])

    psetup = option("players")
    psetup[pidx]["skin"] = skin

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].set_skin(skin)

def name(c, arg):
    u"""\u2022 /name <player> <name>
    Set name for the player.
    <player> - index of the player."""
    sarg = arg.split()
    pidx = int(sarg[0])

    psetup = option("players")
    psetup[pidx]["name"] = sarg[1]
    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].profile["name"]=sarg[1]

def alias(c, arg):
    u"""\u2022 /alias <newname> <oldname>
    Define command <newname> to execute <oldname> command"""
    global commands
    k, v = arg.split()
    commands[k] = commands[v]

def say(c, arg):
    u"""\u2022 /say <player> <message>
    Say the <message> to the public.
    <player> - index of the player"""
    sarg = arg.split(" ", 1)
    pidx = int(sarg[0])

    if 'f' not in c.locals:
        return
    fld = c.locals["f"]
    fld.players[pidx].say0(sarg[1])

def get_option(c, arg):
    u"""\u2022 /get <optname>
    Print value for <optname>"""
    if not options().has_key(arg):
        c.message("- Unknown option: %s"%arg)
        c.message("Available options: %s"%options().keys())
    else:
        c.message(u"%s \u21D2 %s"%(arg, repr(option(arg))))

def set_option(c, arg):
    u"""\u2022 /set <optname> <value>
    Set <optname> to <value>"""
    k, v = arg.split(" ", 1)
    options()[k] = eval(v)
    get_option(c, k)

def opt_command(c, arg):
    u"""\u2022 /opt <list|get|set> [<args>]
    List, get or set option values.
    /opt get <optname>         - get option value
    /opt set <optname> <value> - set option value
    /opt list                  - list all options values"""
    if arg == "list":
        # Exclude system "player" option
        for opt in options():
            if opt != "players":
                get_option(c, opt)
    elif arg.startswith("get"):
        _, oarg = arg.split(" ", 1)
        get_option(c, oarg)
    elif arg.startswith("set"):
        _, oarg = arg.split(" ", 1)
        set_option(c, oarg)
    else:
        help(c, "opt")

def opt_completion(x):
    if len(x) > 1 and x[1] in ["get", "set"] and len(x) < 4:
        oa = x[2] if len(x) > 2 else ""
        return filter(lambda s: s.startswith(oa), options().keys())
    elif len(x) < 3:
        oa = x[1] if len(x) > 1 else ""
        return filter(lambda s: s.startswith(oa), ["list", "get", "set"])
    else:
        return []

opt_command.completion_fun = opt_completion

def quit(c):
    u"""\u2022 /quit - Quit the game."""
    print "quit"
    sys.exit(0)

def screenshot(c, fn=None):
    u"""\u2022 /screenshot [<filename>] - Take a screenshot"""
    if not fn:
        import time
        fn = "sealhunter-%s.png"%time.strftime("%Y-%m-%d--%X")

    c.message("+ Screenshot -> %s"%fn)
    pygame.image.save(pygame.display.get_surface(), fn)

def clear_field(c):
    u"""\u2022 /clear
    Clear blood and corpses from the field."""
    if 'f' in c.locals:
        c.locals['f'].clear_field('player' in c.locals)
        c.orig_screen = pygame.display.get_surface().copy()

def import_plugin(c, arg):
    u"""\u2022 /import <plugin>
    Import sealhunter plugin from file <PLUGIN>.
    NOT YET supported"""
    # NOT YET
    exec("import %s"%arg)

def exec_file(c, arg):
    u"""\u2022 /exec <file>
    Execute console commands from <FILE>."""
    def not_comment(l):
        _, line = l
        line = line.lstrip()
        return not line or line[0] != "#"

    c.this_cmd = "exec"
    with open(arg, "r") as f:
        lnum = 0
        for lnum, line in ifilter(not_comment, enumerate(f)):
            line = line.strip()         # strip ws and \n
            try:
                if line and line[0] == "/":
                    c.send_command(line[1:])
                else:
                    c.send_python(line)
            except Exception as err:
                c.message("Error (%s) line=%d: %s"%(err.__class__, lnum, err))

    # Run post exec hooks
    if c.post_cmd:
        c.post_cmd()
    c.post_cmd = None

##                err = c.safe_send_command(l[:-1])
##                if err:
##                    c.message("Error (%s) line=%d: %s"%(err.__class__, lnum, err))
#        map(c.safe_send_command, filter(ws_and_comments, f))

def echo(c, arg):
    u"""\u2022 /echo <msg>
    Output message <MSG> to the console"""
    c.message(arg)

def level(c, arg):
    u"""\u2022 /level <num> [<ticks>]
    Start player level <NUM>."""
    import levels

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

def newgame(c, *arg):
    u"""\u2022 /newgame [<n>]
    Start a new game with <N> players. Single player by default."""
    n = int(arg[0]) if arg else 1
    psetup = option("players")
    if n > len(psetup):
        c.message("- Only %d players available in your configuration"%n)
    else:
        import sealhunter
        pnames = map(lambda x:x["name"], psetup[:n])
        sealhunter.new_game(pnames, c)

def addbot(c, *arg):
    u"""\u2022 /addbot [<ailevel>]
    Add bot to the game.  Default AILEVEL is 3.
    <AILEVEL> is the number in range [0-5], 5 is highest AI level."""
    n = int(arg[0]) if arg else 3
    if 'f' not in c.locals:
        c.message("- Please start /newgame first")
        return

    fld = c.locals["f"]
    import player
    bot = player.AIPlayer(field=fld, ailevel=n)
    fld.add(bot)

def help(c, *arg):
    u"""\u2022 /help [<cmd>]
    Print help for the command <CMD>.
    If <CMD> is not provided print help for all available commands."""
    def msg_help_doc(cfun):
        c.message("%s"%cfun.__doc__)

    global commands
    if len(arg):
        if commands.get(arg[0]):
            msg_help_doc(commands[arg[0]])
        else:
            c.message("- Unknown command `%s'"%arg)
    else:
        for cmd, cfun in commands.iteritems():
            c.message("%s"%cfun.__doc__)

def help_completion(x):
    global commands
    x = x[1] if len(x) > 1 else ""
    return filter(lambda s: s.startswith(x), commands.keys())

help.completion_fun = help_completion

commands = {"fs":fullscreen, "opt":opt_command,
            "quit":quit, "screenshot": screenshot,
            "bind":bind, "clear":clear_field,
            "skin":skin, "name":name, "alias":alias,
            "say": say, "level":level, "exec":exec_file,
            "echo":echo, "newgame":newgame,
            "import":import_plugin, "help": help,
            "addbot":addbot}

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
        self.keymap = {}
        self.this_cmd_event = None
        self.this_cmd = None
        self.post_cmd = None

        if not pygame.display.get_init():
            raise pygame.error, "Display not initialized. Initialize the display before creating a Console"

        if not pygame.font.get_init():
            pygame.font.init()

        self.parent_screen = screen
        self.rect = pygame.Rect(rect)
        self.size = self.rect.size

        self.locals = locals
        self.variables = {"bg_alpha":int, "bg_color": list,
                        "txt_color_i": list, "txt_color_o": list,
                        "ps1": str, "ps2": str, "ps3": str,
                        "active": bool, "repeat_rate": list,
                        "preserve_events":bool, "motd":list }

        self.init_variables()

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
        self.max_lines = self.size[HEIGHT] / self.font_height

        self.max_chars = (self.size[WIDTH]/(self.font.size(ascii_letters)[WIDTH]/len(ascii_letters))) - 1
        self.txt_wrapper = textwrap.TextWrapper()

        self.c_out = []
        self.c_out.extend(self.motd)
        self.c_hist = [""]
        self.c_hist_pos = 0
        self.c_in = ""
        self.c_pos = 0
        self.c_draw_pos = 0
        self.c_scroll = 0
        self.completions = []

        self.changed = True

        self.set_interpreter()

        # define some keys
        self.define_key("left", self.move_left)
        self.define_key("right", self.move_right)
        self.define_key("tab", self.complete)
        self.define_key("backspace", self.backspace_char)
        self.define_key("delete", self.delete_char)
        self.define_key("return", self.submit)
        self.define_key("home", self.move_to_bol)
        self.define_key("end", self.move_to_eol)
        self.define_key("up", self.prev_history)
        self.define_key("down", self.next_history)
        self.define_key("pageup", self.scroll_up)
        self.define_key("pagedown", self.scroll_down)

        # define few Emacs-like keys
        self.define_key("C-b", self.move_left)
        self.define_key("C-f", self.move_right)
        self.define_key("C-a", self.move_to_bol)
        self.define_key("C-k", self.kill_line)
        self.define_key("C-e", self.move_to_eol)
        self.define_key("C-d", self.delete_char)
        self.define_key("C-p", self.prev_history)
        self.define_key("C-n", self.next_history)

    ##################
    #-Initialization-#
    def init_variables(self):
        self.bg_alpha = CONSOLE_BG_ALPHA
        self.bg_color = CONSOLE_BG_COLOR
        self.txt_color_i = CONSOLE_ICOLOR
        self.txt_color_o = CONSOLE_OCOLOR
        self.cur_color = CONSOLE_CCOLOR
        self.ps1 = CONSOLE_PS1
        self.ps2 = CONSOLE_PS2
        self.ps3 = CONSOLE_PS3
        self.active = CONSOLE_ACTIVE
        self.repeat_rate = CONSOLE_REPEAT_RATE
        self.motd = CONSOLE_MOTD + ["+ Use /help to list commands"]

    def beep(self):
        """Play beep sound."""
        play_sound("audio/aktivist/hit2.wav")

    def output(self, text):
        """Prepare text to be displayed
        Arguments:
            text -- Text to be displayed
        """
        if not text:
            return;

        try:
            self.changed = True
            if not isinstance(text,str) and not isinstance(text,unicode):
                text = repr(text)
            text = text.expandtabs()
            text = text.splitlines()
            self.txt_wrapper.width = self.max_chars
            for line in text:
                for w in self.txt_wrapper.wrap(line):
                    self.c_out.append(w)
        except Exception as ex:
            print "console output EX: ", ex
            pass

    def set_active(self,b=None):
        '''Activate or Deactivate the console
        Arguments:
            b -- Optional boolean argument, True=Activate False=Deactivate
        '''
        if not b:
            self.active = not self.active
        else:
            self.active = b

    def visible_range(self):
        n_max = self.max_chars - len(self.c_ps)
        vis_range = self.c_draw_pos, self.c_draw_pos + n_max
        return vis_range

    def format_completions(self):
        """Format completion list self.completions by grouping them."""
        def group_by_n(n, it):
            args = [iter(it)] * n
            return izip_longest(fillvalue="", *args)

        def group_column_lens(groups):
            return map(lambda g: 4+max(map(len, g)), zip(*groups))

        for n in xrange(1,11):
            ngrps = group_by_n(n, self.completions)
            if sum(group_column_lens(ngrps)) > self.max_chars:
                n = n - 1
                break

        ngrps = list(group_by_n(n, self.completions))
        nlens = group_column_lens(ngrps)

        def mkcmpline(clens, comps):
            return "".join(map(lambda l, x: x+" "*(l-len(x)), clens, comps))
        return map(lambda g: mkcmpline(nlens, g), ngrps)

    def format_cursor(self):
        return " "*len(self.c_ps) + " "*self.c_pos + u"\u2588"

    def format_input_line(self):
        '''Format input line to be displayed'''
        # Unicode: 2192 RIGHTARROWDS ARROW
        #          2190 LEFTARROWDS ARROW
        vr = self.visible_range()
        return self.c_ps + self.c_in[vr[0]:vr[1]]

    def draw(self):
        '''Draw the console to the parent screen'''
        if not self.active:
            return;

        if self.changed:
            self.changed = False

            comps = self.format_completions()

            # Draw Output
            olines = self.max_lines - len(comps)
            self.txt_layer.fill(self.bg_color)
            lines = self.c_out[-(olines+self.c_scroll):len(self.c_out)-self.c_scroll]

            # Show scrolling arrows at che bottom if scrolling
            if self.c_scroll:
                # unicode: 2193 DOWNARROWS ARROW
                lines[-1] = u"\u2193"*self.max_chars

            y_pos = self.size[HEIGHT] - \
                    (self.font_height*(len(lines)+len(comps)+1))
            for line in lines:
                tmp_surf = self.font.render(line, True, self.txt_color_o)
                self.txt_layer.blit(tmp_surf, (1, y_pos, 0, 0))
                y_pos += self.font_height

            # Draw cursor
            #y_pos = self.size[HEIGHT]-self.font_height
            tmp_surf = self.font.render(self.format_cursor(),
                                        True, self.cur_color)
            self.txt_layer.blit(tmp_surf, (1,y_pos,0,0))

            # Draw Input
            tmp_surf = self.font.render(self.format_input_line(),
                                        True, self.txt_color_i)
            self.txt_layer.blit(tmp_surf, (1,y_pos,0,0))

            # Draw completions
            for cline in comps:
                y_pos += self.font_height
                tmp_surf = self.font.render(cline, True, self.txt_color_o)
                self.txt_layer.blit(tmp_surf, (1, y_pos, 0, 0))

            # Clear background and blit text to it
            self.bg_layer.fill(self.bg_color)
            self.bg_layer.blit(self.txt_layer,(0,0,0,0))

        # Draw console to parent screen
        # self.parent_screen.fill(self.txt_color_i, (self.rect.x-1, self.rect.y-1, self.size[WIDTH]+2, self.size[HEIGHT]+2))
        pygame.draw.rect(self.parent_screen, self.txt_color_i,
                         (self.rect.x-1, self.rect.y-1, self.size[WIDTH]+2,
                          self.size[HEIGHT]+2), 1)
        self.parent_screen.blit(self.bg_layer,self.rect)

    def resize(self, rect):
        """Resize the console."""
        pass

    #######################################################################
    # Functions to communicate with the console and the python interpreter#
    def set_interpreter(self):
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

        if text:
            self.add_to_history(text)
        text = text.strip()
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
            self.message("- Unknown command: `%s'"%cmd)
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
        '''Sends input the the python interpreter.
In effect giving the user the ability to do anything python can.
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

    def define_key(self, keyspec, keycmd):
        specs = {"C-b":u"\x02", "C-f":u"\x06", "C-a":u"\x01",
                 "C-e":u"\x05", "C-p":u"\x10", "C-n":"\x0e", "C-d":u"\x04",
                 "C-k":u"\x0b",
                 "C-v":u"\x16", "tab":u"\t", "return":u"\r",
                 "left":u"\uf702", "right":u"\uf703", "up":u"\uf700",
                 "down":u"\uf701", "backspace":u"\x7f",
                 #"delete":u"\x", todo
                 "home":u"\uf729", "end":u"\uf72b",
                 "pageup":u"\uf72c", "pagedown":u"\uf72d"}
        if keyspec in specs:
            ukey = specs[keyspec]
            self.keymap[ukey] = keycmd
        else:
            if "keys" in option("debug"):
                print "- WARN: keyspec '%s' not found"%keyspec

    def lookup_key(self, ukey):
        """Lookup a key, return self-insert if binding not found."""
        return self.keymap.get(ukey, self.self_insert)

    def completions_list(self):
        cmd = self.c_in.strip()
        if not cmd or cmd[0] != "/":
            # TODO: python completion
            # use Completer from rlcompleter module
            return []

        cargs = cmd[1:].split()
        if not cargs: cargs = [""]
        incmd = commands.get(cargs[0], None)
        if incmd:
            # Command specific completion
            comps = getattr(incmd, 'completion_fun', lambda x: [])(cargs)
        else:
            # Command name completion
            comps = filter(lambda x: x.startswith(cargs[0]),
                           commands.keys())
        return comps

    # KEY commands
    def complete(self, beep=True):
        """Complete console command."""
        _comps = self.completions_list()
        self.completions = _comps
        if not _comps:
            # No completions, just beep
            self.beep()
            return

        # At least one completion is available
        cargs = self.c_in.strip()[1:].split()
        if not cargs: cargs = [""]

        # Search for the longest similiar prefix across all
        # completions. NOTE: for len(comps)==1 we always get lscomp
        def same_prefix(s1, s2):
            return "".join(map(lambda x:x[0],
                               takewhile(lambda x:x[0]==x[1], zip(s1, s2))))

        lscomp = reduce(same_prefix, _comps, _comps[0])
        if lscomp and len(lscomp) > len(cargs[-1]):
            # Perform completion
            crest = lscomp[len(cargs[-1]):] + " "
            self.c_pos += len(crest)
            self.c_in += crest

            if len(_comps) == 1:
                self.completions = []
        else:
            # Multiple completions matches or already fully matched the
            # input
            self.beep()

    def move_left(self):
        if self.c_pos > 0:
            self.set_pos(self.c_pos-1)

    def move_right(self):
        if self.c_pos < len(self.c_in):
            self.set_pos(self.c_pos+1)

    def move_to_bol(self):
        self.set_pos(0)

    def move_to_eol(self):
        self.set_pos(len(self.c_in))

    def prev_history(self):
        if len(self.c_out):
            if self.c_hist_pos > 0:
                self.c_hist_pos -= 1
            self.c_in = self.c_hist[self.c_hist_pos]
            self.set_pos(len(self.c_in))

    def next_history(self):
        if len(self.c_out):
            if self.c_hist_pos < len(self.c_hist)-1:
                self.c_hist_pos += 1
            self.c_in = self.c_hist[self.c_hist_pos]
            self.set_pos(len(self.c_in))

    def scroll_up(self):
        if self.c_scroll < len(self.c_out)-len(self.motd):
            self.c_scroll += 1
        else:
            self.beep()

    def scroll_down(self):
        if self.c_scroll > 0:
            self.c_scroll -= 1
        else:
            self.beep()

    def backspace_char(self):
        if self.c_pos > 0:
            self.c_in = self.c_in[:self.c_pos-1] + self.c_in[self.c_pos:]
            self.set_pos(self.c_pos-1)

    def delete_char(self):
        if self.c_pos < len(self.c_in):
            self.c_in = self.c_in[:self.c_pos] + self.c_in[self.c_pos+1:]

    def kill_line(self):
        """Kill to the end of line."""
        self.c_in = self.c_in[:self.c_pos]

    def submit(self):
        self.submit_input(self.c_in)

    def self_insert(self):
        """Self insert last event char."""
        # reset completions list on any input
        self.c_in = self.str_insert(self.c_in, self.this_cmd_event.unicode)

    def process_input(self):
        '''\
        Loop through pygame events and evaluate them
        '''
        if not self.active:
            return;

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                self.changed = True

                self.this_cmd_event = event

                ## Special Character Manipulation
                if event.key in CONSOLE_KEYS:
                    self.active = False
                elif event.key == K_ESCAPE:
                    self.active = False
                elif event.unicode:
                    if "keys" in option("debug"):
                        print "Console: lookup for key", event
                    keycmd = self.lookup_key(event.unicode)
                    keycmd()

                    # Update completions
                    if self.completions:
                        self.completions = self.completions_list()
