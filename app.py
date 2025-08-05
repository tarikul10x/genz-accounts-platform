import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern to prevent database loops"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration with better error handling
    database_url = os.environ.get("DATABASE_URL", "sqlite:///genZ_accounts.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Import models to ensure they're registered before table creation
    with app.app_context():
        try:
            import models
            logger.info("Models imported successfully")
        except Exception as e:
            logger.error(f"Failed to import models: {e}")
            raise
    
    # Register blueprints
    with app.app_context():
        try:
            from routes import main_bp, admin_bp, user_bp, auth_bp
            app.register_blueprint(main_bp)
            app.register_blueprint(admin_bp, url_prefix='/admin')
            app.register_blueprint(user_bp, url_prefix='/user')
            app.register_blueprint(auth_bp, url_prefix='/auth')
            logger.info("Blueprints registered successfully")
        except Exception as e:
            logger.error(f"Failed to register blueprints: {e}")
            raise
    
    # Create tables and initialize data
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Initialize default data
            from utils import initialize_default_data
            initialize_default_data()
            logger.info("Default data initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # Don't raise here to prevent app from crashing
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
