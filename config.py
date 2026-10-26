import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_canteen_super_enterprise_secret_2026')
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        db_user = os.environ.get('MYSQL_USER', 'root')
        db_password = os.environ.get('MYSQL_PASSWORD', '')
        db_host = os.environ.get('MYSQL_HOST', 'localhost')
        db_name = os.environ.get('MYSQL_DB', 'smart_canteen_db')
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:3306/{db_name}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
