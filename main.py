import charsprites, charproperties, blockproperties, backgroundproperties
import pygame, os, sys, time, math, re, random
import levelparser as ps
import levelselect
import dialogue
import savegame
from pathlib import Path
import resvg_py
from io import BytesIO

time.sleep(0.15)
parsed_levels = ps.parse_level()

main_menubuttons = [
    "OPTIONS", "WATCH BFDIA 5a", "NEW GAME", "LEVEL CREATOR", "EXPLORE", "MODS"
]

settings_buttons = [
    "BACK"
]

pygame.init()
pygame.display.set_caption("5b")
screen_width, screen_height = 960, 540
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

font_large = pygame.font.Font("assets/ui/fonts/arial.ttf", 24)
font_small = pygame.font.Font("assets/ui/fonts/arial.ttf", 16)
font_button = pygame.font.Font("assets/ui/fonts/arial.ttf", 30)
font_level_title = pygame.font.Font("assets/ui/fonts/arial.ttf", 30)
font_level_title.set_bold(True)

multiline_text = "By Cary Huang\nMusic by Michael Huang\nPython Port by asdguiv"
text_lines = multiline_text.split('\n')

rendered_lines = [
    font_large.render(text_lines[0], True, (255, 255, 255)),
    font_small.render(text_lines[1], True, (255, 255, 255)),
    font_small.render(text_lines[2], True, (255, 255, 255))
]

def load_svg_surface(path, width, height):
    full_path = Path(__file__).resolve().parent / path.lstrip("/")
    if not full_path.exists():
        surface = pygame.Surface((width, height))
        surface.fill((150, 150, 150))
        return surface
    with open(full_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    png_data = resvg_py.svg_to_bytes(svg_string=svg_content, width=width, height=height)
    surface = pygame.image.load(BytesIO(png_data)).convert_alpha()
    return surface

svg_size_cache = {}

def svg_intrinsic_size(path):
    if path in svg_size_cache:
        return svg_size_cache[path]
    size = (1.0, 1.0)
    full_path = Path(__file__).resolve().parent / path.lstrip("/")
    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            header = f.read(1000)
        match = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', header)
        if match and float(match.group(2)) > 0:
            size = (float(match.group(1)), float(match.group(2)))
    svg_size_cache[path] = size
    return size

def load_bg_surface(path, width, height):
    full_path = Path(__file__).resolve().parent / path.lstrip("/")
    if not full_path.exists():
        surface = pygame.Surface((width, height))
        surface.fill((40, 40, 40))
        return surface
    surface = pygame.image.load(str(full_path)).convert()
    return pygame.transform.smoothscale(surface, (width, height))

def bg_path_from_header(header):
    try:
        bg_index = int(header.split(",")[3])
    except (ValueError, IndexError):
        return None
    return f"/assets/backgrounds/bg{bg_index:04d}.png"

svg_surface = load_svg_surface("assets/ui/poopers.svg", 942, 426)
svg_rect = svg_surface.get_rect()
svg_rect.bottomleft = (15, screen_height - 15)

game_state = "main_menu"
level_select_menu = levelselect.LevelSelectMenu((screen_width, screen_height), load_svg_surface)
dialogue_box = dialogue.DialogueBox((screen_width, screen_height), load_svg_surface)
active_hit_button = None
current_level_index = 0
current_loaded_level = -1
running = True

texture_cache = {}
invisible_refs = set()
animated_blocks = {}
for block in blockproperties.block_sprites:
    if not block.get("blocktexture"):
        invisible_refs.add(block["referential"])
        continue
    texture_cache[block["referential"]] = block["blocktexture"]
    if block.get("blockanimation"):
        frame_dir = Path(__file__).resolve().parent / block["blockanimation"].lstrip("/")
        frames = sorted(frame_dir.glob("*.svg")) if frame_dir.is_dir() else []
        if frames:
            animated_blocks[block["referential"]] = [
                block["blockanimation"].rstrip("/") + "/" + frame.name for frame in frames
            ]

svg_viewbox_cache = {}

def svg_viewbox(path):
    if path in svg_viewbox_cache:
        return svg_viewbox_cache[path]
    full_path = Path(__file__).resolve().parent / path.lstrip("/")
    with open(full_path, "r", encoding="utf-8") as f:
        header = f.read(1000)
    match = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)', header)
    box = tuple(float(v) for v in match.groups()) if match else (0.0, 0.0, 30.0, 30.0)
    svg_viewbox_cache[path] = box
    return box

