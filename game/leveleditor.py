import math
import pygame
from data import blockproperties, charproperties, objectproperties, backgroundproperties
from game import levelparser
from game.assets import ROOT, load_svg_surface, load_bg_surface
from game.blocks import invisible_refs, block_sizes, toggle_blocks, lever_blocks, texture_cache
from game.entities import CharacterEntity, GameObject
from game.render import draw_level, draw_character, draw_object, draw_svg_at, draw_rotated_svg, character_portrait, LEVER_ANGLE

FONT_PATH = "assets/ui/fonts/arial.ttf"
TOOL_ICON_PATH = "assets/ui/leveleditor/tool{:04d}.svg"
MY_LEVELS_PATH = ROOT / "assets" / "leveldata" / "mylevels.txt"

CANVAS_RECT = pygame.Rect(0, 0, 658, 485)
BAR_RECT = pygame.Rect(0, 485, 658, 55)
PANEL_RECT = pygame.Rect(658, 0, 302, 540)
TAB_STRIP_RECT = pygame.Rect(658, 0, 302, 50)
CONTENT_RECT = pygame.Rect(663, 55, 292, 428)
TAB_HEIGHT = 44
TAB_PAD = 18
TAB_GAP = 4
TAB_RADIUS = 10
TAB_SCROLL_SPEED = 40
PAN_KEEP_PX = 60
EXIT_RECT = pygame.Rect(843, 493, 100, 36)

TILE_PX = 20
MIN_TILE_PX = 8
MAX_TILE_PX = 40
SCROLL_SPEED = 12
DEFAULT_WIDTH = 32
DEFAULT_HEIGHT = 18
MAX_LEVEL_SIZE = 300
UNDO_LIMIT = 100
MESSAGE_FRAMES = 150

BG_COLOR = (102, 102, 102)
BAR_COLOR = (153, 153, 153)
PANEL_COLOR = (204, 204, 204)
TAB_COLORS = ((119, 119, 119), (85, 85, 85))
TAB_STRIP_COLOR = (153, 153, 153)
TAB_TEXT_SELECTED = (51, 51, 51)
BUTTON_COLOR = (68, 68, 68)
BUTTON_HOVER = (95, 95, 95)
BUTTON_DISABLED = (130, 130, 130)
TOOL_SELECTED = (130, 130, 130)
GRID_COLOR = (51, 51, 51)
HIGHLIGHT = (255, 204, 0)
WHITE = (255, 255, 255)

TABS = ["Level Info", "Characters / Objects", "Tiles", "Background", "Dialogue", "Options"]
TOOLS = ["pencil", "eraser", "rect", "fill", "picker", "select", "row", "column"]
ACTIONS = [("copy", 9), ("undo", 10), ("redo", 8), ("clear", 11)]

PLAYER_STATE = "10"
OBJECT_STATE = "06"
MOVING_STATE = "03"
MOVING_STATES = ("03", "04")
DEFAULT_PATH_SPEED = 10
MAX_PATH_SPEED = 99
FIRST_OBJECT_ID = 35
PATH_ARROWS = {"0": "\u2191", "1": "\u2193", "2": "\u2190", "3": "\u2192"}
PATH_STEPS = {"0": (0, -1), "1": (0, 1), "2": (-1, 0), "3": (1, 0)}
ROW_H = 30
SPEAKER_ICON = 26
LOAD_BOX_RECT = pygame.Rect(80, 50, 800, 440)
LOAD_TEXT_RECT = pygame.Rect(100, 95, 760, 330)
LOAD_BUTTONS = {
    "Paste": pygame.Rect(100, 440, 110, 34),
    "Clear": pygame.Rect(220, 440, 110, 34),
    "Load": pygame.Rect(630, 440, 110, 34),
    "Cancel": pygame.Rect(750, 440, 110, 34),
}
NARRATOR = "99"
FACES = ("S", "H")


def tool_rect(index):
    return pygame.Rect(32 + index * 50, 492, 40, 40)


def action_rect(index):
    return pygame.Rect(432 + index * 50, 492, 40, 40)


