block_sprites = [
    {
        "blockid": "0",
        "blockname": "RedTile",
        "referential": "/",
        "blocktexture": "/assets/blocks/b0001.svg",
        # 1 for solid, 2 for no collision, 3 for directionally solid platform, 4 for WinToken_Collectible slot info:
        # first slot: top, second slot: bottom, 3rd slot: left, 4th slot: right
        "CollisionDataFourSided": "1111",
        # Block size is in tiles
        "BlockSize": "1"
    },
    {
        "blockid": "1",
        "blockname": "RedBgTile",
        "referential": "7",
        "blocktexture": "/assets/blocks/b0009.svg",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "2",
        "blockname": "GreenTile",
        "referential": "8",
        "blocktexture": "/assets/blocks/b0010.svg",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "3",
        "blockname": "GreenBgTile",
        "referential": "9",
        "blocktexture": "/assets/blocks/b0011.svg",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "4",
        "blockname": "WinToken",
        "referential": ":",
        "blocktexture": "/assets/blocks/b0012.svg",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "5",
        "blockname": "ConveyorLeft",
        "referential": "<",
        "blocktexture": "/assets/blocks/b0014f0000.svg",
        "blockanimation": "/assets/blocks/conveyor",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "6",
        "blockname": "DBlock",
        "referential": "6",
        "blocktexture": "",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "7",
        "blockname": "EndingDoor",
        "referential": "4",
        "blocktexture": "/assets/blocks/door_end.svg",
        "CollisionDataFourSided": "2222",
        "BlockSizeXY": "2,4"
    },
    {
        "blockid": "8",
        "blockname": "ETree",
        "referential": "5",
        "blocktexture": "/assets/blocks/tree_e/b0007f0000.svg",
        "blockanimation": "/assets/blocks/tree_e",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "9",
        "blockname": "SemiWhitePlatform",
        "referential": "@",
        "blocktexture": "/assets/blocks/b0018.svg",
        "CollisionDataFourSided": "3222",
    },
    {
        "blockid": "10",
        "blockname": "SpikeTop",
        "referential": "1",
        "blocktexture": "/assets/blocks/b0020.svg",
        # New property: 5 (Deadly Side)
        "CollisionDataFourSided": "5111",
    },
    {
        "blockid": "11",
        "blockname": "PurpleBlock",
        "referential": "w",
        "blocktexture": "/assets/blocks/b0073.svg",
        "CollisionDataFourSided": "1111",
    },
    {
        "blockid": "12",
        "blockname": "PurpleBgBlock",
        "referential": "{",
        "blocktexture": "/assets/blocks/b0077.svg",
        "CollisionDataFourSided": "2222",
    },
    {
        "blockid": "13",
        "blockname": "SpikeBottom",
        "referential": "A",
        "blocktexture": "/assets/blocks/b0019.svg",
        "CollisionDataFourSided": "1511",
    },
        {
        "blockid": "14",
        "blockname": "PipelikeBlock",
        "referential": "F",
        "blocktexture": "/assets/blocks/b0024.svg",
        "CollisionDataFourSided": "2222",
    },
    {
        "blockid": "15",
        "blockname": "SpikeDecoPipe",
        "referential": "E",
        "blocktexture": "/assets/blocks/b0023.svg",
        "CollisionDataFourSided": "1511",
    },
    {
        "blockid": "16",
        "blockname": "VTree",
        "referential": "$",
        "blocktexture": "/assets/blocks/tree_v/b0059f0000.svg",
        "blockanimation": "/assets/blocks/tree_v",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
    {
        "blockid": "17",
        "blockname": "ConveyorRight",
        "referential": ">",
        "blocktexture": "/assets/blocks/cv_r/b0016f0000.svg",
        "blockanimation": "/assets/blocks/conveyor/cv_r",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "18",
        "blockname": "PurpleSpringy",
        "referential": ";",
        "blocktexture": "/assets/blocks/spring/b0013f0000.svg",
        "blockanimation": "/assets/blocks/spring",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "19",
        "blockname": "DecourRockBottom1",
        "referential": "X",
        "blocktexture": "/assets/blocks/b0042.svg",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "20",
        "blockname": "DecourRockBottom2",
        "referential": "Y",
        "blocktexture": "/assets/blocks/b0044.svg",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "21",
        "blockname": "DecourDirtBlack",
        "referential": "^",
        "blocktexture": "/assets/blocks/b0048.svg",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "22",
        "blockname": "YellowToggleBlock",
        "referential": "M",
        "blocktexture": "/assets/blocks/yellow_toggleables/1/yellow_on.svg",
        "blocktextureoff": "/assets/blocks/yellow_toggleables/1/yellow_off.svg",
        "togglegroup": "yellow",
        "startson": "true",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "23",
        "blockname": "YellowToggleBlockDark",
        "referential": "N",
        "blocktexture": "/assets/blocks/yellow_toggleables/2/darky_on.svg",
        "blocktextureoff": "/assets/blocks/yellow_toggleables/2/darky_off.svg",
        "togglegroup": "yellow",
        "startson": "false",
        "CollisionDataFourSided": "1111",
        "BlockSize": "1"
    },
    {
        "blockid": "24",
        "blockname": "YellowLever",
        "referential": "Q",
        "blocktexture": "/assets/blocks/yellow_toggleables/yellow_switch/b0035leverbase.svg",
        "leverhandle": "/assets/blocks/yellow_toggleables/yellow_switch/b00leverhandle.svg",
        "togglegroup": "yellow",
        "CollisionDataFourSided": "2222",
        "BlockSize": "1"
    },
]