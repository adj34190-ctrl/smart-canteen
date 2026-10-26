import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_canteen_super_enterprise_secret_2026')
    
    raw_db_url = os.environ.get('DATABASE_URL')
    
    if raw_db_url:
        # Render ke postgres:// ya postgresql:// ko exact psycopg driver format deta hai
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif raw_db_url.startswith("postgresql://"):
            raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///canteen.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
