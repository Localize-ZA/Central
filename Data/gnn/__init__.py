import os
from neomodel import (
    StructuredNode, StructuredRel,
    StringProperty, IntegerProperty, FloatProperty, DateTimeProperty,
    RelationshipTo, RelationshipFrom, config
)


def get_compose_neo4j_url(
    *,
    host: str | None = None,
    port: str | None = None,
    user: str | None = None,
    password: str | None = None,
    scheme: str | None = None,
) -> str:
    """Build Neo4j bolt URL using docker-compose defaults with env overrides.

    Defaults match docker-compose service localize_neo4j:
      host=localhost, port=7687, user=neo4j, password=password123
    """
    host = host or os.getenv("NEO4J_HOST", "localhost")
    port = port or os.getenv("NEO4J_BOLT_PORT", "7687")
    user = user or os.getenv("NEO4J_USER", "neo4j")
    password = password or os.getenv("NEO4J_PASSWORD", "password123")
    scheme = scheme or os.getenv("NEO4J_SCHEME", "bolt")
    return f"{scheme}://{user}:{password}@{host}:{port}"


def configure_neo4j(url: str | None = None) -> str:
    """Configure neomodel DATABASE_URL and return the URL used."""
    url = url or os.getenv("NEO4J_URL") or get_compose_neo4j_url()
    config.DATABASE_URL = url
    return url


# Define relationship models with properties
class TransactionRel(StructuredRel):
    amount = FloatProperty(required=True)
    date = DateTimeProperty(required=True)
    product_id = StringProperty()   # optional, if you want a reference
    quantity = IntegerProperty(default=1)


class Citizen(StructuredNode):
    citizen_id = IntegerProperty(required=True)
    citizen_uuid = StringProperty(unique_index=True, required=True)
    
    # citizen -> business with transaction details
    businesses = RelationshipTo('Business', 'PURCHASED_FROM', model=TransactionRel)
    # citizen -> product with transaction details
    products = RelationshipTo('Product', 'PURCHASED_PRODUCT', model=TransactionRel)


class Business(StructuredNode):
    business_id = IntegerProperty(required=True)
    name = StringProperty(required=True)
    citizens = RelationshipFrom('Citizen', 'PURCHASED_FROM', model=TransactionRel)
    
    products = RelationshipTo('Product', 'SELLS',model=TransactionRel)
    manufacturers = RelationshipFrom('Manufacturer', 'SUPPLIES_TO', model=TransactionRel)

class Manufacturer(StructuredNode):
    manufacturer_id = IntegerProperty(required=True)
    name = StringProperty(required=True)
    
    products = RelationshipFrom('Product', 'PRODUCED_BY')
    businesses = RelationshipTo('Business', 'SUPPLIES_TO', model=TransactionRel)

class Product(StructuredNode):
    product_id = IntegerProperty(required=True)
    name = StringProperty(required=True)
    
    manufacturer = RelationshipTo('Manufacturer', 'PRODUCED_BY')
    citizens = RelationshipFrom('Citizen', 'PURCHASED_PRODUCT', model=TransactionRel)
    businesses = RelationshipFrom('Business', 'SELLS', model=TransactionRel)
