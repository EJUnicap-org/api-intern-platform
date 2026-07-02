from datetime import datetime
import enum
from sqlalchemy import Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True, default=datetime.utcnow)from datetime import datetime
import enum
from sqlalchemy import Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True, default=datetime.utcnow)
