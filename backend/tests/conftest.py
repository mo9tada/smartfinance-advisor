import os
import sys

# Tests import backend modules the same way the app does (backend/ on sys.path).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
