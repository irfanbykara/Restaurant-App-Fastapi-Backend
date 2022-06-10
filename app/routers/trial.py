from fastapi import FastAPI,Response,status,APIRouter,Depends, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional,List
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from .. import models,schemas
from ..database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

router = APIRouter(
    prefix = "/trial",
    tags = ['Trial']
)


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.TrialOut)
def create_trial(trial:schemas.TrialIn,db: Session = Depends(get_db)):
    #
    # #Hash the password - user.password
    lat = trial.dict()['lat']
    long = trial.dict()['long']
    wkt_spot1 = f'POINT({lat} {long})'
    spot1 = models.Trial( name="Gas Station",  geom=WKTElement( wkt_spot1 ,srid=4326))
    db.add(spot1)
    db.commit()
    db.refresh(spot1)
    #
# lake = Lake( name='GeoTrial', geom='P((3 0,6 0,6 3,3 3,3 0))', point="POINT(2 9)" )
    #
    # new_trial = models.Trial(
    #    **trial.dict()
    # )
    # db.add(new_trial)
    # db.commit()
    # db.refresh(new_trial)
    return spot1

@router.get("/{id}",response_model=schemas.TrialOut)
def get_trial(id:int,db: Session = Depends(get_db)):

    trial = db.query(models.Trial).filter(models.Trial.id == id).first()
    if trial == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Trial with id: {id} was not found.')
    return trial
