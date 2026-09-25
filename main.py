from data import charproperties, objectproperties
import pygame, time, random
from game import levelparser as ps
from game import levelselect, dialogue, savegame, leveleditor
from game.assets import load_svg_surface, load_bg_surface, bg_path_from_header, loaded_bg_surfaces
from game.blocks import touching_tiles, touches_door, level_has_wintoken, wintoken_refs, dialogue_refs, lever_blocks, push_lever, reset_toggles
from game.entities import CharacterEntity, GameObject, PLAYER_CHARID
from game.render import draw_object, draw_character, draw_level, camera_offset, reset_levers, VIEW_COLS, VIEW_ROWS

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
font_button = pygame.font.Font("assets/ui/fonts/arial.ttf", 29)
font_button.set_bold(True)
font_credit_big = pygame.font.Font("assets/ui/fonts/arial.ttf", 29)
font_credit_small = pygame.font.Font("assets/ui/fonts/arial.ttf", 14)
font_level_title = pygame.font.Font("assets/ui/fonts/arial.ttf", 30)
font_level_title.set_bold(True)

multiline_text = "By Cary Huang\nMusic by Michael Huang\nPython Port by asdguiv"
text_lines = multiline_text.split('\n')

rendered_lines = [
    font_credit_big.render(text_lines[0], True, (255, 255, 255)),
    font_credit_small.render(text_lines[1], True, (255, 255, 255)),
    font_credit_small.render(text_lines[2], True, (255, 255, 255))
]

MENU_BUTTON_W = 276
MENU_BUTTON_H = 37
MENU_BUTTON_GAP = 8
MENU_MARGIN = 15
LOGO_SIZE = (1180, 545)
LOGO_POS = (-8, -4)

svg_surface = load_svg_surface("assets/ui/poopers.svg", *LOGO_SIZE)
svg_rect = svg_surface.get_rect(topleft=LOGO_POS)

game_state = "main_menu"
level_select_menu = levelselect.LevelSelectMenu((screen_width, screen_height), load_svg_surface)
dialogue_box = dialogue.DialogueBox((screen_width, screen_height), load_svg_surface)
level_editor = leveleditor.LevelEditor((screen_width, screen_height))
test_level = None
active_hit_button = None
current_level_index = 0
current_loaded_level = -1
running = True

animation_tick = 0

level_objects = []
DOOR_DELAY_FRAMES = 60
FLASH_FRAMES = 21
DOOR_SHAKE_PX = 6
flash_timer = 0
door_timer = None
dialogue_triggered = False
door_occupancy = []
collected_tokens = set()
spring_started = {}
level_progress = {0: "reached"}
time_spent = 0.0
deaths = 0
session_active = False
savegame.ensure_save_file()
save_available = savegame.has_save()

def main_menu_buttons():
    if not save_available:
        return main_menubuttons
    buttons = list(main_menubuttons)
    buttons.insert(buttons.index("NEW GAME") + 1, "CONTINUE GAME")
    return buttons

CONFIRM_TEXT = ["Are you sure you want to", "erase your saved progress", "and start a new game?"]
CONFIRM_BOX = pygame.Rect(0, 0, 275, 72)
CONFIRM_BUTTON_SIZE = 108
CONFIRM_GAP = 29
CONFIRM_BUTTON_TOP_GAP = 16
CONFIRM_TOP = 82
CONFIRM_MARGIN = 8
CONFIRM_BACKING = (102, 102, 102)
CONFIRM_YES_COLOR = (158, 54, 54)
CONFIRM_NO_COLOR = (28, 74, 31)
confirm_new_game = False
font_confirm = pygame.font.Font("assets/ui/fonts/arial.ttf", 19)
font_confirm_button = pygame.font.Font("assets/ui/fonts/arial.ttf", 42)
font_confirm_button.set_bold(True)

