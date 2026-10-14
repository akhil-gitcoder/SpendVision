from sqlalchemy.orm import Session

from app.models import Category, CategoryType
from app.utils.constants import DEFAULT_CATEGORIES


def seed_categories(db: Session) -> None:
    existing = {
        category.name
        for category in db.query(Category).all()
    }

    for name, category_type in DEFAULT_CATEGORIES:
        if name not in existing:
            db.add(
                Category(
                    name=name,
                    type=CategoryType(category_type),
                )
            )

    db.commit()


def run_seed(db: Session) -> None:
    seed_categories(db)