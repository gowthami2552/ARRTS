"""
run_generate.py — Wrapper for generate_data.py with UTF-8 stdout to avoid Windows encoding issues.
"""
import sys
import io
import os

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import warnings
warnings.filterwarnings("ignore")

import generate_data
generate_data.main()
