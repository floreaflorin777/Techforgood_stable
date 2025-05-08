import sys
import os

# Add your project directory to the Python path
path = '/home/florinm12/tech-for-good1'  # Adjust this to your actual project path
if path not in sys.path:
    sys.path.append(path)

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run() 