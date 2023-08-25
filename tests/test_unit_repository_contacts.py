import unittest
from unittest.mock import MagicMock

from datetime import date, timedelta
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel
from src.repository.contacts import (
    get_contacts,
    get_contact_id,
    get_contact_name,
    get_contact_lastname,
    get_contact_email,
    get_contact_birthdays_along_week,
    create_contact,
    update_contact,
    delete_contact
)


class Test_Contacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().all.return_value = contacts
        result = await get_contacts(user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_id_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact_id(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_name_found(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().all.return_value = contacts
        result = await get_contact_name(contact_name="test_name",
                                        user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_lastname_found(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().all.return_value = contacts
        result = await get_contact_lastname(contact_lastname="test_lastname",
                                            user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_email_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact_email(contact_email="test_email@ex.ua",
                                         user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_birthdays_along_week_found(self):
        td = date.today()
        contacts = [Contact(name="U0", birthday=td.replace(year=1996)
                                       + timedelta(days=8)),
                    Contact(name="U1", birthday=td.replace(year=1996)
                                       + timedelta(days=7)),
                    Contact(name="U2", birthday=td.replace(year=1992)
                                       + timedelta(days=6)),
                    Contact(name="U3", birthday=td.replace(year=2004)),
                    Contact(name="U4", birthday=td.replace(year=1988)
                                       - timedelta(days=1))]
        self.session.query().filter().all.return_value = contacts
        result = await get_contact_birthdays_along_week(user=self.user, db=self.session)
        # for u in result:
        #     print(u.name, u.birthday)
        self.assertEqual(result, contacts[2:4])

    async def test_create_contact(self):
        body = ContactModel(name="Lara",
                            lastname="Craft",
                            email="LaraCraft@gmail.com",
                            phone="(200) 300-2000",
                            birthday=date.today().replace(year=1996)+timedelta(days=5),
                            note="The Game Must Be Continued.")
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.lastname, body.lastname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.note, body.note)

    async def test_update_contact_found(self):
        body = ContactModel(name="Lara",
                            lastname="Craft",
                            email="LaraCraft@gmail.com",
                            phone="(200) 300-2000",
                            birthday=date.today().replace(year=1996)+timedelta(days=5),
                            note="The Game Must Be Continued.")
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(body=body, contact_id=1,
                                      user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        body = ContactModel(name="Lara",
                            lastname="Craft",
                            email="LaraCraft@gmail.com",
                            phone="(200) 300-2000",
                            birthday=date.today().replace(year=1996)+timedelta(days=5),
                            note="The Game Must Be Continued.")
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(body=body, contact_id=1,
                                      user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_delete_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await delete_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_delete_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await delete_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)



if __name__ == '__main__':
    unittest.main()
