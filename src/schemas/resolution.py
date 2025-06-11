from enum import Enum


class ResolutionEnum(int, Enum):
    one_hundred = 100
    one_thousand = 1000
    ten_thousand = 10000
    hundred_thousand = 100000


RESOLUTION_ID_PREFIX = {
    100: "100mN",
    1000: "1kmN",
    10000: "10kmN",
    100000: "100kmN"
}

RESOLUTION_ID_SUFFIX_LENGTH = {
    100: 5,
    1000: 4,
    10000: 3,
    100000: 2
}
