from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import UserModel
from serializers.user import UserSchema, UserLogin, UserToken, UserResponseSchema, UserUpdate, UserPasswordUpdate
from dependencies.get_current_user import get_current_user
from database import get_db

router = APIRouter()

@router.post("/sign-up", response_model=UserResponseSchema)
def create_user(user: UserSchema, db: Session = Depends(get_db)):
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user.username) | (UserModel.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Check if company already has an owner
    if user.role == "owner":
        existing_owner = db.query(UserModel).filter(
            UserModel.company_name == user.company_name,
            UserModel.role == "owner"
        ).first()
        if existing_owner:
            raise HTTPException(status_code=400, detail="This company already has an owner account.")

    new_user = UserModel(
        username=user.username,
        email=user.email,
        role=user.role or "owner",
        company_name=user.company_name 
    )
    new_user.set_password(user.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/sign-in", response_model=UserToken)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()

    if not db_user or not db_user.verify_password(user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = db_user.generate_token()
    return {"token": token, "message": "Login successful"}

@router.put("/me", response_model=UserResponseSchema)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if user_update.username:
        # Check if username exists
        existing_user = db.query(UserModel).filter(UserModel.username == user_update.username).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already exists")
        current_user.username = user_update.username

    if user_update.email:
         # Check if email exists
        existing_email = db.query(UserModel).filter(UserModel.email == user_update.email).first()
        if existing_email and existing_email.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already exists")
        current_user.email = user_update.email
        
    if user_update.company_name:
        current_user.company_name = user_update.company_name

    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
def update_password(
    password_update: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not current_user.verify_password(password_update.current_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.set_password(password_update.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
