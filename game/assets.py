import re
import pygame
import resvg_py
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

loaded_tile_surfaces = {}
loaded_bg_surfaces = {}
loaded_char_surfaces = {}

def load_svg_surface(path, width, height):
    full_path = ROOT / path.lstrip("/")
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
    full_path = ROOT / path.lstrip("/")
    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            header = f.read(1000)
        match = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', header)
        if match and float(match.group(2)) > 0:
            size = (float(match.group(1)), float(match.group(2)))
    svg_size_cache[path] = size
    return size

def load_bg_surface(path, width, height):
    full_path = ROOT / path.lstrip("/")
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

svg_viewbox_cache = {}

def svg_viewbox(path):
    if path in svg_viewbox_cache:
        return svg_viewbox_cache[path]
    full_path = ROOT / path.lstrip("/")
    with open(full_path, "r", encoding="utf-8") as f:
        header = f.read(1000)
    match = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)', header)
    box = tuple(float(v) for v in match.groups()) if match else (0.0, 0.0, 30.0, 30.0)
    svg_viewbox_cache[path] = box
    return box

def get_part_surface(path, w, h):
    key = (path, w, h)
    if key not in loaded_char_surfaces:
        loaded_char_surfaces[key] = load_svg_surface(path, w, h)
    return loaded_char_surfaces[key]
