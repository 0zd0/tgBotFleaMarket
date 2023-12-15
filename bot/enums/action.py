from enum import Enum


class Action(str, Enum):
    add = "add"
    back = "back"
    delete = "delete"
    edit = "edit"
    cancel = "cancel"
    confirm = "confirm"
    accept = "accept"
    block = "block"
    withdraw = "withdraw"
    toggle = "toggle"
    public = "public"
    skip = "skip"
    next = "next"
    prev = "prev"
