import math
import random
import pygame
from data import charsprites, charproperties
from game.entities import CharacterEntity
from game.assets import get_part_surface, load_svg_surface, svg_viewbox, loaded_tile_surfaces
from game.blocks import invisible_refs, animated_blocks, block_sizes, block_rect, texture_cache, wintoken_refs, door_refs, spring_refs, toggle_blocks, toggle_block_on, lever_blocks, toggle_state

MAX_LEG_TILT = 60
PORTRAIT_BG = (0xD2, 0x7E, 0xCA)
PORTRAIT_FILL = 0.86
portrait_cache = {}

WINTOKEN_FADE_NEAR = 2.0
WINTOKEN_FADE_FAR = 7.0
WINTOKEN_MIN_ALPHA = 0
WINTOKEN_SWING_DEGREES = 45
WINTOKEN_SWING_FRAMES = 120
WINTOKEN_SHAKE_RANGE = 4.0
WINTOKEN_SHAKE_PX = 2.0
DOOR_SQUARE_PX = 8
DOOR_SQUARE_GAP_PX = 3
DOOR_SQUARE_TOP_PX = 6
DOOR_SQUARE_EMPTY = (128, 128, 128)
DOOR_SQUARE_FILLED = (0, 200, 0)
LEVER_ANGLE = 45
LEVER_TURN_SPEED = 9
lever_angles = {}
VIEW_COLS = 32
VIEW_ROWS = 18

def wintoken_look(ch, col, row):
    if ch is None:
        return 255, 0, 0
    dist = math.hypot(col + 0.5 - ch.x, row + 0.5 - (ch.y - ch.height / 2.0))
    closeness = min(max((WINTOKEN_FADE_FAR - dist) / (WINTOKEN_FADE_FAR - WINTOKEN_FADE_NEAR), 0.0), 1.0)
    alpha = int(WINTOKEN_MIN_ALPHA + (255 - WINTOKEN_MIN_ALPHA) * closeness)
    shake = max(0.0, 1.0 - dist / WINTOKEN_SHAKE_RANGE) * WINTOKEN_SHAKE_PX
    return alpha, random.uniform(-shake, shake), random.uniform(-shake, shake)

def draw_object(target, obj, foot_x, foot_y, scale):
    if not obj.texture:
        return
    vx, vy, vw, vh = svg_viewbox(obj.texture)
    w = max(1, int(vw * scale))
    h = max(1, int(vh * scale))
    surface = get_part_surface(obj.texture, w, h)
    left = foot_x + vx * scale
    if obj.flipped:
        surface = pygame.transform.flip(surface, True, False)
        left = foot_x - (vx + vw) * scale
    target.blit(surface, (left, foot_y + vy * scale))


def blit_part(canvas, sprite, pos, scale, flip_x=False, angle=0.0, flip_y=False, stretch=1.0):
    w = max(1, round(sprite["size"][0] * scale))
    base_h = max(1, round(sprite["size"][1] * scale))
    h = max(1, round(base_h * stretch))
    surface = get_part_surface(sprite["path"], w, base_h)
    if h != base_h:
        surface = pygame.transform.smoothscale(surface, (w, h))
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

def character_portrait(charid, size):
    key = (charid, size)
    if key in portrait_cache:
        return portrait_cache[key]
    icon = pygame.Surface((size, size))
    icon.fill(PORTRAIT_BG)
    props = charproperties.get_character_properties(charid)
    if props:
        ch = CharacterEntity(charid, 0, 0, props, charproperties.jumpheight_properties)
        ch.on_ground = True
        height_px = ch.stand_height_svg * ch.part_scale
        width_px = ch.body_svg_w * ch.part_scale
        scale = min(1.0, size * PORTRAIT_FILL / max(height_px, width_px, 1.0))
        draw_character(icon, ch, size / 2, size / 2 + height_px * scale / 2, scale)
    portrait_cache[key] = icon
    return icon

