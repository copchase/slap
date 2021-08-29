import random

positive = [
    "POGGERS",
    "oddonePOG"
]

negative = [
    "Pepega",
    "POOGERS",
    "FeelsTastyMan",
    "OMEGALUL",
    "LUL",
    "oddoneLOL",
    "PepeLaugh",
    "HanVetInte",
    "ElNoKaga"
]


def get_positive_emote() -> str:
    return random.choice(positive)


def get_negative_emote() -> str:
    return random.choice(negative)
