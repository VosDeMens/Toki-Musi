from enum import Enum


class Augmentation(str, Enum):
    LONG = "_"
    TRILL_UP = "^"
    TRILL_DOWN = "*"
    SLIDE_UP = "/"
    SLIDE_DOWN = "\\"