def leg_tilt(ch):
    offset = getattr(ch, "ledge_offset", 0.0)
    if not offset or not ch.on_ground:
        return 0.0
    offset_svg = offset * 30.0 / ch.part_scale
    if not ch.facing_right:
        offset_svg = -offset_svg
    tilt = math.degrees(math.atan2(offset_svg, charsprites.LEG_LENGTH))
    return max(-MAX_LEG_TILT, min(MAX_LEG_TILT, tilt))

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

    arm_pose_table = ch.parts.get("arm_poses", {})
    dead = getattr(ch, "dead", False)
    if dead and "dead" in arm_pose_table:
        arm_pose_name = "dead"
    elif ch.carrying is not None and "carry" in arm_pose_table:
        arm_pose_name = "carry"
    else:
        arm_pose_name = ch.pose()
    arms = list(zip(sorted(ch.parts.get("arms", [])), arm_pose_table.get(arm_pose_name, [])))
    arm_scale = s * ch.parts.get("arm_scale", 1.0)
    wave = ch.walk_wave()

    def draw_arms(in_front):
        for arm, arm_pose in arms:
            if arm_pose.get("front", False) != in_front:
                continue
            blit_part(
                canvas,
                charsprites.arm_sprites[arm_pose["sprite"]],
                at(arm_pose.get("shoulder", arm)),
                arm_scale * arm_pose.get("scale", 1.0),
                flip_x=arm_pose.get("flip_x", False),
                flip_y=arm_pose.get("flip_y", False),
                angle=arm_pose.get("angle", 0) + arm_pose.get("swing", 0) * wave
            )

    draw_arms(False)

    front_leg, back_leg = ch.leg_frames()
    back_hip, front_hip = sorted(ch.hips)[0], sorted(ch.hips)[-1]
    tilt = leg_tilt(ch)
    stretch = 1.0 / math.cos(math.radians(tilt))
    blit_part(canvas, back_leg, at(back_hip), s, angle=tilt, stretch=stretch)
    blit_part(canvas, front_leg, at(front_hip), s, angle=tilt, stretch=stretch)

    canvas.blit(get_part_surface(ch.sprite_path, body_w, body_h), (pad, pad))

    eye_scale = s * ch.parts.get("eye_scale", 1.0)
    for i, eye in enumerate(sorted(ch.parts.get("eyes", []))):
        if dead:
            blit_part(canvas, charsprites.dead_eye_sprite, at(eye), eye_scale, flip_x=i > 0)
        else:
            blit_part(canvas, charsprites.eye_sprite, at(eye), eye_scale)
    if "mouth" in ch.parts:
        blit_part(canvas, charsprites.dead_mouth_sprite if dead else charsprites.mouth_sprite, at(ch.parts["mouth"]), s)

    draw_arms(True)

    foot_canvas_x = pad + ch.body_svg_w * s / 2
    foot_canvas_y = pad + ch.stand_height_svg * s
    if not ch.facing_right:
        canvas = pygame.transform.flip(canvas, True, False)
        foot_canvas_x = canvas_w - foot_canvas_x
    target.blit(canvas, (foot_x - foot_canvas_x, foot_y - foot_canvas_y))

def draw_door_squares(target, left, top, width, occupancy, scale):
    if not occupancy:
        return
    size = DOOR_SQUARE_PX * scale
    gap = DOOR_SQUARE_GAP_PX * scale
    total = len(occupancy) * size + (len(occupancy) - 1) * gap
    x = left + (width - total) / 2
    y = top + DOOR_SQUARE_TOP_PX * scale
    for occupied in occupancy:
        rect = pygame.Rect(round(x), round(y), round(size), round(size))
        pygame.draw.rect(target, DOOR_SQUARE_FILLED if occupied else DOOR_SQUARE_EMPTY, rect)
        x += size + gap

def camera_offset(focus, map_size, view_size):
    if map_size <= view_size:
        return (view_size - map_size) / 2
    return -min(max(focus - view_size / 2, 0.0), map_size - view_size)

