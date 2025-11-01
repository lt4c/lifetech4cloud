#!/usr/bin/env python3
"""
Simple database seeding script to create workers and product relationships
"""
import uuid
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Boolean, Integer, ForeignKey, select, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/lifetech4cloud"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_workers():
    """Seed database with workers and product relationships"""
    db = SessionLocal()
    
    try:
        print("=== SEEDING WORKERS AND PRODUCTS ===\n")
        
        # Check existing workers
        result = db.execute(text("SELECT id, name, status FROM workers"))
        existing_workers = result.fetchall()
        print(f"Existing workers: {len(existing_workers)}")
        for worker in existing_workers:
            print(f"  - {worker.name} (Status: {worker.status})")
        
        # Create workers if needed
        if len(existing_workers) < 2:
            print("\nCreating additional workers...")
            
            # Check if Worker-1 exists
            worker1_exists = any(w.name == "Worker-1" for w in existing_workers)
            if not worker1_exists:
                worker1_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO workers (id, name, base_url, status, max_sessions)
                    VALUES (:id, :name, :base_url, :status, :max_sessions)
                """), {
                    "id": worker1_id,
                    "name": "Worker-1",
                    "base_url": "http://worker1.example.com:8080",
                    "status": "active",
                    "max_sessions": 5
                })
                print(f"  + Created Worker-1")
            
            # Check if Worker-2 exists
            worker2_exists = any(w.name == "Worker-2" for w in existing_workers)
            if not worker2_exists:
                worker2_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO workers (id, name, base_url, status, max_sessions)
                    VALUES (:id, :name, :base_url, :status, :max_sessions)
                """), {
                    "id": worker2_id,
                    "name": "Worker-2",
                    "base_url": "http://worker2.example.com:8080",
                    "status": "active",
                    "max_sessions": 3
                })
                print(f"  + Created Worker-2")
            
            db.commit()
        
        # Get all active workers
        result = db.execute(text("SELECT id, name FROM workers WHERE status = 'active'"))
        all_workers = result.fetchall()
        print(f"\nTotal active workers: {len(all_workers)}")
        
        # Check existing products
        result = db.execute(text("SELECT id, name, price_coins FROM vps_products WHERE is_active = true"))
        existing_products = result.fetchall()
        print(f"Existing active products: {len(existing_products)}")
        for product in existing_products:
            print(f"  - {product.name} (Price: {product.price_coins} coins)")
        
        # Create a test product if needed
        if len(existing_products) == 0:
            print("\nCreating test product...")
            test_product_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO vps_products (id, name, description, price_coins, provision_action, is_active)
                VALUES (:id, :name, :description, :price_coins, :provision_action, :is_active)
            """), {
                "id": test_product_id,
                "name": "Test VPS Package",
                "description": "Test VPS package for development",
                "price_coins": 100,
                "provision_action": 1,
                "is_active": True
            })
            db.commit()
            
            # Refresh products list
            result = db.execute(text("SELECT id, name, price_coins FROM vps_products WHERE is_active = true"))
            existing_products = result.fetchall()
            print(f"  + Created Test VPS Package")
        
        # Check existing relationships
        result = db.execute(text("SELECT COUNT(*) as count FROM vps_product_workers"))
        relationship_count = result.fetchone().count
        print(f"\nExisting product-worker relationships: {relationship_count}")
        
        # Create relationships between all active workers and all active products
        print("\nEnsuring all workers are assigned to all products...")
        for product in existing_products:
            for worker in all_workers:
                # Check if relationship already exists
                result = db.execute(text("""
                    SELECT COUNT(*) as count FROM vps_product_workers 
                    WHERE product_id = :product_id AND worker_id = :worker_id
                """), {
                    "product_id": product.id,
                    "worker_id": worker.id
                })
                
                if result.fetchone().count == 0:
                    # Create relationship
                    db.execute(text("""
                        INSERT INTO vps_product_workers (product_id, worker_id)
                        VALUES (:product_id, :worker_id)
                    """), {
                        "product_id": product.id,
                        "worker_id": worker.id
                    })
                    print(f"  + Assigned {worker.name} to {product.name}")
        
        db.commit()
        
        # Final verification
        print("\n=== FINAL VERIFICATION ===")
        result = db.execute(text("SELECT COUNT(*) as count FROM vps_product_workers"))
        final_count = result.fetchone().count
        print(f"Total product-worker relationships: {final_count}")
        
        for product in existing_products:
            # Count workers for this product
            result = db.execute(text("""
                SELECT COUNT(*) as count FROM vps_product_workers vpw
                JOIN workers w ON w.id = vpw.worker_id
                WHERE vpw.product_id = :product_id AND w.status = 'active'
            """), {"product_id": product.id})
            
            worker_count = result.fetchone().count
            print(f"  - Product '{product.name}': {worker_count} active workers assigned")
        
        print("\n✅ Database seeding completed!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_workers()