import re
from pathlib import Path
from data import blockproperties
from data import backgroundproperties


DIALOGUE_LINE = re.compile(r"^(\d{2})([A-Z]) ?(.*)$")


def parse_dialogue(dialogue_lines):
    parsed = []
    for line in dialogue_lines:
        match = DIALOGUE_LINE.match(line)
        if match:
            parsed.append({"speaker": match.group(1), "face": match.group(2), "text": match.group(3).strip()})
    return parsed

def parse_entities(entity_lines):
    spawns = []
    for line in entity_lines:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        try:
            charid = str(int(parts[0]))
            x = float(parts[1])
            y = float(parts[2])
        except ValueError:
            continue
        extra = parts[3].strip() if len(parts) > 3 else None
        spawns.append({"charid": charid, "x": x, "y": y, "extra": extra})
    return spawns

def parse_level():
    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / "assets" / "leveldata" / "levels.txt"

    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        lines = [line.rstrip('\r\n') for line in file.readlines()]

    known_refs = {block["referential"] for block in blockproperties.block_sprites}
    known_refs.add(".")

    valid_levels = []
    i = 0
    if lines and lines[0].startswith("loadedLevels="):
        i = 1

    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        title = lines[i]
        i += 1
        if i >= len(lines):
            break

        header = lines[i]
        i += 1
        
        parts = header.split(',')
        try:
            width = int(parts[0])
            height = int(parts[1])
            bg_id = int(parts[3])
        except (ValueError, IndexError):
            width = 32
            height = 18
            bg_id = 0

        grid_rows = []
        for _ in range(height):
            if i < len(lines):
                row_str = lines[i][:width].ljust(width, '.')
                grid_rows.append("".join(char if char in known_refs else "." for char in row_str))
                i += 1
            else:
                grid_rows.append("." * width)

        entities = []
        dialogue = []
        while i < len(lines):
            line = lines[i]
            if line.startswith("0000") or line == "000000":
                i += 1
                break
            elif DIALOGUE_LINE.match(line):
                dialogue.append(line)
            elif "," in line:
                entities.append(line)
            i += 1

        bg_asset = None
        for bg in backgroundproperties.backgrounds:
            if int(bg["bgid"]) == bg_id:
                bg_asset = bg["bgasset"]
                break

        valid_levels.append({
            "title": title,
            "header": header,
            "grid": grid_rows,
            "entities": entities,
            "spawns": parse_entities(entities),
            "bg_asset": bg_asset,
            "dialogue": dialogue,
            "lines": parse_dialogue(dialogue)
        })

    return valid_levels