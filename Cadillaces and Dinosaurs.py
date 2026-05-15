import math
import random
import time
import os
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# STATE CONTAINERS

foes = []

ARENA_HALF = 500
HERO_STEP   = 8
FOE_STEP    = 0.8
SHOT_STEP   = 10

cam_elevation   = 150.0
cam_orbit       = 0.0
fpv_mode        = False

hero_pos  = [0, 0]
hero_yaw  = 90.0
hero_face = 90.0

hero_hp         = 100
score           = 0
death_flag      = False
topple_angle    = 0

auto_pilot      = False
top_cam_toggled = False

# --- Jab Mechanics ---
jab_on       = False
jab_tick     = 0
JAB_FRAMES   = 15
JAB_REACH    = 40

# --- Dive Kick Mechanics ---
dive_on       = False
dive_tick     = 0
dive_y_tick   = 0
DIVE_FRAMES   = 25
dive_hvel     = 0
dive_dx       = 0
dive_dz       = 0
DIVE_ANGLE    = 35
DIVE_REACH    = 60
dive_scored   = False

# --- World Dimensions ---
FLOOR_LENGTH  = 5000
SECTOR_SIZE   = 1000

# --- Hop Physics ---
hopping       = False
hop_tick      = 0
HOP_FRAMES    = 30
HOP_APEX      = 50
hero_lift     = 0
LIFT_INIT     = 2.5
PULL_DOWN     = 0.15

# --- Whirl Kick ---
whirl_on        = False
whirl_tick      = 0
WHIRL_FRAMES    = 30
WHIRL_SWEEP     = 120
WHIRL_PUSH      = 18
whirl_counted   = False

# --- Sector System ---
active_sector        = 0
SECTOR_FOE_QUOTA     = 5
sector_foes_deployed = 0
sector_foes_downed   = 0
sector_done          = False

# --- Stage & Overlord ---
stage_num      = 1
foe_index      = 0

overlord_alive      = False
overlord_shots      = []
OVERLORD_SHOT_VEL   = 8.0
overlord_firing     = False
overlord_fire_tick  = 0
OVERLORD_FIRE_WAIT  = 120
overlord_deployed   = False
overlord_vitality   = stage_num * 100 + 100

# --- Razor Discs ---
razor_discs       = []
RAZOR_DISC_VEL    = 7.0

# FEATURE GLOBALS

auto_mode     = False
warhead_pool  = []
WARHEAD_FALL  = 15
WARHEAD_ARM   = 300
BLAST_RADIUS  = 40
BOMB_FLIGHT_SPEED = 18.0
CHEAT_TURN_STEP = 6.0
CHEAT_TURN_TOL  = 5.0
DEFAULT_STRAIGHT_FACE = 90.0

# --- Pickup Items ---
box_pool      = []
loot_pool     = []
chunk_pool    = []
popup_pool    = []
BOXES_PER_SEC = 3

# --- Scenery & FX ---
flora_pool    = []
wreck_pool    = []
ember_pool    = []
cycle_tick    = 0
CYCLE_LENGTH  = 30 * 60
daytime       = True
flake_pool    = []
rock_pool     = []
ruin_pool     = []

# --- Interface State ---
paused        = False
menu_visible  = False
cheat_target_lock = None

# Scenery Generation & Rendering

def build_scenery():
    global flora_pool, wreck_pool, rock_pool, ruin_pool, SECTOR_SIZE, ARENA_HALF

    flora_pool.clear()
    wreck_pool.clear()
    rock_pool.clear()
    ruin_pool.clear()

    shade_keys   = ['dark', 'dark', 'mid', 'mid', 'mid', 'bright', 'bright', 'bright']
    shape_keys   = ['round', 'round', 'pointed', 'pointed', 'tall', 'tall', 'round', 'pointed']

    for sec in range(5):
        sx = sec * SECTOR_SIZE if sec > 0 else -ARENA_HALF
        ex = (sec + 1) * SECTOR_SIZE
        for k in range(8):
            rx = random.randint(int(sx) + 100, int(ex) - 100)
            rz = random.choice([
                random.randint(int(-ARENA_HALF) + 50, -100),
                random.randint(100, int(ARENA_HALF) - 50)
            ])
            flora_pool.append({
                'x': rx, 'z': rz,
                'shape': shape_keys[k % len(shape_keys)],
                'radius': random.randint(40, 60),
                'shade': shade_keys[k % len(shade_keys)],
                'stalk': random.randint(60, 90)
            })

    for sec in range(5):
        sx = sec * SECTOR_SIZE if sec > 0 else -ARENA_HALF
        ex = (sec + 1) * SECTOR_SIZE
        for _ in range(2):
            rx = random.randint(int(sx) + 150, int(ex) - 150)
            rz = random.randint(-200, 200)
            wreck_pool.append({'x': rx, 'z': rz, 'burning': random.choice([True, False])})


    for sec in range(5):
        sx = sec * SECTOR_SIZE if sec > 0 else -ARENA_HALF
        ex = (sec + 1) * SECTOR_SIZE

        for _ in range(5):
            rock_pool.append({
                'x': random.randint(int(sx) + 80, int(ex) - 80),
                'z': random.choice([
                    random.randint(int(-ARENA_HALF) + 60, -150),
                    random.randint(150, int(ARENA_HALF) - 60)
                ]),
                'sx': random.randint(18, 34),
                'sy': random.randint(10, 22),
                'sz': random.randint(16, 30),
            })

        ruin_pool.append({
            'x': sx + 120,
            'z': -ARENA_HALF + 65,
            'h': random.randint(80, 120),
            'w': random.randint(16, 26),
        })
        ruin_pool.append({
            'x': ex - 120,
            'z': ARENA_HALF - 65,
            'h': random.randint(70, 115),
            'w': random.randint(14, 24),
        })


def render_plant(x, z, stalk_h=80, crown_r=60, shape='round', shade='mid'):
    # Roots
    glColor3f(0.25, 0.15, 0.10)
    glPushMatrix()
    glTranslatef(x, 0, z); glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric(); gluCylinder(q, 12, 10, 8, 10, 1)
    glPopMatrix()

    # Stalk
    glColor3f(0.35, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(x, 0, z); glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric(); gluCylinder(q, 10, 8, stalk_h, 12, 1)
    glPopMatrix()

    if shade == 'dark':
        c_main = (0.08, 0.35, 0.08); c_shadow = (0.05, 0.25, 0.05)
    elif shade == 'bright':
        c_main = (0.35, 0.75, 0.35); c_shadow = (0.25, 0.65, 0.25)
    else:
        c_main = (0.20, 0.55, 0.20); c_shadow = (0.15, 0.45, 0.15)

    if shape == 'round':
        glColor3f(*c_shadow)
        glPushMatrix(); glTranslatef(x, stalk_h - 5, z)
        gluSphere(gluNewQuadric(), crown_r * 0.9, 16, 16); glPopMatrix()
        glColor3f(*c_main)
        glPushMatrix(); glTranslatef(x, stalk_h, z)
        gluSphere(gluNewQuadric(), crown_r, 16, 16); glPopMatrix()

    elif shape == 'pointed':
        glColor3f(*c_shadow)
        glPushMatrix(); glTranslatef(x, stalk_h - 5, z); glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), crown_r * 1.1, 0, crown_r * 1.6, 12, 1); glPopMatrix()
        glColor3f(*c_main)
        glPushMatrix(); glTranslatef(x, stalk_h, z); glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), crown_r, 0, crown_r * 1.5, 12, 1); glPopMatrix()

    elif shape == 'tall':
        glColor3f(*c_shadow)
        glPushMatrix(); glTranslatef(x, stalk_h - 5, z); glScalef(1.1, 1.6, 1.1)
        gluSphere(gluNewQuadric(), crown_r * 0.9, 16, 16); glPopMatrix()
        glColor3f(*c_main)
        glPushMatrix(); glTranslatef(x, stalk_h, z); glScalef(1.0, 1.5, 1.0)
        gluSphere(gluNewQuadric(), crown_r, 16, 16); glPopMatrix()


def render_wreck(x, z, burning=False):
    # Body
    glColor3f(0.7, 0.3, 0.1)
    glPushMatrix(); glTranslatef(x, 15, z); glRotatef(-10, 0, 1, 0); glScalef(50, 15, 30)
    glutSolidCube(1); glPopMatrix()

    # Roof
    glColor3f(0.6, 0.25, 0.08)
    glPushMatrix(); glTranslatef(x - 5, 22, z); glRotatef(-15, 0, 1, 0); glScalef(30, 5, 25)
    glutSolidCube(1); glPopMatrix()

    # Tyres
    for wx, wz in [(18, -14), (18, 14), (-18, -14), (-18, 14)]:
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix(); glTranslatef(x + wx, 8, z + wz); glRotatef(90, 0, 0, 1)
        gluCylinder(gluNewQuadric(), 6, 6, 4, 8, 1); glPopMatrix()



