#!/usr/bin/env python3
"""
Debug script to check worker data and relationships
"""
import asyncio
from sqlalchemy import select, func
from app.db import SessionLocal
from app.models import Worker, VpsProduct, vps_product_workers, VpsSession

def debug_workers():
    """Debug worker data and relationships"""
    db = SessionLocal()
    
    try:
        print("=== WORKER DEBUG INFO ===\n")
        
        # 1. Check all workers
        print("1. All Workers:")
        workers = list(db.scalars(select(Worker)))
        for worker in workers:
            print(f"  - ID: {worker.id}")
            print(f"    Name: {worker.name}")
            print(f"    Status: {worker.status}")
            print(f"    Max Sessions: {worker.max_sessions}")
            print(f"    Base URL: {worker.base_url}")
            print(f"    Created: {worker.created_at}")
            print()
        
        # 2. Check active workers only
        print("2. Active Workers:")
        active_workers = list(db.scalars(select(Worker).where(Worker.status == "active")))
        for worker in active_workers:
            print(f"  - {worker.name} (ID: {worker.id})")
        print(f"Total active workers: {len(active_workers)}\n")
        
        # 3. Check all products
        print("3. All VPS Products:")
        products = list(db.scalars(select(VpsProduct)))
        for product in products:
            print(f"  - ID: {product.id}")
            print(f"    Name: {product.name}")
            print(f"    Active: {product.is_active}")
            print(f"    Price: {product.price_coins} coins")
            print()
        
        # 4. Check product-worker relationships
        print("4. Product-Worker Relationships:")
        stmt = select(vps_product_workers)
        relationships = db.execute(stmt).all()
        for rel in relationships:
            product_id, worker_id = rel
            product = db.scalar(select(VpsProduct).where(VpsProduct.id == product_id))
            worker = db.scalar(select(Worker).where(Worker.id == worker_id))
            print(f"  - Product: {product.name if product else 'Unknown'} -> Worker: {worker.name if worker else 'Unknown'}")
        print(f"Total relationships: {len(relationships)}\n")
        
        # 5. Check workers for each active product manually
        print("5. Workers per Active Product:")
        for product in products:
            if product.is_active:
                # Manual query to get workers for this product
                stmt = (
                    select(Worker)
                    .join(vps_product_workers, Worker.id == vps_product_workers.c.worker_id)
                    .where(vps_product_workers.c.product_id == product.id)
                    .where(Worker.status == "active")
                    .order_by(Worker.created_at.desc())
                )
                workers_for_product = list(db.scalars(stmt))
                print(f"  - Product '{product.name}': {len(workers_for_product)} workers")
                for worker in workers_for_product:
                    print(f"    * {worker.name} (ID: {worker.id}, Status: {worker.status})")
        print()
        
        # 6. Check active sessions per worker
        print("6. Active Sessions per Worker:")
        active_statuses = {"pending", "provisioning", "ready"}
        for worker in active_workers:
            session_count = db.scalar(
                select(func.count(VpsSession.id))
                .where(VpsSession.worker_id == worker.id)
                .where(VpsSession.status.in_(active_statuses))
            )
            print(f"  - {worker.name}: {session_count} active sessions (max: {worker.max_sessions})")
        print()
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_workers()