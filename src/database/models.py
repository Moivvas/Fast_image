
from sqlalchemy import Column, Integer, String, Boolean, func, Table, Enum
import enum


from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()


image_m2m_tag = Table(
    "image_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)


class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    public_id = Column(String(150))
    description = Column(String(150))
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    tags = relationship("Tag", secondary=image_m2m_tag, back_populates="images")
    comments = relationship('Comment', backref="images")
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())
    qr_url = Column(String(255), nullable=True)


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    tag_name = Column(String(13), nullable=False, unique=True)
    images = relationship("Image", secondary=image_m2m_tag, back_populates="tags")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    comment = Column(String(255), nullable=False)
    user_id = Column("user_id", ForeignKey('users.id', ondelete='CASCADE'), default=None)
    image_id = Column("image_id", ForeignKey("images.id", ondelete="CASCADE"), default=None)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())


class Role(enum.Enum):
    __tablename__ = 'users_roles'
    admin: str = 'admin'
    moderator: str = 'moderator'
    user: str = 'user'


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    sex = Column(String(7), nullable=False)
    password = Column(String(150), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now())
    refresh_token = Column(String(255))
    forbidden = Column(Boolean, default=False)
    role = Column('role', Enum(Role), default=Role.user)
    images = relationship('Image', backref="users")
    avatar = Column(String(255), nullable=True)


class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    rate = Column(Integer, default=0)
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'))
    image_id = Column('image_id', ForeignKey('images.id', ondelete='CASCADE'))
    user = relationship('User', backref='ratings')
