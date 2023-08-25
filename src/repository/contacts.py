from datetime import date, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from typing import List


from src.database.models import Contact, User
from src.schemas import ContactModel


async def get_contacts(user: User, db: Session) -> List[Contact]:
    '''
    Retrieves a list of contacts for a specific user.

    :param user: The user to retrieve contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contact]
    '''
    return db.query(Contact).filter(Contact.user_id == user.id).all()


async def get_contact_id(contact_id: int, user: User, db: Session) -> Contact:
    '''
    Retrieves a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param user: The user to retrieve the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Contact | None
    '''
    return db.query(Contact).filter(and_(Contact.user_id == user.id,
                                         Contact.id == contact_id)).first()


async def get_contact_name(contact_name: str, user: User, db: Session) -> List[Contact]:
    '''
    Retrieves a list of contact with the specified name for a specific user.

    :param contact_name: The name of the contact to retrieve.
    :type contact_name: str
    :param user: The user to retrieve the contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts with the specified name.
    :rtype: List[Contact]
    '''
    return db.query(Contact).filter(and_(Contact.user_id == user.id,
                func.lower(Contact.name) == func.lower(contact_name))).all()


async def get_contact_lastname(contact_lastname: str, user: User, db: Session) \
            -> List[Contact]:
    '''
    Retrieves a list of contact with the specified lastname for a specific user.

    :param contact_lastname: The lastname of the contact to retrieve.
    :type contact_lastname: str
    :param user: The user to retrieve the contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts with the specified name.
    :rtype: List[Contact]
    '''
    return db.query(Contact).filter(and_(Contact.user_id == user.id,
                func.lower(Contact.lastname) == func.lower(contact_lastname))).all()


async def get_contact_email(contact_email: str, user: User, db: Session) \
        -> Contact:
    '''
    Retrieves a single contact with the specified email for a specific user.

    :param contact_email: The lastname of the contact to retrieve.
    :type contact_email: str
    :param user: The user to retrieve the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified email, or None if it does not exist.
    :rtype: Contact
    '''
    return db.query(Contact).filter(and_(Contact.user_id == user.id,
                func.lower(Contact.email) == func.lower(contact_email))).first()


async def get_contact_birthdays_along_week(user: User, db: Session) -> List[Contact]:
    '''
    Retrieves a list of contact with the birthday along week from the current date
    for a specific user.

    :param user: The user to retrieve the contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts with the birthday which is matched to the needed condition.
    :rtype: List[Contact]
    '''
    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()
    searched_contacts = []

    today = date.today()
    date_shift = timedelta(0)
    today_over_week = today + timedelta(days=7)

    # Period must be in the same year. Otherwise shift dates on 2 weeks
    if today.year < today_over_week.year:
        # The years in both dates must be the same
        date_shift = timedelta(days=14)
        today -= date_shift
        today_over_week -= date_shift

    # Searching appropriate birthdays
    for contact in contacts:
        bday = contact.birthday - date_shift

        try:
            bday = bday.replace(year=today.year)
        except ValueError:
            # Maybe shifted birthday on February, 29 -> March, 1
            bday += timedelta(days=1)
            bday = bday.replace(year=today.year)

        if today <= bday < today_over_week:
            searched_contacts.append(contact)
    return searched_contacts


async def create_contact(body: ContactModel, user: User, db: Session) -> Contact:
    '''
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactModel
    :param user: The user to create the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The newly created contact.
    :rtype: Contact
    '''
    contact = Contact(name=body.name,
                      lastname=body.lastname,
                      email=body.email,
                      phone=body.phone,
                      birthday=body.birthday,
                      note=body.note,
                      user=user)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(body: ContactModel, contact_id: int, user: User, db: Session) \
        -> Contact | None:
    '''
    Updates a single contact with the specified ID for a specific user.

    :param body: The updated data for the contact.
    :type body: ContactModel
    :param contact_id: The ID of the contact to update.
    :type note_id: int
    :param user: The user to update the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    '''
    contact = db.query(Contact).filter(and_(Contact.user_id == user.id,
                                            Contact.id == contact_id)).first()
    if contact:
        contact.name = body.name
        contact.lastname = body.lastname
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.note = body.note
        db.commit()
    return contact


async def delete_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    '''
    Delete a single contact with the specified ID for a specific user.

    :param note_id: The ID of the contact to delete.
    :type note_id: int
    :param user: The user to delete the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The deleted contact, or None if it does not exist.
    :rtype: Contact | None
    '''
    contact = db.query(Contact).filter(and_(Contact.user_id == user.id,
                                            Contact.id == contact_id)).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact
