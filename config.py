import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_canteen_super_enterprise_secret_2026')
    
    # Render se aane wali DATABASE_URL
    raw_db_url = os.environ.get('DATABASE_URL')
    
    if raw_db_url:
        # SQLAlchemy 2.0+ ke liye postgres:// ko standard postgresql:// banata hai
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        # Safe fallback
        SQLALCHEMY_DATABASE_URI = 'sqlite:///canteen.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
