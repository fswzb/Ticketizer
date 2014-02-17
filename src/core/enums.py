# -*- coding: utf-8 -*-
class TrainType:
    NONE = 0
    OTHER = 1
    K = 2
    T = 4
    Z = 8
    D = 16
    G = 32
    ALL = 63

    FULL_NAME_LOOKUP = {
        K: "快速",
        T: "特快",
        Z: "直达",
        D: "动车",
        G: "高铁"
    }

    ABBREVIATION_LOOKUP = {
        K: "K",
        T: "T",
        Z: "Z",
        D: "D",
        G: "G"
    }

    REVERSE_ABBREVIATION_LOOKUP = {
        "K": K,
        "T": T,
        "Z": Z,
        "D": D,
        "G": G
    }


class TicketType:
    NONE = 0
    OTHER = 1
    NO_SEAT = 2
    HARD_SEAT = 4
    SOFT_SEAT = 8
    HARD_SLEEPER = 16
    SOFT_SLEEPER = 32
    SOFT_SLEEPER_PRO = 64
    SECOND_CLASS = 128
    FIRST_CLASS = 256
    SPECIAL = 512
    BUSINESS = 1024
    ALL = 2047

    FULL_NAME_LOOKUP = {
        OTHER:            "其他",
        NO_SEAT:          "无座",
        HARD_SEAT:        "硬座",
        SOFT_SEAT:        "软座",
        HARD_SLEEPER:     "硬卧",
        SOFT_SLEEPER:     "软卧",
        SOFT_SLEEPER_PRO: "高级软卧",
        SECOND_CLASS:     "二等座",
        FIRST_CLASS:      "一等座",
        SPECIAL:          "特等座",
        BUSINESS:         "商务座"
    }

    ABBREVIATION_LOOKUP = {
        OTHER:            "qt",
        NO_SEAT:          "wz",
        HARD_SEAT:        "yz",
        SOFT_SEAT:        "rz",
        HARD_SLEEPER:     "yw",
        SOFT_SLEEPER:     "rw",
        SOFT_SLEEPER_PRO: "gr",
        SECOND_CLASS:     "ze",
        FIRST_CLASS:      "zy",
        SPECIAL:          "tz",
        BUSINESS:         "swz"
    }

    REVERSE_ABBREVIATION_LOOKUP = {
        "qt":  OTHER,
        "wz":  NO_SEAT,
        "yz":  HARD_SEAT,
        "rz":  SOFT_SEAT,
        "yw":  HARD_SLEEPER,
        "rw":  SOFT_SLEEPER,
        "gr":  SOFT_SLEEPER_PRO,
        "ze":  SECOND_CLASS,
        "zy":  FIRST_CLASS,
        "tz":  SPECIAL,
        "swz": BUSINESS
    }

    ID_LOOKUP = {
        # OTHER:            "",
        NO_SEAT:          "W",
        HARD_SEAT:        "1",
        SOFT_SEAT:        "2",
        HARD_SLEEPER:     "3",
        SOFT_SLEEPER:     "4",
        SOFT_SLEEPER_PRO: "6",
        SECOND_CLASS:     "O",
        FIRST_CLASS:      "M",
        SPECIAL:          "P",
        BUSINESS:         "9"
    }

    REVERSE_ID_LOOKUP = {
        # "":  OTHER,
        "W": NO_SEAT,
        "1": HARD_SEAT,
        "2": SOFT_SEAT,
        "3": HARD_SLEEPER,
        "4": SOFT_SLEEPER,
        "6": SOFT_SLEEPER_PRO,
        "O": SECOND_CLASS,
        "M": FIRST_CLASS,
        "P": SPECIAL,
        "9": BUSINESS
    }

    REVERSE_ID2_LOOKUP = {
        # "MIN": OTHER,
        "WZ": NO_SEAT,
        "A1": HARD_SEAT,
        "A2": SOFT_SEAT,
        "A3": HARD_SLEEPER,
        "A4": SOFT_SLEEPER,
        "A6": SOFT_SLEEPER_PRO,
        "O":  SECOND_CLASS,
        "M":  FIRST_CLASS,
        "P":  SPECIAL,
        "A9": BUSINESS
    }


class TicketStatus:
    NOT_APPLICABLE = 0
    NOT_YET_SOLD = 1
    LARGE_COUNT = 2
    SOLD_OUT = 3
    NORMAL = 4

    TEXT_LOOKUP = {
        NOT_APPLICABLE: "--",
        NOT_YET_SOLD:   "*",
        LARGE_COUNT:    "有",
        SOLD_OUT:       "无"
    }

    REVERSE_TEXT_LOOKUP = {
        "--": NOT_APPLICABLE,
        "*":  NOT_YET_SOLD,
        "有": LARGE_COUNT,
        "无": SOLD_OUT
    }


class TicketPricing:
    NORMAL = "ADULT"
    STUDENT = "0X00"


class TicketDirection:
    ONE_WAY = "dc"
    ROUND_TRIP = "fc"


class IdentificationType:
    SECOND_GEN_ID = "1"
    FIRST_GEN_ID = "2"
    HONGKONG_MACAU = "C"
    TAIWAN = "G"
    PASSPORT = "B"

    TEXT_LOOKUP = {
        SECOND_GEN_ID:  "二代身份证",
        FIRST_GEN_ID:   "一代身份证",
        HONGKONG_MACAU: "港澳通行证",
        TAIWAN:         "台湾通行证",
        PASSPORT:       "护照"
    }


class PassengerType:
    ADULT = "1"
    CHILD = "2"
    STUDENT = "3"
    DISABLED = "4"

    TEXT_LOOKUP = {
        ADULT: "成人",
        CHILD: "儿童",
        STUDENT: "学生",
        DISABLED: "残疾军人"
    }


class Gender:
    MALE = "M"
    FEMALE = "F"

    TEXT_LOOKUP = {
        MALE: "男",
        FEMALE: "女"
    }