import asyncio

from sqlalchemy.orm import Session

from app.admin.seed import create_test_data
from app.db import SessionLocal


async def create_test_user_product():
    db = SessionLocal()
    try:
        user, product = create_test_data(db)
        print(f"Successfully created test user and product")
        print(f"User ID: {user.id}")
        print(f"Product ID: {product.id}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(create_test_user_product())