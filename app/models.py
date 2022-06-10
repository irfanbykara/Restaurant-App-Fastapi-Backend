from .database import Base
from sqlalchemy import Column,Integer,Boolean,String,ForeignKey,Float,BigInteger
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

class Trial(Base):
    __tablename__ ="trial"
    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    geom = Column(Geometry( geometry_type='POINT', srid=4326, management=True))  # 4326 = WGS84 Lat Long


class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    password = Column(String,nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String,nullable=False,unique=True)
    is_provider = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False,)
    motto = Column(String, nullable=True,)
    address = Column(String, nullable=True,)
    city = Column(String, nullable=True,)
    profile_pic_url = Column(String,nullable=True)
    district = Column(String, nullable=True,)
    menu_items = relationship("MenuItem", back_populates="owner")
    opportunities = relationship("Opportunity", back_populates="owner")
    provider_images = relationship("ProviderImage", back_populates = "owner")
    geom = Column(Geometry(geometry_type='POINT', srid=4326, management=True))  # 4326 = WGS84 Lat
    related_categories=Column(String,nullable=True)


class MenuItem(Base):
    __tablename__ = 'menu_items'
    id = Column(Integer, primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    content = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    owner = relationship("User", back_populates="menu_items")
    owner_id = Column( Integer, ForeignKey( "users.id"))
    menu_item_pic_url = Column(String, nullable=True)

class ProviderImage(Base):
    __tablename__ = 'provider_images'
    id = Column(Integer, primary_key=True,nullable=False)
    provider_image_url = Column(String,nullable=False)
    owner = relationship("User", back_populates = "provider_images")
    owner_id = Column(Integer,ForeignKey("users.id"))

class Opportunity(Base):
    __tablename__ = 'opportunities'
    id = Column(Integer, primary_key=True,nullable=False)
    title = Column(String, nullable=False)
    start_day = Column(BigInteger,nullable=False)
    end_day = Column(BigInteger, nullable=False)
    start_hour = Column(BigInteger,nullable=False)
    end_hour = Column(BigInteger,nullable=False)
    is_daily = Column(Boolean,nullable=False)
    is_active = Column(Boolean,nullable=False)
    initial_price = Column(Float,nullable=False)
    opportunity_price = Column(Float,nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    owner = relationship("User",back_populates="opportunities")
    opportunity_pic_url = Column(String, nullable=True)
    category = Column(String,nullable=False)

class Like(Base):
    __tablename__ = 'likes'
    consumer_id = Column(Integer, ForeignKey("users.id",
                     ondelete="CASCADE"),primary_key=True)
    provider_id = Column(Integer, ForeignKey("users.id",
                     ondelete="CASCADE"),primary_key=True)

