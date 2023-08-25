from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import pickle
import redis.asyncio as redis
from sqlalchemy.orm import Session
from typing import Optional


from src.conf.config import settings
from src.database.db import get_db
from src.repository import users as repository_users


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    # Do not allow changing hash algorithm
    ALGORITHM = "HS256"
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    rds = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password: str, hashed_password: str):
        '''
        Compares passwords.

        :param plain_password: Given plain password.
        :type plain_password: str
        :param hashed_password: Given hashed password.
        :type hashed_password: str
        :return: True if password is the same.
        :rtype: bool
        '''
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        '''
        Retrieves the hash of the plain password.

        :param password: Plain password.
        :type password: str
        :return: Hashed password.
        :rtype: str
        '''
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict,
                                  expires_delta: Optional[float] = None):
        '''
        Creates access token with specific data within it.

        :param data: Data dictionary to include into access token. For
                example, {"sub": "RoyBebru@gmail.com"}.
        :type data: dict
        :param expires_delta: Optional time while access token is valid.
                If expires_delta is omitted then default value
                is 15 minutes.
        :type expires_delta: float
        :return: Access token
        :rtype: str
        '''
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire,
                          "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY,
                                          algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict,
                                   expires_delta: Optional[float] = None):
        '''
        Creates refresh token with specific data within it.

        :param data: Data dictionary to include into refresh token. For
                example, {"sub": "RoyBebru@gmail.com"}.
        :type data: dict
        :param expires_delta: Optional time while refresh token is valid.
                If expires_delta is omitted then default value
                is 7 days.
        :type expires_delta: float
        :return: Refresh token
        :rtype: str
        '''
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire,
                          "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY,
                                           algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        '''
        Decodes a refresh token.

        :param refresh_token: Refresh token in aim to decode.
        :type refresh_token: str
        :raises HTTPExpression: Exception is raised if refresh token has
                wrong format, or is outdated.
        '''
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY,
                                 algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme),
                               db: Session = Depends(get_db)):
        '''
        Retrieve a current user by given access token  If token is good
        user can be retrieced from redis cache.

        :param token: Access token.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: Curent user.
        :rtype: User
        '''
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = await self.rds.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            await self.rds.set(f"user:{email}", pickle.dumps(user))
            await self.rds.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user

    async def get_email_from_token(self, token: str):
        '''
        Retrieves user email address which is stored within access or update token.

        :param token: Given access or update token.
        :type token: str
        :return: User's email address.
        :rtype: str | None
        :raises HTTPException: If token is wrong exception with
                HTTP_422_UNPROCESSIBLE_ENTITY status is raised.
        '''
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

    def create_email_token(self, data: dict, days=7):
        '''
        Creates email token.

        :param data: Data dictionary which must be included within token.
        :type data: dict
        :param days: Days while token is valid. By default it is 7 days.
        :type days: int
        :return: Email token.
        :rtype: str
        '''
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=days)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token


auth_service = Auth()
