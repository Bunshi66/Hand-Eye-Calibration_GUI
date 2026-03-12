import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LIBS_DIR = os.path.join(PROJECT_ROOT, 'libs')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')

if LIBS_DIR not in sys.path:
    sys.path.insert(0, LIBS_DIR)