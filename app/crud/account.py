# app/crud/account.py
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate
from app.crud.base_crud import BaseCRUD


class CRUDAccount(BaseCRUD[Account, AccountCreate, AccountUpdate]):
    pass


account_crud = CRUDAccount(Account)
