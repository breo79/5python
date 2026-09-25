import math
from data import charsprites
from game.assets import svg_intrinsic_size
from game.blocks import block_sides, SOLID_CODES, SIDE_TOP, SIDE_BOTTOM, SIDE_LEFT, SIDE_RIGHT, conveyor_speeds

PLAYER_CHARID = "1"
PICKUP_REACH = 0.2
CARRY_SLOWDOWN = 0.5
THROW_SPEED_X = 0.18
BOOK_UNIT_PX = 30
CARRY_FRONT_OFFSET_PX = 20

EDGE_EPS = 0.001

class Body:
    pushable = False
    ignoring = None
    belt = 0.0
    gravity = 0.015
    terminal_velocity = 0.5

    def left(self):
        return self.x - self.width / 2.0

    def right(self):
        return self.x + self.width / 2.0

    def top(self):
        return self.y - self.height

    def overlaps_x(self, other):
        return self.left() < other.right() - EDGE_EPS and self.right() > other.left() + EDGE_EPS

    def overlaps(self, other):
        return self.overlaps_x(other) and self.top() < other.y - EDGE_EPS and self.y > other.top() + EDGE_EPS

    def side_code(self, grid, col, row, side):
        if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
            return "2"
        return block_sides.get(grid[row][col], "2222")[side]

    def hits_side(self, grid, col, row, side):
        code = self.side_code(grid, col, row, side)
        if code == "5":
            self.touched_deadly = True
        return code in SOLID_CODES

    def resolve_tiles_x(self, grid, direction):
        half_w = self.width / 2.0
        start_col = int(math.floor(self.left()))
        end_col = int(math.floor(self.right() - 0.0001))
        start_row = int(math.floor(self.top()))
        end_row = int(math.floor(self.y - 0.0001))
        blocked = False
        if direction > 0:
            for r in range(start_row, end_row + 1):
                if self.hits_side(grid, end_col, r, SIDE_LEFT):
                    self.x = end_col - half_w
                    blocked = True
                    break
        elif direction < 0:
            for r in range(start_row, end_row + 1):
                if self.hits_side(grid, start_col, r, SIDE_RIGHT):
                    self.x = (start_col + 1) + half_w
                    blocked = True
                    break

        cols_count = len(grid[0]) if grid else 32
        if self.left() < 0:
            self.x = half_w
            blocked = True
        elif self.right() > cols_count:
            self.x = cols_count - half_w
            blocked = True
        return blocked

    def ignores(self, other):
        return other is self or other is self.ignoring or other.ignoring is self

    def collide_bodies_y(self, bodies, prev_bottom):
        for other in bodies:
            if self.ignores(other) or not self.overlaps_x(other):
                continue
            other_top = other.top()
            if self.vy >= 0 and prev_bottom <= other_top + EDGE_EPS and self.y > other_top:
                self.y = other_top
                self.vy = 0.0
                self.on_ground = True

    def move(self, grid, bodies=()):
        self.touched_deadly = False
        self.vy += self.gravity
        if self.vy > self.terminal_velocity:
            self.vy = self.terminal_velocity

        self.x += self.vx
        if self.resolve_tiles_x(grid, self.vx):
            self.vx = 0.0

        if self.belt:
            self.x += self.belt
            self.resolve_tiles_x(grid, self.belt)
        self.belt = 0.0

        prev_bottom = self.y
        self.y += self.vy

        start_col = int(math.floor(self.left() + 0.01))
        end_col = int(math.floor(self.right() - 0.01))
        start_row = int(math.floor(self.top()))
        end_row = int(math.floor(self.y))

        self.on_ground = False
        if self.vy >= 0:
            for c in range(start_col, end_col + 1):
                lands_on_platform = prev_bottom <= end_row + 0.001 and self.side_code(grid, c, end_row, SIDE_TOP) == "3"
                if lands_on_platform or self.hits_side(grid, c, end_row, SIDE_TOP):
                    self.y = float(end_row)
                    self.vy = 0.0
                    self.on_ground = True
                    for belt_col in range(start_col, end_col + 1):
                        if 0 <= end_row < len(grid) and 0 <= belt_col < len(grid[0]):
                            self.belt = conveyor_speeds.get(grid[end_row][belt_col], 0.0) or self.belt
                    break
        elif self.vy < 0:
            for c in range(start_col, end_col + 1):
                if self.hits_side(grid, c, start_row, SIDE_BOTTOM):
                    self.y = float(start_row + 1) + self.height
                    self.vy = 0.0
                    break

        self.collide_bodies_y(bodies, prev_bottom)

