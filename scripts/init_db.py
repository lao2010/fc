import sys
sys.path.append('e:\\fc')  # Add project root to Python path
from models import db
from main import app  # Import Flask app instance directly

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset successfully")