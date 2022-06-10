from pydantic import BaseModel,EmailStr,Field,validator
from typing import Optional
from datetime import datetime
from typing import Optional,Dict,Union
from pydantic.types import conint
from pydantic import root_validator
from shapely.geometry import Point, asShape
from shapely.geometry.base import BaseGeometry
import geoalchemy2.shape
import logging
from geoalchemy2.elements import WKBElement
import geoalchemy2
from enum import Enum
from .geoalchemy_utils import geoalchemy_utils

class TrialBase(BaseModel):
    name: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class TrialOut(TrialBase):
    geom: Optional[Dict]

    _validate_geom = validator("geom", pre=True, allow_reuse=True)(geoalchemy_utils.dump_geom)

class TrialIn(TrialBase):
    name: str
    lat: float
    long: float

class UserBase(BaseModel):
    pass
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class UserIn(UserBase):
    email: EmailStr
    password: str
    name: str
    last_name: str


class UserOut(UserBase):
    id: str
    name: str
    last_name: str
    is_provider: bool
    email: EmailStr
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    geom: Optional[Dict]

    _validate_geom = validator( "geom", pre=True, allow_reuse=True )( geoalchemy_utils.dump_geom)


class Token(BaseModel):
    access_token: str
    token_type: str

class ProviderIn(UserIn):
    email: EmailStr
    password: str
    name: str
    last_name: str
    lat: Optional[float] = None
    long: Optional[float] = None


class ConsumerIn(UserIn):
    pass


class ConsumerOut(UserOut):
    pass

class ProviderOut(UserOut):
    motto: Optional[str] = None
    is_favorite: bool

class ProviderUpdate(UserBase):
    motto: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    is_favorite: bool


class ConsumerUpdate(UserBase):
    lat: Optional[float] = None
    long: Optional[float] = None



class TokenData(BaseModel):
    id: Optional[str] = None

class MenuItemBase(BaseModel):

    name : str
    content : Optional[str] = None
    price : float
    class Config:
        orm_mode = True

class MenuItemIn(MenuItemBase):
    pass

class MenuItemOut(MenuItemBase):
    id: int
    owner_id: int
    menu_item_pic_url: Optional[str]


class OpportunityBase(BaseModel):
    title: str
    start_day: int
    end_day: int
    start_hour: int
    end_hour: int
    is_daily: bool
    initial_price: float
    opportunity_price: float
    is_active: bool

    class Config:
        orm_mode = True

class OpportunityIn(OpportunityBase):
    pass

class OpportunityOut(OpportunityBase):
    id: int
    opportunity_pic_url: Optional[str] = None

class OpportunityUpdate(OpportunityBase):
    pass

class LikeBase(BaseModel):
    provider_id: int
    dir: conint( le=1 )

    class Config:
        orm_mode = True

class GeoPoint(BaseModel):
    lat: float
    long: float

    class Config:
        orm_mode = True




