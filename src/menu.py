# Copyright (C) 2009 by Zajcev Evgeny <zevlg@yandex.ru>

import pygame
from pygame.locals import *

import sealhunter
from misc import *
from constants import *

MMENU_POSITION = (450, 240)

MENU_PCOLOR = (50, 50, 50)
MENU_ACOLOR = (0, 100, 0)
SUBMENU_PCOLOR = (40, 40, 40)
SUBMENU_ACOLOR = (100, 100, 0)

MENU_SHADOW_COLOR = (20, 20, 20)

SH_CONSOLE = None

def menu_init():
    global MENU_BG
    global PYGAME_POWERED
    global SHBIG_FONT
    global VERSION_FONT
    global MENU_FONT
    global TFONT

    MENU_BG = load_texture("Misc/main.png")
    SHBIG_FONT = load_font('kinifed.ttf', 80)
    SHBIG_FONT.set_italic(True)

    VERSION_FONT = load_font("default.ttf", 12)
    TFONT = load_font('trebuc.ttf', 20)
    MENU_FONT = load_font('Kroftsmann.ttf', 40)
#    MENU_FONT.set_bold(True)
    pp = load_texture("Misc/pygame_powered.gif", True)
    PYGAME_POWERED = pygame.transform.smoothscale(pp, (62,25))
#    PYGAME_POWERED = pygame.transform.rotate(pp1, -60)
#    PYGAME_POWERED = load_texture("Misc/pygame_powered.gif")

def shadowFont(fnt, txt, x, y, col, offset, ts, bigX=0):
    ts.blit(fnt.render(txt, True, MENU_SHADOW_COLOR), (x+offset, y+offset))
    ts.blit(fnt.render(txt, True, col), (x, y))
    (sx,sy) = fnt.size(txt)
    if sx > bigX:
        return sx
    else:
        return bigX

def drawPane(x, y, w, h, rgb=(0,0,0), alpha=100):
    screen = pygame.display.get_surface()
    sf = pygame.Surface((w, h))
    sf.fill(rgb)
    sf.set_alpha(alpha)
    screen.blit(sf, (x, y))
    return sf

def drawText(x, y, text, rgb=(255,255,255)):
    screen = pygame.display.get_surface()
    for txt in text.split('\n'):
        screen.blit(TFONT.render(txt, True, rgb), (x, y))
        y += 20

def draw_menuscreen():
    screen = pygame.display.get_surface()
    screen.blit(MENU_BG, (0, 0))

    shadowFont(SHBIG_FONT, "SealHunter", 22, 6, (110, 0, 0), 1, screen)
    shadowFont(SHBIG_FONT, "SealHunter", 21, 5, (110, 0, 0), 1, screen)
    shadowFont(SHBIG_FONT, "SealHunter", 20, 4, (110, 0, 0), 1, screen)

    vtext = VERSION_FONT.render("v%s by lg"%sealhunter.__version__,
                                1, (0,0,0))
    screen.blit(vtext, (348, 64))
    screen.blit(PYGAME_POWERED, (360,15))

def loop_menu(menu):
    """Operate on MENU performing events handling."""
    draw_menuscreen()
    menu.draw()
    while not menu.done:
        pygame.display.flip()
        for event in pygame.event.get():
            SH_CONSOLE.handle_event(event)
            if event.type == KEYUP:
                menu.handle_event(event)
                draw_menuscreen()
                menu.draw()

# exported
def do_mainmenu(console=None):
    # Global console
    global SH_CONSOLE
    if not SH_CONSOLE:
        SH_CONSOLE = console or sealhunter.setup_console()

    loop_menu(MainMenu())


