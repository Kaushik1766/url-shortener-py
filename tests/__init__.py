import os
import sys

# Ensure project root is ahead of the test package so imports resolve to the real app package.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)
