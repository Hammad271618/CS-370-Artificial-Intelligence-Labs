"""
MILITARY COLLEGE OF SIGNALS (NUST)
CS-370 - Artificial Intelligence
Lab # 1: Introduction to Python and NumPy for AI Programming
Submitted To : Lec Shehla
Submitted By : GC HAMMAD LATIF (CMS ID: 534740)
Class        : BESE 30B
"""

# ==========================================================================
# Task 1 - Pure Python Statistics
# ==========================================================================
import math

def stats_pure(numbers):
    """Return (mean, median, std_dev) using only core Python."""
    n = len(numbers)
    mean = sum(numbers) / n
    sorted_nums = sorted(numbers)
    if n % 2 == 0:
        median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
    else:
        median = sorted_nums[n // 2]
    variance = sum((x - mean) ** 2 for x in numbers) / n
    std_dev = math.sqrt(variance)
    return mean, median, std_dev

sample_data = [12, 45, 23, 67, 34, 89, 56, 78, 90, 11, 43, 65, 32, 87, 54]
mean, median, std_dev = stats_pure(sample_data)
print(f"Data   : {sample_data}")
print(f"Mean   : {mean:.4f}")
print(f"Median : {median:.4f}")
print(f"Std Dev: {std_dev:.4f}")

# ==========================================================================
# Task 2 - NumPy Statistics and Timing Comparison
# ==========================================================================
import numpy as np
import time
import random

random.seed(42)
N = 1_000_000
large_data = [random.uniform(0, 100) for _ in range(N)]
large_arr  = np.array(large_data)

# Pure Python timing
t_start = time.perf_counter()
p_mean, p_median, p_std = stats_pure(large_data)
t_pure = time.perf_counter() - t_start

# NumPy timing
t_start = time.perf_counter()
n_mean   = np.mean(large_arr)
n_median = np.median(large_arr)
n_std    = np.std(large_arr)
t_numpy  = time.perf_counter() - t_start

speedup = t_pure / t_numpy
print(f"Pure Python  -> Mean: {p_mean:.2f}  Median: {p_median:.2f}  Std: {p_std:.2f}  Time: {t_pure:.6f} s")
print(f"NumPy        -> Mean: {n_mean:.2f}  Median: {n_median:.2f}  Std: {n_std:.2f}  Time: {t_numpy:.6f} s")
print(f"Speed-up factor: {speedup:.1f}x")

# ==========================================================================
# Task 3 - Simple Math/Logic Task: Matrix Calculator
# ==========================================================================
import numpy as np

def matrix_add(A, B):
    if A.shape != B.shape:
        return "Error: Matrices must have same dimensions for addition."
    return A + B

def matrix_sub(A, B):
    if A.shape != B.shape:
        return "Error: Matrices must have same dimensions for subtraction."
    return A - B

def matrix_mul(A, B):
    if A.shape[1] != B.shape[0]:
        return f"Error: Columns of A ({A.shape[1]}) must equal rows of B ({B.shape[0]})."
    return np.dot(A, B)

def matrix_transpose(A):
    return A.T

def matrix_det(A):
    if A.shape[0] != A.shape[1]:
        return "Error: Determinant requires a square matrix."
    return np.linalg.det(A)

# Demonstration on 2x2 matrices and dimension-mismatch validation
A = np.array([[2, 3], [1, 4]])
B = np.array([[5, 6], [7, 8]])
print("1. Addition:\n", matrix_add(A, B))
print("2. Subtraction:\n", matrix_sub(A, B))
print("3. Multiplication:\n", matrix_mul(A, B))
print("4. Transpose of A:\n", matrix_transpose(A))
print(f"5. Determinant of A: {matrix_det(A):.4f}")
print("Dimension mismatch test:", matrix_mul(np.array([[1, 2, 3]]), np.array([[1, 2]])))