class Menu:
    def __init__(self, name, mitems):
        self.name = name
        self.done = False
        self.items = map(lambda mi: mi[0], mitems)
        self.actions = {}
        for mi in mitems:
            self.actions[mi[0]] = mi[1]
        # First items is selected by default
        self.selected = self.items[0]

        self.acolor = MENU_ACOLOR
        self.pcolor = MENU_PCOLOR

        self.x, self.y = 0, 0

        # Calculate menu width and height
        mw = max(map(lambda x: MENU_FONT.size(x)[0], self.items))
        self.osurf = pygame.Surface((mw+20, len(self.items)*40+20))
        self.osurf.fill((0, 0, 0))
        self.osurf.set_alpha(100)

    def draw(self):
        """Draw menu on SURF at X and Y."""
        screen = pygame.display.get_surface()
        screen.blit(self.osurf, (self.x-10, self.y))
        # Draw menu caption
        screen.blit(TFONT.render(self.name, True, (0, 0, 0)), \
                    (self.x, self.y-20))
        # Draw items
        i = 0
        for it in self.items:
            if it == self.selected: col = self.acolor
            else: col = self.pcolor
            shadowFont(MENU_FONT, it, self.x, self.y+i*40+10, col, 1, screen)
            i += 1

    def exit(self):
        self.done = True

    def handle_event(self, event):
        if event.type == KEYUP:
            sidx = self.items.index(self.selected)
            if event.key == K_UP:
                self.selected = self.items[sidx-1]
            elif event.key == K_DOWN:
                self.selected = self.items[(sidx+1)%len(self.items)]
            elif event.key == K_RETURN and self.actions.has_key(self.selected) and self.actions[self.selected]:
                # Execute action
                self.actions[self.selected]()
            elif event.key == K_ESCAPE:
                self.done = True

class MainMenu(Menu):
    def __init__(self):
        Menu.__init__(self, '-- Main menu --',
                      [('New game', self.newgame),
                       ('Options', self.options),
                       ('Stats', self.stats),
                       ('Help', self.help),
                       ('Exit', self.exit)])
        self.x, self.y = MMENU_POSITION

    def newgame(self):
        loop_menu(NewGameMenu(self))

    def options(self):
        loop_menu(OptionsMenu())

    def stats(self):
        loop_menu(StatsMenu())

    def help(self):
        loop_menu(HelpMenu())

    def draw(self):
        Menu.draw(self)

        if self.selected == 'Options':
            drawPane(100, 280, 260, 110)
            drawText(110, 300, """Use quake console
To setup options
Press "~" to popup console""")
        elif self.selected == "Stats":
            drawPane(100, 280, 205, 60)
            drawText(110, 290, "TODO", (150,0,0))
            drawText(110, 310, """Sorry, no stats yet.""")

class SinglePlayerMenu(Menu):
    def __init__(self, menu):
        epls = filter(lambda p: p.get("enabled", False), option("players"))
        Menu.__init__(self, "--Select a player--",
                      [(p["name"], self.chooseplayer) for p in epls])
        self.acolor = SUBMENU_ACOLOR
        self.x, self.y = 110, 180
        # parent menu
        self.pmenu = menu

    def chooseplayer(self):
        sealhunter.new_game([self.selected], SH_CONSOLE)
        self.done = True

    def draw(self):
        self.pmenu.draw()
        Menu.draw(self)

class NewGameMenu(Menu):
    def __init__(self, menu):
        Menu.__init__(self, '-- New game --',
                      [#('1 Player', self.player1),
                       #('2 Players', self.player2),
                       ('Single-player', self.single),
                       ('Multi-player', self.multi),
                       ('Network', self.network),
                       ('Back', self.exit)])
        self.acolor = SUBMENU_ACOLOR
        self.x, self.y = 110, 180
        # parent menu
        self.pmenu = menu

    def single(self):
        loop_menu(SinglePlayerMenu(self.pmenu))
        self.done = True

    def multi(self):
        pnames = [p["name"] for p in option("players")
                  if p.get("enabled", False)]
        sealhunter.new_game(pnames, SH_CONSOLE)
        self.done = True

    def network(self):
        self.done = True

    def draw(self):
        self.pmenu.draw()
        Menu.draw(self)

        if self.selected == 'Network':
            drawPane(100, 380, 205, 80)
            drawText(110, 390, "TODO", (150,0,0))
            drawText(110, 410, """Sorry, network is not
yet implemented.""")

