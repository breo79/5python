import math
import random
import pygame
from data import charsprites
from game.assets import get_part_surface, load_svg_surface, svg_viewbox, loaded_tile_surfaces
from game.blocks import invisible_refs, animated_blocks, block_sizes, block_rect, texture_cache, wintoken_refs, door_refs

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

    arm_pose_table = ch.parts.get("arm_poses", {})
    arm_pose_name = "carry" if ch.carrying is not None and "carry" in arm_pose_table else ch.pose()
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

def draw_level(screen, grid, offset_x, offset_y, tile_size, animation_tick, collected_tokens, active_character, door_squares):
    screen_w, screen_h = screen.get_size()
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
