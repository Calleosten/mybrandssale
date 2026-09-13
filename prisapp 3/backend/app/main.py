from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from . import models, schemas
from .database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prisbevakning API")


def _product_to_out(p: models.Product) -> schemas.ProductOut:
    out = schemas.ProductOut.model_validate(p)
    out.brand_name = p.brand.name if p.brand else None
    return out


@app.get("/brands", response_model=List[str])
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(models.Brand).all()
    return [b.name for b in brands]


@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(brand: str | None = None, on_sale_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Product)
    if brand:
        q = q.join(models.Brand).filter(models.Brand.name == brand)
    if on_sale_only:
        q = q.filter(models.Product.is_on_sale == True)  # noqa: E712
    return [_product_to_out(p) for p in q.all()]


@app.get("/products/{product_id}/history", response_model=List[schemas.PriceHistoryOut])
def product_history(product_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.product_id == product_id)
        .order_by(desc(models.PriceHistory.checked_at))
        .all()
    )
    return history


@app.post("/watchlist", response_model=schemas.WatchlistOut)
def add_to_watchlist(item: schemas.WatchlistCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produkten hittades inte")

    entry = models.WatchlistItem(
        user_id=item.user_id,
        product_id=item.product_id,
        notify_threshold_percent=item.notify_threshold_percent,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/watchlist/{user_id}", response_model=List[schemas.WatchlistOut])
def get_watchlist(user_id: str, db: Session = Depends(get_db)):
    items = db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == user_id).all()
    return items


@app.delete("/watchlist/{item_id}")
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Bevakning hittades inte")
    db.delete(item)
    db.commit()
    return {"status": "removed"}


@app.post("/device-tokens")
def register_device_token(payload: schemas.DeviceTokenCreate, db: Session = Depends(get_db)):
    existing = db.query(models.DeviceToken).filter(models.DeviceToken.fcm_token == payload.fcm_token).first()
    if existing:
        existing.user_id = payload.user_id
    else:
        db.add(models.DeviceToken(user_id=payload.user_id, fcm_token=payload.fcm_token))
    db.commit()
    return {"status": "ok"}