def draw_svg_at(screen, path, x, y, k):
    vx, vy, vw, vh = svg_viewbox(path)
    w, h = max(1, round(vw * k)), max(1, round(vh * k))
    cache_key = (path, w, h)
    if cache_key not in loaded_tile_surfaces:
        loaded_tile_surfaces[cache_key] = load_svg_surface(path, w, h)
    screen.blit(loaded_tile_surfaces[cache_key], (x + vx * k, y + vy * k))

def draw_rotated_svg(screen, path, pivot_x, pivot_y, k, angle):
    vx, vy, vw, vh = svg_viewbox(path)
    w, h = max(1, round(vw * k)), max(1, round(vh * k))
    cache_key = (path, w, h)
    if cache_key not in loaded_tile_surfaces:
        loaded_tile_surfaces[cache_key] = load_svg_surface(path, w, h)
    surface = pygame.transform.rotate(loaded_tile_surfaces[cache_key], angle)
    center_offset = pygame.math.Vector2((vx + vw / 2) * k, (vy + vh / 2) * k).rotate(-angle)
    screen.blit(surface, surface.get_rect(center=(pivot_x + center_offset.x, pivot_y + center_offset.y)))

def reset_levers():
    lever_angles.clear()

def step_levers():
    for info in lever_blocks.values():
        group = info["group"]
        target = -LEVER_ANGLE if toggle_state.get(group, False) else LEVER_ANGLE
        current = lever_angles.get(group, LEVER_ANGLE)
        if current < target:
            current = min(target, current + LEVER_TURN_SPEED)
        elif current > target:
            current = max(target, current - LEVER_TURN_SPEED)
        lever_angles[group] = current

def draw_level(screen, grid, offset_x, offset_y, tile_size, animation_tick, collected_tokens, active_character, door_squares, spring_started):
    screen_w, screen_h = screen.get_size()
    step_levers()
    big_blocks = []
    for r_idx, row in enumerate(grid):
        for c_idx, char in enumerate(row):
            if char == "." or char in invisible_refs:
                continue

            if char in animated_blocks:
                frames = animated_blocks[char]
                if char in spring_refs:
                    since = animation_tick - spring_started.get((c_idx, r_idx), -len(frames))
                    frame_path = frames[since if 0 <= since < len(frames) else 0]
                else:
                    frame_path = frames[animation_tick % len(frames)]
                vx, vy, vw, vh = svg_viewbox(frame_path)
                k = tile_size / 30.0
                ax = offset_x + c_idx * tile_size + vx * k
                ay = offset_y + r_idx * tile_size + vy * k
                aw, ah = max(1, int(vw * k)), max(1, int(vh * k))
                if ax + aw < 0 or ax > screen_w or ay + ah < 0 or ay > screen_h:
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
            if tx + tile_size < 0 or tx > screen_w or ty + tile_size < 0 or ty > screen_h:
                continue

            if char in toggle_blocks:
                info = toggle_blocks[char]
                draw_svg_at(screen, info["on"] if toggle_block_on(char) else info["off"], tx, ty, tile_size / 30.0)
                continue

            if char in lever_blocks:
                info = lever_blocks[char]
                k = tile_size / 30.0
                draw_rotated_svg(screen, info["handle"], tx + 15 * k, ty + 30 * k, k, lever_angles.get(info["group"], LEVER_ANGLE))
                draw_svg_at(screen, texture_cache[char], tx, ty, k)
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
                    if alpha <= 0:
                        continue
                    swing = WINTOKEN_SWING_DEGREES * math.sin(animation_tick / WINTOKEN_SWING_FRAMES * 2.0 * math.pi)
                    token = pygame.transform.rotate(surface, swing)
                    token.set_alpha(alpha)
                    center = (tx + tile_size / 2 + shake_x, ty + tile_size / 2 + shake_y)
                    screen.blit(token, token.get_rect(center=center))
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
        if char in door_refs:
            draw_door_squares(screen, offset_x + bx * tile_size, offset_y + by * tile_size, bw * tile_size, door_squares, tile_size / 30.0)