class OptionsMenu(Menu):
    def __init__(self):
        Menu.__init__(self, '-- Options --',
                      [#('P1 Controls', self.p1controls),
                       #('P2 Controls', self.p2controls),
                       ('Players', self.players),
                       ('System', self.sysopts),
                       ('Game', self.gameopts),
                       ('Fun', self.funopts),
                       ('Main menu', self.exit)])
        self.x, self.y = MMENU_POSITION

    def players(self):
        pass
    def funopts(self):
        pass

    def p1controls(self):
        pass
    def p2controls(self):
        pass
    def gameopts(self):
        pass
    def sysopts(self):
        pass

class StatsMenu(Menu):
    def __init__(self):
        Menu.__init__(self, '-- Stats --',
                      [('General', self.general),
                       ('Kills', self.kills),
                       ('Deaths', self.deaths),
                       ('Highscore', self.highscore),
                       ('Main menu', self.exit)])
        self.x, self.y = MMENU_POSITION

    def general(self):
        pass
    def kills(self):
        pass
    def deaths(self):
        pass
    def highscore(self):
        pass

class HelpMenu(Menu):
    def __init__(self):
        Menu.__init__(self, '-- Help --',
                      [('General', None),
                       ('Enemies', None),
                       ('Weapons', None),
                       ('About', None),
                       ('Main menu', self.exit)])
        self.x, self.y = MMENU_POSITION

        self.weapons = self.enemies = []
        self.weapon = self.enemy = 0

    def handle_event(self, event):
        Menu.handle_event(self, event)
        if event.type == KEYUP and event.key == K_RIGHT:
            if self.selected == 'Enemies':
                self.enemy += 1
                if self.enemy >= len(self.enemies): self.enemy = 0
            elif self.selected == 'Weapons':
                self.weapon += 1
                if self.weapon >= len(self.weapons): self.weapon = 0
        elif event.type == KEYUP and event.key == K_LEFT:
            if self.selected == 'Enemies':
                self.enemy -= 1
                if self.enemy < 0: self.enemy = len(self.enemies)-1
            elif self.selected == 'Weapons':
                self.weapon -= 1
                if self.weapon < 0: self.weapon = len(self.weapons)-1

    def draw_enemies(self):
        def make_grayscale(pic):
            np = pic.copy()
            for y in range(pic.get_height()):
                for x in range(pic.get_width()):
                    cc = np.get_at((x,y))
                    avgc = reduce(lambda c1,c2:c1+c2,cc[:3])/3
                    np.set_at((x,y), (avgc,avgc,avgc,cc[3]))
            return np

        if not self.enemies:
            # initialize enemies
            ens = ["Bruns", "Knubbs", "VitS", "Pingvin", "Bear", "Turtle"]
            self.enemies = map(load_texture, ["Enemies/%s/Walking/anim_1.png"%e for e in ens])
            self.enemies.insert(2,load_texture("Aktivist/Running/anim_1.png"))
        scr = pygame.display.get_surface()
        pane = drawPane(50,128,340,332)
        drawText(60, 138, "Enemies encountered:")
        xoff, yoff = 70, 168
        for e in self.enemies:
            if self.enemies.index(e) == self.enemy:
                e.set_alpha(None)
#                ne = e
            else:
                e.set_alpha(75)
