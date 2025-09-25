from fastapi import APIRouter
from Data.gnn import Product
from neomodel import db
import datetime

router = APIRouter()

query = """
MATCH (m:Manufacturer)-[r:SUPPLIES_TO]->(b:Business)-[:SELLS]->(p:Product)
WHERE p.name = $product_name AND r.date >= $start_date
RETURN m.name, b.name, p.name, r.amount, r.quantity, r.date
"""

@router.get("/product/{product_id}")
async def get_product(product_id: int):
    
    results, meta = db.cypher_query(query, {
        "start_date": datetime(2025, 1, 1)
    })

    for row in results:
        print(row)
    return {"product_id": product_id}