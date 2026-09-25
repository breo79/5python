character_sprites = [
    {
        "charid": "0",
        "charname": "Ruby",
        "rubySprite_StillLimbless": "/assets/bodyparts/ruby/e0000.svg"
    },
    {
        "charid": "1",
        "charname": "Book",
        "bookSprite_StillLimbless": "/assets/bodyparts/book/e0001.svg"
    },
    {
        "charid": "2",
        "charname": "Ice Cube",
        "icecubeSprite_StillLimbless": "/assets/bodyparts/bubbster/e0002.svg"
    },
    {
        "charid": "3",
        "charname": "Match",
        "matchSprite_StillLimbless": "/assets/bodyparts/match/e0003.svg"
    },
    {
        "charid": "4",
        "charname": "Pencil",
        "pencilSprite_StillLimbless": "/assets/bodyparts/pencil/e0004.svg"
    },
    {
        "charid": "5",
        "charname": "Bubble",
        "bubbleSprite_StillLimbless": "/assets/bodyparts/bubbster/e0005.svg"
    },
    {
        "charid": "6",
        "charname": "Lego Brick",
        "brickSprite_StillLimbless": "/assets/bodyparts/asshole/e0006.svg"
    },
    {
        "charid": "7",
        "charname": "Waffle",
        "waffleSprite_StillLimbless": "/assets/bodyparts/waffle/e0007.svg"
    },
    {
        "charid": "8",
        "charname": "Tune",
        "tuneSprite_stillLimbless": "/assets/bodyparts/tune/e0008.svg",
        "tuneSprite_stillLimblessAlt1": "/assets/bodyparts/tune/bp0060.svg",
        "tuneSprite_StillLimblessAlt2": "/assets/bodyparts/tune/bp0061.svg"
    }
]
def get_limbless_sprite(charid):
    for entry in character_sprites:
        if entry["charid"] == charid:
            for key, value in entry.items():
                if "stilllimbless" in key.lower():
                    return value
    return None

leg_sprites = {
    "stand": {"path": "/assets/bodyparts/limbs/bp0006.svg", "size": (37, 66), "anchor": (19, 33)},
    "air": {"path": "/assets/bodyparts/limbs/bp0007.svg", "size": (44, 97), "anchor": (22.5, 47)},
    "walk": [
        {"path": f"/assets/bodyparts/limbs/bp{i:04d}.svg", "size": (64, 80), "anchor": (32, 39.8)}
        for i in range(8, 36)
    ],
}
LEG_LENGTH = 33

eye_sprite = {"path": "/assets/bodyparts/limbs/bp0000.svg", "size": (19, 44), "anchor": (9.7, 21.8)}
mouth_sprite = {"path": "/assets/bodyparts/limbs/bp0001.svg", "size": (57, 8), "anchor": (28.5, 4)}
arm_sprites = {
    "straight": {"path": "/assets/bodyparts/limbs/bp0002.svg", "size": (12, 74), "anchor": (6, 37)},
    "bent": {"path": "/assets/bodyparts/limbs/bp0003.svg", "size": (26, 76), "anchor": (13, 37)},
    "curled": {"path": "/assets/bodyparts/limbs/bp0041.svg", "size": (48, 72), "anchor": (24, 36)}
}

character_parts = {
    "1": {
        "eyes": [(66, 76), (108, 76)],
        "eye_scale": 1.3,
        "mouth": (86, 120),
        "arms": [(3, 110), (157, 110)],
        "arm_scale": 1.3,
        "arm_poses": {
            "stand": [
                {"sprite": "straight", "angle": -6, "front": True},
                {"sprite": "straight", "angle": 6, "front": True}
            ],
            "walk": [
                {"sprite": "curled", "angle": 45, "swing": -45, "front": True},
                {"sprite": "bent", "angle": 10, "swing": 100}
            ],
            "air": [
                {"sprite": "bent", "angle": -70, "front": True},
                {"sprite": "bent", "flip_x": True, "angle": 70, "front": True}
            ]
        },
        "hips": [(60, 174), (102, 174)]
    }
}

def get_character_parts(charid):
    return character_parts.get(charid, {})
