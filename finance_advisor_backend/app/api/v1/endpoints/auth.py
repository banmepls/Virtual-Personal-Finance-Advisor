"""
app/api/v1/endpoints/auth.py
-----------------------------
JWT Authentication endpoints: register and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.bank_connection import BTConnection
from app.services.bt_service import bt_service
from app.schemas.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, UserRegisterResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with hashed password, eToro nickname, and optional BT connectivity."""
    # Check uniqueness
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    if request.etoro_nickname:
        user.etoro_key = request.etoro_nickname
        
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Initialize Banca Transilvania Consent
    bt_consent_id = None
    bt_message = "Skipped BT connect."
    try:
        consent_data = await bt_service.create_consent(user.id)
        consent_id = consent_data["consentId"]
        is_sandbox = consent_data.get("_sandbox", False)
        
        conn = BTConnection(user_id=user.id, consent_id=consent_id, is_sandbox=is_sandbox)
        db.add(conn)
        await db.commit()
        bt_consent_id = consent_id
        bt_message = "BT Sandbox connected." if is_sandbox else "BT consent created. Please complete OAuth."
    except Exception as e:
        logger.warning(f"Failed to initialize BT consent for new user {user.id}: {e}")
        bt_message = "Registration successful, but BT initialization failed."

    return UserRegisterResponse(
        user=user,
        bt_consent_id=bt_consent_id,
        bt_message=bt_message
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return a JWT access token."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)
