import os
import sys

# Ensure project root is in Python path for module resolution in serverless environments
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