animation_tick = 0

solid_refs = {
    block["referential"]
    for block in blockproperties.block_sprites
    if block.get("CollisionDataFourSided", "2222") == "1111"
}

def parse_block_size(block):
    if "BlockSizeXY" in block:
        w, h = block["BlockSizeXY"].split(",")
        return float(w), float(h)
    size = float(block.get("BlockSize", 1))
    return size, size

block_sizes = {block["referential"]: parse_block_size(block) for block in blockproperties.block_sprites}

wintoken_refs = {
    block["referential"]
    for block in blockproperties.block_sprites
    if block["blockid"] == "4"
}

def wintoken_look(ch, col, row):
    if ch is None:
        return 255, 0, 0
    dist = math.hypot(col + 0.5 - ch.x, row + 0.5 - (ch.y - ch.height / 2.0))
    closeness = min(max((WINTOKEN_FADE_FAR - dist) / (WINTOKEN_FADE_FAR - WINTOKEN_FADE_NEAR), 0.0), 1.0)
    alpha = int(WINTOKEN_MIN_ALPHA + (255 - WINTOKEN_MIN_ALPHA) * closeness)
    shake = max(0.0, 1.0 - dist / WINTOKEN_SHAKE_RANGE) * WINTOKEN_SHAKE_PX
    return alpha, random.uniform(-shake, shake), random.uniform(-shake, shake)

dialogue_refs = {
    block["referential"]
    for block in blockproperties.block_sprites
    if block["blockid"] == "6"
}

door_refs = {
    block["referential"]
    for block in blockproperties.block_sprites
    if block["blockid"] == "7"
}

def block_rect(char, col, row):
    w, h = block_sizes.get(char, (1.0, 1.0))
    return (col + 1 - w, row + 1 - h, w, h)

def touching_tiles(ch, grid, refs):
    left = ch.x - ch.width / 2.0
    right = ch.x + ch.width / 2.0
    top = ch.y - ch.height
    bottom = ch.y
    hits = []
    for r_idx, row in enumerate(grid):
        for c_idx, char in enumerate(row):
            if char in refs:
                dx, dy, dw, dh = block_rect(char, c_idx, r_idx)
                if left < dx + dw and right > dx and top < dy + dh and bottom > dy:
                    hits.append((c_idx, r_idx))
    return hits

def touches_door(ch, grid):
    return bool(touching_tiles(ch, grid, door_refs))

def level_has_wintoken(grid):
    return any(char in wintoken_refs for row in grid for char in row)

loaded_tile_surfaces = {}
loaded_bg_surfaces = {}
loaded_char_surfaces = {}

