"""
MILITARY COLLEGE OF SIGNALS (NUST)
CS-370 - Artificial Intelligence
Lab # 8: Games II - Alpha-Beta Pruning, Expectiminimax and TD Learning
Submitted To : Lec Shehla
Submitted By : GC HAMMAD LATIF (CMS ID: 534740)
Class        : BESE 30B
"""

# ==========================================================================
# Task 1 - Minimax vs Alpha-Beta Pruning Node Reduction in Tic-Tac-Toe
# ==========================================================================
import math

def winner(b):
    lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, c, d in lines:
        if b[a] == b[c] == b[d] != " ":
            return b[a]
    return None

def is_full(b):
    return " " not in b

nodes_minimax = 0
nodes_alphabeta = 0

def minimax_count(board, depth, is_max):
    global nodes_minimax
    nodes_minimax += 1
    win = winner(board)
    if win == "X": return 10 - depth
    if win == "O": return depth - 10
    if is_full(board): return 0

    scores = []
    for i in range(9):
        if board[i] == " ":
            board[i] = "X" if is_max else "O"
            scores.append(minimax_count(board, depth + 1, not is_max))
            board[i] = " "
    return max(scores) if is_max else min(scores)

def alphabeta_count(board, depth, alpha, beta, is_max):
    global nodes_alphabeta
    nodes_alphabeta += 1
    win = winner(board)
    if win == "X": return 10 - depth
    if win == "O": return depth - 10
    if is_full(board): return 0

    if is_max:
        v = -math.inf
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                v = max(v, alphabeta_count(board, depth + 1, alpha, beta, False))
                board[i] = " "
                alpha = max(alpha, v)
                if v >= beta:
                    break  # Beta cutoff
        return v
    else:
        v = math.inf
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                v = min(v, alphabeta_count(board, depth + 1, alpha, beta, True))
                board[i] = " "
                beta = min(beta, v)
                if v <= alpha:
                    break  # Alpha cutoff
        return v

empty_board = [" "] * 9
val_mm = minimax_count(empty_board, 0, True)
val_ab = alphabeta_count(empty_board, 0, -math.inf, math.inf, True)

reduction_pct = ((nodes_minimax - nodes_alphabeta) / nodes_minimax) * 100.0
speedup_factor = nodes_minimax / nodes_alphabeta

print("=== Search Tree Node Exploration: Empty Tic-Tac-Toe Board ===")
print(f"Minimax Nodes Explored   : {nodes_minimax:,}")
print(f"Alpha-Beta Nodes Explored: {nodes_alphabeta:,}")
print(f"Nodes Pruned             : {nodes_minimax - nodes_alphabeta:,}")
print(f"Search Space Reduction   : {reduction_pct:.2f}%")
print(f"Search Pruning Factor    : {speedup_factor:.2f}x speedup")
print(f"Game Value Equivalence   : Minimax={val_mm}, Alpha-Beta={val_ab} (Identical Draw)")

# ==========================================================================
# Task 2 - Expectiminimax Decision Function & Threshold Analysis for Dice Game
# ==========================================================================
DIE_FACES = [1, 2, 3, 4, 5, 6]

def expected_value_of_rolling(turn_total, depth=5):
    """
    Computes expected value of choosing ROLL, modeling subsequent CHANCE outcomes
    and downstream optimal MAX decisions up to a lookahead horizon of 'depth'.
    """
    if depth == 0:
        return float(turn_total)
    
    expected_val = 0.0
    p = 1.0 / 6.0
    for face in DIE_FACES:
        if face == 1:
            # Bust: turn ends immediately, accumulated turn score is lost
            expected_val += p * 0.0
        else:
            new_total = turn_total + face
            # CHANCE node resolves to player's optimal choice: bank (HOLD) or continue (ROLL)
            val_if_hold = float(new_total)
            val_if_roll = expected_value_of_rolling(new_total, depth - 1)
            expected_val += p * max(val_if_hold, val_if_roll)
    return expected_val

def decide(turn_total, depth=5):
    hold_val = float(turn_total)
    roll_val = expected_value_of_rolling(turn_total, depth=depth)
    decision = "ROLL" if roll_val > hold_val else "HOLD"
    return hold_val, roll_val, decision

print("=== Expectiminimax Decision Table (Turn Totals 0 to 25) ===")
print(f"{'Turn Total':>10} | {'E[HOLD]':>8} | {'E[ROLL]':>8} | {'Decision':>8} | {'Net Advantage':>14}")
print("-" * 58)
for t in [0, 5, 10, 15, 20, 25]:
    e_hold, e_roll, dec = decide(t)
    diff = e_roll - e_hold
    print(f"{t:>10d} | {e_hold:>8.2f} | {e_roll:>8.2f} | {dec:>8} | {diff:>+14.2f}")

print("\n=== Fine-Grained Threshold Boundary Analysis (18 to 22) ===")
for t in range(18, 23):
    e_hold, e_roll, dec = decide(t)
    diff = e_roll - e_hold
    print(f"Turn Total={t:2d} -> E[HOLD]={e_hold:5.2f}, E[ROLL]={e_roll:5.2f} => {dec} (Net: {diff:+.2f})")

# ==========================================================================
# Task 3 - TD(0) Temporal-Difference Learning on 4-State Random Walk
# ==========================================================================
import random

def td_random_walk(episodes, alpha=0.08, gamma=1.0, seed=42):
    """
    Simulates TD(0) value learning on a 4-state Markov random walk.
    Non-terminal states: 0, 1, 2, 3 (true values: 0.2, 0.4, 0.6, 0.8).
    Left terminal boundary (<0): reward 0.
    Right terminal boundary (>=4): reward 1.
    """
    random.seed(seed)
    n_states = 4
    V = [0.5] * n_states  # Unbiased initial estimate
    
    for _ in range(episodes):
        state = n_states // 2  # Start in middle state (state 2)
        while True:
            action = random.choice([-1, 1])  # Equal 0.5 probability left/right
            next_state = state + action
            
            if next_state < 0:
                reward, done, v_next = 0.0, True, 0.0
            elif next_state >= n_states:
                reward, done, v_next = 1.0, True, 0.0
            else:
                reward, done, v_next = 0.0, False, V[next_state]
            
            # TD(0) Bellman update
            td_target = reward + gamma * v_next
            td_error = td_target - V[state]
            V[state] += alpha * td_error
            
            if done:
                break
            state = next_state
    return [round(v, 4) for v in V]

td_results = {}
for ep in [10, 100, 1000]:
    td_results[ep] = td_random_walk(episodes=ep)

true_values = [0.2000, 0.4000, 0.6000, 0.8000]

print("=== TD(0) Random Walk Value Estimation Across Episodes ===")
print(f"{'State':<10} | {'True V*(s)':<10} | {'10 Episodes':<12} | {'100 Episodes':<12} | {'1000 Episodes':<14} | {'Final Abs Error':<15}")
print("-" * 84)
for i in range(4):
    v_10 = td_results[10][i]
    v_100 = td_results[100][i]
    v_1000 = td_results[1000][i]
    err = abs(v_1000 - true_values[i])
    print(f"State {i+1} (s={i}) | {true_values[i]:<10.4f} | {v_10:<12.4f} | {v_100:<12.4f} | {v_1000:<14.4f} | {err:<15.4f}")
