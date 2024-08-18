from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def make_move(game, position, player):
    board = list(game.board)