def confirm_layout():
    center_x = screen_width - MENU_MARGIN - MENU_BUTTON_W // 2
    box = CONFIRM_BOX.copy()
    buttons = main_menu_buttons()
    stack_h = len(buttons) * MENU_BUTTON_H + (len(buttons) - 1) * MENU_BUTTON_GAP
    new_game_top = screen_height - MENU_MARGIN - stack_h + buttons.index("NEW GAME") * (MENU_BUTTON_H + MENU_BUTTON_GAP)
    total_h = CONFIRM_BOX.height + CONFIRM_BUTTON_TOP_GAP + CONFIRM_BUTTON_SIZE
    box.midtop = (center_x, max(CONFIRM_TOP, new_game_top - CONFIRM_MARGIN - 4 - total_h))
    buttons_y = box.bottom + CONFIRM_BUTTON_TOP_GAP
    yes = pygame.Rect(center_x - CONFIRM_GAP // 2 - CONFIRM_BUTTON_SIZE, buttons_y, CONFIRM_BUTTON_SIZE, CONFIRM_BUTTON_SIZE)
    no = pygame.Rect(center_x + CONFIRM_GAP // 2, buttons_y, CONFIRM_BUTTON_SIZE, CONFIRM_BUTTON_SIZE)
    return box, yes, no

def draw_confirm_new_game(target):
    box, yes, no = confirm_layout()
    backing = box.union(yes).union(no).inflate(CONFIRM_MARGIN * 2, CONFIRM_MARGIN * 2)
    backing.width = max(backing.width, MENU_BUTTON_W + CONFIRM_MARGIN)
    backing.centerx = box.centerx
    pygame.draw.rect(target, CONFIRM_BACKING, backing, border_radius=14)
    pygame.draw.rect(target, (255, 255, 255), box, border_radius=18)
    line_h = font_confirm.get_linesize()
    text_top = box.centery - line_h * len(CONFIRM_TEXT) // 2
    for i, line in enumerate(CONFIRM_TEXT):
        surf = font_confirm.render(line, True, (102, 102, 102))
        target.blit(surf, surf.get_rect(midtop=(box.centerx, text_top + i * line_h)))
    for rect, color, label in ((yes, CONFIRM_YES_COLOR, "YES"), (no, CONFIRM_NO_COLOR, "NO")):
        shown = color if not rect.collidepoint(pygame.mouse.get_pos()) else tuple(min(255, c + 25) for c in color)
        pygame.draw.rect(target, shown, rect, border_radius=12)
        surf = font_confirm_button.render(label, True, (255, 255, 255))
        target.blit(surf, surf.get_rect(center=rect.center))

def start_new_game():
    global level_progress, time_spent, deaths, current_level_index, session_active, save_available, game_state
    level_progress = {0: "reached"}
    time_spent = 0.0
    deaths = 0
    current_level_index = 0
    session_active = True
    save_progress()
    save_available = True
    game_state = "level_select"

def save_progress():
    if session_active:
        savegame.write_save(level_progress, time_spent)
level_characters = []
active_character = None

while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    button_width = MENU_BUTTON_W
    button_height = MENU_BUTTON_H
    button_margin_right = MENU_MARGIN
    button_margin_bottom = MENU_MARGIN
    button_spacing = MENU_BUTTON_GAP

    if game_state == "main_menu":
        if savegame.ensure_save_file():
            save_available = False
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
        elif confirm_new_game:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                confirm_new_game = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                _, yes_rect, no_rect = confirm_layout()
                if yes_rect.collidepoint(event.pos):
                    confirm_new_game = False
                    start_new_game()
                elif no_rect.collidepoint(event.pos):
                    confirm_new_game = False
        elif game_state == "level_editor":
            action = level_editor.handle_event(event)
            if action == "exit":
                game_state = "main_menu"
            elif action and action[0] == "test":
                test_level = action[1]
                current_loaded_level = -1
                game_state = "playing"
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
                                elif text == "LEVEL CREATOR":
                                    game_state = "level_editor"
                                elif text == "NEW GAME":
                                    if parsed_levels and savegame.has_save():
                                        confirm_new_game = True
                                    elif parsed_levels:
                                        start_new_game()
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
                if event.key == pygame.K_ESCAPE and test_level is not None:
                    test_level = None
                    current_loaded_level = -1
                    dialogue_box.close()
                    game_state = "level_editor"
                elif event.key == pygame.K_ESCAPE:
                    save_progress()
                    game_state = "level_select"
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) and event.mod & pygame.KMOD_CTRL and parsed_levels and test_level is None:
                    step = 1 if event.key == pygame.K_RIGHT else -1
                    if step == 1 and level_progress.get(current_level_index) != "green":
                        level_progress[current_level_index] = "yellow"
                    current_level_index = (current_level_index + step) % len(parsed_levels)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    dialogue_box.advance()
                elif event.key == pygame.K_r:
                    reset_toggles()
                    reset_levers()
                    collected_tokens = set()
                    spring_started = {}
                    door_timer = None
                    flash_timer = FLASH_FRAMES
                    for ch in level_characters:
                        ch.release()
                        ch.reset()
                    for obj in level_objects:
                        obj.reset()
                elif event.key in (pygame.K_UP, pygame.K_w) and active_character and not active_character.dead and not dialogue_box.active:
                    if active_character.carrying is None:
                        active_character.pick_up(level_objects)
                    else:
                        active_character.throw()
                elif event.key in (pygame.K_DOWN, pygame.K_s) and active_character and not active_character.dead and not dialogue_box.active:
                    active_character.set_down()
                elif event.key in (pygame.K_TAB, pygame.K_z):
                    if len(level_characters) > 1:
                        idx = (level_characters.index(active_character) + 1) % len(level_characters)
                        active_character = level_characters[idx]

    screen.fill((102, 102, 102))

    if game_state == "main_menu" or game_state == "settings":
        screen.blit(svg_surface, svg_rect)

        margin_x = 16
        margin_y = 4
        line_spacing = 3

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
            if confirm_new_game and text == "NEW GAME":
                current_y += button_height + button_spacing
                continue

            if active_hit_button == text and rect.collidepoint(mouse_pos):
                btn_color = (184, 184, 184)
            elif rect.collidepoint(mouse_pos):
                if mouse_pressed[0]:
                    btn_color = (184, 184, 184)
                else:
                    btn_color = (212, 212, 212)
            else:
                btn_color = (255, 255, 255)

            pygame.draw.rect(screen, btn_color, rect, border_radius=7)

            text_surf = font_button.render(text, True, (90, 90, 90))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

            current_y += button_height + button_spacing

        if confirm_new_game:
            draw_confirm_new_game(screen)

    elif game_state == "level_editor":
        level_editor.draw(screen, animation_tick)

    elif game_state == "level_select":
        level_select_menu.draw(
            screen,
            [lvl["title"] for lvl in parsed_levels],
            level_progress,
            wt_count=sum(1 for state in level_progress.values() if state == "green"),
            time_text=savegame.format_time(time_spent),
            deaths=deaths
        )

    elif game_state == "playing":
        if parsed_levels or test_level is not None:
            lvl = test_level if test_level is not None else parsed_levels[current_level_index]

            if current_loaded_level != current_level_index:
                current_loaded_level = current_level_index
                door_timer = None
                door_occupancy = []
                flash_timer = FLASH_FRAMES
                reset_toggles()
                reset_levers()
                collected_tokens = set()
                spring_started = {}
                dialogue_box.close()
                dialogue_triggered = False
                if test_level is None:
                    level_progress.setdefault(current_level_index, "reached")
                level_characters = []
                level_objects = []
                for spawn in lvl.get("spawns", []):
                    object_props = objectproperties.get_object_properties(spawn["charid"])
                    if object_props:
                        level_objects.append(GameObject(spawn["charid"], spawn["x"], spawn["y"], object_props, spawn.get("extra")))
                        continue
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

            shown = door_occupancy if len(door_occupancy) == len(level_characters) else [False] * len(level_characters)
            draw_level(screen, grid, offset_x, offset_y, tile_size, animation_tick, collected_tokens, active_character, shown, spring_started)

            keys_down = pygame.key.get_pressed()
            ctrl_held = pygame.key.get_mods() & pygame.KMOD_CTRL
            can_move = not ctrl_held and not dialogue_box.active
            input_state = {
                "left": can_move and (keys_down[pygame.K_LEFT] or keys_down[pygame.K_a]),
                "right": can_move and (keys_down[pygame.K_RIGHT] or keys_down[pygame.K_d]),
                "jump": can_move and keys_down[pygame.K_SPACE]
            }

            bodies = [obj for obj in level_objects if not obj.gone and obj.carrier is None] + [ch for ch in level_characters if not ch.dead]
            for obj in level_objects:
                obj.update(grid, bodies)
                if not obj.gone and obj.carrier is None:
                    draw_object(screen, obj, offset_x + obj.x * tile_size, offset_y + obj.y * tile_size, tile_size / 30.0)

            for ch in level_characters:
                ch.died = False
                if ch is active_character:
                    ch.update(input_state, grid, bodies)
                else:
                    ch.update({"left": False, "right": False, "jump": False}, grid, bodies)
                if ch.died:
                    if test_level is None:
                        deaths += 1
                    ch.release()
                if ch.dead and not ch.death_visible():
                    continue

                foot_x = offset_x + (ch.x * tile_size)
                foot_y = offset_y + (ch.y * tile_size)
                draw_character(screen, ch, foot_x, foot_y, tile_size / 30.0)

                if ch.carrying is not None:
                    held = ch.carrying
                    held.follow(ch)
                    draw_object(screen, held, offset_x + held.x * tile_size, offset_y + held.y * tile_size, tile_size / 30.0)

            for body in bodies:
                if body.deadly or body.vx == 0.0:
                    continue
                for col, row in touching_tiles(body, grid, lever_blocks):
                    push_lever(lever_blocks[grid[row][col]]["group"], body.vx)

            for body in bodies:
                for spot in body.sprung:
                    spring_started[spot] = animation_tick
                body.sprung = []

            if active_character and not active_character.dead:
                collected_tokens.update(touching_tiles(active_character, grid, wintoken_refs))
                if not dialogue_triggered and lvl.get("lines") and touching_tiles(active_character, grid, dialogue_refs):
                    dialogue_triggered = True
                    dialogue_box.start(lvl["lines"], [ch.charid for ch in level_characters])

            door_occupancy = [not ch.dead and touches_door(ch, grid) for ch in level_characters]
            if not (door_occupancy and all(door_occupancy)):
                door_timer = None
            elif door_timer is None:
                door_timer = DOOR_DELAY_FRAMES
            else:
                door_timer -= 1
                if door_timer <= 0 and test_level is not None:
                    test_level = None
                    current_loaded_level = -1
                    dialogue_box.close()
                    game_state = "level_editor"
                elif door_timer <= 0:
                    got_token = bool(collected_tokens) or not level_has_wintoken(grid)
                    if level_progress.get(current_level_index) != "green":
                        level_progress[current_level_index] = "green" if got_token else "yellow"
                    current_level_index = (current_level_index + 1) % len(parsed_levels)
                    level_progress.setdefault(current_level_index, "reached")
                    save_progress()

            title_surf = font_level_title.render(lvl["title"], True, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(bottomleft=(15, screen_height - 12)))

            back_hint = font_small.render(("ESC back to editor" if test_level is not None else "ESC level select") + " | R reset | UP pick up/throw | DOWN set down | Z switch char | CTRL+LEFT/RIGHT change level", True, (255, 255, 255))
            if dialogue_box.active:
                dialogue_box.draw(screen)
            else:
                screen.blit(back_hint, (15, 15))

            if door_timer is not None:
                door_progress = 1.0 - door_timer / DOOR_DELAY_FRAMES
                shake = DOOR_SHAKE_PX * door_progress
                scene = screen.copy()
                screen.fill((255, 255, 255))
                screen.blit(scene, (random.uniform(-shake, shake), random.uniform(-shake, shake)))
                tint = pygame.Surface((screen_width, screen_height))
                tint.fill((255, 255, 255))
                tint.set_alpha(int(255 * door_progress))
                screen.blit(tint, (0, 0))

            if flash_timer > 0:
                flash = pygame.Surface((screen_width, screen_height))
                flash.fill((255, 255, 255))
                flash.set_alpha(int(255 * flash_timer / FLASH_FRAMES))
                screen.blit(flash, (0, 0))
                flash_timer -= 1

    animation_tick += 1
    pygame.display.flip()
    frame_seconds = clock.tick(60) / 1000.0
    if game_state == "playing" and test_level is None:
        time_spent += frame_seconds

pygame.quit()
