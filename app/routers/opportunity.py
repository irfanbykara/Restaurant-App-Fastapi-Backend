from fastapi import FastAPI,Response,status,Depends, HTTPException, APIRouter, File,UploadFile
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional,List,Union
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from .. import models, schemas,utils,oauth2
from ..database import engine, SessionLocal, get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from geoalchemy2.elements import WKTElement
from geoalchemy2.comparator import Comparator
from sqlalchemy import func
from ..geoalchemy_utils import geoalchemy_utils
import geoalchemy2
from geoalchemy2 import Geometry
from shapely import wkb
from shapely.geometry import Point
from geoalchemy2.types import Geography
from sqlalchemy.sql import cast
from geoalchemy2.shape import to_shape
import geopy.distance
from sqlalchemy import and_, or_
from sqlalchemy.sql import text
router = APIRouter(
    prefix="/opportunities",
    tags = ['Opportunities']
)

# Get all opportunities.
@router.get("/",response_model=List[schemas.OpportunityOut])
async def get_opportunities(db: Session = Depends(get_db), limit:int = 10,skip:int = 0,search:Optional[str]=""):
    search = "%{}%".format(search )
    opportunities = db.query(models.Opportunity).filter(models.Opportunity.title.like(search)).limit(limit).offset(skip).all()
    return opportunities

@router.get("/nearest-opportunities",status_code=status.HTTP_200_OK)
async def fetch_nearest_opportunities(db: Session = Depends(get_db),limit:int=10, current_user:int=Depends(oauth2.get_current_user), search: Optional[str] = ""):

    point = wkb.loads(bytes(current_user.geom.data))

    lat = float(point.x)
    long = float(point.y)

    result_query = db.query( models.Opportunity,
                             ).join(models.User,models.Opportunity.owner_id==models.User.id).filter(models.Opportunity.title.contains(search)). \
        order_by(
        func.ST_DistanceSphere( models.User.geom,
                          func.Geometry( func.ST_GeographyFromText(
                              'POINT({} {})'.format( lat, long ) ) ) )).limit(limit).all()
    return result_query

@router.get("/opportunities-in-range",status_code=status.HTTP_200_OK)
async def fetch_opportunities_in_range(lat:float,long:float,distance:float = 0.1,db: Session = Depends(get_db),limit:int=10, current_user:int=Depends(oauth2.get_current_user),):
    # load long[1], lat[0] into shapely
    point = wkb.loads( bytes( current_user.geom.data ) )
    # distance = distance * 0.014472
    lat = float( point.x )
    long = float( point.y )

    center_point = Point( lat, long )
    # 'POINT (-0.1198244000000000 51.5112138999999871)'

    wkb_element = wkb.dumps(center_point, hex=True, srid=4326)
    print('*'*50)
    print(type(cast(models.User.geom, Geography(srid=4326))))
    print(type(wkb_element))
    point = WKTElement( 'POINT({0} {1})'.format( lat, long ), srid=4326 )

    print('*'*50)

    opportunities = db.query( models.Opportunity ).join(models.User,models.Opportunity.owner_id==models.User.id). \
        filter( func.ST_DWithin( cast(models.User.geom, Geography(srid=4326)),  wkb_element, distance,   )).all()

    return opportunities

