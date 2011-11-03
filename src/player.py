# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

from itertools import *

import pygame

import weapons
from objects import *
from constants import *
from misc import *
from enemies import Bruns, Vits
from hud import hud

def command(meth):
    """Decorator to execute method as command."""
    def cmd(self, event, arg):
        meth(self, arg)
    return cmd

class Player(AnimateStates, Creature):
    STATES_WITH_WEAPON = ['Walking', 'Stopped', 'InAir', 'Jump', 'JumpFall']
    def __init__(self, profile, **kwargs):
        ss = {"Stopped":{0:[(5,19), (2,0), (11,9)]},
              "Walking":{0:[(6,19), (3,0), (12,9)],
                         1:[(5,19), (2,0), (11,9)]},
              "Jump":  {"keep_last":True,
                        0:[(5,19), (2,1), (11,10)],
                        1:[(5,19), (2,0), (11,9)],
                        2:[(5,20), (2,0), (11,9)],
                        3:[(5,20), (2,0), (11,9)]},
              "JumpFall": {"keep_last":True,
                           0:[(5,19), (2,0), (11,9)],
                           1:[(5,18), (2,0), (11,9)],
                           2:[(5,17), (2,0), (11,9)]},
              "Sitting": {0:[(12,17), (9,0), (18,8)]},
              "GetUp": {"keep_last":True,
                        0:[(12,17), (9,0), (18,8)],
                        1:[(12,17), (9,0), (18,8)],
                        2:[(12,17), (9,0), (18,8)],
                        3:[(12,17), (7,0), (16,8)],
                        4:[(12,17), (6,0), (15,8)],
                        5:[(12,18), (4,0), (13,8)],
                        6:[(12,19), (5,0), (14,8)],
                        7:[(12,19), (7,0), (16,8)]},
              "Kick": {0:[(9,19), (3,0), (12,8)]},
              "InAir": {0:[(10,17), (10,0), (18,8)]}
              }
        AnimateStates.__init__(self, "Player1", 'Stopped',
                               states_setup=ss, ticks_step=2)

        kwargs.update(reflection="player" in option("reflections"),
                      opaque=PLAYER_REFLECTION_OPAQUE,
                      bouncing=10)
        Creature.__init__(self, PLAYER_LIFE, **kwargs)

        self.sounds = {"jump": map(load_sound, aglob("player/jump*.wav")),
                       "laugh": map(load_sound, aglob("player/laugh*.wav")),
                       "scream-death": load_sound("player/scream-death.wav"),
                       "scream-hit": load_sound("player/scream-hit.wav")}

        # Some enemy related settings
        self.headshot_multiplier = 2
        self.headshot_bonus = 0
        self.bounty = 1000

        # Player profile (name, skin, keys, etc)
        self.profile = profile
        self.money = self.earned_money = 0
        self.keysdown = set()

        # Player this game statistics
        self.pstats = {"kills": 0,      # total kills
                       "avg-damage":0,  # average damage per shot
                       "damage": 0,     # total damage given
                       "kills-stats": {}, # per enemy kills statistics
                       "distance": 0,   # distance move
                      }                 # player statistics

        # Change the skin
        self.apply_skin()

        # Cross and cross info
        self.font = load_font("default.ttf", MONEY_FONT_SIZE)
        self.font_color = (255, 0, 0, 155)

        # Start position
        self.x, self.y = self.profile["start-at"]
        self.apply_position()

        # Sprites for weapon and its reflection
        self.weapons = [weapons.Pistol(self)]
        self.weapon = self.weapons[0]
        self.field.add(self.weapon, append=True)

        # Sprites for crosshair and crosshair info
        if self.profile["crosshair"]:
            self.setup_crosshair()
            self.add(self.cross)

        if self.profile["crosshair-info"]:
            self.cross_info = dirty_sprite()
            self.cross_info._layer = 300 # above everything
            self.setup_crosshair_info()
            self.add(self.cross_info)

        if self.profile["money-info"]:
            self.money_info = dirty_sprite()
            self.money_info._layer = 300 # above everything
            self.setup_money_info()
            self.add(self.money_info)

        if self.profile["show-hud"]:
            self.hud = hud(self)
            self.add(self.hud)

    def apply_skin(self):
        # Substitute colors in state images according to skin
        def convt(t):
            return substitute_color(t.copy(), PLAYER_SCOLOR,
                                    self.profile["skin"])

        for st in self.states:
            self.states[st] = map(convt, self.states[st])
        
    def set_skin(self, skin):
        """Set new skin for the player."""
        if 'player' in option("debug"):
            debug("Set skin: %s"%(skin,))

        # Reload states to ensure they have PLAYER_SCOLOR color
        self.states = dict([(basename(dr), load_animation(dr))
                            for dr in tglob("Player1/*")])

        self.profile["skin"] = skin
        self.apply_skin()

        # NOTE: money-info has player's color
        if self.profile["money-info"]:
            self.setup_money_info()

        # And update the player's sprite as well
        self.update()
        self.scs.dirty = 1

    def setup_crosshair(self):
        self.cross = dirty_sprite()
        self.cross._layer = TOP_LAYER
        self.cross.image = load_texture("Misc/blue_crosshair_1.png").copy()
        substitute_color(self.cross.image, PLAYER_CHCOLOR,
                         self.profile["crosshair-color"])
        move_sprite(self.cross, -100, -100)

    def setup_crosshair_info(self):
        if self.weapon.state == 'Reload':
            rprc = int((self.weapon.ticks*100.0)/self.weapon.reload_ticks)
            text = "%d%%"%((rprc/10)*10)
            coff = int(1.5*rprc)
            tcol = (255-coff, coff, 0, 255-rprc)
        else:
            bprc = int(self.weapon.bullets*100.0/self.weapon.clip_size)
            text = "%d"%self.weapon.bullets
            coff = int(1.5*bprc)
            tcol = (255-coff, coff, 0, 255-bprc)

        _sci = self.cross_info
        _sci.image = self.font.render(text, True, tcol)
        _sci.rect = _sci.image.get_rect()
        cix = self.xx() - self.weapon.cross_xoffset
        ciy = self.yy() - self.weapon.aim_position - MONEY_FONT_SIZE
        _sci.rect.center = cix, ciy
        _sci.dirty = 1

    def setup_money_info(self):
        mcol = self.profile["skin"]
        _smi = self.money_info
        _smi.image = self.font.render("%d$"%self.money, True, mcol)
        _smi.rect = _smi.image.get_rect()
        _smi.dirty = 1

    def toggle_crosshair(self):
        """Toggle crosshair visibility."""
        self.profile["crosshair"] = not self.profile["crosshair"]
        if self.profile["crosshair"]:
            self.setup_crosshair()
            self.cross.add(self, self.field)
        else:
            self.cross.kill()

    def toggle_crosshair_info(self):
        """Toggle crosshair info visibility."""
        self.profile["crosshair-info"] = not self.profile["crosshair-info"]
        if self.profile["crosshair-info"]:
            self.setup_crosshair_info()
            self.cross_info.add(self, self.field)
        else:
            self.cross_info.kill()

    def can_walk(self):
        """Return True if player can walk."""
        if self.state in ['Stopped', 'Walking']:
            return True
        if self.state == 'InAir' and self.z <= 0:
            return True
        return False

    def states_with_weapon(self):
        return ['Walking', 'Stopped', 'InAir', 'Jump', 'JumpFall']

    def tick(self, f):
        # possible change state
        AnimateStates.tick(self, f)

        # Check if there are crawling bruns under falling player
        if self.z_speed < 0 and self.z < (abs(self.z_speed)+G_ACCEL):
            def crawling_brunsals():
                def is_crawling(c):
                    return c.state in ["StartCrawl", "Crawl"]
                return filter(is_crawling, self.field.creatures(Bruns))

            crbruns = crawling_brunsals()
            csix = self.rect.collidelistall(map(lambda c: c.rect, crbruns))
            for ci in csix:
                self.earn_money(crbruns[ci].bounty)
                self.kills(crbruns[ci])
                crbruns[ci].die("KrossatHuvud")
            self.apply_earned_money()

        # Adjust player's state
        if self.can_walk():
            if self.keysdown & set(['left', 'right', 'up', 'down']):
                self.state_start('Walking')
            else:
                self.state_start('Stopped')
        elif self.state == 'Jump':
            if self.z_speed <= 0:
                self.state_start('JumpFall')
        elif self.state == 'JumpFall':
            if self.z == 0:
                if 'player' in option("debug"):
                    debug("After jump: %d,%d"%(self.x, self.y))

                self.x_speed /= 2.0
                self.y_speed /= 2.0
                self.z_speed = 0
                self.state_start('Sitting')
        elif self.state == "Sitting":
            self.state_start("GetUp")
        elif self.state == 'GetUp':
            if self.state_idx == self.state_frames()-1:
                if self.x_speed > 0 or self.y_speed > 0:
                    self.state_start("Walking")
                else:
                    self.state_start("Stopped")

        if self.state in ['Walking', 'Stopped']:
            if self.z > 8 and self.x_speed > 1:
                self.state_start('InAir')

        # Move player if not in air and walking
        if self.z == 0 and self.state in 'Walking':
            if 'left' in self.keysdown and self.x_speed > -PLAYER_XMAX:
                self.x_speed -= PLAYER_XACC
            if 'right' in self.keysdown and self.x_speed < PLAYER_XMAX:
                self.x_speed += PLAYER_XACC
            if 'up' in self.keysdown and self.y_speed > -PLAYER_YMAX:
                self.y_speed -= PLAYER_YACC
            if 'down' in self.keysdown and self.y_speed < PLAYER_YMAX:
                self.y_speed += PLAYER_YACC

        self.apply_speed()
        if not (self.keysdown & set(['up', 'down'])):
            self.apply_yfric()
        if not (self.keysdown & set(['left', 'right'])):
            self.apply_xfric()

        # Check that player is inside field
        if self.x >= 640: self.x = 640-1; self.x_speed = 0
        if self.x < 0: self.x = 0; self.x_speed = 0
        if self.y > FLIMIT_HEIGHT[1]:
            self.y = FLIMIT_HEIGHT[1]
            self.y_speed = 0

        while not f.is_inside(self.x, self.y-8, True):
            self.y += 0.5
            self.y_speed = 0

        # process keys
        if self.state in Player.STATES_WITH_WEAPON:
            if 'fire' in self.keysdown:
                if self.weapon.fire(f):
                    self.x_speed += self.weapon.x_recoil
                    self.z_speed += self.weapon.z_recoil
                    if self.profile["show-hud"]:
                        self.hud.update_bullets(self.weapon)

        # Check the life and damage before Creature.tick
        if self.total_hit > 0:
            if self.total_hit > 100 and self.is_alive():
                play_sound(self.sounds["scream-hit"], True)
            elif not self.is_alive():
                play_sound(self.sounds["scream-death"])

        Creature.tick(self, f)

        # Move sprites
        AnimateStates.update(self)
        self.apply_position()
        self.update_reflection()

        if self.profile["crosshair"]:
            cx = self.xx()-self.weapon.cross_xoffset
            cy = self.yy()-self.weapon.aim_position
            _sc = self.cross
            if _sc.rect.center != (cx, cy):
                _sc.rect.center = cx, cy
                _sc.dirty = 1

        if self.profile["crosshair-info"]:
            self.setup_crosshair_info()

        if self.profile["money-info"]:
            _smir = self.money_info.rect
            _nc = (self.xx()+2, self.yy()-18-MONEY_FONT_SIZE)
            if _smir.center != _nc:
                _smir.center = _nc
                self.money_info.dirty = 1

    def has_weapon(self, wpnname):
        """Return True if player has WEAPON of WPNNAME."""
        return wpnname in map(lambda w: w.__class__.__name__, self.weapons)

    def buy_weapon(self, wpnname=None):
        def buy_it(n):
            self.earn_money(-WEAPONS[n]["price"])
            self.apply_earned_money()

            play_sound("ui/buygun.wav")
            # Call weapon constructor
            nwpn = getattr(weapons, n)(self)
            self.weapons.append(nwpn)
            self.switch_weapon(nwpn)

            if self.profile["show-hud"]:
                self.hud.new_weapon(nwpn)

            return nwpn

        # Buy certain weapon
        if wpnname:
            if self.money >= WEAPONS[wpnname]["price"]:
                return buy_it(wpnname)
            return None

        # Find and buy most expensive weapon the player can buy
        for wpn in sorted(WEAPONS.items(),
                          key=lambda x: x[1]["price"], reverse=True):
            if not self.has_weapon(wpn[0]) \
                   and self.money >= wpn[1]["price"]:
                return buy_it(wpn[0])
        return None

    def switch_weapon(self, newpn):
        """Switch to new weapon NEWPN."""
        play_sound("weapons/reload.wav")
        self.field.remove(*self.weapon)
        self.weapon = newpn
        self.field.add(self.weapon, append=True)

        if self.profile["show-hud"]:
            self.hud.select_weapon(self.weapon)

    def earn_money(self, amount):
        """Earn AMOUNT of money."""
        self.earned_money += amount

    def apply_earned_money(self):
        """Apply earned, by this tick, money to the player."""
        if self.earned_money != 0:
            self.money += self.earned_money

            if self.profile["show-earned-money"]:
                ea = EarnMoney(self.earned_money, self.x+2,
                               self.y-22-MONEY_FONT_SIZE-EARNMONEY_FONT_SIZE,
                               font_color=self.profile["skin"])
                self.field.add(ea)

            if self.profile["money-info"]:
                self.setup_money_info()

            self.earned_money = 0

            # Possible auto-buy weapon
            for ab in self.profile["autobuy-list"]:
                if (not self.has_weapon(ab)) and \
                   (self.money >= WEAPONS[ab]["price"]):
                    self.buy_weapon(ab)
                    break

        if self.profile["show-hud"]:
            self.hud.update_money(self.money)

    def handle_event(self, event):
        keys = self.profile["keys"]
        if event.type not in [KEYDOWN, KEYUP]:
            return

        # For debug
        if 'player' in option("debug") and event.type == KEYUP:
            if event.key == 49:
                self.buy_weapon("Magnum")
            elif event.key == 50:
                self.buy_weapon("Pistol")
            elif event.key == 51:
                self.buy_weapon("MP5")
            elif event.key == 52:
                self.buy_weapon("Shotgun")
            elif event.key == 53:
                self.buy_weapon("MAC10")
            elif event.key == 54:
                self.buy_weapon("Flunk")
            elif event.key == 55:
                self.buy_weapon("M4")
            elif event.key == 56:
                self.buy_weapon("AWP")
            elif event.key == 57:
                self.buy_weapon("VintageShotgun")
            elif event.key == 48:
                self.buy_weapon("Minigun")

        # Execute the binding
        if keys.has_key(event.key):
            scmd = keys[event.key].partition(" ")
            cmd = getattr(self, scmd[0], self.invalid_cmd)
            cmd(event, scmd[2])

    # Commands
    def invalid_cmd(self, event, arg):
        if event.type == KEYDOWN:
            keys = self.profile["keys"]
            cmd = keys[event.key]

            if cmd and cmd[0] == "/":
                # Possible a console command
                self.field.console.send_command(cmd[1:])
            else:
                self.say0("- Invalid command: %s"%cmd)

    def generic_cmd(self, event, arg):
        keys = self.profile["keys"]
        if event.type == KEYDOWN:
            self.keysdown.add(keys[event.key])
        elif event.type == KEYUP:
            self.keysdown.remove(keys[event.key])

    def say0(self, msg):
        """Say the message MSG."""
        self.field.message("%s: %s"%(self.profile["name"], msg))

    def jump_zxy(self, z, xc=1.0, yc=1.0):
        """Jump with zspeed Z."""
        self.state_start("Jump")

        if 'player' in option("debug"):
            debug("Before jump: %d,%d"%(self.x, self.y))

        # calculate speeds
        self.z_speed = z
        self.x_speed *= xc
        self.y_speed *= yc

        play_rnd_sound(self.sounds["jump"])

    def kills(self, enemy, prj=None):
        """ENEMY has been killed by player."""
        self.pstats["kills"] += 1
        if self.profile["show-hud"]:
            self.hud.update_kills(self.pstats["kills"])

    def nice_shot(self, prj):
        """Notice a nice shot by the player."""
        _ps = min(prj.given_damage/prj.weapon.damage, 8)
        play_sound("player/laugh%d.wav"%_ps)

        # Astonish some vitseal
        vitses = self.field.creatures(Vits)
        if vitses: choice(vitses).nosa()

    def hit(self, prj, dmg, head=False):
        """Player has been wounded by projectile PRJ and damage DMG."""
        Creature.hit(self, prj, dmg, head=head)

        if head and prj.is_bullet():
            self.field.add(*blood(n=2, xrs=(-6,-3), zrs=(0,2),
                                  w=(2,3), h=(2,3),
                                  x=prj.x,y=prj.y+18,z=18))

        # Recoil, gets into account splash
        ek = dmg / 150.0
        if prj.is_grenade():
            px, py = self.scs.rect.center
            xw, yh = px-prj.x, py-prj.y
            tl = math.sqrt(xw**2+yh**2)
            self.x_speed += ek*xw/tl
            self.y_speed += ek*yh/tl
        else:
            # Bullet
            if prj.x > self.x: self.x_speed -= ek
            else: self.x_speed += ek

