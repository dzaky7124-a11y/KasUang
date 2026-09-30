from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

def get_utc_now():
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="USER")  # "ADMIN" or "USER"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    wallets: List["Wallet"] = Relationship(back_populates="user", cascade_delete=True)
    transactions: List["Transaction"] = Relationship(back_populates="user", cascade_delete=True)

class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    type: str = Field(default="CASH")  # CASH, BANK, EWALLET, OTHER
    initial_balance: float = Field(default=0.0)
    color: str = Field(default="#10B981")  # Emerald/Green default
    icon: str = Field(default="wallet")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_utc_now)

    user: Optional[User] = Relationship(back_populates="wallets")
    transactions: List["Transaction"] = Relationship(back_populates="wallet", cascade_delete=True)

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", nullable=True, index=True)
    name: str
    type: str = Field(default="EXPENSE")  # INCOME or EXPENSE
    icon: str = Field(default="tag")
    color: str = Field(default="#6B7280")
    created_at: datetime = Field(default_factory=get_utc_now)

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    wallet_id: int = Field(foreign_key="wallet.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", nullable=True, index=True)
    type: str = Field(default="EXPENSE")  # INCOME, EXPENSE, TRANSFER
    amount: float
    date: str = Field(index=True)  # YYYY-MM-DD format
    description: str
    note: Optional[str] = Field(default="")
    transfer_wallet_id: Optional[int] = Field(default=None, nullable=True)
    proof_image: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=get_utc_now)

    user: Optional[User] = Relationship(back_populates="transactions")
    wallet: Optional[Wallet] = Relationship(back_populates="transactions")

class SystemConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=get_utc_now)

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    message: str
    type: str = Field(default="INFO")  # INFO, WARNING, SUCCESS
    created_by_name: str = Field(default="Administrator")
    created_at: datetime = Field(default_factory=get_utc_now)

