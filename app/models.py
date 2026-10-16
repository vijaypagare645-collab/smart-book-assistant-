
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    extracted_text: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
