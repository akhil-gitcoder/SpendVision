from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UserOut,
)
from app.services.auth import (
    SESSION_COOKIE,
    clear_session_cookie,
    hash_password,
    issue_session,
    revoke_session,
    verify_password,
)
from app.services.auth_throttle import check_auth_attempt
from app.utils.deps import get_current_user


router = APIRouter()


@router.post(
    "/signup",
    response_model=UserOut,
    status_code=201,
)
def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()
    check_auth_attempt(email)

    existing_user = db.query(User).filter(
        func.lower(User.email) == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        auth_identifier=hash_password(payload.password),
    )

    db.add(user)

    try:
        db.flush()

        issue_session(
            db,
            user,
            response,
            request.cookies.get(SESSION_COOKIE),
        )
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        ) from exc

    return user


@router.post("/login", response_model=UserOut)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()
    check_auth_attempt(email)

    user = db.query(User).filter(
        func.lower(User.email) == email
    ).first()

    if not verify_password(payload.password, user):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    issue_session(
        db,
        user,
        response,
        request.cookies.get(SESSION_COOKIE),
    )

    return user


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    db: Session = Depends(get_db),
):
    revoke_session(
        db,
        request.cookies.get(SESSION_COOKIE),
    )

    db.commit()

    response = Response(
        status_code=204,
        headers={"Cache-Control": "no-store"},
    )

    clear_session_cookie(response)
    return response


@router.get("/me", response_model=UserOut)
def me(
    user: User = Depends(get_current_user),
):
    return user