import os
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session, sessionmaker

os.environ["DISCORD_CLIENT_ID"] = "1234567890"
os.environ["DISCORD_CLIENT_SECRET"] = "test-secret"
os.environ["DISCORD_REDIRECT_URI"] = "http://localhost:8000/auth/discord/callback"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key"
os.environ["BACKEND_URL"] = "http://localhost:8000"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/postgres"

from app.models import VpsProduct, User
from app.settings import Settings

settings = Settings()
db_url = "postgresql://postgres:quangpro1@localhost:5432/postgres"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_test_user_product():
    product = VpsProduct(
        name="Test VPS",
        description="Test VPS for worker",
        price_coins=100
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    user = User(
        username="test_user",
        email="test@example.com",
        coins=1000,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"Created product ID: {product.id}")
    print(f"Created user ID: {user.id}")
    
    return user, product

if __name__ == "__main__":
    create_test_user_product()