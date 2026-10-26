import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_canteen_super_enterprise_secret_2026')
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Render postgres:// ya postgresql:// ko pg8000 driver format me convert karta hai
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+pg8000://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback to local SQLite if no cloud DB provided
        SQLALCHEMY_DATABASE_URI = 'sqlite:///canteen.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
