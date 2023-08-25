from libgravatar import Gravatar
from sqlalchemy import func
from sqlalchemy.orm import Session


from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User:
    '''
    Retrieves an user with the unique specific email address.

    :param email: The email address to retrieve user for.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: An user which is identified by email address.
    :rtype: User
    '''
    return db.query(User).filter(
            func.lower(User.email) == func.lower(email)).first()


async def create_user(body: UserModel, db: Session) -> User:
    '''
    Creates a new user in system which can manage hist own
    contacts.

    :param body: The data for the user to create.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: The newly created user.
    :rtype: User
    '''
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    '''
    Updates refresh token for specific user if token is present. Otherwise
    (if it is None) token is removed.

    :param user: User to update his refresh token
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: Nothing
    :rtype: None
    '''
    user.refresh_token = token
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    '''
    Updates a refresh token for specific user if token is present. Otherwise
    (if it is None) token is removed.

    :param user: User to update his refresh token.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: Nothing
    :rtype: None
    '''
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirmed_email(email: str, db: Session) -> None:
    '''
    Calls when user confirms his own email address.

    :param email: User email address.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: Nothing
    :rtype: None
    '''
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def reset_password_new(user: User, password: str, db: Session) -> None:
    '''
    Calls to set a new password instead old forgotten one.

    :param user: User who wants to reset password.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: Nothing
    :rtype: None
    '''
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()
    user.password = password
    db.commit()
