character_properties = [
    {
        "id": "0",
        "name": "Ruby",
        "width": "28",
        "height": "45.4",

        "weight": "0.81",
        "CarriedObjectHeight": "27",
        "friction": "0.8",
        "heatspeed": "1"
    },
    {
        "id": "1",
        "name": "Book",
        "width": "23",
        "height": "56",

        "weight": "0.36",
        "CarriedObjectHeight": "31",
        "friction": "0.8",
        "heatspeed": "1.7"
    },
    {
        "id": "2",
        "name": "Ice Cube",
        "width": "20",
        "height": "51",

        "weight": "0.41",
        "CarriedObjectHeight": "20",
        "friction": "0.85",
        "heatspeed": "5"
    },
    {
        "id": "3",
        "name": "Match",
        "width": "10",
        "height": "86",

        "weight": "0.26",
        "CarriedObjectHeight": "31",
        "friction": "0.8",
        "heatspeed": "1.6"
    },
    {
        "id": "3",
        "name": "Match",
        "width": "10",
        "height": "86",

        "weight": "0.26",
        "CarriedObjectHeight": "31",
        "friction": "0.8",
        "heatspeed": "1.6"
    },
    {
        "id": "4",
        "name": "Pencil",
        "width": "10",
        "height": "84",

        "weight": "0.23",
        "CarriedObjectHeight": "31",
        "friction": "0.8",
        "heatspeed": "1.4"
    },
    {
        "id": "5",
        "name": "Bubble",
        "width": "28",
        "height": "70",

        "weight": "0.075",
        "CarriedObjectHeight": "28",
        "friction": "0.8",
        "heatspeed": "9"
    },
    {
        "id": "6",
        "name": "Lego Brick",
        "width": "28",
        "height": "70",

        "weight": "0.2",
        "CarriedObjectHeight": "20",
        "friction": "0.75",
        "heatspeed": "0.6"
    },
    {
        "id": "7",
        "name": "Waffle",
        "width": "44",
        "height": "65",

        "weight": "0.8",
        "CarriedObjectHeight": "20",
        "friction": "0.8",
        "heatspeed": "0.8"
    },
    {
        "id": "8",
        "name": "Tune",
        "width": "16",
        "height": "56",

        "weight": "0.25",
        "CarriedObjectHeight": "17",
        "friction": "0.76",
        "heatspeed": "0.8"
    }
]

jumpheight_properties = [
    {
        "charid": "0",
        "jumpheight": "61.8"
    },
    {
        "charid": "1",
        "jumpheight": "95.4"
    },
    {
        "charid": "2",
        "jumpheight": "89.03219917"
    },
    {
        "charid": "3",
        "jumpheight": "113.2126592"
    },
    {
        "charid": "4",
        "jumpheight": "120.6654625"
    },
    {
        "charid": "5",
        "jumpheight": "215.4337514"
    },
    {
        "charid": "6",
        "jumpheight": "129.8359214"
    },
    {
        "charid": "7",
        "jumpheight": "62.2346791"
    },
    {
        "charid": "8",
        "jumpheight": "115.5"
    }
]
def get_character_properties(charid):
    for entry in character_properties:
        if entry["id"] == charid:
            return entry
    return None