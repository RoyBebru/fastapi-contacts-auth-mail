from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Path
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List


from src.database.db import get_db
from src.database.models import User
from src.repository import contacts as repository_contacts
from src.schemas import ContactModel, ResponseContactModel
from src.services.auth import auth_service


router = APIRouter(prefix='/contacts')


@router.get("/", response_model=List[ResponseContactModel],
            description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a list of contacts for the current user. Call of this
    function is rate limited.

    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: List of contacts
    :rtype: List[ResponseContactModel]
    '''
    contacts = await repository_contacts.get_contacts(current_user, db)
    return contacts


@router.get("/by_id/{contact_id}", response_model=ResponseContactModel)
async def read_contact_id(contact_id: int = Path(
                    description="The ID of the contact to get", ge=1),
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a contact with specific ID for the current user.

    :param contact_id: ID of the contact.
    :type contact_id: int
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Suitable contact
    :rtype: ResponseContactModel
    :raises HTTPException: If a contact is absent for the current user, then
                exception with HTTP_404_NOT_FOUND status is raised.
    '''
    contact = await repository_contacts.get_contact_id(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT FOUND')
    return contact


@router.get("/by_name/{contact_name}", response_model=List[ResponseContactModel])
async def read_contact_name(contact_name: str = Path(
                    description="The case insensitive name of the contact to get"),
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a list of contacts for the current user with a specific contact name.

    :param contact_name: Case insensitive contact name.
    :type contact_name: str
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: List of contacts
    :rtype: List[ResponseContactModel]
    '''
    contacts = await repository_contacts.get_contact_name(contact_name,
                                                          current_user, db)
    return contacts


@router.get("/by_lastname/{contact_lastname}",
            response_model=List[ResponseContactModel])
async def read_contact_lastname(contact_lastname: str = Path(
                    description="The case insensitive lastname of the contact to get"),
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a list of contacts for the current user with a specific
    contact lastname.

    :param contact_lastname: Case insensitive contact lastname.
    :type contact_lastname: str
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: List of contacts
    :rtype: List[ResponseContactModel]
    '''
    contacts = await repository_contacts.get_contact_lastname(contact_lastname,
                                                              current_user, db)
    return contacts


@router.get("/by_email/{contact_email}", response_model=ResponseContactModel)
async def read_contact_email(contact_email: str = Path(
                    description="The case insensitive email of the contact to get"),
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a contact with a specific email for the current user.

    :param contact_id: The case insencitive email address of the contact.
    :type contact_id: int
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Suitable contact
    :rtype: ResponseContactModel
    :raises HTTPException: If a contact is absent for the current user, then
                exception with HTTP_404_NOT_FOUND status is raised.
    '''
    contact = await repository_contacts.get_contact_email(contact_email,
                                                          current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT FOUND')
    return contact


@router.get("/birthdays_along_week", response_model=List[ResponseContactModel])
async def read_contact_birthdays_along_week(
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Retrieves a list of contacts for the current user with birtdays which
    are happened during near 7 days.

    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: List of contacts
    :rtype: List[ResponseContactModel]
    '''
    contacts = await repository_contacts.get_contact_birthdays_along_week(
                current_user, db)
    return contacts


@router.post("/", response_model=ResponseContactModel,
             status_code=status.HTTP_201_CREATED)
async def create_contact(
                body: ContactModel,
                current_user: User = Depends(auth_service.get_current_user),
                db: Session = Depends(get_db)):
    '''
    Creates new contact for the current user.

    :param body: Contact data.
    :type body: ContactModel
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: contact
    :rtype: ResponseContactModel

    :raises HTTPException:
            This exception is raised when such contact already exists.

    | For example, use Postman POST request to
      URL=.../contacts/ with the following JSON raw body to create
      new contact:
    | {
    |   "name": "Lara",
    |   "lastname": "Craft",
    |   "email": "LaraCraft@gmail.com",
    |   "phone": "(304) 625-2000",
    |   "birthday": "2001-11-27",
    |   "note": "The game must be continued."
    | }
    '''
    try:
        contact = await repository_contacts.create_contact(body, current_user, db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="ALREADY EXISTS")
    return contact


@router.put("/{contact_id}", response_model=ResponseContactModel)
async def update_contact(body: ContactModel, contact_id: int = Path(ge=1),
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    '''
    Updates an existent contact for the current user.

    :param body: New contact data.
    :type body: ContactModel
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: contact
    :rtype: ResponseContactModel

    :raises HTTPException:
            This exception is raised when contact data already exists
            for the other contact or contact is absent.
    '''
    try:
        contact = await repository_contacts.update_contact(body,
                                                           contact_id, current_user, db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="ALREADY EXISTS")
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return contact


@router.delete("/{contact_id}", response_model=ResponseContactModel)
async def delete_contact(contact_id: int = Path(
                description="The ID of contact to delete", ge=1),
            current_user: User = Depends(auth_service.get_current_user),
            db: Session = Depends(get_db)):
    '''
    Deletes an existent contact with a specific ID for the current user.

    :param contact_id: The ID of contact to delete.
    :type contact_id: int
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: contact
    :rtype: ResponseContactModel

    :raises HTTPException:
            This exception is raised when contact is absent.
    '''
    contact = await repository_contacts.delete_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return contact
