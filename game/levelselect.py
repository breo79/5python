import math
import pygame
from pathlib import Path

FONT_PATH = "assets/ui/fonts/arial.ttf"
BG_PATH = "assets/ui/menu2.svg"
BORDER_PATH = "assets/ui/menu2border.svg"
BORDER_IMG_PATH = "assets/ui/menu2borderimg.png"
WT_PATH = "assets/blocks/b0012.svg"

GRID_COLS = 8
GRID_X = 42
GRID_Y = 157
CELL_W = 104
CELL_H = 43
STEP_X = 110.2
STEP_Y = 49.8
SCROLL_EDGE = 110
SCROLL_MAX_SPEED = 14

MAIN_SLOTS = 100
BONUS_SLOTS = 33
TOTAL_SLOTS = MAIN_SLOTS + BONUS_SLOTS

STATE_COLORS = {
    "green": (0, 200, 0),
    "yellow": (240, 230, 0),
    "reached": (255, 128, 0)
}
BUTTON_LOCKED = (90, 90, 90)


def lighten(color, amount=0.35):
    return tuple(round(c + (255 - c) * amount) for c in color)


def slot_label(index):
    if index < MAIN_SLOTS:
        return f"{index + 1:03d}"
    return f"B{index - MAIN_SLOTS + 1:02d}"


def make_font(size, bold=False):
    font = pygame.font.Font(FONT_PATH, size)
    font.set_bold(bold)
    return font


def render_outlined(font, text, color, outline, width=2):
    base = font.render(text, True, color)
    edge = font.render(text, True, outline)
    surface = pygame.Surface((base.get_width() + width * 2, base.get_height() + width * 2), pygame.SRCALPHA)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                surface.blit(edge, (dx + width, dy + width))
    surface.blit(base, (width, width))
    return surface


