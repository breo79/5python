import pygame
from game.render import character_portrait

FONT_PATH = "assets/ui/fonts/arial.ttf"
BOX_PATH = "assets/ui/dialogue/dia.svg"

BOX_W = 500
BOX_H = 100
BOX_Y = 14
TEXT_X = 108
TEXT_Y = 8
TEXT_WIDTH = 370
FONT_SIZE = 19
LINE_HEIGHT = 21
EASE_FRAMES = 27
ICON_SIZE = 84
ICON_POS = (8, 8)


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def wrap_text(font, text, width):
    lines = []
    current = ""
    for word in text.split(" "):
        candidate = word if not current else current + " " + word
        if font.size(candidate)[0] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class DialogueBox:
    def __init__(self, screen_size, load_svg_surface):
        self.screen_w, self.screen_h = screen_size
        self.box = load_svg_surface(BOX_PATH, BOX_W, BOX_H)
        self.font = pygame.font.Font(FONT_PATH, FONT_SIZE)
        self.lines = []
        self.index = 0
        self.frame = 0
        self.rendered = []
        self.speakers = []
        self.icon = None

    @property
    def active(self):
        return self.index < len(self.lines)

    def start(self, lines, speakers=()):
        self.lines = list(lines)
        self.speakers = list(speakers)
        self.index = 0
        self.show_current()

    def advance(self):
        if not self.active:
            return
        self.index += 1
        self.show_current()

    def close(self):
        self.lines = []
        self.index = 0

    def show_current(self):
        self.frame = 0
        if self.active:
            line = self.lines[self.index]
            text = line["text"]
            speaker = int(line["speaker"]) if line["speaker"].isdigit() else -1
            self.icon = character_portrait(self.speakers[speaker], ICON_SIZE) if 0 <= speaker < len(self.speakers) else None
            self.rendered = [self.font.render(line, True, (0, 0, 0)) for line in wrap_text(self.font, text, TEXT_WIDTH)]

    def draw(self, screen):
        if not self.active:
            return
        t = ease_out_cubic(min(self.frame / EASE_FRAMES, 1.0))
        self.frame += 1

        panel = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
        panel.blit(self.box, (0, 0))
        if self.icon is not None:
            panel.blit(self.icon, ICON_POS)
        for i, line_surf in enumerate(self.rendered):
            panel.blit(line_surf, (TEXT_X, TEXT_Y + i * LINE_HEIGHT))
        center = (self.screen_w // 2, BOX_Y + BOX_H // 2)
        if t < 1.0:
            size = (max(1, round(BOX_W * t)), max(1, round(BOX_H * t)))
            panel = pygame.transform.smoothscale(panel, size)
        screen.blit(panel, panel.get_rect(center=center))
