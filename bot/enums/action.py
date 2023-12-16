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
    select = "select"
    public = "public"
    skip = "skip"
    next = "next"
    prev = "prev"
    duplicate = "duplicate"
