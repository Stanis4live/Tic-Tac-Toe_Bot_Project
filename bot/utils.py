from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_keyboard(game):
    board = game.board
    size = game.board_size
    buttons = [
        InlineKeyboardButton(board[i], callback_data=str(i))
        if board[i] == ' '
        else InlineKeyboardButton(board[i], callback_data='ignore')
        for i in range(size ** 2)
    ]
    keyboard = [buttons[i:i + size] for i in range(0, size ** 2, size)]
    return InlineKeyboardMarkup(keyboard)

def check_winner(board, size):
    winning_combinations = []

    for i in range(size):
        horizontal = [i * size + j for j in range(size)]
        vertical = [i + j * size for j in range(size)]
        winning_combinations.append(horizontal)
        winning_combinations.append(vertical)

    diagonal1 = [i * (size + 1) for i in range(size)]
    diagonal2 = [(i + 1) * (size - 1) for i in range(size)]
    winning_combinations.append(diagonal1)
    winning_combinations.append(diagonal2)

    for combination in winning_combinations:
        if all(board[i] == board[combination[0]] and board[i] != ' ' for i in combination):
            return board[combination[0]]
    return None


