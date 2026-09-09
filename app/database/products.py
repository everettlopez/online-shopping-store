from sqlmodel import Session, select
from app.models.product import Product

def database_get_products(session: Session, sort: str | None = None):
    products = session.exec(select(Product)).all()

    if sort == "product_id":
        products = sorted(products, key=lambda p: p.product_id)
    elif sort == "category_id":
        products = sorted(products, key=lambda p: p.category_id)
    elif sort == "name":
        products = sorted(products, key=lambda p: p.name)
    elif sort == "price":
        products = sorted(products, key=lambda p: p.price)
    elif sort == "size":
        products = sorted(products, key=lambda p: p.size)
    elif sort == "active":
        products = sorted(products, key=lambda p: p.is_active)
    elif sort == "color":
        products = sorted(products, key = lambda p: p.color)
    elif sort == "created":
        products = sorted(products, key = lambda p: p.created_at)
    elif sort == "updated":
        products = sorted(products, key = lambda p: p.updated_at)
    else:
        return products
    
    return products