#                ne = make_grayscale(e)
            scr.blit(e, (xoff, yoff+(32-e.get_height())))
            xoff += e.get_width() + 12
        # enemy description
        if self.enemy == 0:
            edesc = """Seal

Common Scandinavian Brown Seal

Bounty: $50
Headshot Bonus: $10
Headshot Multiplier: x2
Hit Points: 26 + Level*21
Speed: 25-55 pixels/second
Special: May crawl while critically
wounded"""
        elif self.enemy == 1:
            edesc = """    Fat Seal

The rare giant albino subspecies
of the Scandinavian Seal

Bounty: $200 + $200 if boss
Eyeshot Bonus: $0
Eyeshot Multiplier: x1.25
Hit Points: Level*250 (1250 if boss)
Speed: 35 pixels/second
Special: Regenerates hit points
when standing still"""
        elif self.enemy == 2:
            edesc = """       British Activist

Parents divorced during puberty

Bounty: $100
Headshot Bonus: $15
Headshot Multiplier: x2
Hit Points: 30 + Level*35
Speed: 55-100 pixels/second
Special: Carries a seal cub"""
        elif self.enemy == 3:
            edesc = """                Seal Cub

Cute and fluffy

Bounty: $25
Hit Points: 10 + Level*5
Speed: 22-37 pixels/second"""
        elif self.enemy == 4:
            edesc = """                     Penguin

Yes, you CAN find these in Norway

Bounty: $100
Headshot Bonus: $10
Headshot Multiplier: x2
Hit Points: Level*25
Speed: 32-55 pixels/second
Special: Dives and gains 87-157
speed"""
        elif self.enemy == 5:
            edesc = """                          Polar Bear

Only slightly endangered

Bounty: $500
Headshot Bonus: $0
Headshot Multiplier: x2
Hit Points: 1700 (2000 if boss)
Speed: 40-370 pixels/second
Special: Gets enraged when hit"""
        elif self.enemy == 6:
            edesc = """                           Galapagos Turtle

Recently escaped from Tromso Zoo
after 140 years of captivity

Bounty: $500
Headshot Bonus: $0
Headshot Multiplier: x1
Hit Points: 2500
Speed: 30 pixels/second
Special: Hides in his shell after
taking damage"""
        drawText(60, 200, edesc)

    def create_weapon(self, wpn):
        pl = load_texture("Player1/Stopped/anim.png")
        wt = load_texture("Weapons/Hands/%s/%s.png"%wpn[:2])
        sf = pygame.Surface((wpn[4],wpn[5]))
        sf.fill((0,0,0))
        if wpn[2] < 0: po, wo = 0,-wpn[2]
        else: po, wo = wpn[2], 0
        sf.blit(pl, (po,0))
        sf.blit(wt, (wo,wpn[3]))
        sf.set_colorkey((0,0,0))
        return sf

    def draw_weapons(self):
        if not self.weapons:
            # initialize weapons
            wps = [("USP","usp", 5, 8, 17, 20),
                   ("Magnum","magnum_1", 9,8,21,20),
                   ("MP5","mp5", 5, 11, 17, 20),
                   ("Grenade","grenade", -3,11,12,20),
                   ("Shotgun","shotgun", 6,10,20,20),
                   ("MAC10","mac10", 6,7,18,20),
                   ("Flunk","flunk", 11,6,23,20),
                   ("Colt","colt", 13,9,25,20),
                   ("AWP","awp",29,6,43,20),
                   ("Farfar","farfar",23,6,37,20),
                   ("Minigun","minigun",28,4,42,20)]
            self.weapons = map(self.create_weapon, wps)

        scr = pygame.display.get_surface()
        pane = drawPane(50,128,340,332)
        drawText(55, 133, "Weapons:")
        xoff, yoff = 58, 150
        for w in self.weapons:
            if self.weapons.index(w) == self.weapon: w.set_alpha(None)
            else: w.set_alpha(75)
            scr.blit(w, (xoff, yoff+(32-w.get_height())))
            xoff += w.get_width() + 5

        # TODO: take info from WEAPONS
        if self.weapon == 0:
            wdesc = """Pistol

Damage: 18
Accuracy: Perfect
Clip Size: 12
Reload time: 2 seconds
Rate of fire: 4/second
Damage per second: 41"""
        elif self.weapon == 1:
            wdesc = """Magnum - $500

Damage: 60 (+5 per level)
Accuracy: Perfect
Clip Size: 6
Reload time: 2.2 seconds
Rate of fire: 2.5/second
Pierce: 70%
Damage per second: 90 (-> 120)"""
        elif self.weapon == 2:
            wdesc = """  MP5 - $1000

Damage: 23 (+2 per level)
Accuracy: Good (\xb11.5\xb0)
Clip size: 30
Reload time: 1.6 seconds
Rate of fire: 10/second
Damage per second: 153 (-> 206)"""
        elif self.weapon == 3:
            wdesc = """   Grenades - $1.500

Damage: 250 (at epicentre, drops
proportionally to distance)
Splash radius: 95 pixels
Clip size: 1
Reload time: 1 second
Rate of fire: 1/second
Damage per second: 250"""
        elif self.weapon == 4:
            wdesc = """     Shotgun - $2.500

Damage: 40 per bullet at point
blank range, drops to 16 at max
range (a whole screen)
Bullets per shot: 8
Accuracy: Abysmal (\xb17.5\xb0)
Clip size: 8
Reload time: 2.5 seconds
Rate of fire: 1.2/second
Damage per second: 316 -> 126
(worst case = 15)"""
        elif self.weapon == 5:
            wdesc = """       Dual Mac10s - $3.500

Damage: 37
Accuracy: Poor (\xb14\xb0)
Clip size: 60
Reload time: 2.6 seconds
Rate of fire: 16/second
Damage per second: 361"""
        elif self.weapon == 6:
            wdesc = """         Grenade Launcher - $5.000

Damage: 400 (at epicentre, drops
proportionally to distance)
Splash radius: 100 pixels
Clip size: 5
Reload time: 3 seconds
Rate of fire: 2.5/second
Damage per second: 434"""
        elif self.weapon == 7:
            wdesc = """             Assault rifle - $6.000

Damage: 40
Accuracy: Good (\xb11.5\xb0)
Clip size: 30
Reload time: 1.6 seconds
Rate of fire: 10/second
Pierce: 80%
Damage per second: 400"""
        elif self.weapon == 8:
            wdesc = """                Sniper Rifle - $7.500

Damage: 855
Accuracy: Perfect
Clip size: 5
Reload time: 2.2 seconds
Rate of fire: 0.75/second
Pierce: 90%
Damage per second: 593"""
        elif self.weapon == 9:
            wdesc = """   1876 Vintage Shotgun - $10.000

Damage: 125 per bullet, drops to
65 at max range
Bullets per shot: 7+8=15
Accuracy: Poor (\xb15.25\xb0)
Clip size: 2
Fire Delay: 0.7 seconds
Reload time: 1.5 seconds
Rate of fire: 0.5 second
Pierce: 33%
Damage per second: 750 (drops to
375, worst case = 25)"""
        elif self.weapon == 10:
            wdesc = """                           Minigun - $12.500

Damage: 65
Accuracy: Very good (\xb11\xb0)
Clip size: 150
Rate of fire: ~16 bullets per second
Reload time: 2.4 seconds
Pierce: 50%
Damage per second: 844"""
        drawText(60, 188, wdesc)

    def draw(self):
        Menu.draw(self)

        if self.selected == 'General':
            drawPane(50,128,340,332)
            drawText(60,138,"""The objective of the game is to
prevent the seals and other arctic
creatures from reaching the ocean
(see map below) where they eat
our fish and mate and reproduce""")
            shmap = load_texture("Misc/map.png", True)
            pygame.display.get_surface().blit(shmap, (70, 248))
        elif self.selected == 'Enemies':
            self.draw_enemies()
        elif self.selected == 'Weapons':
            self.draw_weapons()
        elif self.selected == 'About':
            # About pane
            drawPane(50,128,340,220)
            iri = load_texture("Misc/iri-small.png", True)
            pygame.display.get_surface().blit(iri, (198, 258))
            drawText(60,138,"""SealHunter v%s by Zajcev Evgeny

Thanks to:
  * Original SealHunter team
  * Python and Pygame developers
  * Asker for his patience
  * My girlfriend   Irina for her
    love and silence

Contact: zevlg@yandex.ru"""%sealhunter.__version__)

class ToggleButton:
    def __init__(self, name, default=False):
        self.name = name
        self.value = default

    def draw(self, selected=False):
        pass
