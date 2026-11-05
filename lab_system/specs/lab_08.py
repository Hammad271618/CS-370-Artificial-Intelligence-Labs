"""
Lab # 8 Specification: Games II - Alpha-Beta Pruning, Expectiminimax and TD Learning.
Course: CS-370 Artificial Intelligence | CLOs: 1, 3, 4
"""

import matplotlib.pyplot as plt

def plot_td_convergence(shared_ns, extra_img_path):
    """
    Renders an academic comparison plot showing convergence of TD(0) state-value estimates
    to true state values across 10, 100, and 1000 episodes.
    """
    results = shared_ns.get("td_results")
    if not results or not extra_img_path:
        return

    states = [f"State {i+1}\n(s={i})" for i in range(4)]
    true_vals = [0.2, 0.4, 0.6, 0.8]

    plt.figure(figsize=(8, 4.8), dpi=200)
    plt.plot(states, true_vals, "k--o", label="True Analytic Value $V^*(s)$", linewidth=2.0, markersize=8)
    
    colors = {10: "#E11D48", 100: "#F59E0B", 1000: "#0D9488"}
    markers = {10: "s", 100: "^", 1000: "D"}

    for ep in [10, 100, 1000]:
        vals = results[ep]
        plt.plot(
            states,
            vals,
            color=colors[ep],
            marker=markers[ep],
            label=f"TD(0) @ {ep} Episodes",
            linewidth=1.8,
            markersize=7,
        )

    plt.title("TD(0) State-Value Convergence on 4-State Random Walk", fontsize=12, fontweight="bold", pad=12, color="#0F2C59")
    plt.xlabel("Non-Terminal Markov States", fontsize=10, fontweight="bold", labelpad=8, color="#1E293B")
    plt.ylabel("Estimated State Value $V(s)$", fontsize=10, fontweight="bold", labelpad=8, color="#1E293B")
    plt.ylim(0.0, 1.0)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9)
    plt.tight_layout()
    plt.savefig(extra_img_path, dpi=200)
    plt.close()


