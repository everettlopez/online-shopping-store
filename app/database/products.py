from sqlmodel import Session, select
from app.models.product import Product
from app.models.category import Category
from app.schemas.category import CategoryRead
from app.schemas.product import ProductRead

def database_get_product_reads(session: Session, product_ids) -> dict[int, ProductRead]:
    """Load products with their categories in two queries, shaped for API responses
    (ProductRead needs the category). Missing products are left out."""
    product_ids = set(product_ids)
    if not product_ids:
        return {}

    products = session.exec(select(Product).where(Product.product_id.in_(product_ids))).all()
    category_ids = {p.category_id for p in products}
    categories = {c.category_id: c for c in session.exec(select(Category).where(Category.category_id.in_(category_ids))).all()}

    return {
        p.product_id: ProductRead(
            **p.model_dump(exclude={"category_id"}),
            category=CategoryRead.model_validate(categories[p.category_id])
        )
        for p in products
    }

def database_get_product_read(session: Session, product_id: int) -> ProductRead | None:
    return database_get_product_reads(session, [product_id]).get(product_id)