class LevelEditor:
    def __init__(self, screen_size):
        self.screen_w, self.screen_h = screen_size
        self.font_tab = pygame.font.Font(FONT_PATH, 26)
        self.font_button = pygame.font.Font(FONT_PATH, 20)
        self.font_small = pygame.font.Font(FONT_PATH, 15)
        self.font_exit = pygame.font.Font(FONT_PATH, 28)
        self.font_exit.set_bold(True)

        self.tool_icons = [load_svg_surface(TOOL_ICON_PATH.format(i), 40, 40) for i in range(12)]
        self.palette = [block["referential"] for block in blockproperties.block_sprites]
        self.palette_icons = {ref: self.make_tile_icon(ref, 30) for ref in self.palette}
        self.characters = list(dict.fromkeys(entry["id"] for entry in charproperties.character_properties if entry.get("id") is not None))
        self.character_names = {entry["id"]: entry.get("name", entry["id"]) for entry in charproperties.character_properties}
        self.objects = [entry["entityid"] for entry in objectproperties.object_properties]
        self.object_names = {entry["entityid"]: entry.get("objectname", entry["entityid"]) for entry in objectproperties.object_properties}
        self.previews = {}
        self.entity_icons = {}
        self.bg_thumbs = {}
        self.bg_views = {}

        self.tab = 2
        self.tool = "pencil"
        self.tab_widths = [self.font_tab.size(name)[0] + TAB_PAD * 2 for name in TABS]
        self.tab_scroll = 0
        self.scroll_tab_into_view(self.tab)
        self.selected_tile = "/"
        self.selected_entity = "1"
        self.panel_scroll = 0
        self.show_my_levels = False
        self.message = ""
        self.message_timer = 0
        self.editing = None
        self.load_box = None
        self.selected_index = None
        self.undo_stack = []
        self.redo_stack = []
        self.new_level()

    def new_level(self):
        self.title = "Untitled"
        self.saved_title = None
        self.bg = 0
        self.grid = [["."] * DEFAULT_WIDTH for _ in range(DEFAULT_HEIGHT)]
        self.entities = []
        self.dialogue = []
        self.necessary_deaths = "000000"
        self.reset_view_state()

    def reset_view_state(self):
        self.tile_px = TILE_PX
        self.view_x = 0.0
        self.view_y = 0.0
        self.selection = None
        self.stamp = None
        self.drag_start = None
        self.drag_end = None
        self.dragging_entity = None
        self.painting = None
        self.selected_index = None
        self.clamp_view(center=True)

    def tab_rect(self, index):
        x = TAB_STRIP_RECT.x + 5 + sum(w + TAB_GAP for w in self.tab_widths[:index]) - self.tab_scroll
        return pygame.Rect(x, TAB_STRIP_RECT.bottom - TAB_HEIGHT, self.tab_widths[index], TAB_HEIGHT)

    def max_tab_scroll(self):
        total = sum(self.tab_widths) + TAB_GAP * (len(TABS) - 1) + 10
        return max(0, total - TAB_STRIP_RECT.width)

    def scroll_tabs(self, amount):
        self.tab_scroll = min(max(self.tab_scroll + amount, 0), self.max_tab_scroll())

    def scroll_tab_into_view(self, index):
        rect = self.tab_rect(index)
        if rect.left < TAB_STRIP_RECT.left + 5:
            self.scroll_tabs(rect.left - TAB_STRIP_RECT.left - 5)
        elif rect.right > TAB_STRIP_RECT.right - 5:
            self.scroll_tabs(rect.right - TAB_STRIP_RECT.right + 5)

    def select_tab(self, index):
        if self.tab != index:
            self.tab = index
            self.panel_scroll = 0
            self.show_my_levels = False
        self.scroll_tab_into_view(index)

    @property
    def cols(self):
        return len(self.grid[0]) if self.grid else 0

    @property
    def rows(self):
        return len(self.grid)

    def notify(self, text):
        self.message = text
        self.message_timer = MESSAGE_FRAMES

    def snapshot(self):
        return (
            [row[:] for row in self.grid],
            [dict(e) for e in self.entities],
            self.title,
            self.bg,
            [dict(d) for d in self.dialogue],
        )

    def restore(self, state):
        grid, entities, title, bg, dialogue = state
        self.grid = [row[:] for row in grid]
        self.entities = [dict(e) for e in entities]
        self.title = title
        self.bg = bg
        self.dialogue = [dict(d) for d in dialogue]
        self.clamp_view()

    def push_undo(self):
        self.undo_stack.append(self.snapshot())
        if len(self.undo_stack) > UNDO_LIMIT:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.snapshot())
            self.restore(self.undo_stack.pop())

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.snapshot())
            self.restore(self.redo_stack.pop())

    def clamp_view(self, center=False):
        level_w = self.cols * self.tile_px
        level_h = self.rows * self.tile_px
        margin = 8
        if center:
            self.view_x = (CANVAS_RECT.width - level_w) / 2 if level_w <= CANVAS_RECT.width - margin * 2 else margin
            self.view_y = (CANVAS_RECT.height - level_h) / 2 if level_h <= CANVAS_RECT.height - margin * 2 else margin
        self.view_x = min(max(self.view_x, PAN_KEEP_PX - level_w), CANVAS_RECT.width - PAN_KEEP_PX)
        self.view_y = min(max(self.view_y, PAN_KEEP_PX - level_h), CANVAS_RECT.height - PAN_KEEP_PX)

    def tile_at(self, pos):
        col = math.floor((pos[0] - self.view_x) / self.tile_px)
        row = math.floor((pos[1] - self.view_y) / self.tile_px)
        return col, row

    def level_point(self, pos):
        return (pos[0] - self.view_x) / self.tile_px, (pos[1] - self.view_y) / self.tile_px

    def in_bounds(self, col, row):
        return 0 <= col < self.cols and 0 <= row < self.rows

    def to_string(self):
        lines = [self.title, f"{self.cols},{self.rows},{len(self.entities):02d},{self.bg:02d},L"]
        lines += ["".join(row) for row in self.grid]
        for e in self.entities:
            line = f"{int(e['charid']):02d},{e['x']:05.2f},{e['y']:05.2f}"
            if e.get("extra"):
                line += "," + e["extra"]
            lines.append(line)
        lines.append(f"{len(self.dialogue):02d}")
        lines += [f"{d['speaker']}{d['face']} {d['text']}" for d in self.dialogue]
        lines.append(self.necessary_deaths)
        return "\n".join(lines)

    def load_string(self, text):
        text = text.replace("\r\n", "\n").strip("\n")
        if text.startswith("loadedLevels="):
            text = text.split("\n", 1)[1] if "\n" in text else ""
        levels = levelparser.parse_level_lines([line.rstrip("\r") for line in text.split("\n")])
        if not levels:
            return False
        self.load_level(levels[0], text)
        return True

    def load_level(self, lvl, source_text=""):
        self.push_undo()
        self.title = lvl["title"]
        self.saved_title = None
        parts = lvl["header"].split(",")
        try:
            self.bg = int(parts[3])
        except (ValueError, IndexError):
            self.bg = 0
        self.grid = [list(row) for row in lvl["grid"]] or [["."] * DEFAULT_WIDTH for _ in range(DEFAULT_HEIGHT)]
        self.entities = [
            {"charid": s["charid"], "x": s["x"], "y": s["y"], "extra": s.get("extra")}
            for s in lvl.get("spawns", [])
        ]
        self.dialogue = [dict(d) for d in lvl.get("lines", [])]
        tail = [line for line in source_text.split("\n") if line.startswith("0000")]
        self.necessary_deaths = tail[0].strip() if tail else "000000"
        self.reset_view_state()

    def test_level(self):
        levels = levelparser.parse_level_lines(self.to_string().split("\n"))
        return levels[0] if levels else None

    def copy_to_clipboard(self):
        text = self.to_string()
        try:
            pygame.scrap.put_text(text)
            self.notify("Level string copied")
        except Exception:
            (ROOT / "assets" / "leveldata" / "clipboard.txt").write_text(text, encoding="utf-8")
            self.notify("Saved to leveldata/clipboard.txt")

    def clipboard_text(self):
        try:
            return (pygame.scrap.get_text() or "").replace("\r\n", "\n").replace("\x00", "")
        except Exception:
            return ""

    def open_load_box(self):
        self.load_box = {"text": ""}

    def confirm_load_box(self):
        text = self.load_box["text"]
        if text.strip() and self.load_string(text):
            self.load_box = None
            self.notify("Level loaded")
        else:
            self.notify("That isn't a level string")

    def handle_load_box(self, event):
        if event.type == pygame.TEXTINPUT:
            self.load_box["text"] += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.load_box = None
            elif event.key == pygame.K_BACKSPACE:
                self.load_box["text"] = self.load_box["text"][:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if event.mod & pygame.KMOD_CTRL:
                    self.confirm_load_box()
                else:
                    self.load_box["text"] += "\n"
            elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_v:
                self.load_box["text"] += self.clipboard_text()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, rect in LOAD_BUTTONS.items():
                if rect.collidepoint(event.pos):
                    if label == "Paste":
                        self.load_box["text"] += self.clipboard_text()
                    elif label == "Clear":
                        self.load_box["text"] = ""
                    elif label == "Load":
                        self.confirm_load_box()
                    else:
                        self.load_box = None
                    break
        return None

    def draw_load_box(self, screen):
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, PANEL_COLOR, LOAD_BOX_RECT, border_radius=8)
        self.draw_label(screen, "Load String - paste a level string (Ctrl+V), then press Load", (LOAD_BOX_RECT.x + 20, LOAD_BOX_RECT.y + 14))
        pygame.draw.rect(screen, WHITE, LOAD_TEXT_RECT)
        pygame.draw.rect(screen, BUTTON_COLOR, LOAD_TEXT_RECT, 2)
        line_h = self.font_small.get_linesize()
        lines = self.load_box["text"].split("\n")
        if pygame.time.get_ticks() // 500 % 2 == 0:
            lines[-1] += "|"
        visible = lines[-((LOAD_TEXT_RECT.height - 10) // line_h):]
        screen.set_clip(LOAD_TEXT_RECT.inflate(-8, -8))
        for i, line in enumerate(visible):
            screen.blit(self.font_small.render(line, True, (30, 30, 30)), (LOAD_TEXT_RECT.x + 6, LOAD_TEXT_RECT.y + 5 + i * line_h))
        screen.set_clip(None)
        count = self.font_small.render(f"{len(lines)} lines", True, (60, 60, 60))
        screen.blit(count, count.get_rect(topright=(LOAD_TEXT_RECT.right, LOAD_TEXT_RECT.bottom + 4)))
        for label, rect in LOAD_BUTTONS.items():
            self.draw_button(screen, rect, label)
        if self.message_timer > 0:
            text = self.font_small.render(self.message, True, (150, 30, 30))
            screen.blit(text, text.get_rect(midleft=(LOAD_BUTTONS["Clear"].right + 16, LOAD_BUTTONS["Clear"].centery)))

    def is_character(self, charid):
        return charid.isdigit() and int(charid) < FIRST_OBJECT_ID

    def speaker_ids(self):
        return [e["charid"] for e in self.entities if self.is_character(e["charid"])]

    def entity_name(self, charid):
        return self.character_names.get(charid) or self.object_names.get(charid) or f"Entity {charid}"

    def entity_motion(self, e):
        parts = (e.get("extra") or "").split()
        state = parts[0] if parts else ""
        code = parts[1] if len(parts) > 1 else ""
        speed = int(code[:2]) if code[:2].isdigit() and int(code[:2]) > 0 else DEFAULT_PATH_SPEED
        path = "".join(ch for ch in code[2:] if ch in PATH_STEPS)
        return state, speed, path

    def set_entity_motion(self, e, moving, speed, path):
        e["extra"] = f"{MOVING_STATE} {speed:02d}{path}" if moving else OBJECT_STATE

    def selected_placed(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.entities):
            return self.entities[self.selected_index]
        return None

    def path_summary(self, path):
        runs = []
        for step in path:
            if runs and runs[-1][0] == step:
                runs[-1][1] += 1
            else:
                runs.append([step, 1])
        return "  ".join(f"{PATH_ARROWS[step]}{count}" for step, count in runs) or "no path yet"

    def placed_top(self):
        rects = self.entity_rects()
        return max(rect.bottom for _, rect in rects) + 50 if rects else CONTENT_RECT.y + 30 - self.panel_scroll

    def placed_rows(self):
        rows = []
        y = self.placed_top()
        x = CONTENT_RECT.x + 4
        for i, e in enumerate(self.entities):
            row = {"row": pygame.Rect(x, y, 284, ROW_H - 2), "delete": pygame.Rect(x + 256, y + 1, 26, ROW_H - 4)}
            y += ROW_H
            if i == self.selected_index and not self.is_character(e["charid"]):
                row["static"] = pygame.Rect(x + 4, y, 70, 26)
                row["moving"] = pygame.Rect(x + 78, y, 70, 26)
                row["speed-"] = pygame.Rect(x + 204, y, 22, 26)
                row["speed+"] = pygame.Rect(x + 258, y, 22, 26)
                y += 30
                for n, step in enumerate("0123"):
                    row["step" + step] = pygame.Rect(x + 4 + n * 38, y, 34, 26)
                row["undo_step"] = pygame.Rect(x + 158, y, 58, 26)
                row["clear_path"] = pygame.Rect(x + 222, y, 58, 26)
                y += 30
                row["summary"] = pygame.Rect(x + 4, y, 276, 22)
                y += 28
            rows.append((i, e, row))
        return rows

    def handle_placed_click(self, pos):
        for i, e, row in self.placed_rows():
            if row["delete"].collidepoint(pos):
                self.push_undo()
                del self.entities[i]
                self.selected_index = None
                return True
            if row["row"].collidepoint(pos):
                self.selected_index = None if self.selected_index == i else i
                return True
            if "static" not in row:
                continue
            state, speed, path = self.entity_motion(e)
            moving = state in MOVING_STATES
            for name, rect in row.items():
                if name in ("row", "delete", "summary") or not rect.collidepoint(pos):
                    continue
                self.push_undo()
                if name == "static":
                    self.set_entity_motion(e, False, speed, path)
                elif name == "moving":
                    self.set_entity_motion(e, True, speed, path)
                elif name == "speed-" and moving:
                    self.set_entity_motion(e, True, max(1, speed - 1), path)
                elif name == "speed+" and moving:
                    self.set_entity_motion(e, True, min(MAX_PATH_SPEED, speed + 1), path)
                elif name.startswith("step"):
                    self.set_entity_motion(e, True, speed, path + name[4])
                elif name == "undo_step":
                    self.set_entity_motion(e, moving, speed, path[:-1])
                elif name == "clear_path":
                    self.set_entity_motion(e, moving, speed, "")
                return True
        return False

    def draw_placed_list(self, screen):
        top = self.placed_top()
        self.draw_label(screen, f"In this level ({len(self.entities)})", (CONTENT_RECT.x + 8, top - 22), font=self.font_small)
        for i, e, row in self.placed_rows():
            selected = i == self.selected_index
            pygame.draw.rect(screen, TOOL_SELECTED if selected else BUTTON_COLOR, row["row"])
            icon = pygame.transform.smoothscale(self.entity_icon(e["charid"]), (ROW_H - 4, ROW_H - 4))
            screen.blit(icon, (row["row"].x + 2, row["row"].y + 1))
            state, speed, path = self.entity_motion(e)
            label = f"{self.entity_name(e['charid'])}  ({e['x']:g}, {e['y']:g})"
            screen.blit(self.font_small.render(label, True, WHITE), (row["row"].x + 34, row["row"].y + 6))
            self.draw_button(screen, row["delete"], "x", font=self.font_small)
            if "static" not in row:
                continue
            moving = state in MOVING_STATES
            pygame.draw.rect(screen, (190, 190, 190), (row["static"].x - 4, row["static"].y - 2, 284, row["summary"].bottom - row["static"].y + 6))
            self.draw_toggle(screen, row["static"], "Static", not moving)
            self.draw_toggle(screen, row["moving"], "Moving", moving)
            self.draw_label(screen, "Speed", (row["speed-"].x - 44, row["speed-"].y + 4), font=self.font_small)
            self.draw_button(screen, row["speed-"], "-", enabled=moving, font=self.font_small)
            self.draw_button(screen, row["speed+"], "+", enabled=moving, font=self.font_small)
            speed_text = self.font_small.render(f"{speed:02d}", True, (40, 40, 40))
            screen.blit(speed_text, speed_text.get_rect(center=((row["speed-"].right + row["speed+"].left) // 2, row["speed-"].centery)))
            for step in "0123":
                self.draw_button(screen, row["step" + step], PATH_ARROWS[step])
            self.draw_button(screen, row["undo_step"], "Back", font=self.font_small)
            self.draw_button(screen, row["clear_path"], "Clear", font=self.font_small)
            summary = self.path_summary(path) + (f"   ({len(path)} tiles, {speed} frames each)" if path else "")
            self.draw_label(screen, summary, (row["summary"].x, row["summary"].y + 3), font=self.font_small)

    def draw_toggle(self, screen, rect, label, active):
        pygame.draw.rect(screen, HIGHLIGHT if active else BUTTON_COLOR, rect)
        text = self.font_small.render(label, True, (40, 40, 40) if active else WHITE)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_path_preview(self, screen, e):
        state, speed, path = self.entity_motion(e)
        if state not in MOVING_STATES or not path:
            return
        t = self.tile_px
        _, _, _, h = self.entity_box(e)
        x, y = e["x"], e["y"] - h / 2
        points = [(self.view_x + x * t, self.view_y + y * t)]
        for step in path:
            dx, dy = PATH_STEPS[step]
            x, y = x + dx, y + dy
            points.append((self.view_x + x * t, self.view_y + y * t))
        if len(points) > 1:
            pygame.draw.lines(screen, HIGHLIGHT, False, points, 3)
        for point in points:
            pygame.draw.circle(screen, HIGHLIGHT, point, 3)
        pygame.draw.circle(screen, WHITE, points[0], 5, 2)

    def read_my_levels(self):
        if not MY_LEVELS_PATH.exists():
            return []
        text = MY_LEVELS_PATH.read_text(encoding="utf-8")
        return [chunk.strip("\n") for chunk in text.split("\n\n") if chunk.strip()]

    def write_my_levels(self, chunks):
        MY_LEVELS_PATH.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")

    def save_level(self, as_copy=False):
        chunks = self.read_my_levels()
        if as_copy:
            self.title = self.title + " (copy)"
            chunks.append(self.to_string())
        else:
            titles = [chunk.split("\n", 1)[0] for chunk in chunks]
            key = self.saved_title if self.saved_title in titles else self.title
            if key in titles:
                chunks[titles.index(key)] = self.to_string()
            else:
                chunks.append(self.to_string())
        self.saved_title = self.title
        self.write_my_levels(chunks)
        self.notify("Saved to My Levels")

    def set_tile(self, col, row, char):
        if self.in_bounds(col, row):
            self.grid[row][col] = char

    def paint_line(self, a, b, char):
        (c0, r0), (c1, r1) = a, b
        steps = max(abs(c1 - c0), abs(r1 - r0), 1)
        for i in range(steps + 1):
            self.set_tile(round(c0 + (c1 - c0) * i / steps), round(r0 + (r1 - r0) * i / steps), char)

    def flood_fill(self, col, row, char):
        if not self.in_bounds(col, row):
            return
        target = self.grid[row][col]
        if target == char:
            return
        stack = [(col, row)]
        while stack:
            c, r = stack.pop()
            if not self.in_bounds(c, r) or self.grid[r][c] != target:
                continue
            self.grid[r][c] = char
            stack.extend(((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)))

    def rect_bounds(self, a, b):
        return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])

    def fill_rect(self, a, b, char):
        c0, r0, c1, r1 = self.rect_bounds(a, b)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                self.set_tile(c, r, char)

    def insert_row(self, row):
        row = min(max(row, 0), self.rows)
        self.grid.insert(row, ["."] * self.cols)
        for e in self.entities:
            if e["y"] > row:
                e["y"] += 1
        self.clamp_view()

    def delete_row(self, row):
        if self.rows <= 1 or not 0 <= row < self.rows:
            return
        del self.grid[row]
        self.entities = [e for e in self.entities if not row < e["y"] <= row + 1]
        for e in self.entities:
            if e["y"] > row + 1:
                e["y"] -= 1
        self.clamp_view()

    def insert_column(self, col):
        col = min(max(col, 0), self.cols)
        for grid_row in self.grid:
            grid_row.insert(col, ".")
        for e in self.entities:
            if e["x"] > col:
                e["x"] += 1
        self.clamp_view()

    def delete_column(self, col):
        if self.cols <= 1 or not 0 <= col < self.cols:
            return
        for grid_row in self.grid:
            del grid_row[col]
        self.entities = [e for e in self.entities if not col <= e["x"] < col + 1]
        for e in self.entities:
            if e["x"] >= col + 1:
                e["x"] -= 1
        self.clamp_view()

    def resize(self, cols, rows):
        cols = min(max(cols, 1), MAX_LEVEL_SIZE)
        rows = min(max(rows, 1), MAX_LEVEL_SIZE)
        if (cols, rows) == (self.cols, self.rows):
            return
        self.push_undo()
        grid = [row[:cols] + ["."] * (cols - len(row)) for row in self.grid[:rows]]
        grid += [["."] * cols for _ in range(rows - len(grid))]
        self.grid = grid
        self.entities = [e for e in self.entities if e["x"] < cols and e["y"] <= rows]
        self.clamp_view()

    def copy_selection(self):
        if not self.selection:
            self.notify("Select an area first")
            return
        c0, r0, c1, r1 = self.selection
        self.stamp = [
            [self.grid[r][c] if self.in_bounds(c, r) else "." for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)
        ]
        self.tool = "paste"
        self.notify("Click to paste, right click to stop")

    def paste_stamp(self, col, row):
        for dr, stamp_row in enumerate(self.stamp):
            for dc, char in enumerate(stamp_row):
                self.set_tile(col + dc, row + dr, char)

    def clear(self):
        self.push_undo()
        self.grid = [["."] * self.cols for _ in range(self.rows)]

    def preview(self, charid):
        if charid in self.previews:
            return self.previews[charid]
        preview = None
        object_props = objectproperties.get_object_properties(charid)
        if object_props:
            preview = GameObject(charid, 0, 0, object_props)
        else:
            props = charproperties.get_character_properties(charid)
            if props:
                preview = CharacterEntity(charid, 0, 0, props, charproperties.jumpheight_properties)
                preview.on_ground = True
        self.previews[charid] = preview
        return preview

    def entity_box(self, e):
        preview = self.preview(e["charid"])
        width = preview.width if preview else 1.0
        height = preview.height if preview else 1.0
        return e["x"] - width / 2, e["y"] - height, width, height

    def entity_at(self, pos):
        px, py = self.level_point(pos)
        for e in reversed(self.entities):
            x, y, w, h = self.entity_box(e)
            if x <= px <= x + w and y <= py <= y + h:
                return e
        return None

    def snap_entity(self, pos):
        px, py = self.level_point(pos)
        return round(px * 2) / 2, float(math.floor(py) + 1)

    def draw_entity(self, target, e, foot_x, foot_y, scale):
        preview = self.preview(e["charid"])
        if isinstance(preview, CharacterEntity):
            draw_character(target, preview, foot_x, foot_y, scale)
        elif isinstance(preview, GameObject):
            draw_object(target, preview, foot_x, foot_y, scale)
        else:
            size = 30 * scale
            rect = pygame.Rect(foot_x - size / 2, foot_y - size, size, size)
            pygame.draw.rect(target, (200, 50, 200), rect)
            label = self.font_small.render(e["charid"], True, WHITE)
            target.blit(label, label.get_rect(center=rect.center))

    def entity_icon(self, charid):
        if charid not in self.entity_icons:
            icon = pygame.Surface((44, 44), pygame.SRCALPHA)
            preview = self.preview(charid)
            height_px = preview.height * 30 if preview else 30
            width_px = preview.width * 30 if preview else 30
            scale = min(1.0, 38 / max(height_px, width_px, 1))
            self.draw_entity(icon, {"charid": charid}, 22, 22 + height_px * scale / 2, scale)
            self.entity_icons[charid] = icon
        return self.entity_icons[charid]

    def make_tile_icon(self, ref, size):
        icon = pygame.Surface((size, size), pygame.SRCALPHA)
        k = size / 30.0
        if ref in invisible_refs or ref not in texture_cache:
            pygame.draw.rect(icon, (120, 120, 160), icon.get_rect(), border_radius=3)
            label = pygame.font.Font(FONT_PATH, 14).render(ref, True, WHITE)
            icon.blit(label, label.get_rect(center=icon.get_rect().center))
        elif ref in toggle_blocks:
            draw_svg_at(icon, toggle_blocks[ref]["on"], 0, 0, k)
        elif ref in lever_blocks:
            draw_rotated_svg(icon, lever_blocks[ref]["handle"], 15 * k, 30 * k, k, LEVER_ANGLE)
            draw_svg_at(icon, texture_cache[ref], 0, 0, k)
        else:
            bw, bh = block_sizes.get(ref, (1.0, 1.0))
            fit = 1.0 / max(bw, bh)
            surf = load_svg_surface(texture_cache[ref], max(1, int(size * bw * fit)), max(1, int(size * bh * fit)))
            icon.blit(surf, surf.get_rect(center=icon.get_rect().center))
        return icon

    def bg_view(self):
        if self.bg not in self.bg_views:
            path = f"/assets/backgrounds/bg{self.bg:04d}.png"
            view = load_bg_surface(path, self.screen_w, self.screen_h)
            fade = pygame.Surface(view.get_size())
            fade.fill(WHITE)
            fade.set_alpha(110)
            view.blit(fade, (0, 0))
            self.bg_views[self.bg] = view
        return self.bg_views[self.bg]

    def bg_thumb(self, bg_id):
        if bg_id not in self.bg_thumbs:
            self.bg_thumbs[bg_id] = load_bg_surface(f"/assets/backgrounds/bg{bg_id:04d}.png", 88, 50)
        return self.bg_thumbs[bg_id]

    def option_buttons(self):
        top = CONTENT_RECT.y + 8
        return [
            ("Copy String", pygame.Rect(673, top, 130, 30), True),
            ("Load String", pygame.Rect(813, top, 130, 30), True),
            ("Test Level", pygame.Rect(673, top + 40, 130, 30), True),
            ("Save Level", pygame.Rect(673, top + 80, 130, 30), True),
            ("Save Copy", pygame.Rect(813, top + 80, 130, 30), self.saved_title is not None),
            ("New Blank Level", pygame.Rect(673, top + 120, 270, 30), True),
            ("My Levels", pygame.Rect(673, top + 160, 270, 30), True),
            ("Share to Explore", pygame.Rect(673, top + 200, 270, 30), False),
        ]

    def info_buttons(self):
        top = CONTENT_RECT.y
        return [
            ("title", pygame.Rect(673, top + 32, 270, 30)),
            ("width-", pygame.Rect(773, top + 82, 30, 30)),
            ("width+", pygame.Rect(893, top + 82, 30, 30)),
            ("height-", pygame.Rect(773, top + 122, 30, 30)),
            ("height+", pygame.Rect(893, top + 122, 30, 30)),
        ]

    def palette_rects(self):
        items = []
        per_row = 7
        for i, ref in enumerate(self.palette):
            x = CONTENT_RECT.x + 8 + (i % per_row) * 40
            y = CONTENT_RECT.y + 4 + (i // per_row) * 40 - self.panel_scroll
            items.append((ref, pygame.Rect(x, y, 34, 34)))
        return items

    def entity_rects(self):
        items = []
        per_row = 5
        y = CONTENT_RECT.y + 22 - self.panel_scroll
        for group in (self.characters, self.objects):
            for i, charid in enumerate(group):
                x = CONTENT_RECT.x + 8 + (i % per_row) * 56
                items.append((charid, pygame.Rect(x, y + (i // per_row) * 52, 48, 48)))
            y += math.ceil(len(group) / per_row) * 52 + 24
        return items

    def bg_rects(self):
        items = []
        for i in range(backgroundproperties.BACKGROUND_COUNT):
            x = CONTENT_RECT.x + 4 + (i % 3) * 96
            y = CONTENT_RECT.y + 4 + (i // 3) * 58 - self.panel_scroll
            items.append((i, pygame.Rect(x, y, 90, 52)))
        return items

    def dialogue_rows(self):
        items = []
        for i, line in enumerate(self.dialogue):
            y = CONTENT_RECT.y + 4 + i * 32 - self.panel_scroll
            items.append((i, {
                "speaker": pygame.Rect(CONTENT_RECT.x + 4, y, 34, 28),
                "face": pygame.Rect(CONTENT_RECT.x + 40, y, 24, 28),
                "text": pygame.Rect(CONTENT_RECT.x + 66, y, 194, 28),
                "delete": pygame.Rect(CONTENT_RECT.x + 262, y, 26, 28),
            }))
        add_y = CONTENT_RECT.y + 4 + len(self.dialogue) * 32 - self.panel_scroll
        return items, pygame.Rect(CONTENT_RECT.x + 4, add_y, 284, 28)

    def my_level_rows(self):
        return [
            (i, chunk, pygame.Rect(CONTENT_RECT.x + 4, CONTENT_RECT.y + 36 + i * 32 - self.panel_scroll, 284, 28))
            for i, chunk in enumerate(self.read_my_levels())
        ]

    def next_speaker(self, speaker):
        options = [f"{i:02d}" for i in range(len(self.speaker_ids()))] + [NARRATOR]
        if speaker not in options:
            return options[0]
        return options[(options.index(speaker) + 1) % len(options)]

    def handle_event(self, event):
        if self.load_box is not None:
            return self.handle_load_box(event)
        if event.type == pygame.TEXTINPUT and self.editing:
            self.type_text(event.text)
            return None
        if event.type == pygame.KEYDOWN:
            return self.handle_key(event)
        if event.type == pygame.MOUSEWHEEL:
            self.handle_wheel(event)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            return self.handle_press(event.pos, event.button)
        if event.type == pygame.MOUSEMOTION:
            self.handle_drag(event.pos, event.buttons)
            return None
        if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.handle_release(event.pos)
        return None

    def edit_target_text(self):
        kind, index = self.editing
        if kind == "title":
            return self.title
        return self.dialogue[index]["text"]

    def set_edit_target_text(self, text):
        kind, index = self.editing
        if kind == "title":
            self.title = text
        else:
            self.dialogue[index]["text"] = text

    def type_text(self, text):
        self.set_edit_target_text(self.edit_target_text() + text)

    def handle_key(self, event):
        ctrl = event.mod & pygame.KMOD_CTRL
        if self.editing:
            if event.key == pygame.K_BACKSPACE:
                self.set_edit_target_text(self.edit_target_text()[:-1])
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                self.editing = None
            elif ctrl and event.key == pygame.K_v:
                try:
                    self.type_text((pygame.scrap.get_text() or "").replace("\n", " "))
                except Exception:
                    pass
            return None
        if ctrl and event.key == pygame.K_z:
            self.undo()
        elif ctrl and event.key == pygame.K_y:
            self.redo()
        elif ctrl and event.key == pygame.K_c:
            self.copy_selection()
        elif event.key == pygame.K_ESCAPE:
            if self.tool == "paste":
                self.tool = "select"
            self.selection = None
        return None

    def handle_wheel(self, event):
        mouse = pygame.mouse.get_pos()
        if CANVAS_RECT.collidepoint(mouse):
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL:
                before = self.level_point(mouse)
                self.tile_px = min(MAX_TILE_PX, max(MIN_TILE_PX, self.tile_px + event.y * 2))
                self.view_x = mouse[0] - before[0] * self.tile_px
                self.view_y = mouse[1] - before[1] * self.tile_px
            elif mods & pygame.KMOD_SHIFT:
                self.view_x += event.y * SCROLL_SPEED * 3
            else:
                self.view_y += event.y * SCROLL_SPEED * 3
                self.view_x -= event.x * SCROLL_SPEED * 3
            self.clamp_view()
        elif TAB_STRIP_RECT.collidepoint(mouse):
            self.scroll_tabs((event.x - event.y) * TAB_SCROLL_SPEED)
        elif PANEL_RECT.collidepoint(mouse):
            self.panel_scroll = max(0, self.panel_scroll - event.y * 30)

    def handle_press(self, pos, button):
        self.editing = None
        if EXIT_RECT.collidepoint(pos):
            return "exit"
        if TAB_STRIP_RECT.collidepoint(pos):
            for i, _ in enumerate(TABS):
                if self.tab_rect(i).collidepoint(pos):
                    self.select_tab(i)
            return None
        for i, name in enumerate(TOOLS):
            if tool_rect(i).collidepoint(pos):
                self.tool = name
                if name != "select":
                    self.selection = None
                return None
        for i, (name, _) in enumerate(ACTIONS):
            if action_rect(i).collidepoint(pos):
                if name == "copy":
                    self.copy_selection()
                elif name == "undo":
                    self.undo()
                elif name == "redo":
                    self.redo()
                elif name == "clear":
                    self.clear()
                return None
        if PANEL_RECT.collidepoint(pos):
            return self.handle_panel_click(pos, button)
        if CANVAS_RECT.collidepoint(pos):
            self.handle_canvas_press(pos, button)
        return None

    def handle_panel_click(self, pos, button):
        if not CONTENT_RECT.collidepoint(pos):
            return None
        if self.tab == 0:
            for name, rect in self.info_buttons():
                if not rect.collidepoint(pos):
                    continue
                step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                if name == "title":
                    self.push_undo()
                    self.editing = ("title", None)
                elif name == "width-":
                    self.resize(self.cols - step, self.rows)
                elif name == "width+":
                    self.resize(self.cols + step, self.rows)
                elif name == "height-":
                    self.resize(self.cols, self.rows - step)
                elif name == "height+":
                    self.resize(self.cols, self.rows + step)
        elif self.tab == 1:
            for charid, rect in self.entity_rects():
                if rect.collidepoint(pos):
                    self.selected_entity = charid
                    return None
            self.handle_placed_click(pos)
        elif self.tab == 2:
            for ref, rect in self.palette_rects():
                if rect.collidepoint(pos) and CONTENT_RECT.collidepoint(pos):
                    self.selected_tile = ref
                    if self.tool in ("eraser", "picker", "select", "row", "column", "paste"):
                        self.tool = "pencil"
        elif self.tab == 3:
            for bg_id, rect in self.bg_rects():
                if rect.collidepoint(pos) and CONTENT_RECT.collidepoint(pos) and bg_id != self.bg:
                    self.push_undo()
                    self.bg = bg_id
        elif self.tab == 4:
            rows, add_rect = self.dialogue_rows()
            for index, rects in rows:
                if rects["speaker"].collidepoint(pos):
                    self.push_undo()
                    self.dialogue[index]["speaker"] = self.next_speaker(self.dialogue[index]["speaker"])
                elif rects["face"].collidepoint(pos):
                    self.push_undo()
                    face = self.dialogue[index]["face"]
                    self.dialogue[index]["face"] = FACES[(FACES.index(face) + 1) % len(FACES)] if face in FACES else FACES[0]
                elif rects["text"].collidepoint(pos):
                    self.push_undo()
                    self.editing = ("dialogue", index)
                elif rects["delete"].collidepoint(pos):
                    self.push_undo()
                    del self.dialogue[index]
                    return None
            if add_rect.collidepoint(pos):
                self.push_undo()
                self.dialogue.append({"speaker": "00", "face": "S", "text": ""})
                self.editing = ("dialogue", len(self.dialogue) - 1)
        elif self.tab == 5:
            if self.show_my_levels:
                return self.handle_my_levels_click(pos)
            for label, rect, enabled in self.option_buttons():
                if rect.collidepoint(pos):
                    return self.run_option(label, enabled)
        return None

    def handle_my_levels_click(self, pos):
        if pygame.Rect(CONTENT_RECT.x + 4, CONTENT_RECT.y + 4, 90, 26).collidepoint(pos):
            self.show_my_levels = False
            self.panel_scroll = 0
            return None
        for _, chunk, rect in self.my_level_rows():
            if rect.collidepoint(pos) and CONTENT_RECT.collidepoint(pos):
                if self.load_string(chunk):
                    self.saved_title = self.title
                    self.notify("Loaded " + self.title)
                self.show_my_levels = False
                self.panel_scroll = 0
        return None

    def run_option(self, label, enabled):
        if not enabled:
            if label == "Share to Explore":
                self.notify("Explore isn't available yet")
            return None
        if label == "Copy String":
            self.copy_to_clipboard()
        elif label == "Load String":
            self.open_load_box()
        elif label == "Test Level":
            level = self.test_level()
            if level:
                return ("test", level)
        elif label == "Save Level":
            self.save_level()
        elif label == "Save Copy":
            self.save_level(as_copy=True)
        elif label == "New Blank Level":
            self.push_undo()
            self.new_level()
        elif label == "My Levels":
            self.show_my_levels = True
            self.panel_scroll = 0
        return None

    def handle_canvas_press(self, pos, button):
        col, row = self.tile_at(pos)
        if self.tab == 1:
            hit = self.entity_at(pos)
            if button == 3:
                if hit:
                    self.push_undo()
                    self.entities.remove(hit)
                    self.selected_index = None
                return
            self.push_undo()
            if hit:
                self.dragging_entity = hit
                self.selected_index = self.entities.index(hit)
            else:
                x, y = self.snap_entity(pos)
                if 0 <= x <= self.cols and 0 < y <= self.rows:
                    is_object = self.selected_entity in self.objects
                    entity = {"charid": self.selected_entity, "x": x, "y": y, "extra": OBJECT_STATE if is_object else PLAYER_STATE}
                    self.entities.append(entity)
                    self.dragging_entity = entity
                    self.selected_index = len(self.entities) - 1
            return

        if self.tool == "paste":
            if button == 3:
                self.tool = "select"
            elif self.stamp:
                self.push_undo()
                self.paste_stamp(col, row)
            return
        if self.tool in ("pencil", "eraser"):
            self.push_undo()
            char = "." if self.tool == "eraser" or button == 3 else self.selected_tile
            self.painting = (char, (col, row))
            self.set_tile(col, row, char)
        elif self.tool == "rect":
            self.drag_start = self.drag_end = (col, row)
            self.painting = ("." if button == 3 else self.selected_tile, None)
        elif self.tool == "fill":
            self.push_undo()
            self.flood_fill(col, row, "." if button == 3 else self.selected_tile)
        elif self.tool == "picker":
            if self.in_bounds(col, row) and self.grid[row][col] != ".":
                self.selected_tile = self.grid[row][col]
                self.tool = "pencil"
                self.select_tab(2)
        elif self.tool == "select":
            self.drag_start = self.drag_end = (col, row)
            self.selection = None
        elif self.tool == "row":
            self.push_undo()
            if button == 3:
                self.delete_row(row)
            else:
                self.insert_row(row)
        elif self.tool == "column":
            self.push_undo()
            if button == 3:
                self.delete_column(col)
            else:
                self.insert_column(col)

    def handle_drag(self, pos, buttons):
        if not (buttons[0] or buttons[2]):
            return
        col, row = self.tile_at(pos)
        if self.dragging_entity is not None:
            x, y = self.snap_entity(pos)
            self.dragging_entity["x"] = min(max(x, 0.0), float(self.cols))
            self.dragging_entity["y"] = min(max(y, 1.0), float(self.rows))
        elif self.tool in ("pencil", "eraser") and self.painting:
            char, last = self.painting
            self.paint_line(last, (col, row), char)
            self.painting = (char, (col, row))
        elif self.tool in ("rect", "select") and self.drag_start is not None:
            self.drag_end = (col, row)

    def handle_release(self, pos):
        if self.tool == "rect" and self.drag_start is not None and self.painting:
            self.push_undo()
            self.fill_rect(self.drag_start, self.drag_end, self.painting[0])
        elif self.tool == "select" and self.drag_start is not None:
            c0, r0, c1, r1 = self.rect_bounds(self.drag_start, self.drag_end)
            c0, r0 = max(c0, 0), max(r0, 0)
            c1, r1 = min(c1, self.cols - 1), min(r1, self.rows - 1)
            self.selection = (c0, r0, c1, r1) if c0 <= c1 and r0 <= r1 else None
        self.drag_start = None
        self.drag_end = None
        self.painting = None
        self.dragging_entity = None

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.editing:
            return
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_LEFT] or keys[pygame.K_a]) - (keys[pygame.K_RIGHT] or keys[pygame.K_d])
        dy = (keys[pygame.K_UP] or keys[pygame.K_w]) - (keys[pygame.K_DOWN] or keys[pygame.K_s])
        if dx or dy:
            self.view_x += dx * SCROLL_SPEED
            self.view_y += dy * SCROLL_SPEED
            self.clamp_view()

    def draw(self, screen, animation_tick):
        self.update()
        screen.fill(BG_COLOR)
        screen.blit(self.bg_view(), (0, 0))
        self.draw_canvas(screen, animation_tick)
        self.draw_bar(screen)
        self.draw_panel(screen)
        if self.load_box is not None:
            self.draw_load_box(screen)

    def draw_canvas(self, screen, animation_tick):
        screen.set_clip(CANVAS_RECT)
        t = self.tile_px
        draw_level(screen, self.grid, self.view_x, self.view_y, t, animation_tick, set(), None, [], {})
        for r_idx, row in enumerate(self.grid):
            for c_idx, char in enumerate(row):
                if char in invisible_refs:
                    icon = pygame.transform.smoothscale(self.palette_icons[char], (t, t))
                    icon.set_alpha(150)
                    screen.blit(icon, (self.view_x + c_idx * t, self.view_y + r_idx * t))

        level_rect = pygame.Rect(round(self.view_x), round(self.view_y), self.cols * t, self.rows * t)
        for c in range(self.cols + 1):
            x = round(self.view_x + c * t)
            pygame.draw.line(screen, GRID_COLOR, (x, level_rect.top), (x, level_rect.bottom))
        for r in range(self.rows + 1):
            y = round(self.view_y + r * t)
            pygame.draw.line(screen, GRID_COLOR, (level_rect.left, y), (level_rect.right, y))

        for e in self.entities:
            self.draw_entity(screen, e, self.view_x + e["x"] * t, self.view_y + e["y"] * t, t / 30.0)
            if self.tab == 1:
                x, y, w, h = self.entity_box(e)
                selected = e is self.selected_placed()
                pygame.draw.rect(screen, WHITE if selected else HIGHLIGHT, (self.view_x + x * t, self.view_y + y * t, w * t, h * t), 2 if selected else 1)
        if self.tab == 1 and self.selected_placed() is not None:
            self.draw_path_preview(screen, self.selected_placed())

        mouse = pygame.mouse.get_pos()
        if CANVAS_RECT.collidepoint(mouse):
            self.draw_cursor(screen, mouse)

        if self.drag_start is not None and self.drag_end is not None:
            c0, r0, c1, r1 = self.rect_bounds(self.drag_start, self.drag_end)
            self.draw_tile_box(screen, c0, r0, c1, r1, HIGHLIGHT if self.tool == "rect" else WHITE)
        elif self.selection:
            self.draw_tile_box(screen, *self.selection, WHITE)
        screen.set_clip(None)

    def draw_tile_box(self, screen, c0, r0, c1, r1, color):
        t = self.tile_px
        rect = pygame.Rect(round(self.view_x + c0 * t), round(self.view_y + r0 * t), (c1 - c0 + 1) * t, (r1 - r0 + 1) * t)
        pygame.draw.rect(screen, color, rect, 2)

    def draw_cursor(self, screen, mouse):
        t = self.tile_px
        col, row = self.tile_at(mouse)
        if self.tab == 1:
            if self.dragging_entity is None and self.entity_at(mouse) is None:
                x, y = self.snap_entity(mouse)
                ghost = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                self.draw_entity(ghost, {"charid": self.selected_entity}, self.view_x + x * t, self.view_y + y * t, t / 30.0)
                ghost.set_alpha(130)
                screen.blit(ghost, (0, 0))
            return
        if self.tool == "paste" and self.stamp:
            for dr, stamp_row in enumerate(self.stamp):
                for dc, char in enumerate(stamp_row):
                    if char != "." and char in self.palette_icons:
                        icon = pygame.transform.smoothscale(self.palette_icons[char], (t, t))
                        icon.set_alpha(150)
                        screen.blit(icon, (self.view_x + (col + dc) * t, self.view_y + (row + dr) * t))
            self.draw_tile_box(screen, col, row, col + len(self.stamp[0]) - 1, row + len(self.stamp) - 1, WHITE)
            return
        if self.tool == "row":
            y = round(self.view_y + row * t)
            pygame.draw.line(screen, HIGHLIGHT, (self.view_x, y), (self.view_x + self.cols * t, y), 3)
            return
        if self.tool == "column":
            x = round(self.view_x + col * t)
            pygame.draw.line(screen, HIGHLIGHT, (x, self.view_y), (x, self.view_y + self.rows * t), 3)
            return
        if self.tool in ("pencil", "rect", "fill") and self.selected_tile in self.palette_icons:
            icon = pygame.transform.smoothscale(self.palette_icons[self.selected_tile], (t, t))
            icon.set_alpha(140)
            screen.blit(icon, (self.view_x + col * t, self.view_y + row * t))
        self.draw_tile_box(screen, col, row, col, row, WHITE)

    def draw_button(self, screen, rect, label, enabled=True, font=None):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color = BUTTON_DISABLED if not enabled else (BUTTON_HOVER if hover else BUTTON_COLOR)
        pygame.draw.rect(screen, color, rect)
        text = (font or self.font_button).render(label, True, WHITE)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_bar(self, screen):
        pygame.draw.rect(screen, BAR_COLOR, BAR_RECT)
        for i, name in enumerate(TOOLS):
            rect = tool_rect(i)
            active = self.tool == name or (name == "select" and self.tool == "paste")
            pygame.draw.rect(screen, TOOL_SELECTED if active else BUTTON_COLOR, rect)
            screen.blit(self.tool_icons[i], rect)
        for i, (name, icon) in enumerate(ACTIONS):
            rect = action_rect(i)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(screen, BUTTON_HOVER if hover else BUTTON_COLOR, rect)
            screen.blit(self.tool_icons[icon], rect)

    def draw_panel(self, screen):
        pygame.draw.rect(screen, PANEL_COLOR, PANEL_RECT)
        pygame.draw.rect(screen, TAB_STRIP_COLOR, TAB_STRIP_RECT)
        screen.set_clip(TAB_STRIP_RECT)
        for i, name in enumerate(TABS):
            rect = self.tab_rect(i)
            selected = i == self.tab
            color = PANEL_COLOR if selected else TAB_COLORS[i % 2]
            pygame.draw.rect(screen, color, rect, border_top_left_radius=TAB_RADIUS, border_top_right_radius=TAB_RADIUS)
            label = self.font_tab.render(name, True, TAB_TEXT_SELECTED if selected else WHITE)
            screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery + 1)))
        screen.set_clip(None)
        if self.tab_scroll > 0:
            self.draw_tab_fade(screen, TAB_STRIP_RECT.left, 1)
        if self.tab_scroll < self.max_tab_scroll():
            self.draw_tab_fade(screen, TAB_STRIP_RECT.right - 18, -1)

        screen.set_clip(CONTENT_RECT)
        [self.draw_info, self.draw_entities_tab, self.draw_tiles_tab, self.draw_bg_tab, self.draw_dialogue_tab, self.draw_options_tab][self.tab](screen)
        screen.set_clip(None)

        pygame.draw.rect(screen, WHITE, EXIT_RECT, border_radius=6)
        exit_text = self.font_exit.render("EXIT", True, BG_COLOR)
        screen.blit(exit_text, exit_text.get_rect(center=EXIT_RECT.center))

        if self.message_timer > 0:
            text = self.font_small.render(self.message, True, (40, 40, 40))
            screen.blit(text, text.get_rect(midleft=(PANEL_RECT.x + 8, EXIT_RECT.centery)))

    def draw_tab_fade(self, screen, x, direction):
        for i in range(18):
            alpha = int(200 * (1 - i / 18)) if direction > 0 else int(200 * i / 18)
            strip = pygame.Surface((1, TAB_STRIP_RECT.height), pygame.SRCALPHA)
            strip.fill((*TAB_STRIP_COLOR, alpha))
            screen.blit(strip, (x + i, TAB_STRIP_RECT.y))

    def draw_label(self, screen, text, pos, color=(40, 40, 40), font=None):
        screen.blit((font or self.font_button).render(text, True, color), pos)

    def draw_text_field(self, screen, rect, text, active):
        pygame.draw.rect(screen, WHITE, rect)
        pygame.draw.rect(screen, HIGHLIGHT if active else BUTTON_COLOR, rect, 2)
        shown = text + ("|" if active and pygame.time.get_ticks() // 500 % 2 == 0 else "")
        surf = self.font_button.render(shown, True, (30, 30, 30))
        clip = screen.get_clip()
        screen.set_clip(rect.inflate(-6, 0).clip(clip))
        x = min(rect.x + 5, rect.right - 5 - surf.get_width()) if active else rect.x + 5
        screen.blit(surf, (x, rect.y + 4))
        screen.set_clip(clip)

    def draw_info(self, screen):
        top = CONTENT_RECT.y
        self.draw_label(screen, "Title", (673, top + 8))
        self.draw_text_field(screen, self.info_buttons()[0][1], self.title, self.editing == ("title", None))
        self.draw_label(screen, "Width", (673, top + 87))
        self.draw_label(screen, "Height", (673, top + 127))
        for name, rect in self.info_buttons()[1:]:
            self.draw_button(screen, rect, "-" if name.endswith("-") else "+")
        self.draw_label(screen, str(self.cols), (848 - self.font_button.size(str(self.cols))[0] // 2, top + 87))
        self.draw_label(screen, str(self.rows), (848 - self.font_button.size(str(self.rows))[0] // 2, top + 127))
        self.draw_label(screen, f"Characters / objects: {len(self.entities)}", (673, top + 172), font=self.font_small)
        self.draw_label(screen, f"Dialogue lines: {len(self.dialogue)}", (673, top + 192), font=self.font_small)
        self.draw_label(screen, "Shift + click resizes by 10", (673, top + 222), font=self.font_small)
        self.draw_label(screen, "WASD / arrows move the level", (673, top + 242), font=self.font_small)
        self.draw_label(screen, "Ctrl + wheel changes grid size", (673, top + 262), font=self.font_small)

    def draw_entities_tab(self, screen):
        rects = self.entity_rects()
        self.draw_label(screen, "Characters", (CONTENT_RECT.x + 8, CONTENT_RECT.y + 2 - self.panel_scroll), font=self.font_small)
        objects_top = min((rect.y for charid, rect in rects if charid in self.objects), default=CONTENT_RECT.y)
        self.draw_label(screen, "Objects", (CONTENT_RECT.x + 8, objects_top - 20), font=self.font_small)
        hover_name = None
        for charid, rect in rects:
            selected = charid == self.selected_entity
            pygame.draw.rect(screen, TOOL_SELECTED if selected else BUTTON_COLOR, rect)
            icon = self.entity_icon(charid)
            screen.blit(icon, icon.get_rect(center=rect.center))
            if selected:
                pygame.draw.rect(screen, HIGHLIGHT, rect, 2)
            if rect.collidepoint(pygame.mouse.get_pos()):
                hover_name = self.character_names.get(charid) or self.object_names.get(charid)
        objects_bottom = max(rect.bottom for _, rect in rects)
        name = hover_name or self.entity_name(self.selected_entity)
        self.draw_label(screen, "Placing: " + name, (CONTENT_RECT.x + 8, objects_bottom + 4), font=self.font_small)
        self.draw_placed_list(screen)

    def draw_tiles_tab(self, screen):
        names = {block["referential"]: block["blockname"] for block in blockproperties.block_sprites}
        hover_name = None
        for ref, rect in self.palette_rects():
            pygame.draw.rect(screen, TOOL_SELECTED if ref == self.selected_tile else BUTTON_COLOR, rect)
            screen.blit(self.palette_icons[ref], (rect.x + 2, rect.y + 2))
            if ref == self.selected_tile:
                pygame.draw.rect(screen, HIGHLIGHT, rect, 2)
            if rect.collidepoint(pygame.mouse.get_pos()):
                hover_name = names.get(ref)
        self.draw_label(screen, hover_name or names.get(self.selected_tile, ""), (CONTENT_RECT.x + 8, CONTENT_RECT.bottom - 22), font=self.font_small)

    def draw_bg_tab(self, screen):
        for bg_id, rect in self.bg_rects():
            screen.blit(self.bg_thumb(bg_id), (rect.x + 1, rect.y + 1))
            pygame.draw.rect(screen, HIGHLIGHT if bg_id == self.bg else BUTTON_COLOR, rect, 3 if bg_id == self.bg else 1)

    def draw_dialogue_tab(self, screen):
        rows, add_rect = self.dialogue_rows()
        speakers = self.speaker_ids()
        for index, rects in rows:
            line = self.dialogue[index]
            speaker = line["speaker"]
            slot = int(speaker) if speaker.isdigit() else -1
            if 0 <= slot < len(speakers):
                pygame.draw.rect(screen, BUTTON_COLOR, rects["speaker"])
                icon = character_portrait(speakers[slot], SPEAKER_ICON)
                screen.blit(icon, icon.get_rect(center=rects["speaker"].center))
            else:
                self.draw_button(screen, rects["speaker"], speaker, font=self.font_small)
            self.draw_button(screen, rects["face"], line["face"], font=self.font_small)
            self.draw_text_field(screen, rects["text"], line["text"], self.editing == ("dialogue", index))
            self.draw_button(screen, rects["delete"], "x", font=self.font_small)
        self.draw_button(screen, add_rect, "Add Line")

    def draw_options_tab(self, screen):
        if self.show_my_levels:
            self.draw_button(screen, pygame.Rect(CONTENT_RECT.x + 4, CONTENT_RECT.y + 4, 90, 26), "Back", font=self.font_small)
            rows = self.my_level_rows()
            if not rows:
                self.draw_label(screen, "No saved levels yet", (CONTENT_RECT.x + 8, CONTENT_RECT.y + 40), font=self.font_small)
            for _, chunk, rect in rows:
                self.draw_button(screen, rect, chunk.split("\n", 1)[0], font=self.font_small)
            return
        for label, rect, enabled in self.option_buttons():
            self.draw_button(screen, rect, label, enabled)