class CharacterEntity:
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

        self.gravity = 0.015
        self.jump_speed = math.sqrt(2.0 * self.gravity * self.jump_height_tiles)
        self.walk_accel = 0.04
        self.max_walk_speed = 0.14
        self.terminal_velocity = 0.5

        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.walk_phase = 0.0

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

    def is_tile_solid(self, grid, col, row, solid_tokens):
        if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
            return False
        return grid[row][col] in solid_tokens

    def update(self, keys, grid, solid_tokens):
        move_dir = 0
        if keys.get("left"):
            move_dir -= 1
        if keys.get("right"):
            move_dir += 1

        if move_dir != 0:
            self.vx += move_dir * self.walk_accel
            if self.vx > self.max_walk_speed:
                self.vx = self.max_walk_speed
            elif self.vx < -self.max_walk_speed:
                self.vx = -self.max_walk_speed
            self.facing_right = move_dir > 0
        else:
            self.vx *= self.friction
            if abs(self.vx) < 0.005:
                self.vx = 0.0

        if keys.get("jump") and self.on_ground:
            self.vy = -self.jump_speed
            self.on_ground = False

        self.vy += self.gravity
        if self.vy > self.terminal_velocity:
            self.vy = self.terminal_velocity

        half_w = self.width / 2.0

        self.x += self.vx
        left = self.x - half_w
        right = self.x + half_w
        top = self.y - self.height
        bottom = self.y

        start_col = int(math.floor(left))
        end_col = int(math.floor(right - 0.0001))
        start_row = int(math.floor(top))
        end_row = int(math.floor(bottom - 0.0001))

        if self.vx > 0:
            for r in range(start_row, end_row + 1):
                if self.is_tile_solid(grid, end_col, r, solid_tokens):
                    self.x = end_col - half_w
                    self.vx = 0.0
                    break
        elif self.vx < 0:
            for r in range(start_row, end_row + 1):
                if self.is_tile_solid(grid, start_col, r, solid_tokens):
                    self.x = (start_col + 1) + half_w
                    self.vx = 0.0
                    break

        cols_count = len(grid[0]) if grid else 32
        if self.x - half_w < 0:
            self.x = half_w
            self.vx = 0.0
        elif self.x + half_w > cols_count:
            self.x = cols_count - half_w
            self.vx = 0.0

        self.y += self.vy
        left = self.x - half_w
        right = self.x + half_w
        top = self.y - self.height
        bottom = self.y

        start_col = int(math.floor(left + 0.01))
        end_col = int(math.floor(right - 0.01))
        start_row = int(math.floor(top))
        end_row = int(math.floor(bottom))

        self.on_ground = False
        if self.vy >= 0:
            for c in range(start_col, end_col + 1):
                if self.is_tile_solid(grid, c, end_row, solid_tokens):
                    self.y = float(end_row)
                    self.vy = 0.0
                    self.on_ground = True
                    break
        elif self.vy < 0:
            for c in range(start_col, end_col + 1):
                if self.is_tile_solid(grid, c, start_row, solid_tokens):
                    self.y = float(start_row + 1) + self.height
                    self.vy = 0.0
                    break

        if self.on_ground:
            if self.vx != 0.0:
                self.walk_phase += abs(self.vx) / self.max_walk_speed
            else:
                self.walk_phase = 0.0

        if self.y > len(grid) + 3:
            self.reset()

def get_part_surface(path, w, h):
    key = (path, w, h)
    if key not in loaded_char_surfaces:
        loaded_char_surfaces[key] = load_svg_surface(path, w, h)
    return loaded_char_surfaces[key]

def blit_part(canvas, sprite, pos, scale, flip_x=False, angle=0.0, flip_y=False):
    w = max(1, round(sprite["size"][0] * scale))
    h = max(1, round(sprite["size"][1] * scale))
    surface = get_part_surface(sprite["path"], w, h)
    anchor_x = sprite["anchor"][0] * w / sprite["size"][0]
    anchor_y = sprite["anchor"][1] * h / sprite["size"][1]
    if flip_x:
        surface = pygame.transform.flip(surface, True, False)
        anchor_x = w - anchor_x
    if flip_y:
        surface = pygame.transform.flip(surface, False, True)
        anchor_y = h - anchor_y
    center_offset = pygame.math.Vector2(w / 2 - anchor_x, h / 2 - anchor_y)
    if angle:
        surface = pygame.transform.rotate(surface, angle)
        center_offset = center_offset.rotate(-angle)
    rect = surface.get_rect(center=(pos[0] + center_offset.x, pos[1] + center_offset.y))
    canvas.blit(surface, rect)

