# Renders a speech balloon

import pygame
import math


# Returns a surface filled with the given color, but having the same
# alpha channel as the given image.
def set_color(img, color):
    newsurf = pygame.Surface(img.get_size()).convert_alpha()
    newsurf.fill(color)
    alpha = pygame.surfarray.pixels_alpha(img)
    pygame.surfarray.pixels_alpha(newsurf)[:] = alpha
    if (len(color) == 4):
        adjust_alpha(newsurf, color[-1])
    return newsurf


# Use the image to sweep a border around itself
def sweep_border(surf, border, borderColor=(0,0,0)):
    bsurf = set_color(surf, borderColor)
    (w, h) = surf.get_size()
    newsurf = pygame.Surface((w+2*border, h+2*border)).convert_alpha()
    newsurf.fill((0,0,0,0))
    if (border <= 2):
        step = 90
    elif (border <= 6):
        step = 45
    else:
        step = 10
    for angle in xrange(0,360,step):
        (x, y) = (border*math.cos(math.radians(angle)),
                  border*math.sin(math.radians(angle)))
        newsurf.blit(bsurf, (border+x, border+y))
    newsurf.blit(surf, (border, border))
    return newsurf


class SpeechBalloon(object):
    spoutDist = 60
    spoutSpread = 40
    bgcolor = (255,255,255)
    # The starting position (tip of the spout)
    start = None
    # The ending position (center of the ellipse)
    end = None
    # The speech balloon surface
    surf = None
    # The offset into the surface of the location of the spout's tip
    tipOffset = None
    # The region occupied by the ball of the speech balloon (offset within
    # the surface).
    ballRect = None

    def __init__(this, size, start, end, corner_radius=20):
        this.size = size
        this.start = start
        this.end = end

        this.corner_radius = corner_radius

    def create(this):
        (w, h) = this.size

        # Figure out how big to make the surface
        spoutVec = map(lambda a,b: a-b, this.start, this.end)

        this.ballRect = pygame.Rect(0, 0, 0, 0)
        this.ballRect.size = (w, h)
        this.ballRect.center = (0, 0)

        rect = this.ballRect.union(pygame.Rect((spoutVec, (0, 0))))

        this.surf = pygame.Surface(rect.size).convert_alpha()
        this.surf.fill((0,0,0,0))

        center = (-rect.x, -rect.y)
        this.ballRect.center = center

        _r = this.corner_radius
        _br = this.ballRect
        _brx = _br.x
        _bry = _br.y
        _r1, _r2 = _br.copy(), _br.copy()
        _r1.x += _r/2; _r1.w -= _r
        _r2.y += _r/2; _r2.h -= _r
        _pdr = pygame.draw.rect
        map(lambda r: _pdr(this.surf, this.bgcolor, r), [_r1, _r2])

        _rd2 = _r/2
        _cos = [(_r1.x,_r2.y), (_r1.x, _r2.y+_r2.h),
                (_r1.x+_r1.w,_r2.y),(_r1.x+_r1.w, _r2.y+_r2.h)]
        _rr = pygame.Rect((0,0,_r,_r))
        _pde = pygame.draw.ellipse
        def dcor(c):
            _rr.center = c
            _pde(this.surf, this.bgcolor, _rr)
        map(dcor, _cos)

        # Figure out where the tip of the spout is located
        this.tipOffset = map(lambda a,b:a+b, center, spoutVec)

        perp1 = (center[0]-_r/2, center[1]+_r/2)
        perp2 = (center[0]+_r/2, center[1]-_r/2)
#        perp = numpy.array((spoutVec[1], -spoutVec[0]))
#        perp = (this.spoutSpread/2) * perp/norm(perp)

        # Now draw the spout
        pts = (this.tipOffset, perp1, perp2)
#                center + perp.astype("int"),
#                center - perp.astype("int"))
        pygame.draw.polygon(this.surf, this.bgcolor, pts, 0)

def speech_balloon(text, btype="speech"):
    tl = text.splitlines()
    

if (__name__ == "__main__"):
    pygame.init()
    display = pygame.display.set_mode((640,480))
    display.fill((0,0,0))

    font = pygame.font.SysFont("", 32)
    textImage = font.render("Hello speech balloon!", True, (0,0,0))

    balloon = None
    lastPos = None
    done = False
    while not done:
        # Process events
        for event in pygame.event.get():
            if (event.type == pygame.KEYDOWN and
                event.key == pygame.K_ESCAPE or 
                event.type == pygame.QUIT):
                done = True
                break

        # Create a speech balloon stretching from the center of the screen
        # to the mouse cursor.
        pos = pygame.mouse.get_pos()
        if (pos != lastPos):
            # Note it's somewhat inefficient to do this on every frame (done 
            # here just for fun). Normally you would create this object once, 
            # then re-use the rendered image.
            balloon = SpeechBalloon(
                (textImage.get_width()+30, textImage.get_height()+40), 
                display.get_rect().center, pos, corner_radius=40)
            balloon.create()
            # Render some text in the balloon
            r = textImage.get_rect()
            r.center = balloon.ballRect.center
            balloon.surf.blit(textImage, r)
            lastPos = pos

        # Now render the balloon and text on the display
        (xp, yp) = balloon.start
        display.fill((220,220,255))
        r = display.blit(balloon.surf, 
                     (xp-balloon.tipOffset[0], yp-balloon.tipOffset[1]))
        #pygame.draw.rect(display, (255,255,0), r, 1)

        pygame.display.flip()
