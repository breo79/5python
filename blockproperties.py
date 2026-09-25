block_sprites = [
    {
        "blockid": "0",
        "blockname": "RedTile",
        "referential": "/",
        "blocktexture": "/assets/blocks/b0001.svg",
        # 1 for solid, 2 for no collision, 3 for directionally solid platform, 4 for WinToken_Collectible slot info:
        # first slot: top, second slot: bottom, 3rd slot: left, 4th slot: right
        "CollisionDataFourSided": "1111"
    },
    {
        "blockid": "1",
        "blockname": "RedBgTile",
        "referential": "7",
        "blocktexture": "/assets/blocks/b0009.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "2",
        "blockname": "GreenTile",
        "referential": "8",
        "blocktexture": "/assets/blocks/b0010.svg",
        "CollisionDataFourSided": "1111"
    },
    {
        "blockid": "3",
        "blockname": "GreenBgTile",
        "referential": "9",
        "blocktexture": "/assets/blocks/b0011.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "4",
        "blockname": "WinToken",
        "referential": ":",
        "blocktexture": "/assets/blocks/b0012.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "5",
        "blockname": "Conveyor",
        "referential": "Z",
        # Multiple SVGS would be here, since the block is animated, but i dont feel like it rn
        "blocktexture": "/assets/blocks/b0014f0000.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "6",
        "blockname": "poop",
        "referential": "6",
        "blocktexture": "/assets/blocks/b0009.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "7",
        "blockname": "poop again",
        "referential": "4",
        "blocktexture": "/assets/blocks/b0009.svg",
        "CollisionDataFourSided": "2222"
    },
    {
        "blockid": "8",
        "blockname": "battle for poop island again",
        "referential": "5",
        "blocktexture": "/assets/blocks/b0009.svg",
        "CollisionDataFourSided": "2222"
    }
]