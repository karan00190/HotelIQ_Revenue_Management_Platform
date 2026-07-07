from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hotel import Hotel
from app.models.schemas import HotelCreate, HotelResponse

router = APIRouter(prefix="/hotels", tags=["Hotels"])


@router.get("/", response_model=list[HotelResponse])
def list_hotels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Hotel).offset(skip).limit(limit).all()


@router.get("/{hotel_id}", response_model=HotelResponse)
def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return hotel


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
def create_hotel(hotel_in: HotelCreate, db: Session = Depends(get_db)):
    existing = db.query(Hotel).filter(Hotel.name == hotel_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A hotel with this name already exists",
        )
    hotel = Hotel(**hotel_in.model_dump())
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    db.delete(hotel)
    db.commit()
    return None