# Few command decorators, see below the usage
def event_type(et):
    """Decorator to execute cmd only for given event type ET."""
    def cmd_method(meth):
        def command(self, event, arg):
            if event.type == et:
                meth(self, event, arg)
        return command
    return cmd_method

def state_with_weapon(meth):
    """Decorator to execute cmd only if player's state with weapon."""
    def cmd_with_weapon(self, event, arg):
        if self.state in Player.STATES_WITH_WEAPON:
            meth(self, event, arg)
    return cmd_with_weapon

def weapon_not_firing(meth):
    """Decorator to execute cmd only if not firing at the moment."""
    def cmd_weapon_not_firing(self, event, arg):
        if self.weapon.state != "Fire":
            meth(self, event, arg)
    return cmd_weapon_not_firing

# Player Commands
Player.left  = Player.generic_cmd
Player.right = Player.generic_cmd
Player.up    = Player.generic_cmd
Player.down  = Player.generic_cmd
Player.fire  = Player.generic_cmd

@event_type(KEYDOWN)
@state_with_weapon
@weapon_not_firing
def buy(self, event, arg):
    self.buy_weapon(arg)
Player.buy = buy

@event_type(KEYDOWN)
@state_with_weapon
def reload(self, event, arg):
    self.weapon.reload(self.field)
Player.reload = reload

@event_type(KEYDOWN)
@state_with_weapon
@weapon_not_firing
def switch(self, event, arg):
    if arg:
        print "SWITCH", arg
        self.switch_weapon(self, arg)
    else:
        # Switch to next/prev weapon
        nwidx = self.weapons.index(self.weapon)
        twpns = len(self.weapons)
        if nwidx == (twpns-1) and twpns > 1:
            nwidx -= 1
        elif nwidx < (twpns-1):
            nwidx += 1
        self.switch_weapon(self.weapons[nwidx])

Player.switch = switch

def jump(self, event, arg):
    if self.state in ['Walking', 'Stopped']:
        print "arg: %s"%arg
        z, xc, yc = map(int, islice(chain(arg.split(), repeat('1')), 0, 3))
        self.jump_zxy(z, xc, yc)

Player.jump = jump

@event_type(KEYDOWN)
@command
def say(self, msg):
    self.say0(msg)

Player.say = say
