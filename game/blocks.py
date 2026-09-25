from data import blockproperties
from game.assets import ROOT

texture_cache = {}
invisible_refs = set()
animated_blocks = {}
for block in blockproperties.block_sprites:
    if not block.get("blocktexture"):
        invisible_refs.add(block["referential"])
        continue
    texture_cache[block["referential"]] = block["blocktexture"]
    if block.get("blockanimation"):
        frame_dir = ROOT / block["blockanimation"].lstrip("/")
        frames = sorted(frame_dir.glob("*.svg")) if frame_dir.is_dir() else []
        if frames:
            animated_blocks[block["referential"]] = [
                block["blockanimation"].rstrip("/") + "/" + frame.name for frame in frames
            ]

SIDE_TOP, SIDE_BOTTOM, SIDE_LEFT, SIDE_RIGHT = 0, 1, 2, 3
SOLID_CODES = {"1", "5"}

block_sides = {
    block["referential"]: (block.get("CollisionDataFourSided", "2222") + "2222")[:4]
    for block in blockproperties.block_sprites
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

CONVEYOR_SPEED = 7.2 / 60.0

conveyor_speeds = {}
for block in blockproperties.block_sprites:
    if block.get("blockname") == "ConveyorLeft":
        conveyor_speeds[block["referential"]] = -CONVEYOR_SPEED
    elif block.get("blockname") == "ConveyorRight":
        conveyor_speeds[block["referential"]] = CONVEYOR_SPEED

SPRING_BOOST_TILES = 7.5

spring_refs = {
    block["referential"]
    for block in blockproperties.block_sprites
    if block.get("blockname") == "PurpleSpringy"
}

toggle_blocks = {
    block["referential"]: {
        "group": block["togglegroup"],
        "starts_on": str(block.get("startson", "true")).lower() == "true",
        "on": block["blocktexture"],
        "off": block.get("blocktextureoff", block["blocktexture"]),
    }
    for block in blockproperties.block_sprites
    if block.get("togglegroup") and not block.get("leverhandle")
}

lever_blocks = {
    block["referential"]: {"group": block["togglegroup"], "handle": block["leverhandle"]}
    for block in blockproperties.block_sprites
    if block.get("leverhandle")
}

toggle_state = {}

def reset_toggles():
    toggle_state.clear()

def push_lever(group, direction):
    toggle_state[group] = direction > 0

def toggle_block_on(char):
    info = toggle_blocks[char]
    return info["starts_on"] != toggle_state.get(info["group"], False)

def sides_of(char):
    if char in toggle_blocks and not toggle_block_on(char):
        return "2222"
    return block_sides.get(char, "2222")

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