def render_rock(x, z, sx, sy, sz):
    glColor3f(0.38, 0.34, 0.30)
    glPushMatrix(); glTranslatef(x, sy * 0.55, z); glScalef(sx, sy, sz)
    gluSphere(gluNewQuadric(), 1, 12, 12); glPopMatrix()
    glColor3f(0.48, 0.44, 0.40)
    glPushMatrix(); glTranslatef(x - sx * 0.15, sy * 0.8, z + sz * 0.12); glScalef(sx * 0.35, sy * 0.28, sz * 0.32)
    gluSphere(gluNewQuadric(), 1, 10, 10); glPopMatrix()


def render_ruin_column(x, z, h, w):
    glColor3f(0.40, 0.39, 0.36)
    glPushMatrix(); glTranslatef(x, h * 0.5, z); glScalef(w, h, w)
    glutSolidCube(1); glPopMatrix()
    glColor3f(0.28, 0.26, 0.24)
    glPushMatrix(); glTranslatef(x, h + 6, z); glScalef(w * 1.2, 12, w * 1.2)
    glutSolidCube(1); glPopMatrix()


def render_road_overlay():
    road_y = 0.5
    glColor3f(0.16, 0.16, 0.17)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_HALF, road_y, -95); glVertex3f(FLOOR_LENGTH, road_y, -95)
    glVertex3f(FLOOR_LENGTH, road_y, 95); glVertex3f(-ARENA_HALF, road_y, 95)
    glEnd()

    glColor3f(0.88, 0.74, 0.18)
    dash_x = -ARENA_HALF + 40
    while dash_x < FLOOR_LENGTH - 40:
        glBegin(GL_QUADS)
        glVertex3f(dash_x, road_y + 0.2, -4); glVertex3f(dash_x + 42, road_y + 0.2, -4)
        glVertex3f(dash_x + 42, road_y + 0.2, 4); glVertex3f(dash_x, road_y + 0.2, 4)
        glEnd()
        dash_x += 88

    glColor3f(0.26, 0.22, 0.20)
    for crack_x in range(-360, int(FLOOR_LENGTH), 260):
        span = 18 + ((crack_x // 20) % 4) * 6
        glBegin(GL_TRIANGLES)
        glVertex3f(crack_x, road_y + 0.1, -55)
        glVertex3f(crack_x + span, road_y + 0.1, -48)
        glVertex3f(crack_x + 10, road_y + 0.1, -68)
        glEnd()

        glBegin(GL_TRIANGLES)
        glVertex3f(crack_x + 40, road_y + 0.1, 58)
        glVertex3f(crack_x + 58, road_y + 0.1, 47)
        glVertex3f(crack_x + 70, road_y + 0.1, 66)
        glEnd()


def render_backdrop_hills():
    ridge_y = 185
    if daytime:
        tone_a = (0.26, 0.36, 0.28)
        tone_b = (0.20, 0.28, 0.22)
    else:
        tone_a = (0.11, 0.14, 0.12)
        tone_b = (0.08, 0.10, 0.09)

    glColor3f(*tone_b)
    glBegin(GL_TRIANGLES)
    glVertex3f(-ARENA_HALF - 350, 0, -ARENA_HALF - 300)
    glVertex3f(900, ridge_y, -ARENA_HALF - 300)
    glVertex3f(FLOOR_LENGTH + 450, 0, -ARENA_HALF - 300)
    glEnd()

    glColor3f(*tone_a)
    glBegin(GL_TRIANGLES)
    glVertex3f(-ARENA_HALF - 350, 0, ARENA_HALF + 300)
    glVertex3f(1200, ridge_y + 35, ARENA_HALF + 300)
    glVertex3f(FLOOR_LENGTH + 450, 0, ARENA_HALF + 300)
    glEnd()


def render_all_scenery():
    for pl in flora_pool:
        render_plant(pl['x'], pl['z'], pl['stalk'], pl['radius'], pl['shape'], pl['shade'])
    for wr in wreck_pool:
        render_wreck(wr['x'], wr['z'], wr.get('burning', False))
    for rock in rock_pool:
        render_rock(rock['x'], rock['z'], rock['sx'], rock['sy'], rock['sz'])
    for ruin in ruin_pool:
        render_ruin_column(ruin['x'], ruin['z'], ruin['h'], ruin['w'])


def scenery_blocks(tx, tz, margin=15):
    """Returns True if (tx, tz) collides with any scenery object."""
    for pl in flora_pool:
        if math.hypot(tx - pl['x'], tz - pl['z']) < pl['radius'] * 0.5 + margin:
            return True
    for wr in wreck_pool:
        if math.hypot(tx - wr['x'], tz - wr['z']) < 40 + margin:
            return True
    for bx in box_pool:
        if math.hypot(tx - bx['pos'][0], tz - bx['pos'][1]) < 20 + margin:
            return True
    return False


def wrap_angle(deg):
    while deg < 0:
        deg += 360
    while deg >= 360:
        deg -= 360
    return deg


def signed_turn_delta(target_deg, current_deg):
    return (target_deg - current_deg + 180) % 360 - 180


def nearest_auto_target():
    nearest = None
    nearest_dist = 10 ** 9
    for foe in foes:
        if foe.get('marked', False):
            continue
        ground_dist = math.hypot(hero_pos[0] - foe['pos'][0], hero_pos[1] - foe['pos'][2])
        if ground_dist < WARHEAD_ARM and ground_dist < nearest_dist:
            nearest = foe
            nearest_dist = ground_dist
    return nearest


def jab_extension_value():
    phase = jab_tick / float(max(1, JAB_FRAMES))
    if phase < 0.20:
        return 8.0 * (phase / 0.20)
    if phase < 0.55:
        return 8.0 + 38.0 * ((phase - 0.20) / 0.35)
    if phase < 0.80:
        return 46.0 - 20.0 * ((phase - 0.55) / 0.25)
    return 26.0 * (1.0 - ((phase - 0.80) / 0.20))


# CYCLE & PARTICLE UPDATES 

def tick_day_cycle():
    global cycle_tick, daytime
    cycle_tick += 1
    if cycle_tick >= CYCLE_LENGTH:
        cycle_tick = 0
        daytime = not daytime


def tick_snowfall():
    global flake_pool
    if not daytime:
        if random.random() < 0.5:
            flake_pool.append({
                'x': hero_pos[0] + random.uniform(-500, 500),
                'y': random.uniform(100, 200),
                'z': hero_pos[1] + random.uniform(-400, 400),
                'vz': random.uniform(-1.5, -0.5),
                'vx': random.uniform(-0.3, 0.3),
                'sz': random.uniform(2, 5),
                'ttl': 300
            })
    surviving = []
    for fl in flake_pool:
        fl['x'] += fl['vx']
        fl['y'] += fl['vz']
        fl['ttl'] -= 1
        if fl['y'] > 2 and fl['ttl'] > 0:
            surviving.append(fl)
    flake_pool[:] = surviving


def render_snowfall():
    glColor3f(1.0, 1.0, 1.0)
    for fl in flake_pool:
        glPushMatrix(); glTranslatef(fl['x'], fl['y'], fl['z'])
        gluSphere(gluNewQuadric(), fl['sz'], 6, 6); glPopMatrix()


def tick_embers():
    global ember_pool
    for wr in wreck_pool:
        if wr.get('burning') and random.random() < 0.3:
            ember_pool.append({
                'x': wr['x'] + random.uniform(-20, 20),
                'z': wr['z'] + random.uniform(-10, 10),
                'y': 15 + random.uniform(0, 10),
                'vy': random.uniform(2, 4),
                'ttl': random.randint(20, 40),
                'sz': random.uniform(3, 8),
                'r': 1.0, 'g': random.uniform(0.3, 0.7), 'b': 0.0
            })
    alive = []
    for em in ember_pool:
        em['y']  += em['vy']
        em['vy'] *= 0.95
        em['ttl'] -= 1
        em['sz']  *= 0.97
        if em['ttl'] > 0:
            alive.append(em)
    ember_pool[:] = alive


def render_embers():
    for em in ember_pool:
        glColor3f(em['r'], em['g'], em['b'])
        glPushMatrix(); glTranslatef(em['x'], em['y'], em['z'])
        gluSphere(gluNewQuadric(), em['sz'], 6, 6); glPopMatrix()


# CAMERA

def setup_view():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, 1000 / 800, 0.1, 5000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    eye_y = 36 + hero_lift
    rad = math.radians(hero_face)

    # FIRST PERSON MODE
    
    if fpv_mode:
        eye_x = hero_pos[0]
        eye_z = hero_pos[1]

        look_x = eye_x + math.sin(rad) * 100
        look_z = eye_z + math.cos(rad) * 100

        gluLookAt(
            eye_x, eye_y, eye_z,
            look_x, eye_y, look_z,
            0, 1, 0
        )
        return

    # THIRD PERSON MODE

    orbit_rad = math.radians(hero_face + cam_orbit)

    dist = 120
    height = cam_elevation

    cam_x = hero_pos[0] - math.sin(orbit_rad) * dist
    cam_y = eye_y + height
    cam_z = hero_pos[1] - math.cos(orbit_rad) * dist

    gluLookAt(
        cam_x, cam_y, cam_z,
        hero_pos[0], eye_y, hero_pos[1],
        0, 1, 0
    )

# FLOOR & WALLS

def render_floor():
    TILE = 30
    level_palettes = {
        1: ((0.70, 0.75, 0.80), (0.60, 0.65, 0.70)),
        2: ((0.25, 0.40, 0.20), (0.35, 0.30, 0.20)),
        3: ((0.85, 0.75, 0.60), (0.80, 0.70, 0.55)),
        4: ((0.60, 0.60, 0.65), (0.50, 0.50, 0.55)),
    }
    ca, cb = level_palettes.get(stage_num, ((1.0, 1.0, 1.0), (0.8, 0.7, 1.0)))

    ix = -ARENA_HALF
    while ix < FLOOR_LENGTH:
        jz = -ARENA_HALF
        while jz < ARENA_HALF:
            parity = (int(ix // TILE) + int(jz // TILE)) % 2
            glColor3f(*(ca if parity == 0 else cb))
            glBegin(GL_QUADS)
            glVertex3f(ix, 0, jz);          glVertex3f(ix + TILE, 0, jz)
            glVertex3f(ix + TILE, 0, jz + TILE); glVertex3f(ix, 0, jz + TILE)
            glEnd()
            jz += TILE
        ix += TILE

    render_road_overlay()


def render_border_walls():
    H = 50
    glColor3f(0, 0, 1); glBegin(GL_QUADS)
    glVertex3f(-ARENA_HALF, 0, -ARENA_HALF); glVertex3f(-ARENA_HALF, 0, ARENA_HALF)
    glVertex3f(-ARENA_HALF, H, ARENA_HALF);  glVertex3f(-ARENA_HALF, H, -ARENA_HALF)
    glEnd()

    glColor3f(1, 1, 0); glBegin(GL_QUADS)
    glVertex3f(-ARENA_HALF, 0, ARENA_HALF); glVertex3f(FLOOR_LENGTH, 0, ARENA_HALF)
    glVertex3f(FLOOR_LENGTH, H, ARENA_HALF); glVertex3f(-ARENA_HALF, H, ARENA_HALF)
    glEnd()

    glColor3f(0, 1, 0); glBegin(GL_QUADS)
    glVertex3f(FLOOR_LENGTH, 0, -ARENA_HALF); glVertex3f(FLOOR_LENGTH, 0, ARENA_HALF)
    glVertex3f(FLOOR_LENGTH, H, ARENA_HALF);  glVertex3f(FLOOR_LENGTH, H, -ARENA_HALF)
    glEnd()

    glColor3f(0, 0.8, 0.8); glBegin(GL_QUADS)
    glVertex3f(FLOOR_LENGTH, 0, -ARENA_HALF); glVertex3f(-ARENA_HALF, 0, -ARENA_HALF)
    glVertex3f(-ARENA_HALF, H, -ARENA_HALF);  glVertex3f(FLOOR_LENGTH, H, -ARENA_HALF)
    glEnd()

# HERO RENDERING

def render_hero():
    glPushMatrix()
    glTranslatef(hero_pos[0], 25 + hero_lift, hero_pos[1])
    glRotatef(hero_face, 0, 1, 0)

    if dive_on:
        lean = 30 * (dive_tick / DIVE_FRAMES)
        glRotatef(lean, 1, 0, 0)

    if death_flag:
        glRotatef(topple_angle, 1, 0, 0)

    q = gluNewQuadric()

    # Torso
    glColor3f(0.35, 0.48, 0.28)
    glPushMatrix(); glTranslatef(0, 8, 0); glScalef(2.3, 3.1, 1.5); glutSolidCube(10); glPopMatrix()

    # Skull
    glColor3f(0, 0, 0)
    glPushMatrix(); glTranslatef(0, 26, 0); gluSphere(q, 7.5, 22, 22); glPopMatrix()

    # Left forearm
    glColor3f(0.98, 0.83, 0.72)
    glPushMatrix(); glTranslatef(-11.5, 13, 5); gluCylinder(q, 4.2, 4.2, 16, 12, 12); glPopMatrix()

    # Right forearm / jab
    glColor3f(0.98, 0.83, 0.72)
    glPushMatrix(); glTranslatef(11.5, 13, 5)
    glove_shift = 0
    if jab_on and not dive_on:
        extension = jab_extension_value()
        glove_shift = extension * 0.18
        glTranslatef(0, 0, extension)
    gluCylinder(q, 4.2, 4.2, 16, 12, 12)
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix(); glTranslatef(0, 0, 16 + glove_shift); gluCylinder(q, 3.8, 0, 6.5, 18, 18); glPopMatrix()
    glPopMatrix()

    # Legs
    for side in [-1, 1]:
        glPushMatrix(); glTranslatef(side * 8.5, -3, 0)
        if whirl_on:
            ang = (side * whirl_tick / WHIRL_FRAMES) * 360
            glRotatef(ang, 0, 1, 0); glRotatef(110, 1, 0, 0)
            glColor3f(1.0, 0.4, 0.0)
        elif dive_on and side == 1:
            ext = (dive_tick / DIVE_FRAMES) * 35
            glRotatef(45 + ext, 1, 0, 0); glTranslatef(0, 0, ext * 0.5)
            glColor3f(1.0, 0.3, 0.0)
        else:
            glRotatef(90, 1, 0, 0); glColor3f(0, 0, 0.75)
        gluCylinder(q, 5.2, 5.2, 26, 12, 12)
        glPopMatrix()

    glPopMatrix()

# ENEMY RENDERING

def render_type_grunt(q, sz):
    glColor3f(0.1, 0.2, 0.7)
    for side in [-4, 4]:
        glPushMatrix(); glTranslatef(side, 0, 0); glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 3, 3, 14, 8, 8); glPopMatrix()
    glColor3f(0.9, 0.8, 0.1)
    glPushMatrix(); glTranslatef(0, 25, 0); glScalef(1.2, 1.5, 0.8); glutSolidCube(15); glPopMatrix()
    glColor3f(0.8, 0.6, 0.5)
    glPushMatrix(); glTranslatef(0, 38, 0); gluSphere(q, 6, 16, 16); glPopMatrix()


def render_type_scout(q, sz):
    glColor3f(0.2, 0.15, 0.1)
    for side in [-5, 5]:
        glPushMatrix(); glTranslatef(side, 0, 0); glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 4, 3, 12, 8, 8); glPopMatrix()
    glColor3f(0.1, 0.4, 0.1)
    glPushMatrix(); glTranslatef(0, 22, 0); glScalef(1.5, 1.4, 1.0); glutSolidCube(15); glPopMatrix()
    glColor3f(0.8, 0.6, 0.5)
    glPushMatrix(); glTranslatef(0, 35, 0); gluSphere(q, 6, 16, 16); glPopMatrix()


def render_type_beast(q, sz):
    gait = math.sin(time.time() * 4.0)
    bob = math.sin(time.time() * 2.0) * 0.8
    tail_wave = math.sin(time.time() * 3.0) * 10.0
    jaw_open = max(0.0, math.sin(time.time() * 5.0)) * 10.0

    glPushMatrix()
    glTranslatef(0, 12 + bob, 0)

    # Hind legs
    for side, phase in [(-1, gait), (1, -gait)]:
        upper_ang = 12 * phase
        lower_ang = -8 * phase
        glColor3f(0.18, 0.55, 0.18)
        glPushMatrix(); glTranslatef(side * 7.5, -11, -1.0); glRotatef(upper_ang, 1, 0, 0); glRotatef(90, 1, 0, 0)
        gluCylinder(q, 3.8, 3.2, 15, 10, 10); glPopMatrix()
        glColor3f(0.15, 0.47, 0.15)
        glPushMatrix(); glTranslatef(side * 7.5, -21, 5.5); glRotatef(88 + lower_ang, 1, 0, 0)
        gluCylinder(q, 2.7, 1.7, 12, 10, 10); glPopMatrix()

    # Body
    glColor3f(0.28, 0.76, 0.30)
    glPushMatrix(); glScalef(1.55, 1.0, 2.7); gluSphere(q, 8.5, 18, 18); glPopMatrix()
    glColor3f(0.20, 0.56, 0.20)
    glPushMatrix(); glTranslatef(0, 4, -4); glScalef(1.1, 0.75, 2.0); gluSphere(q, 7.0, 16, 16); glPopMatrix()

    # Tail
    glColor3f(0.18, 0.58, 0.18)
    glPushMatrix(); glTranslatef(0, 1.2, -20); glRotatef(180 + tail_wave, 0, 1, 0); glRotatef(-10, 1, 0, 0)
    gluCylinder(q, 4.6, 1.0, 26, 12, 12); glPopMatrix()

    # Neck
    glColor3f(0.22, 0.62, 0.22)
    glPushMatrix(); glTranslatef(0, 4.5, 15); glRotatef(-34, 1, 0, 0); gluCylinder(q, 4.2, 3.0, 14, 12, 12); glPopMatrix()

    # Head
    glColor3f(0.30, 0.82, 0.32)
    glPushMatrix(); glTranslatef(0, 10.5, 24.5); glScalef(0.95, 0.8, 1.55); gluSphere(q, 5.2, 16, 16); glPopMatrix()

    # Snout and jaw
    glColor3f(0.24, 0.68, 0.24)
    glPushMatrix(); glTranslatef(0, 9.8, 31.2); glRotatef(-6, 1, 0, 0); glRotatef(90, 1, 0, 0)
    gluCylinder(q, 2.6, 0.8, 8.5, 10, 10); glPopMatrix()
    glColor3f(0.62, 0.78, 0.52)
    glPushMatrix(); glTranslatef(0, 8.0, 28.7); glRotatef(jaw_open, 1, 0, 0); glScalef(0.75, 0.18, 1.25)
    glutSolidCube(8); glPopMatrix()

    # Arms
    for side in [-1, 1]:
        glColor3f(0.20, 0.60, 0.20)
        glPushMatrix(); glTranslatef(side * 5.0, 0.5, 11.5); glRotatef(32, 1, 0, 0); glRotatef(side * 18, 0, 0, 1)
        gluCylinder(q, 1.4, 0.8, 8.0, 8, 8); glPopMatrix()

    # Back spikes
    spike_z = -8
    while spike_z < 16:
        glColor3f(0.13, 0.40, 0.13)
        glPushMatrix(); glTranslatef(0, 8.5, spike_z); glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 1.5, 0.0, 4.0, 6, 1); glPopMatrix()
        spike_z += 6

    # Eyes
    for side in [-1, 1]:
        glColor3f(0.95, 0.18, 0.10)
        glPushMatrix(); glTranslatef(side * 1.7, 11.4, 28.5); gluSphere(q, 0.8, 8, 8); glPopMatrix()

    glPopMatrix()


def render_type_brute(q, sz):
    glColor3f(0.2, 0.3, 0.2)
    for side in [-10, 10]:
        glPushMatrix(); glTranslatef(side, 0, 0); glRotatef(-90, 1, 0, 0)
        gluCylinder(q, 5, 5, 16, 10, 10); glPopMatrix()
    glColor3f(0.9, 0.9, 0.9)
    glPushMatrix(); glTranslatef(0, 24, 0); glScalef(1.5, 1.3, 1.3)
    gluSphere(q, 13, 20, 20); glPopMatrix()
    glColor3f(0.8, 0.6, 0.5)
    glPushMatrix(); glTranslatef(0, 42, 0); glScalef(1.1, 1.0, 1.1)
    gluSphere(q, 7, 16, 16); glPopMatrix()


def render_overlord_model(q):
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix(); glTranslatef(0, 10, 0); glScalef(2.5, 4.0, 1.8); glutSolidCube(10); glPopMatrix()
    glColor3f(0.8, 0.6, 0.5)
    glPushMatrix(); glTranslatef(0, 35, 0); gluSphere(q, 8, 16, 16)
    glColor3f(0.1, 0.1, 0.1); glTranslatef(0, 5, 0); glRotatef(-90, 1, 0, 0)
    gluCylinder(q, 10, 7, 4, 16, 16); glPopMatrix()
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix(); glTranslatef(12, 25, 0)
    if overlord_firing:
        glRotatef(-90, 1, 0, 0)
    gluCylinder(q, 4, 3, 15, 8, 8); glPopMatrix()


def render_razor_discs():
    for disc in razor_discs:
        glPushMatrix(); glTranslatef(disc['pos'][0], 25, disc['pos'][1])
        glRotatef(disc['angle'], 0, 1, 0)
        glColor3f(1.0, 0.0, 0.0); glPushMatrix(); glTranslatef(-3, 0, 0); glScalef(6.0, 0.8, 1.5); glutSolidCube(1); glPopMatrix()
        glColor3f(0.8, 0.7, 0.2); glPushMatrix(); glScalef(1.0, 1.0, 4.0); glutSolidCube(1); glPopMatrix()
        glColor3f(0.9, 0.9, 0.9); glPushMatrix(); glTranslatef(4, 0, 0); glScalef(8.0, 0.2, 2.0); glutSolidCube(1); glPopMatrix()
        glPopMatrix()


def render_projectiles():
    glColor3f(1, 1, 0)
    q = gluNewQuadric()
    for sh in overlord_shots:
        glPushMatrix(); glTranslatef(sh['pos'][0], 25, sh['pos'][1])
        gluSphere(q, 3, 8, 8); glPopMatrix()
    render_razor_discs()


def render_all_foes():
    for foe in foes:
        glPushMatrix()
        glTranslatef(foe['pos'][0], foe['pos'][1], foe['pos'][2])
        adx = hero_pos[0] - foe['pos'][0]
        adz = hero_pos[1] - foe['pos'][2]
        face_ang = math.degrees(math.atan2(adx, adz))
        glRotatef(face_ang, 0, 1, 0)
        glScalef(foe['scale'], foe['scale'], foe['scale'])
        q = gluNewQuadric()
        ft = foe.get('kind', 1)
        if ft == 1:   render_type_grunt(q, foe['scale'])
        elif ft == 2: render_type_scout(q, foe['scale'])
        elif ft == 3: render_type_beast(q, foe['scale'])
        elif ft == 4: render_type_brute(q, foe['scale'])
        elif ft == 5: render_overlord_model(q)
        glPopMatrix()

# ATTACK VISUAL INDICATORS

def render_dive_indicator():
    if not dive_on: return
    glPushMatrix()
    glTranslatef(hero_pos[0], hero_lift + 25, hero_pos[1])
    glRotatef(hero_face, 0, 1, 0)
    prog = dive_tick / DIVE_FRAMES
    glTranslatef(0, -10, 25 + prog * 35)
    glColor3f(1, 0.4, 0)
    glPushMatrix(); glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 8, 30, 16, 16); glPopMatrix()
    glPopMatrix()