def draw_character(target, ch, foot_x, foot_y, char_scale):
    if not ch.sprite_path:
        return
    s = ch.part_scale * char_scale
    pad = 70 * s
    body_w = max(1, round(ch.body_svg_w * s))
    body_h = max(1, round(ch.body_svg_h * s))
    canvas_w = int(body_w + pad * 2)
    canvas_h = int(pad * 2 + ch.stand_height_svg * s)
    canvas = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)

    def at(point):
        return (pad + point[0] * s, pad + point[1] * s)

    arms = list(zip(sorted(ch.parts.get("arms", [])), ch.parts.get("arm_poses", {}).get(ch.pose(), [])))
    arm_scale = s * ch.parts.get("arm_scale", 1.0)
    wave = ch.walk_wave()

    def draw_arms(in_front):
        for arm, arm_pose in arms:
            if arm_pose.get("front", False) != in_front:
                continue
            blit_part(
                canvas,
                charsprites.arm_sprites[arm_pose["sprite"]],
                at(arm),
                arm_scale,
                flip_x=arm_pose.get("flip_x", False),
                flip_y=arm_pose.get("flip_y", False),
                angle=arm_pose.get("angle", 0) + arm_pose.get("swing", 0) * wave
            )

    draw_arms(False)

    front_leg, back_leg = ch.leg_frames()
    back_hip, front_hip = sorted(ch.hips)[0], sorted(ch.hips)[-1]
    blit_part(canvas, back_leg, at(back_hip), s)
    blit_part(canvas, front_leg, at(front_hip), s)

    canvas.blit(get_part_surface(ch.sprite_path, body_w, body_h), (pad, pad))

    eye_scale = s * ch.parts.get("eye_scale", 1.0)
    for eye in ch.parts.get("eyes", []):
        blit_part(canvas, charsprites.eye_sprite, at(eye), eye_scale)
    if "mouth" in ch.parts:
        blit_part(canvas, charsprites.mouth_sprite, at(ch.parts["mouth"]), s)

    draw_arms(True)

    foot_canvas_x = pad + ch.body_svg_w * s / 2
    foot_canvas_y = pad + ch.stand_height_svg * s
    if not ch.facing_right:
        canvas = pygame.transform.flip(canvas, True, False)
        foot_canvas_x = canvas_w - foot_canvas_x
    target.blit(canvas, (foot_x - foot_canvas_x, foot_y - foot_canvas_y))

PLAYER_CHARID = "1"
DOOR_DELAY_FRAMES = 60
FLASH_FRAMES = 21
flash_timer = 0
WINTOKEN_FADE_NEAR = 2.0
WINTOKEN_FADE_FAR = 10.0
WINTOKEN_MIN_ALPHA = 40
WINTOKEN_SHAKE_RANGE = 4.0
WINTOKEN_SHAKE_PX = 2.0
door_timer = None
dialogue_triggered = False
collected_tokens = set()
level_progress = {0: "reached"}
time_spent = 0.0
session_active = False
save_available = savegame.has_save()

def main_menu_buttons():
    if not save_available:
        return main_menubuttons
    buttons = list(main_menubuttons)
    buttons.insert(buttons.index("NEW GAME") + 1, "CONTINUE GAME")
    return buttons

def save_progress():
    if session_active:
        savegame.write_save(level_progress, time_spent)
VIEW_COLS = 32
VIEW_ROWS = 18

def camera_offset(focus, map_size, view_size):
    if map_size <= view_size:
        return (view_size - map_size) / 2
    return -min(max(focus - view_size / 2, 0.0), map_size - view_size)
level_characters = []
active_character = None

