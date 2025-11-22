import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set the default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UCLYellowPages.settings')