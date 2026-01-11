import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Vercel environment variable before importing app
os.environ['VERCEL'] = '1'

from app import app as application

# Handler for Vercel
app = application