class LevelSelectMenu:
    def __init__(self, screen_size, load_svg_surface):
        self.width, self.height = screen_size
        self.scroll = 0.0

        self.background = load_svg_surface(BG_PATH, 960, 1620)
        self.overlay = self.build_overlay(load_svg_surface)
        self.wt_icon = load_svg_surface(WT_PATH, 68, 68)

        self.font_logo = make_font(118, bold=True)
        self.font_heading = make_font(50)
        self.font_stats = make_font(22)
        self.font_cell = make_font(42, bold=True)
        self.font_corner = make_font(30, bold=True)

        self.logo = self.font_logo.render("5b", True, (0, 0, 0))
        self.heading = [self.font_heading.render(line, True, (0, 0, 0)) for line in ("Level", "Select")]

        self.corner_buttons = []
        for i, label in enumerate(("QUAL", "MUTE", "BACK")):
            rect = pygame.Rect(589 + i * 118, 470, 102, 36)
            self.corner_buttons.append((label, rect, render_outlined(self.font_corner, label, (235, 235, 235), (130, 130, 130))))

    def build_overlay(self, load_svg_surface):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        full_path = Path(__file__).resolve().parent.parent / BORDER_IMG_PATH
        if full_path.exists():
            metal = pygame.image.load(str(full_path)).convert_alpha()
            overlay.blit(pygame.transform.smoothscale(metal, (self.width, self.height)), (0, 0))
        else:
            overlay.fill((150, 150, 150, 255))
        pygame.draw.rect(overlay, (0, 0, 0, 0), pygame.Rect(20, 20, 920, 500), border_radius=19)
        overlay.blit(load_svg_surface(BORDER_PATH, self.width, self.height), (0, 0))
        return overlay

    def content_height(self, level_count):
        rows = math.ceil(TOTAL_SLOTS / GRID_COLS)
        grid_bottom = GRID_Y + (rows - 1) * STEP_Y + CELL_H + 40
        return max(grid_bottom, self.background.get_height())

    def max_scroll(self, level_count):
        return max(0.0, self.content_height(level_count) - self.height)

    def cell_rect(self, index):
        col = index % GRID_COLS
        row = index // GRID_COLS
        return pygame.Rect(round(GRID_X + col * STEP_X), round(GRID_Y + row * STEP_Y - self.scroll), CELL_W, CELL_H)

    def level_at(self, pos, level_count, progress):
        if not pygame.Rect(20, 20, 920, 500).collidepoint(pos):
            return None
        for label, rect, _ in self.corner_buttons:
            if rect.collidepoint(pos):
                return None
        for i in range(level_count):
            if i in progress and self.cell_rect(i).collidepoint(pos):
                return i
        return None

    def update_scroll(self, level_count):
        if not pygame.mouse.get_focused():
            return
        mouse_y = pygame.mouse.get_pos()[1]
        if mouse_y < SCROLL_EDGE:
            speed = -SCROLL_MAX_SPEED * (SCROLL_EDGE - mouse_y) / SCROLL_EDGE
        elif mouse_y > self.height - SCROLL_EDGE:
            speed = SCROLL_MAX_SPEED * (mouse_y - (self.height - SCROLL_EDGE)) / SCROLL_EDGE
        else:
            return
        self.scroll = min(max(self.scroll + speed, 0.0), self.max_scroll(level_count))

    def handle_event(self, event, level_count, progress):
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for label, rect, _ in self.corner_buttons:
                if rect.collidepoint(event.pos):
                    return ("button", label)
            index = self.level_at(event.pos, level_count, progress)
            if index is not None:
                return ("level", index)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return ("button", "BACK")
        return None

    def draw(self, screen, level_titles, progress, wt_count=0, time_text="00:00:00.0", deaths=0):
        self.update_scroll(len(level_titles))
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 0))
        screen.blit(self.background, (0, -self.scroll))

        top = -self.scroll
        screen.blit(self.logo, (44, top + 32))
        screen.blit(self.heading[0], (212, top + 40))
        screen.blit(self.heading[1], (212, top + 88))
        screen.blit(self.wt_icon, (400, top + 36))
        screen.blit(self.font_heading.render(f"x {wt_count}", True, (0, 0, 0)), (480, top + 44))

        for i, (label, value) in enumerate((("Time:", time_text), ("Deaths:", str(deaths)))):
            label_surf = self.font_stats.render(label, True, (0, 0, 0))
            screen.blit(label_surf, label_surf.get_rect(topright=(754, top + 30 + i * 30)))
            screen.blit(self.font_stats.render(value, True, (0, 0, 0)), (770, top + 30 + i * 30))

        hovered = self.level_at(mouse_pos, len(level_titles), progress)
        for i in range(TOTAL_SLOTS):
            rect = self.cell_rect(i)
            if rect.bottom < 0 or rect.top > self.height:
                continue
            if i < len(level_titles) and i in progress:
                fill = STATE_COLORS[progress[i]]
                if i == hovered:
                    fill = lighten(fill)
            else:
                fill = BUTTON_LOCKED
            pygame.draw.rect(screen, fill, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            number = self.font_cell.render(slot_label(i), True, (0, 0, 0))
            screen.blit(number, number.get_rect(center=rect.center))

        screen.blit(self.overlay, (0, 0))

        for label, rect, text_surf in self.corner_buttons:
            alpha = 200 if rect.collidepoint(mouse_pos) else 150
            button = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(button, (255, 255, 255, alpha), button.get_rect(), border_radius=6)
            screen.blit(button, rect.topleft)
            screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        if hovered is not None:
            tip = self.font_stats.render(level_titles[hovered], True, (255, 255, 255))
            tip_bg = pygame.Surface((tip.get_width() + 16, tip.get_height() + 8), pygame.SRCALPHA)
            tip_bg.fill((0, 0, 0, 170))
            tip_pos = (min(mouse_pos[0] + 14, self.width - tip_bg.get_width() - 4), mouse_pos[1] + 18)
            screen.blit(tip_bg, tip_pos)
            screen.blit(tip, (tip_pos[0] + 8, tip_pos[1] + 4))