class CharacterEntity(Body):
    def __init__(self, charid, x, y, props, jump_props):
        self.charid = str(charid)
        self.props = props or {}
        self.name = self.props.get("name", "Unknown")

        self.sprite_path = charsprites.get_limbless_sprite(self.charid)
        self.body_svg_w, self.body_svg_h = svg_intrinsic_size(self.sprite_path) if self.sprite_path else (1.0, 1.0)
        self.parts = charsprites.get_character_parts(self.charid)
        self.hips = self.parts.get("hips", [
            (self.body_svg_w * 0.4, self.body_svg_h),
            (self.body_svg_w * 0.6, self.body_svg_h)
        ])

        self.body_height_px = float(self.props.get("height", 45.4))
        self.part_scale = self.body_height_px / self.body_svg_h
        self.stand_height_svg = max(hip[1] for hip in self.hips) + charsprites.LEG_LENGTH

        self.width_px = float(self.props.get("width", 28)) * 2.0
        self.height_px = self.stand_height_svg * self.part_scale - float(self.props.get("HitboxTrim", 0))
        self.width = self.width_px / 30.0
        self.height = self.height_px / 30.0

        self.weight = float(self.props.get("weight", 0.5))
        self.friction = float(self.props.get("friction", 0.8))

        jump_px = 60.0
        for entry in jump_props:
            if str(entry.get("charid")) == self.charid:
                jump_px = float(entry.get("jumpheight", 60.0))
                break
        self.jump_height_tiles = jump_px / 30.0

        self.jump_speed = math.sqrt(2.0 * self.gravity * self.jump_height_tiles)
        self.walk_accel = 0.04
        self.max_walk_speed = 0.14
        self.carry_height_px = float(self.props.get("CarriedObjectHeight", self.height_px / 2.0))
        self.carrying = None

        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.walk_phase = 0.0
        self.died = False

    def reset(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.walk_phase = 0.0

    def pose(self):
        if not self.on_ground:
            return "air"
        if self.vx == 0.0:
            return "stand"
        return "walk"

    def walk_wave(self):
        if self.pose() != "walk":
            return 0.0
        return math.sin(self.walk_phase / len(charsprites.leg_sprites["walk"]) * 2.0 * math.pi)

    def leg_frames(self):
        walk = charsprites.leg_sprites["walk"]
        if not self.on_ground:
            air = charsprites.leg_sprites["air"]
            return air, air
        if self.vx == 0.0:
            stand = charsprites.leg_sprites["stand"]
            return stand, stand
        frame = int(self.walk_phase) % len(walk)
        return walk[frame], walk[(frame + len(walk) // 2) % len(walk)]

    def carry_factor(self):
        if self.carrying is None:
            return 1.0
        return max(0.2, 1.0 - self.carrying.weight * CARRY_SLOWDOWN)

    def reachable_object(self, objects):
        best = None
        best_gap = PICKUP_REACH
        for obj in objects:
            if obj.gone or obj.carrier is not None or not obj.pickupable:
                continue
            if obj.y <= self.top() or obj.top() >= self.y:
                continue
            gap = max(obj.left() - self.right(), self.left() - obj.right(), 0.0)
            if gap <= best_gap:
                best = obj
                best_gap = gap
        return best

    def pick_up(self, objects):
        obj = self.reachable_object(objects)
        if obj is not None:
            self.carrying = obj
            obj.carrier = self
            obj.follow(self)

    def release(self):
        obj = self.carrying
        if obj is not None:
            obj.carrier = None
            obj.ignoring = self
            self.carrying = None
        return obj

    def throw(self):
        obj = self.release()
        if obj is not None:
            direction = 1 if self.facing_right else -1
            release_height = self.carry_height_px / 30.0
            airtime = obj.throw_distance / THROW_SPEED_X
            obj.vx = direction * THROW_SPEED_X
            obj.vy = -(obj.gravity * airtime / 2.0 - release_height / airtime)
            obj.thrown = True

    def set_down(self):
        obj = self.release()
        if obj is not None:
            obj.vx = 0.0
            obj.vy = 0.0

    def update(self, keys, grid, bodies=()):
        move_dir = 0
        if keys.get("left"):
            move_dir -= 1
        if keys.get("right"):
            move_dir += 1

        carry_factor = self.carry_factor()
        max_speed = self.max_walk_speed * carry_factor
        if move_dir != 0:
            self.vx += move_dir * self.walk_accel
            if self.vx > max_speed:
                self.vx = max_speed
            elif self.vx < -max_speed:
                self.vx = -max_speed
            self.facing_right = move_dir > 0
        else:
            self.vx *= self.friction
            if abs(self.vx) < 0.005:
                self.vx = 0.0

        if keys.get("jump") and self.on_ground:
            self.vy = -self.jump_speed * math.sqrt(carry_factor)
            self.on_ground = False

        self.move(grid, bodies)

        if self.on_ground:
            if self.vx != 0.0:
                self.walk_phase += abs(self.vx) / self.max_walk_speed
            else:
                self.walk_phase = 0.0

        if self.touched_deadly or self.y > len(grid) + 3:
            self.reset()
            self.died = True

class GameObject(Body):
    pushable = True
    carrier = None

    def __init__(self, entityid, x, y, props):
        self.entityid = str(entityid)
        self.props = props
        self.name = props.get("objectname", "Object")
        self.texture = props.get("objecttexture")
        self.width_px = float(props.get("width", 30))
        self.height_px = float(props.get("height", 30))
        self.width = self.width_px / 30.0
        self.height = self.height_px / 30.0
        self.weight = float(props.get("weight", 0.5))
        self.friction = float(props.get("friction", 0.7))
        self.pickupable = str(props.get("pickupable", "false")).lower() == "true"
        self.throw_distance = float(props.get("throwdistance", 2.0)) * BOOK_UNIT_PX / 30.0
        self.flipped = False
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.reset()

    def reset(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.gone = False
        self.carrier = None
        self.ignoring = None
        self.thrown = False

    def follow(self, carrier):
        facing = 1 if carrier.facing_right else -1
        self.flipped = not carrier.facing_right
        self.x = carrier.x + facing * CARRY_FRONT_OFFSET_PX / 30.0
        self.y = carrier.y - carrier.carry_height_px / 30.0
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    def update(self, grid, bodies=()):
        if self.gone or self.carrier is not None:
            return
        if self.on_ground:
            self.vx *= self.friction
            if abs(self.vx) < 0.005:
                self.vx = 0.0
        self.move(grid, bodies)
        if self.ignoring is not None and not self.overlaps_x(self.ignoring):
            self.ignoring = None
        if self.thrown and self.on_ground:
            self.vx = 0.0
            self.thrown = False
        if self.y > len(grid) + 3:
            self.gone = True