def render_jab_indicator():
    if not jab_on or dive_on: return
    glPushMatrix()
    glTranslatef(hero_pos[0], 25, hero_pos[1])
    glRotatef(hero_face, 0, 1, 0)
    dist = 20 + (jab_tick / JAB_FRAMES) * 20
    glTranslatef(0, 0, dist)
    fade = 1 - (jab_tick / JAB_FRAMES) * 0.5
    glColor3f(1, fade, 0)
    gluSphere(gluNewQuadric(), 8 + (jab_tick / JAB_FRAMES) * 4, 16, 16)
    glPopMatrix()


# HUD & UI

def hud_text(px, py, msg, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(px, py)
    for ch in msg:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)


def draw_wire_box(edge_len):
    half = edge_len / 2.0
    pts = [
        (-half, -half, -half), ( half, -half, -half),
        ( half,  half, -half), (-half,  half, -half),
        (-half, -half,  half), ( half, -half,  half),
        ( half,  half,  half), (-half,  half,  half),
    ]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    glBegin(GL_LINES)
    for a, b in edges:
        glVertex3f(*pts[a])
        glVertex3f(*pts[b])
    glEnd()


def draw_octa_body(radius):
    top = (0, radius, 0)
    bottom = (0, -radius, 0)
    ring = [(-radius, 0, 0), (0, 0, radius), (radius, 0, 0), (0, 0, -radius)]
    faces = [
        (top, ring[0], ring[1]), (top, ring[1], ring[2]),
        (top, ring[2], ring[3]), (top, ring[3], ring[0]),
        (bottom, ring[1], ring[0]), (bottom, ring[2], ring[1]),
        (bottom, ring[3], ring[2]), (bottom, ring[0], ring[3]),
    ]
    glBegin(GL_TRIANGLES)
    for a, b, c in faces:
        glVertex3f(*a)
        glVertex3f(*b)
        glVertex3f(*c)
    glEnd()