@router.get("/fetch-nearest-opportunities-within-radius",status_code=status.HTTP_200_OK)
async def fetch_nearest_opportunities_within_radius(distance:float = 5000,db: Session = Depends(get_db),limit:int=10, current_user:int=Depends(oauth2.get_current_user),
                                                    sorting:Optional[str] = None, filter:Optional[str]=None):
    # load long[1], lat[0] into shapely
    point = wkb.loads( bytes( current_user.geom.data ) )
    # distance = distance * 0.014472
    lat = float( point.x )
    long = float( point.y )

    center_point = Point( lat, long )
    # 'POINT (-0.1198244000000000 51.5112138999999871)'

    wkb_element = wkb.dumps(center_point, hex=True, srid=4326)


    opportunities = db.query( models.Opportunity ).join(models.User,models.Opportunity.owner_id==models.User.id). \
        filter( func.ST_Distance_Sphere( models.User.geom, wkb_element ) < distance ).order_by(models.Opportunity.end_day).all()

    return opportunities


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.OpportunityOut)
async def create_opportunity(opportunity:schemas.OpportunityIn,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),is_provider:bool=Depends(utils.provider_validator)):

    if not is_provider:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not authorized to perform this action.')
    new_opportunity = models.Opportunity(
        **opportunity.dict(),
    owner_id=current_user.id,
    )
    db.add(new_opportunity)
    db.commit()
    db.refresh(new_opportunity)

    return new_opportunity



@router.get("/{id}",response_model=schemas.OpportunityOut)
async def get_opportunity (id:int,response:Response,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    opportunity = db.query(models.Opportunity).filter(models.Opportunity.id==id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Opportunity item with id: {id} was not found.')
    return opportunity


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT,)
def delete_opportunity(id,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),
                       is_provider:bool = Depends(utils.provider_validator)):

    if not is_provider:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not authorized to perform this action.')

    opportunity = db.query(models.Opportunity).filter(models.Opportunity.id==id)



    if not opportunity.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Menu item with id: {id} was not found.')
    if opportunity.first().owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )
    opportunity.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}",response_model=schemas.OpportunityOut)
async def update_opportunity(id:int, new_opportunity:schemas.OpportunityUpdate, db: Session = Depends(get_db), current_user:int=Depends(oauth2.get_current_user),
                             is_provider: bool = Depends(utils.provider_validator)):

    if not is_provider:
        raise HTTPException(
            status = status.HTTP_403_FORBIDDEN,
            detail= 'You are not authorized to perform the requested action.'
        )

    opportunity_query = db.query(models.Opportunity).filter(models.Opportunity.id==id)
    opportunity = opportunity_query.first()
    if opportunity == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Opportunity with id: {id} was not found.')

    if opportunity.owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    opportunity_query.update(new_opportunity.dict(),synchronize_session=False)
    db.commit()
    return opportunity_query.first()


@router.get("/by_provider/{id}",response_model=List[schemas.OpportunityOut])
async def get_opportunities_by_provider(id:int, db: Session = Depends(get_db), limit:int = 10,skip:int = 0,search:Optional[str]="",):
    opportunities = db.query(models.Opportunity).filter(models.Opportunity.owner_id==id).all()
    return opportunities

@router.post("/upload-opportunity-pic/{id}")
async def upload_opportunity_pic(id:int,uploaded_file: Optional[UploadFile] = File(None),db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),
                                 is_provider:bool = Depends(utils.provider_validator)):
    if not is_provider:
        raise HTTPException(
            status = status.HTTP_403_FORBIDDEN,
            detail= 'You are not authorized to perform the requested action.'
        )

    BASE_DIR = f"opportunity_pic/"

    opportunity = db.query( models.Opportunity ).filter( models.Opportunity.id == id )
    opportunity_found = menu_item.first()
    if opportunity_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Opportunity with id: {id} was not found.')
    if opportunity_found.owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    if uploaded_file == None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail = f'Could not find the file.')
    unique_name_indicator = str(time.time()) + '_' + str(id)
    file_path = BASE_DIR + str(unique_name_indicator) + '_' + str(uploaded_file.filename)

    if opportunity_found.opportunity_pic_url !=None:
        if os.path.isfile( opportunity_found.opportunity_pic_url ):
            os.remove( opportunity_found.opportunity_pic_url )
    opportunity_updated = dict()
    opportunity_updated['menu_item_pic_url'] = file_path

    opportunity.update(opportunity_updated,synchronize_session=False)
    db.commit()

    with open(file_path, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())
    return opportunity.first()


