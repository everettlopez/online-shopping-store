from sqlmodel import Session, select
from app.models.category import Category

# The storefront nav and admin product form link to these IDs directly
DEFAULT_CATEGORIES = [
    (1, "New Arrivals"),
    (2, "Women"),
    (3, "Men"),
    (4, "Brands"),
    (5, "Accessories"),
    (6, "Jewelry"),
]

def database_seed_categories(session: Session):

    # Only seed a fresh database, never touch existing categories
    if session.exec(select(Category)).first():
        return

    for category_id, name in DEFAULT_CATEGORIES:
        session.add(Category(category_id=category_id, name=name))

    session.commit()

def database_get_categories(session: Session, sort: str | None = None):

    categories = session.exec(select(Category)).all()

    if sort == "id":
        categories = sorted(categories, key=lambda c: c.category_id)
    elif sort == "name":
        categories = sorted(categories, key=lambda c: c.name)
    else:
        return categories
    
    return categories
