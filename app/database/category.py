from sqlmodel import Session, select
from app.models.category import Category

def database_get_categories(session: Session, sort: str | None = None):

    categories = session.exec(select(Category)).all()

    if sort == "id":
        categories = sorted(categories, key=lambda c: c.category_id)
    elif sort == "name":
        categories = sorted(categories, key=lambda c: c.name)
    else:
        return categories
    
    return categories
