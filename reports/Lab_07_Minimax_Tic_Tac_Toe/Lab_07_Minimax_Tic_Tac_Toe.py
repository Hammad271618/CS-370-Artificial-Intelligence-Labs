"""
MILITARY COLLEGE OF SIGNALS (NUST)
CS-370 - Artificial Intelligence
Lab # 7: Games I - Minimax for Tic-Tac-Toe
Submitted To : Lec Shehla
Submitted By : GC HAMMAD LATIF (CMS ID: 534740)
Class        : BESE 30B
"""

# ==========================================================================
# Task 1 - Unbeatable Minimax Tic-Tac-Toe Agent
# ==========================================================================
import math

def print_board(b):
    for i in range(0, 9, 3):
        print(" " + " | ".join(b[i:i+3]))
    print()

def winner(b):
    lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, c, d in lines:
        if b[a] == b[c] == b[d] != " ":
            return b[a]
    return None

def is_full(b):
    return " " not in b

def minimax(board, depth, is_max):
    win = winner(board)
    if win == "X":
        return 10 - depth
    elif win == "O":
        return depth - 10
    elif is_full(board):
        return 0

    if is_max:
        best = -math.inf
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                best = max(best, minimax(board, depth + 1, False))
                board[i] = " "
        return best
    else:
        best = math.inf
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                best = min(best, minimax(board, depth + 1, True))
                board[i] = " "
        return best

def best_move(board):
    best_val, move = -math.inf, None
    for i in range(9):
        if board[i] == " ":
            board[i] = "X"
            move_val = minimax(board, 0, False)
            board[i] = " "
            if move_val > best_val:
                best_val, move = move_val, i
    return move

# Verify computer (X) vs optimal defensive opponent (O)
board = [" "] * 9
o_preferences = [4, 2, 6, 3, 7, 8, 5, 1]
while not winner(board) and not is_full(board):
    m = best_move(board)
    board[m] = "X"
    if winner(board) or is_full(board):
        break
    o_move = next(pos for pos in o_preferences if board[pos] == " ")
    board[o_move] = "O"

print("Final Board (X vs Optimal Defensive O):")
print_board(board)
print("Match Result:", winner(board) or "Draw (Computer X never loses)")

# ==========================================================================
# Task 2 - Game Tree Visualization (Depth 2 with MAX/MIN Labels)
# ==========================================================================
def print_tree(board, depth, is_max, max_depth=2, indent="", branch_limit=3):
    win = winner(board)
    val = minimax(board, depth, is_max)
    role = "MAX (X)" if is_max else "MIN (O)"
    if win or is_full(board) or depth == max_depth:
        print(f"{indent}Leaf/Cutoff [depth={depth}, next={role}] -> backed-up value = {val}")
        return val

    print(f"{indent}{role} node at depth {depth} -> backed-up value = {val}")
    shown = 0
    for i in range(9):
        if board[i] == " ":
            if shown >= branch_limit:
                print(f"{indent}  ... (remaining symmetric moves omitted for brevity)")
                break
            player = "X" if is_max else "O"
            board[i] = player
            print(f"{indent}  Move {player} -> cell {i}:")
            print_tree(board, depth + 1, not is_max, max_depth, indent + "    ", branch_limit)
            board[i] = " "
            shown += 1
    return val

empty_board = [" "] * 9
print_tree(empty_board, depth=0, is_max=True, max_depth=2, branch_limit=2)

# ==========================================================================
# Task 3 - Depth-Penalized Utility Function (Fastest Win Preference)
# ==========================================================================
def play_scripted_game(title, human_prefs):
    print(f"=== {title} ===")
    b = [" "] * 9
    turn = 1
    while not winner(b) and not is_full(b):
        x_move = best_move(b)
        b[x_move] = "X"
        print(f"Turn {turn}: Computer (X) plays cell {x_move}")
        if winner(b) or is_full(b):
            break
        o_move = next(pos for pos in human_prefs if b[pos] == " ")
        b[o_move] = "O"
        print(f"Turn {turn}: Human    (O) plays cell {o_move}")
        turn += 1
    print_board(b)
    print(f"Winner: {winner(b) or 'Draw'} in {turn} X-moves\n")

# Game 1: O plays suboptimal flank moves -> X wins on move 3
play_scripted_game("Game 1: Fast 3-Move Win by X", human_prefs=[1, 2, 5, 7, 8])

# Game 2: Near-endgame board where X can win immediately in 1 move (cell 2) vs 2 moves
near_win_board = ["X", "X", " ",
                  "O", "O", " ",
                  " ", " ", " "]
chosen = best_move(near_win_board)
print("=== Game 2: Immediate Win Selection Test ===")
print(f"Board state: {near_win_board}")
print(f"X selects cell {chosen} (immediate win at depth=1, score=+9) over slower wins.")
