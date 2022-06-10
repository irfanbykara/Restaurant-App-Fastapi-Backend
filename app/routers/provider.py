from fastapi import FastAPI,Response,status,APIRouter,Depends, HTTPException,UploadFile, File
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional,List
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from .. import models, schemas,utils, oauth2
from ..database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
import time
import os
from geoalchemy2.elements import WKTElement
from geoalchemy2.comparator import Comparator
from sqlalchemy import func
from ..geoalchemy_utils import geoalchemy_utils
import geoalchemy2
from shapely import wkb

from geopy.geocoders import Nominatim

geolocator = Nominatim( user_agent="geoapiExercises" )

router = APIRouter(
    prefix = "/providers",
    tags = ['Providers']
)

@router.post("/",status_code=status.HTTP_201_CREATED,response_model= schemas.ProviderOut)
def create_provider(provider:schemas.ProviderIn,db: Session = Depends(get_db)):

    #Hash the password - user.password
    if provider.dict()['lat']!=None and provider.dict()['long']!=None:
        lat = provider.dict()['lat']
        long = provider.dict()['long']
    else:
        lat,long= 0,0

    spot = f'POINT({lat} {long})'

    existing_provider = db.query(models.User).filter(models.User.email==provider.email).first()
    if existing_provider:
        raise HTTPException( status_code=status.HTTP_409_CONFLICT,
                             detail=f'Provider with email: {existing_provider.email} already exists.' )

    password = utils.hash(provider.password)
    curated_dict = provider.dict()
    del curated_dict['lat']
    del curated_dict['long']
    curated_dict['password'] = password

    new_provider = models.User(
        geom=WKTElement( spot ,srid=4326),
        is_provider= True,
        is_favorite=False,
       **curated_dict,
    )
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return new_provider


@router.get("/favorite-providers",status_code=status.HTTP_200_OK,response_model=List[schemas.ProviderOut])
async def fetch_favorite_providers(db: Session = Depends(get_db),limit:int=10, current_user:int=Depends(oauth2.get_current_user),search: Optional[str] = ""):
    result_query = db.query(models.User).filter(models.User.is_favorite==True, models.User.is_provider==True).all()
    return result_query



@router.get("/{id}",response_model=schemas.ProviderOut)
def get_provider(id:int,db: Session = Depends(get_db)):
    provider = db.query(models.User).filter(models.User.id == id).first()
    if provider == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Provider with id: {id} was not found.')
    return provider


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT,)
def delete_provider(id,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    provider = db.query(models.User).filter(models.User.id==id)

    if not provider.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Provider with id: {id} was not found.')
    provider.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)




@router.put("/{id}",response_model=schemas.ProviderOut)
async def update_provider(id:int, new_provider:schemas.ProviderUpdate,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),):

    # if uploaded_file:
    #     print('successfully uploaded file...')

    if new_provider.dict()['lat']!=None and new_provider.dict()['long']!=None:
        lat = new_provider.dict()['lat']
        long = new_provider.dict()['long']
        spot = f'POINT({lat} {long})'
        address = str(geolocator.geocode( str(lat) + "," + str(long) ))
        district = address.split(',')[0]
        city = address.split( ',' )[1]
    else:
        address = 'Address here...'
        city = 'City here...'
        district = 'District here...'

    provider = db.query(models.User).filter(models.User.id==id)
    provider_found = provider.first()
    if provider_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Provider with id: {id} was not found.')

    if provider_found.id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )
    new_provider_updated= new_provider.dict()
    new_provider_updated['address'] = address
    if lat!=None and long!=None:
        new_provider_updated['geom'] = WKTElement( spot ,srid=4326)
    del new_provider_updated['lat']
    del new_provider_updated['long']
    new_provider_updated['city'] = city
    new_provider_updated['district'] = district

    provider.update(new_provider_updated,synchronize_session=False)
    db.commit()
    return provider.first()

@router.post("/upload-provider-profile-pic/{id}")
async def upload_profile_pic(id:int,uploaded_file: Optional[UploadFile] = File(None),db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),):
    BASE_DIR = f"provider_profile_pic/"
    provider = db.query( models.User ).filter( models.User.id == id )
    provider_found = provider.first()
    if provider_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Provider with id: {id} was not found.')
    if id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    if uploaded_file == None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail = f'Could not find the file.')
    unique_name_indicator = str(time.time()) + '_' + str(id)
    file_path = BASE_DIR + str(unique_name_indicator) + '_' + str(uploaded_file.filename)

    if provider_found.profile_pic_url !=None:
        if os.path.isfile( provider_found.profile_pic_url ):
            os.remove( provider_found.profile_pic_url )
    new_provider_updated = dict()
    new_provider_updated['profile_pic_url'] = file_path

    provider.update(new_provider_updated,synchronize_session=False)
    db.commit()

    with open(file_path, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())
    return provider.first()

@router.post("/upload-provider-pic/{id}")
async def upload_provider_pic(id:int,uploaded_files: List[Optional[UploadFile]] = File(None, description='Provider restaurant images...'),
                              db: Session = Depends(get_db),
                              current_user:int=Depends(oauth2.get_current_user)):
    BASE_DIR = f"provider_pic/"

    if current_user == None or current_user.is_provider != True or current_user.id!=id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )
    for uploaded_file in uploaded_files:
        unique_name_indicator = str( time.time() ) + '_' + str( current_user.id )
        file_path = BASE_DIR + str( unique_name_indicator ) + '_' + str( uploaded_file.filename )
        new_provider_img = models.ProviderImage(
            owner_id = current_user.id,
            provider_image_url = file_path
        )
        db.add(new_provider_img)
        db.commit()
        db.refresh(new_provider_img)
        with open( file_path, "wb+" ) as file_object:
            file_object.write( uploaded_file.file.read() )

    provider_image_query = db.query(models.ProviderImage).filter(models.ProviderImage.owner_id == current_user.id)
    provider_images = provider_image_query.all()
    return provider_images

@router.delete("/delete-provider-image/{id}",status_code=status.HTTP_204_NO_CONTENT,)
async def delete_provider_image(id,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    provider_image = db.query(models.ProviderImage).filter(models.ProviderImage.id==id)
    provider_image_found = provider_image.first()
    if not provider_image.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Provider Image with id: {id} was not found.')
    if provider_image.first().owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    if provider_image_found.provider_image_url !=None:
        if os.path.isfile( provider_image_found.provider_image_url ):
            os.remove( provider_image_found.provider_image_url )

    provider_image.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.get("/nearest-providers/{id}",status_code=status.HTTP_200_OK)
async def fetch_nearest_providers(id:int,db: Session = Depends(get_db),limit:int=10, current_user:int=Depends(oauth2.get_current_user),search: Optional[str] = ""):

    point = wkb.loads(bytes(current_user.geom.data))

    lat = float(point.x)
    long = float(point.y)

    result_query = db.query( models.User.email,
                             ).filter(models.User.email.contains(search)). \
        order_by(
        func.ST_Distance_Sphere( models.User.geom,
                          func.Geometry( func.ST_GeographyFromText(
                              'POINT({} {})'.format( lat, long ) ) ) ) ).limit(limit).all()
    return result_query

