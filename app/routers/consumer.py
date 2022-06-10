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
from geoalchemy2.elements import WKTElement,WKBElement
router = APIRouter(
    prefix = "/consumers",
    tags = ['Consumers']
)


from geopy.geocoders import Nominatim

geolocator = Nominatim( user_agent="geoapiExercises" )

@router.post("/",status_code=status.HTTP_201_CREATED,response_model= schemas.ConsumerOut)
def create_consumer(consumer:schemas.ConsumerIn,db: Session = Depends(get_db)):

    #Hash the password - user.password

    existing_consumer = db.query(models.User).filter(models.User.email==consumer.email).first()
    if existing_consumer:
        raise HTTPException( status_code=status.HTTP_409_CONFLICT,
                             detail=f'Consumer with email: {existing_consumer.email} already exists.' )

    password = utils.hash(consumer.password)
    consumer.password = password
    new_consumer = models.User(
        is_provider = False,
        is_favorite=False,
       **consumer.dict()

    )
    db.add(new_consumer)
    db.commit()
    db.refresh(new_consumer)
    return new_consumer

@router.get("/{id}",response_model=schemas.ConsumerOut)
def get_consumer(id:int,db: Session = Depends(get_db)):
    consumer = db.query(models.User).filter(models.User.id == id).first()
    if consumer == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Consumer with id: {id} was not found.')
    return consumer


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT,)
def delete_consumer(id,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    consumer = db.query(models.User).filter(models.User.id==id)

    if not consumer.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Consumer with id: {id} was not found.')
    consumer.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)




@router.put("/{id}",response_model=schemas.ConsumerOut)
async def update_consumer(id:int, new_consumer:schemas.ConsumerUpdate,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    if new_consumer.dict()['lat']!=None and new_consumer.dict()['long']!=None:
        print('Providedddddd')
        lat = new_consumer.dict()['lat']
        long = new_consumer.dict()['long']
        spot = f'POINT({lat} {long})'
        address = str(geolocator.geocode( str(lat) + "," + str(long) ))
        district = address.split(',')[0]
        city = address.split( ',' )[1]
    else:
        print('Not Providedddd')

        lat, long = 0, 0
        address = 'Address here...'
        city = 'City here...'
        district = 'District here...'

    spot = f'POINT({lat} {long})'
    consumer = db.query(models.User).filter(models.User.id==id)
    consumer_found = consumer.first()
    if consumer_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Consumer with id: {id} was not found.')

    if consumer_found.id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )
    new_consumer_updated= new_consumer.dict()
    new_consumer_updated['address'] = address
    new_consumer_updated['geom'] = WKTElement( spot ,srid=4326)
    del new_consumer_updated['lat']
    del new_consumer_updated['long']
    new_consumer_updated['city'] = city
    new_consumer_updated['district'] = district

    consumer.update(new_consumer_updated,synchronize_session=False)
    db.commit()
    return consumer.first()

@router.post("/upload-consumer-profile-pic/{id}")
async def upload_profile_pic(id:int,uploaded_file: Optional[UploadFile] = File(None),db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),):
    BASE_DIR = f"consumer_profile_pic/"
    consumer = db.query( models.User ).filter( models.User.id == id )
    consumer_found = consumer.first()
    if consumer_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Consumer with id: {id} was not found.')
    if id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    if uploaded_file == None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail = f'Could not find the file.')
    unique_name_indicator = str(time.time()) + '_' + str(id)
    file_path = BASE_DIR + str(unique_name_indicator) + '_' + str(uploaded_file.filename)

    if consumer_found.profile_pic_url != None:
        if os.path.isfile( consumer_found.profile_pic_url ):
            os.remove( consumer_found.profile_pic_url )
    new_consumer_updated = dict()
    new_consumer_updated['profile_pic_url'] = file_path

    consumer.update(new_consumer_updated,synchronize_session=False)
    db.commit()

    with open(file_path, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())
    return consumer.first()