def render_sky_shell():
    if daytime:
        tone = (0.5, 0.8, 0.9)
    else:
        tone = (0.05, 0.05, 0.1)

    x0 = -ARENA_HALF - 700
    x1 = FLOOR_LENGTH + 700
    z0 = -ARENA_HALF - 700
    z1 = ARENA_HALF + 700
    y0 = -20
    y1 = 900

    glColor3f(*tone)
    glBegin(GL_QUADS)
    glVertex3f(x0, y0, z0); glVertex3f(x1, y0, z0); glVertex3f(x1, y1, z0); glVertex3f(x0, y1, z0)
    glVertex3f(x1, y0, z1); glVertex3f(x0, y0, z1); glVertex3f(x0, y1, z1); glVertex3f(x1, y1, z1)
    glVertex3f(x0, y0, z1); glVertex3f(x0, y0, z0); glVertex3f(x0, y1, z0); glVertex3f(x0, y1, z1)
    glVertex3f(x1, y0, z0); glVertex3f(x1, y0, z1); glVertex3f(x1, y1, z1); glVertex3f(x1, y1, z0)
    glVertex3f(x0, y1, z0); glVertex3f(x1, y1, z0); glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1)
    glEnd()


def render_advance_prompt():
    if sector_done and int(time.time() * 2) % 2 == 0:
        glColor3f(0, 1, 0)
        hud_text(800, 600, "GO! >>>", GLUT_BITMAP_TIMES_ROMAN_24)


