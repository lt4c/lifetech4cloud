#!/usr/bin/env python3
"""
Database seeding script to create workers and product relationships
"""
import uuid
from sqlalchemy import select, insert
from app.db import SessionLocal
from app.models import Worker, VpsProduct, vps_product_workers

def seed_workers():
    """Seed database with workers and product relationships"""
    db = SessionLocal()
    
    try:
        print("=== SEEDING WORKERS AND PRODUCTS ===\n")
        
        # Check existing workers
        existing_workers = list(db.scalars(select(Worker)))
        print(f"Existing workers: {len(existing_workers)}")
        for worker in existing_workers:
            print(f"  - {worker.name} (Status: {worker.status})")
        
        # Create workers if needed
        if len(existing_workers) < 2:
            print("\nCreating additional workers...")
            
            # Worker 1
            if not any(w.name == "Worker-1" for w in existing_workers):
                worker1 = Worker(
                    id=uuid.uuid4(),
                    name="Worker-1",
                    base_url="http://worker1.example.com:8080",
                    status="active",
                    max_sessions=5
                )
                db.add(worker1)
                print(f"  + Created {worker1.name}")
            
            # Worker 2
            if not any(w.name == "Worker-2" for w in existing_workers):
                worker2 = Worker(
                    id=uuid.uuid4(),
                    name="Worker-2", 
                    base_url="http://worker2.example.com:8080",
                    status="active",
                    max_sessions=3
                )
                db.add(worker2)
                print(f"  + Created {worker2.name}")
            
            db.commit()
        
        # Get all workers after creation
        all_workers = list(db.scalars(select(Worker).where(Worker.status == "active")))
        print(f"\nTotal active workers: {len(all_workers)}")
        
        # Check existing products
        existing_products = list(db.scalars(select(VpsProduct).where(VpsProduct.is_active == True)))
        print(f"Existing active products: {len(existing_products)}")
        for product in existing_products:
            print(f"  - {product.name} (Price: {product.price_coins} coins)")
        
        # Create a test product if needed
        if len(existing_products) == 0:
            print("\nCreating test product...")
            test_product = VpsProduct(
                id=uuid.uuid4(),
                name="Test VPS Package",
                description="Test VPS package for development",
                price_coins=100,
                provision_action=1,
                is_active=True
            )
            db.add(test_product)
            db.commit()
            existing_products = [test_product]
            print(f"  + Created {test_product.name}")
        
        # Check existing relationships
        existing_relationships = db.execute(select(vps_product_workers)).all()
        print(f"\nExisting product-worker relationships: {len(existing_relationships)}")
        
        # Create relationships between all active workers and all active products
        print("\nEnsuring all workers are assigned to all products...")
        for product in existing_products:
            for worker in all_workers:
                # Check if relationship already exists
                existing = db.execute(
                    select(vps_product_workers)
                    .where(vps_product_workers.c.product_id == product.id)
                    .where(vps_product_workers.c.worker_id == worker.id)
                ).first()
                
                if not existing:
                    # Create relationship
                    db.execute(
                        insert(vps_product_workers).values(
                            product_id=product.id,
                            worker_id=worker.id
                        )
                    )
                    print(f"  + Assigned {worker.name} to {product.name}")
        
        db.commit()
        
        # Final verification
        print("\n=== FINAL VERIFICATION ===")
        final_relationships = db.execute(select(vps_product_workers)).all()
        print(f"Total product-worker relationships: {len(final_relationships)}")
        
        for product in existing_products:
            if product.is_active:
                # Count workers for this product
                worker_count = db.execute(
                    select(Worker)
                    .join(vps_product_workers, Worker.id == vps_product_workers.c.worker_id)
                    .where(vps_product_workers.c.product_id == product.id)
                    .where(Worker.status == "active")
                ).all()
                print(f"  - Product '{product.name}': {len(worker_count)} active workers assigned")
        
        print("\n✅ Database seeding completed!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_workers()