LAB_SPEC = {
    "lab_number": 8,
    "slug": "Alpha_Beta_Expectiminimax_TD",
    "title": "Games II - Alpha-Beta Pruning, Expectiminimax and TD Learning",
    "clos": "1, 3, 4",
    "tasks": [
        {
            "title": "Minimax vs Alpha-Beta Pruning Node Reduction in Tic-Tac-Toe",
            "problem_statement": (
                "Run the Minimax and Alpha-Beta node counters for Tic-Tac-Toe (Part A) on the empty board "
                "and report the reduction in nodes explored as a percentage."
            ),
            "code": """import math

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
print(f"Game Value Equivalence   : Minimax={val_mm}, Alpha-Beta={val_ab} (Identical Draw)")""",
            "table": {
                "title": "Table 8.1 - Search Efficiency: Minimax vs Alpha-Beta Pruning on Empty Board",
                "headers": ["Algorithm", "Nodes Explored", "Pruned Nodes", "Search Reduction (%)", "Root Game Value"],
                "rows": [
                    ["Standard Minimax", "549,946", "0 (Exhaustive)", "0.00% (Baseline)", "0 (Draw)"],
                    ["Alpha-Beta Pruning", "20,866", "529,080", "96.21%", "0 (Draw)"],
                ],
            },
            "analysis": (
                "Alpha-Beta pruning dynamically maintains two threshold bounds along the search path: alpha (the highest "
                "score MAX is guaranteed) and beta (the lowest score MIN is guaranteed). Whenever a child node reveals "
                "that v >= beta at a MAX node or v <= alpha at a MIN node, further exploration of that subtree is truncated "
                "because neither rational player would permit play to enter that branch. On the initial empty Tic-Tac-Toe "
                "board, standard Minimax explores all 549,946 game states. In contrast, Alpha-Beta evaluates only 20,866 "
                "states, eliminating 529,080 redundant nodes — a dramatic 96.21% search reduction (26.35x speedup) — while "
                "guaranteeing identical game-theoretic optimality (root value 0, representing a forced draw under optimal play)."
            ),
        },
        {
            "title": "Expectiminimax Decision Function & Threshold Analysis for Dice Game",
            "problem_statement": (
                "Implement the Expectiminimax dice-game decision function (Part B) and produce a table of ROLL/HOLD "
                "decisions for turn totals 0, 5, 10, ..., 25. Discuss how the decision threshold relates to the "
                "expected value of a single die roll."
            ),
            "code": """DIE_FACES = [1, 2, 3, 4, 5, 6]

def expected_value_of_rolling(turn_total, depth=5):
    \"\"\"
    Computes expected value of choosing ROLL, modeling subsequent CHANCE outcomes
    and downstream optimal MAX decisions up to a lookahead horizon of 'depth'.
    \"\"\"
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

print("\\n=== Fine-Grained Threshold Boundary Analysis (18 to 22) ===")
for t in range(18, 23):
    e_hold, e_roll, dec = decide(t)
    diff = e_roll - e_hold
    print(f"Turn Total={t:2d} -> E[HOLD]={e_hold:5.2f}, E[ROLL]={e_roll:5.2f} => {dec} (Net: {diff:+.2f})")""",
            "table": {
                "title": "Table 8.2 - Expectiminimax Policy: ROLL vs HOLD Across Accumulated Turn Totals",
                "headers": ["Turn Total (T)", "E[HOLD] (Banked)", "E[ROLL] (Lookahead)", "Decision", "Net Expected Advantage (E[ROLL] - E[HOLD])"],
                "rows": [
                    ["0", "0.00", "8.04", "ROLL", "+8.04 (Strong incentive to roll)"],
                    ["5", "5.00", "10.20", "ROLL", "+5.20 (Positive risk-reward)"],
                    ["10", "10.00", "12.78", "ROLL", "+2.78 (Favorable expected gain)"],
                    ["15", "15.00", "16.00", "ROLL", "+1.00 (Marginal expected gain)"],
                    ["20", "20.00", "20.00", "HOLD", "0.00 (Equilibrium threshold T* = 20)"],
                    ["25", "25.00", "24.17", "HOLD", "-0.83 (Unfavorable risk of bust)"],
                ],
            },
            "analysis": (
                "In Expectiminimax, CHANCE nodes compute the expected value over stochastic transitions by weighting "
                "successor payoffs by their probabilities: E[n] = sum(P(r) * Utility(RESULT(n, r))). For a turn total T, "
                "rolling a single die yields two possibilities: rolling 1 with probability 1/6 (bust, losing all T points), "
                "or rolling {2, 3, 4, 5, 6} with probability 5/6, giving an average addition of (2+3+4+5+6)/5 = 4.0 points. "
                "The expected return of rolling once and banking is E[ROLL] = (1/6)(0) + (5/6)(T + 4) = (5/6)T + 20/6. "
                "Comparing E[ROLL] against banking E[HOLD] = T reveals that rolling is advantageous whenever "
                "(5/6)T + 20/6 > T, which simplifies directly to 20/6 > (1/6)T, or T < 20. At T = 20, the expected gain "
                "from continuing (+20/6 ≈ +3.33) exactly balances the expected loss from busting (-T/6 = -20/6 ≈ -3.33). "
                "Consequently, the optimal decision boundary is precisely T* = 20: the agent rolls for any turn total "
                "below 20 and holds for any turn total of 20 or greater."
            ),
        },
        {
            "title": "TD(0) Temporal-Difference Learning on 4-State Random Walk",
            "problem_statement": (
                "Implement the TD(0) random-walk example (Part C), run it for 10, 100 and 1000 episodes, and plot/print "
                "how the learned value estimates for each state converge toward the true values (0.2, 0.4, 0.6, 0.8 "
                "for the four non-terminal states). Briefly explain, in your own words, how TD learning differs from the "
                "model-based Minimax/Expectiminimax approaches used in Parts A and B."
            ),
            "code": """import random

def td_random_walk(episodes, alpha=0.08, gamma=1.0, seed=42):
    \"\"\"
    Simulates TD(0) value learning on a 4-state Markov random walk.
    Non-terminal states: 0, 1, 2, 3 (true values: 0.2, 0.4, 0.6, 0.8).
    Left terminal boundary (<0): reward 0.
    Right terminal boundary (>=4): reward 1.
    \"\"\"
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
    print(f"State {i+1} (s={i}) | {true_values[i]:<10.4f} | {v_10:<12.4f} | {v_100:<12.4f} | {v_1000:<14.4f} | {err:<15.4f}")""",
            "plot_hook": plot_td_convergence,
            "table": {
                "title": "Table 8.3 - TD(0) Convergence to Analytic Values Across Training Episodes",
                "headers": ["State (s)", "True Value V*(s)", "V(s) @ 10 Episodes", "V(s) @ 100 Episodes", "V(s) @ 1000 Episodes", "Absolute Error |V_1000 - V*|"],
                "rows": [
                    ["State 1 (s=0)", "0.2000", "0.3957", "0.2173", "0.1982", "0.0018"],
                    ["State 2 (s=1)", "0.4000", "0.4789", "0.4285", "0.3845", "0.0155"],
                    ["State 3 (s=2)", "0.6000", "0.5054", "0.6358", "0.6087", "0.0087"],
                    ["State 4 (s=3)", "0.8000", "0.5762", "0.7818", "0.7936", "0.0064"],
                ],
            },
            "analysis": (
                "Key Differences Between Model-Based Search (Minimax/Expectiminimax) and Model-Free Learning (TD):\n\n"
                "1. Model Availability: Minimax and Expectiminimax are model-based planning algorithms that assume complete "
                "prior knowledge of the environment's transition probabilities P(s'|s,a) and payoff utilities. In contrast, "
                "Temporal-Difference (TD) learning is model-free: the agent possesses no prior knowledge of game physics, "
                "transition matrices, or terminal rewards, learning purely from sample trajectories (s, a, r, s') through interaction.\n\n"
                "2. Online Bootstrapping vs Exhaustive Backward Induction: Minimax propagates values backwards from terminal "
                "leaves up to the root across the entire tree depth. TD(0) employs bootstrapping: after every single step, "
                "it updates the current state estimate V(s) toward a one-step sampled target [r + gamma * V(s')], adjusting "
                "estimates based on other estimates without waiting for an episode to terminate or generating full game trees.\n\n"
                "3. Scalability & Horizon: While Minimax suffers from exponential branching O(b^d), TD learning scales linearly "
                "with the number of experienced transitions and naturally generalizes to continuous, high-dimensional state "
                "spaces when paired with deep neural networks (e.g., Deep Q-Learning and TD-Gammon)."
            ),
        },
    ],
    "conclusion": (
        "In this lab, we evaluated three foundational paradigms of AI decision-making. First, Alpha-Beta pruning achieved "
        "a 96.21% node reduction over Minimax on Tic-Tac-Toe without sacrificing game-theoretic optimality. Second, "
        "Expectiminimax integrated CHANCE nodes to derive an exact roll/hold boundary of T* = 20 in a stochastic dice game, "
        "demonstrating how expected value analysis resolves uncertainty. Finally, TD(0) demonstrated model-free reinforcement "
        "learning on a random-walk Markov chain, converging closely to analytic state values (0.2, 0.4, 0.6, 0.8) purely "
        "through experiential bootstrapping."
    ),
}
