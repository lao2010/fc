from flask_sqlalchemy import SQLAlchemy

# Initialize db first
db = SQLAlchemy()

# Import User after db is initialized
from .user import User