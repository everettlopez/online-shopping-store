from fastapi import APIRouter, Depends, HTTPException, Security, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.models.address import Address
from datetime import datetime
from app.auth.core import CurrentUser
from app.schemas.address import AddressCreate, AddressRead

router = APIRouter(prefix="/addresses", tags=["Addresses"])

@router.post("/", response_model = AddressRead)
def create_address(data: AddressCreate, user: CurrentUser, session: Session = Depends(get_session)):
    address = Address(
        user_id = user.user_id,
        **data.model_dump()
    )

    session.add(address)
    session.commit()
    session.refresh(address)

    return address

@router.get("/", response_model=list[AddressRead])
def get_addresses(user: CurrentUser, session: Session = Depends(get_session)):
    statement = select(Address).where(Address.user_id == user.user_id)
    return session.exec(statement).all()

@router.put("/{address_id}", response_model=AddressRead)
def update_address(
    address_id: int,
    data: AddressCreate,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    address = session.get(Address, address_id)

    if not address or address.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Address not found")

    for key, value in data.model_dump().items():
        setattr(address, key, value)

    session.add(address)
    session.commit()
    session.refresh(address)

    return address

@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    address = session.get(Address, address_id)

    if not address or address.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Address not found")

    session.delete(address)
    session.commit()

    return {"message": "Address deleted"}