while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    button_width = 350
    button_height = 45
    button_margin_right = 15
    button_margin_bottom = 15
    button_spacing = 8

    if game_state == "main_menu":
        current_buttons = main_menu_buttons()
    elif game_state == "settings":
        current_buttons = settings_buttons
    else:
        current_buttons = []

    if current_buttons:
        total_stack_height = (len(current_buttons) * button_height) + ((len(current_buttons) - 1) * button_spacing)
        start_y = screen_height - button_margin_bottom - total_stack_height
    else:
        start_y = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_progress()
            running = False
        elif game_state == "level_select":
            action = level_select_menu.handle_event(event, len(parsed_levels), level_progress)
            if action == ("button", "BACK"):
                game_state = "main_menu"
            elif action and action[0] == "level":
                game_state = "playing"
                current_level_index = action[1]
                current_loaded_level = -1
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                active_hit_button = None
                if current_buttons:
                    current_y = start_y
                    for text in current_buttons:
                        rect = pygame.Rect(
                            screen_width - button_margin_right - button_width,
                            current_y,
                            button_width,
                            button_height
                        )
                        if rect.collidepoint(mouse_pos):
                            active_hit_button = text
                            break
                        current_y += button_height + button_spacing
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if active_hit_button and current_buttons:
                    current_y = start_y
                    for text in current_buttons:
                        rect = pygame.Rect(
                            screen_width - button_margin_right - button_width,
                            current_y,
                            button_width,
                            button_height
                        )
                        if rect.collidepoint(mouse_pos) and active_hit_button == text:
                            if game_state == "main_menu":
                                if text == "OPTIONS":
                                    game_state = "settings"
                                elif text == "NEW GAME":
                                    if parsed_levels:
                                        level_progress = {0: "reached"}
                                        time_spent = 0.0
                                        current_level_index = 0
                                        session_active = True
                                        save_progress()
                                        save_available = True
                                        game_state = "level_select"
                                elif text == "CONTINUE GAME":
                                    save_data = savegame.load_save()
                                    if save_data and parsed_levels:
                                        level_progress = save_data["progress"]
                                        time_spent = save_data["time_spent"]
                                        unbeaten = [i for i, state in level_progress.items() if state == "reached" and i < len(parsed_levels)]
                                        current_level_index = min(unbeaten) if unbeaten else 0
                                        session_active = True
                                        game_state = "level_select"
                            elif game_state == "settings":
                                if text == "BACK":
                                    game_state = "main_menu"
                        current_y += button_height + button_spacing
                active_hit_button = None
        elif event.type == pygame.KEYDOWN:
            if game_state == "playing":
                if event.key == pygame.K_ESCAPE:
                    save_progress()
                    game_state = "level_select"
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) and event.mod & pygame.KMOD_CTRL and parsed_levels:
                    step = 1 if event.key == pygame.K_RIGHT else -1
                    if step == 1 and level_progress.get(current_level_index) != "green":
                        level_progress[current_level_index] = "yellow"
                    current_level_index = (current_level_index + step) % len(parsed_levels)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    dialogue_box.advance()
                elif event.key == pygame.K_r:
                    collected_tokens = set()
                    door_timer = None
                    flash_timer = FLASH_FRAMES
                    for ch in level_characters:
                        ch.reset()
                elif event.key == pygame.K_TAB:
                    if len(level_characters) > 1:
                        idx = (level_characters.index(active_character) + 1) % len(level_characters)
                        active_character = level_characters[idx]

    screen.fill((102, 102, 102))

    if game_state == "main_menu" or game_state == "settings":
        screen.blit(svg_surface, svg_rect)

        margin_x = 15
        margin_y = 15
        line_spacing = 5

        current_y = margin_y
        for line_surface in rendered_lines:
            line_rect = line_surface.get_rect()
            line_rect.topright = (screen_width - margin_x, current_y)
            screen.blit(line_surface, line_rect)
            current_y += line_rect.height + line_spacing

        if game_state == "settings":
            settings_title = font_large.render("Settings", True, (255, 255, 255))
            screen.blit(settings_title, (margin_x, margin_y))

        current_y = start_y
        for text in current_buttons:
            rect = pygame.Rect(
                screen_width - button_margin_right - button_width,
                current_y,
                button_width,
                button_height
            )

            if active_hit_button == text and rect.collidepoint(mouse_pos):
                btn_color = (184, 184, 184)
            elif rect.collidepoint(mouse_pos):
                if mouse_pressed[0]:
                    btn_color = (184, 184, 184)
                else:
                    btn_color = (212, 212, 212)
            else:
                btn_color = (255, 255, 255)

            pygame.draw.rect(screen, btn_color, rect, border_radius=5)

            text_surf = font_button.render(text, True, (102, 102, 102))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

            current_y += button_height + button_spacing

    elif game_state == "level_select":
        level_select_menu.draw(
            screen,
            [lvl["title"] for lvl in parsed_levels],
            level_progress,
            wt_count=sum(1 for state in level_progress.values() if state == "green"),
            time_text=savegame.format_time(time_spent)
        )

    elif game_state == "playing":
        if parsed_levels:
            lvl = parsed_levels[current_level_index]

            if current_loaded_level != current_level_index:
                current_loaded_level = current_level_index
                door_timer = None
                flash_timer = FLASH_FRAMES
                collected_tokens = set()
                dialogue_box.close()
                dialogue_triggered = False
                level_progress.setdefault(current_level_index, "reached")
                level_characters = []
                for spawn in lvl.get("spawns", []):
                    props = charproperties.get_character_properties(spawn["charid"])
                    if props:
                        c = CharacterEntity(
                            spawn["charid"],
                            spawn["x"],
                            spawn["y"],
                            props,
                            charproperties.jumpheight_properties
                        )
                        level_characters.append(c)

                active_character = next((ch for ch in level_characters if ch.charid == PLAYER_CHARID), None)
                if active_character is None:
                    active_character = CharacterEntity(
                        PLAYER_CHARID,
                        2.0,
                        2.0,
                        charproperties.get_character_properties(PLAYER_CHARID),
                        charproperties.jumpheight_properties
                    )
                    level_characters.insert(0, active_character)

            bg_path = bg_path_from_header(lvl["header"]) or lvl["bg_asset"]
            if bg_path:
                if bg_path not in loaded_bg_surfaces:
                    loaded_bg_surfaces[bg_path] = load_bg_surface(bg_path, screen_width, screen_height)
                screen.blit(loaded_bg_surfaces[bg_path], (0, 0))

            grid = lvl["grid"]
            rows = len(grid)
            cols = len(grid[0]) if rows > 0 else 1

            tile_size = min(screen_width / VIEW_COLS, screen_height / VIEW_ROWS)

            map_pixel_width = cols * tile_size
            map_pixel_height = rows * tile_size
            focus_x = active_character.x * tile_size if active_character else 0.0
            focus_y = (active_character.y - active_character.height / 2.0) * tile_size if active_character else 0.0
            offset_x = camera_offset(focus_x, map_pixel_width, screen_width)
            offset_y = camera_offset(focus_y, map_pixel_height, screen_height)

            big_blocks = []
            for r_idx, row in enumerate(grid):
                for c_idx, char in enumerate(row):
                    if char == "." or char in invisible_refs:
                        continue

                    if char in animated_blocks:
                        frames = animated_blocks[char]
                        frame_path = frames[animation_tick % len(frames)]
                        vx, vy, vw, vh = svg_viewbox(frame_path)
                        k = tile_size / 30.0
                        ax = offset_x + c_idx * tile_size + vx * k
                        ay = offset_y + r_idx * tile_size + vy * k
                        aw, ah = max(1, int(vw * k)), max(1, int(vh * k))
                        if ax + aw < 0 or ax > screen_width or ay + ah < 0 or ay > screen_height:
                            continue
                        cache_key = (frame_path, aw, ah)
                        if cache_key not in loaded_tile_surfaces:
                            loaded_tile_surfaces[cache_key] = load_svg_surface(frame_path, aw, ah)
                        screen.blit(loaded_tile_surfaces[cache_key], (ax, ay))
                        continue

                    if block_sizes.get(char, (1.0, 1.0)) != (1.0, 1.0):
                        big_blocks.append((char, c_idx, r_idx))
                        continue

                    tx = offset_x + (c_idx * tile_size)
                    ty = offset_y + (r_idx * tile_size)
                    if tx + tile_size < 0 or tx > screen_width or ty + tile_size < 0 or ty > screen_height:
                        continue

                    if char in texture_cache:
                        path = texture_cache[char]
                        cache_key = (char, int(tile_size))
                        if cache_key not in loaded_tile_surfaces:
                            loaded_tile_surfaces[cache_key] = load_svg_surface(path, int(tile_size), int(tile_size))
                        surface = loaded_tile_surfaces[cache_key]
                        if char in wintoken_refs:
                            if (c_idx, r_idx) in collected_tokens:
                                continue
                            alpha, shake_x, shake_y = wintoken_look(active_character, c_idx, r_idx)
                            surface.set_alpha(alpha)
                            screen.blit(surface, (tx + shake_x, ty + shake_y))
                        else:
                            screen.blit(surface, (tx, ty))
                    else:
                        rect = pygame.Rect(tx, ty, tile_size, tile_size)
                        pygame.draw.rect(screen, (200, 50, 200), rect)

            for char, c_idx, r_idx in big_blocks:
                bx, by, bw, bh = block_rect(char, c_idx, r_idx)
                surf_w = int(bw * tile_size)
                surf_h = int(bh * tile_size)
                cache_key = (char, surf_w, surf_h)
                if cache_key not in loaded_tile_surfaces:
                    loaded_tile_surfaces[cache_key] = load_svg_surface(texture_cache[char], surf_w, surf_h)
                screen.blit(loaded_tile_surfaces[cache_key], (offset_x + bx * tile_size, offset_y + by * tile_size))

            keys_down = pygame.key.get_pressed()
            ctrl_held = pygame.key.get_mods() & pygame.KMOD_CTRL
            can_move = not ctrl_held and not dialogue_box.active
            input_state = {
                "left": can_move and (keys_down[pygame.K_LEFT] or keys_down[pygame.K_a]),
                "right": can_move and (keys_down[pygame.K_RIGHT] or keys_down[pygame.K_d]),
                "jump": can_move and (keys_down[pygame.K_SPACE] or keys_down[pygame.K_UP] or keys_down[pygame.K_w])
            }

            for ch in level_characters:
                if ch is active_character:
                    ch.update(input_state, grid, solid_refs)
                else:
                    ch.update({"left": False, "right": False, "jump": False}, grid, solid_refs)

                foot_x = offset_x + (ch.x * tile_size)
                foot_y = offset_y + (ch.y * tile_size)
                draw_character(screen, ch, foot_x, foot_y, tile_size / 30.0)

            if active_character:
                collected_tokens.update(touching_tiles(active_character, grid, wintoken_refs))
                if not dialogue_triggered and lvl.get("lines") and touching_tiles(active_character, grid, dialogue_refs):
                    dialogue_triggered = True
                    dialogue_box.start(lvl["lines"])

            if not (active_character and touches_door(active_character, grid)):
                door_timer = None
            elif door_timer is None:
                door_timer = DOOR_DELAY_FRAMES
            else:
                door_timer -= 1
                if door_timer <= 0:
                    got_token = bool(collected_tokens) or not level_has_wintoken(grid)
                    if level_progress.get(current_level_index) != "green":
                        level_progress[current_level_index] = "green" if got_token else "yellow"
                    current_level_index = (current_level_index + 1) % len(parsed_levels)
                    level_progress.setdefault(current_level_index, "reached")
                    save_progress()

            title_surf = font_level_title.render(lvl["title"], True, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(bottomleft=(15, screen_height - 12)))

            back_hint = font_small.render("Press ESC for level select | R to reset | TAB to switch char | CTRL+LEFT/RIGHT to change level", True, (255, 255, 255))
            if dialogue_box.active:
                dialogue_box.draw(screen)
            else:
                screen.blit(back_hint, (15, 15))

            if flash_timer > 0:
                flash = pygame.Surface((screen_width, screen_height))
                flash.fill((255, 255, 255))
                flash.set_alpha(int(255 * flash_timer / FLASH_FRAMES))
                screen.blit(flash, (0, 0))
                flash_timer -= 1

    animation_tick += 1
    pygame.display.flip()
    frame_seconds = clock.tick(60) / 1000.0
    if game_state == "playing":
        time_spent += frame_seconds

pygame.quit()