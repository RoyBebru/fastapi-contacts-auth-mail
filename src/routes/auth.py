from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi import BackgroundTasks, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Annotated

from src.database.db import get_db
from src.schemas import UserModel, ResponseUserModel, TokenModel, RequestEmail
from src.schemas import ResetPasswordModel
from src.schemas import ResponseResetPasswordModel
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email_verification, send_email_reset_password


router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=ResponseUserModel,
             status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request,
                 db: Session = Depends(get_db)):
    '''
    Signs a new user up and sends him a verification email in background with
    a confirmation link.

    :param body: User credentials from request body.
    :type body: UserModel
    :param background_tasks: Fastapi interface to background tasks.
    :type background_tasks: BackgroundTasks
    :param request: An interface onto the incoming request to get base_url, etc.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Result information, including new_user object and text message.
    :rtype: ResponseUserModel

    | For example, use Postman POST request to
      URL=.../.../auth/signup with the following JSON raw body:
    | {
    |   "username": "Roy Bebru",
    |   "email": "roybebru@gmail.com",
    |   "password": "123456"
    | }
    '''
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email_verification, new_user.email,
                              new_user.username,
                              request.base_url)
    return {"user": new_user,
            "detailed": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    '''
    Login procedure for existent user.

    :param body: User credentials from form-data.
    :type body: OAuth2PasswordRequestForm
    :return: Result information and access/refresh tokens.
    :rtype: TokenModel
    :raises HTTPException: If user is absent, or user email is not confirmed,
            or user password is wrong then exception with HTTP_401_UNAUTHORIZED
            status code is raised.

    | For example, use Postman POST request to
      URL=.../.../auth/login with the following x-www-form-urlencoded body:

    | username=roybebru@gmail.com
    | password=123456
    '''
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token,
            "token_type": "bearer"}


@router.post("/reset_password", response_model=ResponseResetPasswordModel,
             status_code=status.HTTP_205_RESET_CONTENT)
async def reset_password(body: ResetPasswordModel, background_tasks: BackgroundTasks,
                         request: Request,
                         db: Session = Depends(get_db)):
    '''
    As soon as the user requests to reset the forgotten password,
    this function will be called. If the user exists and his email
    address is confirmed, an email with a password change form must
    be sent to this user.

    :param body: User's email from request body..
    :type body: ResetPasswordModel
    :param background_tasks: Fastapi interface to background tasks.
    :type background_tasks: BackgroundTasks
    :param request: An interface onto the incoming request to get base_url, etc.
    :type request: Request
    :return: Message about success.
    :rtype: ResponseResetPasswordModel

    :raises HTTPException: If user is absent, or user email is not confirmed,
            then exception with HTTP_401_UNAUTHORIZED
            status code is raised.

    | For example, use Postman POST request to
      URL=.../.../auth/reset_password with the following JSON raw body:
    | {
    |   "email": "roybebru@gmail.com"
    | }
    '''
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if not exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Account is absent")
    if not exist_user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Email not confirmed")
    background_tasks.add_task(send_email_reset_password, exist_user.email,
                              exist_user.username,
                              request.base_url)
    return {"message": "User is successfully informed how to reset password. "
                       "Check your email for instruction."}


@router.post("/reset_password_new/{token}")
async def reset_password_new(token: str,
                password: Annotated[str, Form()],
                db: Session = Depends(get_db)):
    '''
    As soon as the user enters a new password in the HTML form in the email
    and sends it, this function is called.

    :param token: Email token to prevent password changing from
        unauthorized user.
    :type token: str
    :param password: Plain password from form field in html email.
    :type password: str
    :param db: The database session.
    :type db: Session
    :return: Message about success password changing.
    :rtype: dict

    :raises HTTPException: If token is wrong or outdated and email
        cannot be given then exception with HTTP_406_NOT_ACCEPTABLE
        is raised.
    '''
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="Invalid email")
    password = auth_service.get_password_hash(password)
    await repository_users.reset_password_new(user, password, db)
    return {"message": "User password is successfully changed."}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: Session = Depends(get_db)):
    '''
    Updates access and refresh tokens.

    :param credentials:
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :return: Result information and access/refresh tokens.
    :rtype: TokenModel

    :raises HTTPException: If user's refresh token is different from such token
            in given credentials, then exception with HTTP_401_UNAUTHORIZED
            status code is raised.
    '''
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token,
            "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    '''
    Confirms user's email address. This function is called from verification
    email which is sent to user.

    :param token: Access token from header "Authorization: Bearer TOKEN_STRING".
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Result information about email is confirmed.
    :rtype: dict

    :raises HTTPException: If user's access token is wrong, then exception
            with HTTP_401_UNAUTHORIZED status code is raised.
    '''
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks,
                        request: Request,
                        db: Session = Depends(get_db)):
    '''
    Sends verification email to user.

    :param body: User's email.
    :param body: RequstEmail
    :param background_tasks: Fastapi interface to background tasks.
    :type background_tasks: BackgroundTasks
    :param request: An interface onto the incoming request to get base_url, etc.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Result information.
    :rtype: dict
    '''
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email_verification, user.email, user.username,
                                  request.base_url)
    return {"message": "Check your email for confirmation."}
