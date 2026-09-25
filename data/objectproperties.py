object_properties = [
    {
        "entityid": "37",
        "objectname": "Wooden Crate",
        "objecttexture": "/assets/objects/e0037.svg",
        # in px
        "height": "40",
        "width": "40",
        "weight": "0.15",
        "pickupable": "true",
        "throwdistance": "6.3"
    },
    {
        "entityid": "38",
        "objectname": "Metal Crate",
        "objecttexture": "/assets/objects/e0038.svg",
        "height": "50",
        "width": "50",
        "weight": "0.64",
        "pickupable": "true",
        "throwdistance": "3.7"
    },
    {
        # height and width from https://docs.google.com/spreadsheets/d/1Whn9yQSWKMqXINDLlb5AsDGY6wgWlofueCXl3FjFqZ0/edit?gid=0#gid=0
        "entityid": "41",
        "objectname": "Half Box",
        "objecttexture": "/assets/objects/e0041.svg",
        "height": "29",
        "width": "25",
        "throwdistance": "2.5",
        "pickupable": "true"
    },
    {
        "entityid": "46",
        "objectname": "Spike Ball",
        "objecttexture": "/assets/objects/e0046.svg",
        "height": "50",
        "width": "50",
        "sides": "5555"
    },
    {
        "entityid": "44",
        "objectname": "Purple Facer",
        "objecttexture": "/assets/objects/e0044.svg",
        "height": "45",
        "width": "45",
        "sides": "5555"
    }
]

def get_object_properties(entityid):
    for entry in object_properties:
        if entry.get("entityid") == entityid:
            return entry
    return None