def render_ui_panel():
    glClear(GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Play/Pause (top-right)
    if paused:
        glColor3f(0, 1, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(945, 750, 0); glVertex3f(945, 790, 0); glVertex3f(980, 770, 0)
        glEnd()
    else:
        glColor3f(1, 0.8, 0)
        glBegin(GL_QUADS)
        glVertex3f(948, 750, 0); glVertex3f(956, 750, 0); glVertex3f(956, 790, 0); glVertex3f(948, 790, 0)
        glVertex3f(966, 750, 0); glVertex3f(974, 750, 0); glVertex3f(974, 790, 0); glVertex3f(966, 790, 0)
        glEnd()

    # Restart icon
    glColor3f(0, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(940, 700, 0); glVertex3f(980, 700, 0); glVertex3f(980, 740, 0); glVertex3f(940, 740, 0)
    glEnd()
    glColor3f(1, 1, 1)
    glBegin(GL_LINE_STRIP)
    for i in range(270):
        rd = math.radians(i + 45)
        glVertex3f(960 + 10 * math.cos(rd), 720 + 10 * math.sin(rd), 0)
    glEnd()
    glBegin(GL_TRIANGLES)
    glVertex3f(965, 725, 0); glVertex3f(975, 725, 0); glVertex3f(970, 735, 0)
    glEnd()

    # Exit icon
    glColor3f(1, 0, 0)
    glBegin(GL_LINES)
    glVertex3f(945, 655, 0); glVertex3f(975, 685, 0)
    glVertex3f(945, 685, 0); glVertex3f(975, 655, 0)
    glEnd()

    # Restart menu overlay
    if menu_visible:
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex3f(250, 300, 0); glVertex3f(750, 300, 0); glVertex3f(750, 500, 0); glVertex3f(250, 500, 0)
        glEnd()
        glColor3f(1, 1, 1); hud_text(350, 460, "YOU DIED / RESTART MENU")

        glColor3f(0, 0.5, 1)
        glBegin(GL_QUADS)
        glVertex3f(300, 380, 0); glVertex3f(490, 380, 0); glVertex3f(490, 430, 0); glVertex3f(300, 430, 0)
        glEnd()
        glColor3f(1, 1, 1); hud_text(320, 400, f"Restart Level {stage_num}")

        glColor3f(1, 0.5, 0)
        glBegin(GL_QUADS)
        glVertex3f(510, 380, 0); glVertex3f(700, 380, 0); glVertex3f(700, 430, 0); glVertex3f(510, 430, 0)
        glEnd()
        glColor3f(1, 1, 1); hud_text(540, 400, "New Game")

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# WARHEAD (CHEAT) SYSTEM

def right_hand_anchor():
    rad = math.radians(hero_face)
    fx = math.sin(rad)
    fz = math.cos(rad)
    rx = math.cos(rad)
    rz = -math.sin(rad)
    return [
        hero_pos[0] + fx * 16 + rx * 8,
        36 + hero_lift,
        hero_pos[1] + fz * 16 + rz * 8,
    ]

def render_warheads():
    for wh in warhead_pool:
        glPushMatrix(); glTranslatef(wh['pos'][0], wh['pos'][1], wh['pos'][2])
        if wh['phase'] == 'flying':
            glColor3f(1.0, 0.35, 0.0)
            gluSphere(gluNewQuadric(), 6, 12, 12)
            glColor3f(1.0, 0.85, 0.1)
            glPushMatrix(); glTranslatef(0, 0, -6)
            gluSphere(gluNewQuadric(), 3, 10, 10)
            glPopMatrix()
        elif wh['phase'] == 'blasting':
            frac = wh['timer'] / 20.0
            if frac < 0.3:   glColor3f(1.0, 1.0, 0.0)
            elif frac < 0.7: glColor3f(1.0, 0.2, 0.0)
            else:             glColor3f(0.5, 0.5, 0.5)
            gluSphere(gluNewQuadric(), BLAST_RADIUS * frac, 16, 16)
        glPopMatrix()


def tick_warheads():
    global score, sector_foes_downed, hero_face, hero_yaw, cheat_target_lock

    if auto_mode:
        active_target_ids = {
            id(wh.get('target'))
            for wh in warhead_pool
            if wh.get('phase') == 'flying' and wh.get('target') is not None
        }

        if cheat_target_lock is None or cheat_target_lock not in foes or cheat_target_lock.get('marked', False):
            cheat_target_lock = nearest_auto_target()

        if cheat_target_lock is not None and id(cheat_target_lock) not in active_target_ids:
            tx = cheat_target_lock['pos'][0]
            tz = cheat_target_lock['pos'][2]
            desired = wrap_angle(math.degrees(math.atan2(tx - hero_pos[0], tz - hero_pos[1])))
            delta = signed_turn_delta(desired, hero_face)

            if abs(delta) <= CHEAT_TURN_TOL:
                hero_face = desired
                hero_yaw = desired
                cheat_target_lock['marked'] = True
                warhead_pool.append({
                    'pos': right_hand_anchor(),
                    'phase': 'flying',
                    'timer': 0,
                    'target': cheat_target_lock,
                    'speed': BOMB_FLIGHT_SPEED,
                })
                cheat_target_lock = None
            else:
                turn_step = max(-CHEAT_TURN_STEP, min(CHEAT_TURN_STEP, delta))
                hero_face = wrap_angle(hero_face + turn_step)
                hero_yaw = hero_face
        elif cheat_target_lock is None and not active_target_ids:
            # No current cheat target and no bomb in flight:
            # return the player body to the normal straight-facing angle
            hero_face = DEFAULT_STRAIGHT_FACE
            hero_yaw = DEFAULT_STRAIGHT_FACE
    else:
        cheat_target_lock = None

    expired_indices   = []
    foes_to_terminate = []

    for wi, wh in enumerate(warhead_pool):
        if wh['phase'] == 'flying':
            tgt = wh.get('target')
            if tgt is None or tgt not in foes:
                expired_indices.append(wi)
                continue

            tx = tgt['pos'][0]
            ty = tgt['pos'][1] + 20
            tz = tgt['pos'][2]

            dx = tx - wh['pos'][0]
            dy = ty - wh['pos'][1]
            dz = tz - wh['pos'][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)

            if dist <= wh['speed'] or dist < 1e-6:
                wh['pos'] = [tx, ty, tz]
                wh['phase'] = 'blasting'
                wh['timer'] = 0
                for fi, foe in enumerate(foes):
                    blast_dist = math.hypot(wh['pos'][0] - foe['pos'][0], wh['pos'][2] - foe['pos'][2])
                    if blast_dist < 28:
                        foes_to_terminate.append(fi)
            else:
                step = wh['speed'] / dist
                wh['pos'][0] += dx * step
                wh['pos'][1] += dy * step
                wh['pos'][2] += dz * step

        elif wh['phase'] == 'blasting':
            wh['timer'] += 1
            if wh['timer'] > 20:
                expired_indices.append(wi)

    for wi in sorted(expired_indices, reverse=True):
        del warhead_pool[wi]

    unique_kills = sorted(set(foes_to_terminate), reverse=True)
    for fi in unique_kills:
        if fi < len(foes):
            emit_popup(foes[fi]['pos'][0], 50, foes[fi]['pos'][2], "+KILL (CHEAT)")
            del foes[fi]
            sector_foes_downed += 1
            score += 1


# COLLECTIBLES & VISUALS

def emit_popup(x, y, z, txt):
    popup_pool.append({'x': x, 'y': y, 'z': z, 'msg': txt, 'ttl': 50})


def scatter_chunks(x, z):
    for _ in range(8):
        chunk_pool.append({
            'x': x, 'y': 15, 'z': z,
            'vx': random.uniform(-1, 1), 'vy': random.uniform(1, 3), 'vz': random.uniform(-1, 1),
            'ttl': 40
        })


def deploy_boxes_for_sector():
    global box_pool, loot_pool
    box_pool.clear(); loot_pool.clear()
    sec_lo = -ARENA_HALF if active_sector == 0 else active_sector * SECTOR_SIZE
    sec_hi = (active_sector + 1) * SECTOR_SIZE
    lo, hi = sec_lo + 100, sec_hi - 100
    if lo < hi:
        for _ in range(BOXES_PER_SEC):
            bx = random.uniform(lo, hi)
            bz = random.uniform(-ARENA_HALF + 50, ARENA_HALF - 50)
            box_pool.append({'pos': [bx, bz]})


def tick_collectibles():
    global hero_hp, score
    for pp in popup_pool:
        pp['y'] += 1; pp['ttl'] -= 1
    popup_pool[:] = [pp for pp in popup_pool if pp['ttl'] > 0]

    for ch in chunk_pool:
        ch['x'] += ch['vx']; ch['y'] += ch['vy']
        ch['z'] += ch['vz']; ch['vy'] -= 0.3; ch['ttl'] -= 1
    chunk_pool[:] = [ch for ch in chunk_pool if ch['ttl'] > 0]

    attacking = jab_on or dive_on or whirl_on
    broken = []
    if attacking:
        for bi, bx in enumerate(box_pool):
            d = math.hypot(hero_pos[0] - bx['pos'][0], hero_pos[1] - bx['pos'][1])
            if d < 50:
                broken.append(bi)
                scatter_chunks(bx['pos'][0], bx['pos'][1])
                kind  = random.choice(['health', 'score'])
                worth = random.choice([50, 100, 200])
                loot_pool.append({'pos': bx['pos'][:], 'kind': kind, 'worth': worth})
    for bi in sorted(broken, reverse=True):
        del box_pool[bi]

    grabbed = []
    for li, loot in enumerate(loot_pool):
        d = math.hypot(hero_pos[0] - loot['pos'][0], hero_pos[1] - loot['pos'][1])
        if d < 50:
            grabbed.append(li)
            if loot['kind'] == 'health':
                emit_popup(loot['pos'][0], 40, loot['pos'][1], "+20 HP")
                hero_hp = min(100, hero_hp + 20)
            else:
                emit_popup(loot['pos'][0], 40, loot['pos'][1], f"+{loot['worth']} PTS")
                score += loot.get('worth', 50)
    for li in sorted(grabbed, reverse=True):
        del loot_pool[li]


def render_collectibles():
    # Boxes
    for bx in box_pool:
        glPushMatrix(); glTranslatef(bx['pos'][0], 15, bx['pos'][1])
        glColor3f(0.6, 0.4, 0.2); glutSolidCube(30)
        glColor3f(0.0, 0.0, 0.0); draw_wire_box(30.2)
        glPopMatrix()

    # Loot
    spin = time.time() * 100
    for loot in loot_pool:
        glPushMatrix(); glTranslatef(loot['pos'][0], 15, loot['pos'][1])
        glRotatef(spin, 0, 1, 0)
        if loot['kind'] == 'health':
            glColor3f(0.0, 1.0, 0.0); gluSphere(gluNewQuadric(), 10, 16, 16)
        else:
            glColor3f(1.0, 0.8, 0.0); glScalef(1.0, 1.5, 1.0); draw_octa_body(10)
        glPopMatrix()

    # Chunks
    for ch in chunk_pool:
        glPushMatrix(); glTranslatef(ch['x'], ch['y'], ch['z'])
        glColor3f(0.5, 0.3, 0.1); glutSolidCube(3)
        glPopMatrix()

    # Popups
    for pp in popup_pool:
        glColor3f(1, 1, 0)
        glPushMatrix(); glTranslatef(pp['x'], pp['y'], pp['z'])
        glRasterPos2f(0, 0)
        for ch in pp['msg']:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glPopMatrix()

# GAME LOGIC UPDATES

def tick_overlord_shots():
    global overlord_shots, hero_hp, death_flag
    still_live = []
    for sh in overlord_shots:
        sh['pos'][0] += sh['dir'][0] * OVERLORD_SHOT_VEL
        sh['pos'][1] += sh['dir'][1] * OVERLORD_SHOT_VEL
        d = math.hypot(sh['pos'][0] - hero_pos[0], sh['pos'][1] - hero_pos[1])
        if d < 15:
            hero_hp -= 15
            if hero_hp <= 0: death_flag = True
            continue
        if abs(sh['pos'][0] - hero_pos[0]) < 1000:
            still_live.append(sh)
    overlord_shots[:] = still_live


def tick_razor_discs():
    global razor_discs, hero_hp, death_flag
    still_live = []
    for disc in razor_discs:
        disc['pos'][0] += disc['vel'][0]
        disc['pos'][1] += disc['vel'][1]
        disc['angle']   = (disc['angle'] + 20) % 360
        d = math.hypot(disc['pos'][0] - hero_pos[0], disc['pos'][1] - hero_pos[1])
        if d < 20:
            hero_hp -= 10
            if hero_hp <= 0: death_flag = True
            continue
        if abs(disc['pos'][0] - hero_pos[0]) < 1200:
            still_live.append(disc)
    razor_discs[:] = still_live


def deploy_overlord():
    global foes, overlord_vitality
    sec_lo = -ARENA_HALF if active_sector == 0 else active_sector * SECTOR_SIZE
    sx = hero_pos[0] + 200
    foes.append({
        'pos': [sx, 10, 0], 'scale': 1.5, 'kind': 5,
        'state': 'chasing', 'charge_dir': 0, 'hp': overlord_vitality, 'fire_tick': 0
    })
    print("OVERLORD DEPLOYED!")


def _safe_spawn_x(px, lo, hi, spread=500):
    """Generate a spawn X within zone bounds, offset from player."""
    raw = px + random.uniform(-spread, spread)
    return max(lo + 10, min(raw, hi - 10))


def deploy_foe(slot=None, spread=500):
    global foes, foe_index, sector_foes_deployed, SECTOR_FOE_QUOTA
    sec_lo = -ARENA_HALF if active_sector == 0 else active_sector * SECTOR_SIZE
    sec_hi = (active_sector + 1) * SECTOR_SIZE

    entry = {
        'pos': [0, 10, 0], 'scale': 1.3,
        'kind': random.choice([1, 2, 3, 4]),
        'state': 'chasing', 'charge_dir': 0,
        'fire_tick': random.randint(50, 150)
    }

    if slot is not None:
        if slot < len(foes):
            sx = _safe_spawn_x(hero_pos[0], sec_lo, sec_hi, spread)
            sz = max(-ARENA_HALF + 10, min(hero_pos[1] + random.uniform(-spread, spread), ARENA_HALF - 10))
            entry['pos'] = [sx, 10, sz]
            foes[slot] = entry
        return

    if sector_foes_deployed < SECTOR_FOE_QUOTA:
        foe_index += 1; sector_foes_deployed += 1
        sx = _safe_spawn_x(hero_pos[0], sec_lo, sec_hi, spread)
        sz = max(-ARENA_HALF + 10, min(hero_pos[1] + random.uniform(-spread, spread), ARENA_HALF - 10))
        entry['pos'] = [sx, 10, sz]
        foes.append(entry)


def new_game(lvl=1, carry_score=0):
    global hero_pos, hero_yaw, hero_face, hero_hp, score, death_flag, topple_angle
    global auto_pilot, top_cam_toggled, jab_on, jab_tick, dive_on, dive_tick, hopping, hop_tick, hero_lift
    global active_sector, sector_foes_deployed, sector_foes_downed, sector_done, stage_num
    global overlord_deployed, SECTOR_FOE_QUOTA, overlord_vitality, razor_discs, warhead_pool, box_pool, loot_pool
    global paused, menu_visible, flora_pool, wreck_pool, ember_pool, flake_pool, cycle_tick, daytime, cheat_target_lock

    flora_pool.clear(); wreck_pool.clear(); ember_pool.clear(); flake_pool.clear()
    cycle_tick = 0; daytime = True

    razor_discs.clear(); warhead_pool.clear(); box_pool.clear(); loot_pool.clear()

    hero_yaw = 90; hero_face = 90
    score = carry_score
    hero_pos = [0, 0]
    foes.clear()
    death_flag    = False
    auto_pilot    = False; top_cam_toggled = False
    hero_hp       = 100; topple_angle = 0
    jab_on        = False; jab_tick  = 0
    dive_on       = False; dive_tick = 0
    hopping       = False; hop_tick  = 0; hero_lift = 0

    active_sector        = 0
    stage_num            = lvl
    overlord_deployed    = False
    SECTOR_FOE_QUOTA     = 5
    overlord_vitality    = stage_num * 100 + 100
    sector_foes_deployed = 0
    sector_foes_downed   = 0
    sector_done          = False
    paused               = False
    menu_visible         = False
    cheat_target_lock    = None

    deploy_boxes_for_sector()
    build_scenery()

    while len(foes) < 3 and sector_foes_deployed < SECTOR_FOE_QUOTA:
        deploy_foe()


# ENEMY

def tick_foes():
    global overlord_alive, overlord_firing, overlord_fire_tick, overlord_shots, razor_discs

    MELEE_DIST  = 50
    ALIGN_SLACK = 15
    CHARGE_VEL  = 6.0
    CHARGE_DIST = 250

    sec_lo = -ARENA_HALF if active_sector == 0 else active_sector * SECTOR_SIZE
    sec_hi = (active_sector + 1) * SECTOR_SIZE

    for foe in foes:
        if 'state'    not in foe: foe['state']    = 'chasing'
        if 'charge_dir' not in foe: foe['charge_dir'] = 0
        if 'fire_tick'  not in foe: foe['fire_tick']  = random.randint(50, 150)

        dx = hero_pos[0] - foe['pos'][0]
        dz = hero_pos[1] - foe['pos'][2]
        dist = math.hypot(dx, dz)

        # Overlord behaviour
        if foe.get('kind') == 5:
            if overlord_fire_tick > 0:
                overlord_fire_tick -= 1
                overlord_firing = overlord_fire_tick > (OVERLORD_FIRE_WAIT - 20)
                if overlord_fire_tick == OVERLORD_FIRE_WAIT - 10:
                    ang = math.atan2(dx, dz)
                    overlord_shots.append({'pos': [foe['pos'][0], foe['pos'][2]], 'dir': [math.sin(ang), math.cos(ang)]})
                continue
            if dist > 150:
                step = FOE_STEP * 1.5
                foe['pos'][0] += step if dx > 0 else -step
                foe['pos'][2] += step if dz > 0 else -step
            foe['pos'][0] = max(sec_lo, min(foe['pos'][0], sec_hi))
            if random.random() < 0.01:
                overlord_fire_tick = OVERLORD_FIRE_WAIT
            continue

        # Scout fires razor discs
        if foe.get('kind') == 2:
            foe['fire_tick'] -= 1
            if foe['fire_tick'] <= 0 and dist < 400:
                mag = math.hypot(dx, dz)
                if mag != 0:
                    razor_discs.append({
                        'pos': [foe['pos'][0], foe['pos'][2]],
                        'vel': [(dx / mag) * RAZOR_DISC_VEL, (dz / mag) * RAZOR_DISC_VEL],
                        'angle': 0
                    })
                foe['fire_tick'] = random.randint(120, 200)

        # Brute charge logic
        if foe.get('kind') == 4:
            if foe['state'] == 'charging':
                foe['pos'][0] += foe['charge_dir'] * CHARGE_VEL
                if foe['pos'][0] < sec_lo or foe['pos'][0] > sec_hi:
                    foe['pos'][0] = max(sec_lo, min(foe['pos'][0], sec_hi))
                    foe['state'] = 'chasing'
                continue
            if abs(dz) <= ALIGN_SLACK and abs(dx) < CHARGE_DIST:
                foe['state']      = 'charging'
                foe['charge_dir'] = 1 if dx > 0 else -1
                continue

        # General approach / attack state
        if abs(dz) <= ALIGN_SLACK and abs(dx) <= MELEE_DIST:
            foe['state'] = 'attacking'
        elif abs(dz) > ALIGN_SLACK:
            foe['pos'][2] += FOE_STEP if dz > 0 else -FOE_STEP
            foe['pos'][2]  = max(-ARENA_HALF + 10, min(foe['pos'][2], ARENA_HALF - 10))
        elif abs(dx) > MELEE_DIST:
            foe['pos'][0] += FOE_STEP if dx > 0 else -FOE_STEP
            foe['pos'][0]  = max(sec_lo, min(foe['pos'][0], sec_hi))


# COLLISION HANDLERS

def check_whirl_hits():
    global foes, score, whirl_counted, hero_hp, sector_foes_downed, overlord_vitality
    if not whirl_on: return
    hit_slots = []
    for idx, foe in enumerate(foes):
        dx = foe['pos'][0] - hero_pos[0]
        dz = foe['pos'][2] - hero_pos[1]
        if dx * dx + dz * dz <= WHIRL_SWEEP * WHIRL_SWEEP:
            hit_slots.append(idx)
            ang = math.atan2(dx, dz)
            foe['pos'][0] += math.sin(ang) * WHIRL_PUSH
            foe['pos'][2] += math.cos(ang) * WHIRL_PUSH

    if hit_slots and not whirl_counted:
        whirl_counted = True
        to_erase = []
        for idx in hit_slots:
            if foes[idx].get('kind') == 5:
                foes[idx]['hp'] -= 25
                overlord_vitality = foes[idx]['hp']
                if foes[idx]['hp'] <= 0:
                    to_erase.append(idx)
            else:
                to_erase.append(idx)
        for idx in sorted(to_erase, reverse=True):
            del foes[idx]; sector_foes_downed += 1
        hero_hp -= 25
        score   += len(hit_slots)


def check_dive_hits():
    global score, foes, dive_scored, sector_foes_downed, overlord_vitality
    if not dive_on or dive_scored: return
    rad  = math.radians(hero_face)
    fwd  = 25 + (dive_tick / DIVE_FRAMES) * 35
    hbx  = hero_pos[0] + fwd * math.sin(rad)
    hbz  = hero_pos[1] + fwd * math.cos(rad)
    hby  = hero_lift + 25
    got_hit  = False
    kill_idx = []
    for ji, foe in enumerate(foes):
        fx, fy, fz = foe['pos'][0], foe['pos'][1], foe['pos'][2]
        er = 10 * foe['scale']
        x_ok = hbx + 15 > fx - er and hbx - 15 < fx + er
        z_ok = hbz + 15 > fz - er and hbz - 15 < fz + er
        y_ok = hby + 20 > fy - er and hby - 20 < fy + er
        if x_ok and z_ok and y_ok:
            got_hit = True; score += 1
            if foe.get('kind') == 5:
                foe['hp'] -= 15; overlord_vitality = foe['hp']
                if foe['hp'] <= 0: kill_idx.append(ji)
            else:
                kill_idx.append(ji)
    if got_hit: dive_scored = True
    for ji in sorted(kill_idx, reverse=True):
        del foes[ji]; sector_foes_downed += 1


def check_jab_hits():
    global score, foes, sector_foes_downed, overlord_vitality
    if not jab_on or dive_on: return
    rad  = math.radians(hero_face)
    tx   = hero_pos[0] + JAB_REACH * math.sin(rad)
    tz   = hero_pos[1] + JAB_REACH * math.cos(rad)
    kill_idx = []
    for ji, foe in enumerate(foes):
        to_tip  = math.hypot(tx - foe['pos'][0], tz - foe['pos'][2])
        to_hero = math.hypot(foe['pos'][0] - hero_pos[0], foe['pos'][2] - hero_pos[1])
        if to_tip < 15 * foe['scale'] and to_hero < JAB_REACH:
            score += 1
            if foe.get('kind') == 5:
                foe['hp'] -= 10; overlord_vitality = foe['hp']
                if foe['hp'] <= 0: kill_idx.append(ji)
            else:
                kill_idx.append(ji)
    for ji in sorted(kill_idx, reverse=True):
        del foes[ji]; sector_foes_downed += 1


def check_contact_damage():
    global hero_hp, death_flag, foes
    if dive_on or whirl_on: return
    hit_slots = []
    for ji, foe in enumerate(foes):
        d = math.hypot(hero_pos[0] - foe['pos'][0], hero_pos[1] - foe['pos'][2])
        if d < 20:
            penalty = 20 if foe.get('kind') == 4 else 10
            hero_hp -= penalty
            hit_slots.append(ji)
            if hero_hp <= 0: death_flag = True; break
    if not death_flag:
        for ji in set(hit_slots):
            foe = foes[ji]
            if foe.get('kind') == 5:
                dx = foe['pos'][0] - hero_pos[0]
                dz = foe['pos'][2] - hero_pos[1]
                mag = math.hypot(dx, dz)
                if mag != 0:
                    foe['pos'][0] += (dx / mag) * 50
                    foe['pos'][2] += (dz / mag) * 50
            else:
                deploy_foe(ji)
                foes[ji]['kind'] = foe.get('kind', 1)


def auto_pilot_actions():
    global hero_yaw, hero_face, jab_on, jab_tick
    if not auto_pilot or death_flag: return
    hero_yaw  = (hero_yaw + 2) % 360
    hero_face = hero_yaw
    for foe in foes:
        dx = foe['pos'][0] - hero_pos[0]
        dz = foe['pos'][2] - hero_pos[1]
        if math.hypot(dx, dz) < JAB_REACH * 1.5 and not jab_on:
            if random.random() < 0.15:
                jab_on = True; jab_tick = 0


# PHYSICS TICKERS

def tick_hop():
    global hopping, hop_tick, hero_lift
    if hopping and not dive_on:
        hop_tick += 1
        t = hop_tick / HOP_FRAMES
        hero_lift = HOP_APEX * (4 * t * (1 - t))
        if hop_tick >= HOP_FRAMES:
            hop_tick = 0; hero_lift = 0; hopping = False


def tick_dive():
    global dive_on, dive_tick, hero_lift, hopping, hero_pos, hop_tick, active_sector, sector_done, SECTOR_SIZE
    if not dive_on: return
    dive_tick += 1
    nx = hero_pos[0] + dive_hvel * dive_dx
    nz = hero_pos[1] + dive_hvel * dive_dz
    sec_cap = (active_sector + 1) * SECTOR_SIZE
    if not sector_done and nx > sec_cap - 50:
        nx = sec_cap - 50
    if -ARENA_HALF < nx < FLOOR_LENGTH and -ARENA_HALF < nz < ARENA_HALF:
        if not scenery_blocks(nx, nz):
            hero_pos[0], hero_pos[1] = nx, nz
    hero_lift = LIFT_INIT * hop_tick - 0.5 * PULL_DOWN * hop_tick * hop_tick
    if hero_lift < 0: hero_lift = 0
    hop_tick += 1
    if dive_tick >= DIVE_FRAMES or hero_lift <= 0:
        dive_on  = False; dive_tick = 0
        hopping  = False; hop_tick  = 0; hero_lift = 0


def tick_jab():
    global jab_on, jab_tick
    if jab_on:
        jab_tick += 1
        if jab_tick >= JAB_FRAMES:
            jab_on = False; jab_tick = 0


def tick_whirl():
    global whirl_on, whirl_tick, hopping, hero_lift
    if not whirl_on: return
    whirl_tick += 1
    hero_lift = 35
    if whirl_tick >= WHIRL_FRAMES:
        whirl_on = False; whirl_tick = 0; hopping = False; hero_lift = 0


# IDLE CALLBACK

def on_idle():
    global death_flag, topple_angle
    global sector_foes_downed, sector_foes_deployed, SECTOR_FOE_QUOTA
    global sector_done, active_sector, stage_num, SECTOR_SIZE
    global overlord_deployed, foes, paused

    if paused:
        glutPostRedisplay()
        return

    if death_flag:
        if topple_angle < 90:
            topple_angle += 1
        glutPostRedisplay()
        return

    # =========================
    # GAME SYSTEM TICKS
    # =========================
    tick_day_cycle()
    tick_snowfall()
    tick_embers()

    tick_warheads()
    tick_collectibles()
    tick_jab()
    tick_dive()
    tick_foes()
    check_dive_hits()
    check_jab_hits()
    check_contact_damage()
    auto_pilot_actions()
    tick_hop()
    tick_whirl()
    tick_overlord_shots()
    tick_razor_discs()
    check_whirl_hits()

    # =========================
    # SPAWN CONTROL
    # =========================
    if not sector_done and sector_foes_deployed < SECTOR_FOE_QUOTA and len(foes) < 3:
        deploy_foe()

    # =========================
    # ZONE CLEAR CONDITION
    # =========================
    all_enemies_dead = (len(foes) == 0)

    if sector_foes_downed >= SECTOR_FOE_QUOTA:
        sector_done = True

        # boss stage logic
        if active_sector == 4:
            if not overlord_deployed:
                deploy_overlord()
                SECTOR_FOE_QUOTA     = 1
                sector_foes_deployed = 1
                sector_foes_downed   = 0
                overlord_deployed    = True
                sector_done          = False
                glutPostRedisplay()
                return
            else:
                print(f"Stage {stage_num} Complete!")
                new_game(lvl=stage_num + 1, carry_score=score)
                glutPostRedisplay()
                return

    # =========================
    # HARD WALL (NO EARLY ZONE ENTRY)
    # =========================
    advance_wall = (active_sector + 1) * SECTOR_SIZE

    if hero_pos[0] > advance_wall + 50:

        # BLOCK ENTRY if enemies still exist
        if not all_enemies_dead or sector_foes_downed < SECTOR_FOE_QUOTA:
            hero_pos[0] = advance_wall + 50  # push player back
        else:
            # allowed to advance
            active_sector += 1
            sector_foes_deployed = 0
            sector_foes_downed = 0
            sector_done = False

            deploy_boxes_for_sector()
            print(f"Entering Sector {active_sector + 1}")

    # =========================
    # GAME OVER CHECK
    # =========================
    if hero_hp <= 0:
        death_flag = True

    glutPostRedisplay()


# DISPLAY CALLBACK

def on_draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    setup_view()
    render_sky_shell()
    render_backdrop_hills()
    render_floor()
    render_border_walls()
    render_all_scenery()
    render_embers()
    render_snowfall()

    if not fpv_mode:
        render_hero()
    render_all_foes()
    render_jab_indicator()
    render_dive_indicator()
    render_projectiles()
    render_warheads()
    render_collectibles()

    if not death_flag:
        hud_text(10, 770, f"Player HP: {max(0, hero_hp)}")
        hud_text(10, 740, f"Boss HP: {overlord_vitality if overlord_deployed else 'N/A'}")
        hud_text(10, 710, f"Level: {stage_num} | Score: {score} | Zone: {active_sector + 1}")
        hud_text(10, 680, f"Enemies Left: {max(0, SECTOR_FOE_QUOTA - sector_foes_downed)}")
        render_advance_prompt()
    else:
        hud_text(10, 770, f"Game is Over. Your Score is {score}.")
        hud_text(10, 740, 'Press "R" to Restart')

    render_ui_panel()
    glutSwapBuffers()

# INPUT CALLBACKS

def on_key(k, mx, my):
    global hero_yaw, hero_face, auto_pilot, top_cam_toggled, fpv_mode
    global hopping, hop_tick, cheat_target_lock
    global active_sector, sector_done, sector_foes_downed, foes, score, auto_mode
    global whirl_on, whirl_tick, whirl_counted
    global hero_pos

    if paused:
        return

    if death_flag:
        if k.lower() == b'r':
            new_game()
        return

    key = k.lower()

    x, z = hero_pos[0], hero_pos[1]
    nx, nz = x, z

    # =========================
    # MOVEMENT 
    # =========================
    if not dive_on:

        # Manual mode movement uses the player's current visible facing,
        # so after pressing S the body stays backward-facing and A/D still
        # behave as left/right relative to that backward-facing body.
        move_angle = hero_face if not auto_mode else hero_yaw

        if key == b'w' and not auto_mode:
            hero_face = hero_yaw
            move_angle = hero_face
        elif key == b's' and not auto_mode:
            hero_face = wrap_angle(hero_yaw + 180)
            move_angle = hero_face

        rad = math.radians(move_angle)

        forward_x = math.sin(rad)
        forward_z = math.cos(rad)
        right_x = -math.cos(rad)
        right_z = math.sin(rad)

        # W = forward (and restore normal forward-facing in manual mode)
        if key == b'w':
            nx += forward_x * HERO_STEP
            nz += forward_z * HERO_STEP

        # S = backward-facing manual movement
        if key == b's':
            nx += forward_x * HERO_STEP
            nz += forward_z * HERO_STEP

        # A = left relative to current facing
        if key == b'a':
            nx -= right_x * HERO_STEP
            nz -= right_z * HERO_STEP

        # D = right relative to current facing
        if key == b'd':
            nx += right_x * HERO_STEP
            nz += right_z * HERO_STEP

        # apply movement safely
        if -ARENA_HALF < nx < FLOOR_LENGTH and -ARENA_HALF < nz < ARENA_HALF:
            if not scenery_blocks(nx, nz):
                hero_pos[0], hero_pos[1] = nx, nz

    # =========================
    # CHEAT TOGGLE
    # =========================
    if key == b'c':
        auto_mode = not auto_mode
        cheat_target_lock = None

        if not auto_mode:
            top_cam_toggled = False
            hero_face = DEFAULT_STRAIGHT_FACE
            hero_yaw = DEFAULT_STRAIGHT_FACE

        print("Cheat Active: Hand Bombs Online!" if auto_mode else "Cheat Deactivated")

    # =========================
    # CAMERA TOGGLE (CHEAT ONLY)
    # =========================
    if key == b'v':
        if auto_mode:
            top_cam_toggled = not top_cam_toggled

    # =========================
    # WHIRL ATTACK
    # =========================
    if key == b'e' and hopping and not whirl_on:
        whirl_on = True
        whirl_tick = 0
        whirl_counted = False

    # =========================
    # JUMP
    # =========================
    if key == b' ' and not hopping and not dive_on:
        hopping = True
        hop_tick = 0
#Mouse Listener

def on_mouse(btn, state, mx, my):
    global jab_on, jab_tick, dive_on, dive_tick, dive_hvel, dive_dx, dive_dz
    global dive_y_tick, hopping, whirl_on, whirl_tick, whirl_counted
    global paused, menu_visible, death_flag, hero_hp, active_sector, fpv_mode

    def inside(px, py, left, right, bottom, top):
        return left <= px <= right and bottom <= py <= top

    if state != GLUT_DOWN:
        return

    adj_y = 800 - my

    if btn == GLUT_LEFT_BUTTON:
        # Top-right utility buttons
        if inside(mx, adj_y, 936, 984, 746, 794):
            paused = not paused
            if not paused:
                menu_visible = False
            return

        if inside(mx, adj_y, 936, 984, 696, 744):
            menu_visible = not menu_visible
            paused = menu_visible
            return

        if inside(mx, adj_y, 936, 984, 646, 694):
            try:
                glutLeaveMainLoop()
            except Exception:
                os._exit(0)
            return

        # Restart popup choices
        if menu_visible:
            if inside(mx, adj_y, 300, 490, 380, 430):
                new_game(lvl=stage_num, carry_score=score)
                paused = False
                menu_visible = False
            elif inside(mx, adj_y, 510, 700, 380, 430):
                new_game()
            return

    if paused or death_flag:
        return

    if btn == GLUT_LEFT_BUTTON:
        if hopping and not dive_on:
            dive_on = True
            dive_tick = 0
            dive_y_tick = 0
            rad = math.radians(hero_face)
            dive_dx = math.sin(rad)
            dive_dz = math.cos(rad)
            dive_hvel = 8.0
        elif not hopping and not jab_on:
            jab_on = True
            jab_tick = 0

    if btn == GLUT_RIGHT_BUTTON:
        fpv_mode = not fpv_mode

#Special Keys (Arrow keys for camera control)

def on_special(k, mx, my):
    global cam_elevation, cam_orbit
    if k == GLUT_KEY_LEFT:  cam_orbit    -= 2
    if k == GLUT_KEY_RIGHT: cam_orbit    += 2
    if k == GLUT_KEY_UP:    cam_elevation += 3
    if k == GLUT_KEY_DOWN:
        cam_elevation -= 3
        if cam_elevation < 50: cam_elevation = 50

# ENTRY POINT

def main():
    glutInit()
    new_game()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Punch Combat")
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glutDisplayFunc(on_draw)
    glutKeyboardFunc(on_key)
    glutSpecialFunc(on_special)
    glutMouseFunc(on_mouse)
    glutIdleFunc(on_idle)
    glutMainLoop()


if __name__ == "__main__":
    main()