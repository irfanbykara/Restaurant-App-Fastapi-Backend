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
router = APIRouter(
    prefix="/menu-items",
    tags = ['Menu Items']
)

@router.get("/",response_model=List[schemas.MenuItemOut])
async def get_menu_items(db: Session = Depends(get_db), limit:int = 10,skip:int = 0,search:Optional[str]="",):
    menu_items = db.query(models.MenuItem).filter(models.MenuItem.name.contains(search)).limit(limit).offset(skip).all()
    print(menu_items)
    return menu_items


@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.MenuItemOut)
async def create_menu_item(menu_item:schemas.MenuItemIn,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):
    new_menu_item = models.MenuItem(
        owner_id=current_user.id,
       **menu_item.dict()
    )
    db.add(new_menu_item)
    db.commit()
    db.refresh(new_menu_item)

    return new_menu_item



@router.get("/{id}",response_model=schemas.MenuItemOut)
async def get_menu_item (id:int,response:Response,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    menu_item = db.query(models.MenuItem).filter(models.MenuItem.id==id).first()
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Menu item with id: {id} was not found.')
    return menu_item


@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT,)
def delete_menu_item(id,db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user)):

    menu_item = db.query(models.MenuItem).filter(models.MenuItem.id==id)



    if not menu_item.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Menu item with id: {id} was not found.')
    if menu_item.first().owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )
    menu_item.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# @app.post("/upload-file/")
# async def create_upload_file(uploaded_file: UploadFile = File(...)):
#     file_location = f"files/{uploaded_file.filename}"
#     with open(file_location, "wb+") as file_object:
#         file_object.write(uploaded_file.file.read())
#     return {"info": f"file '{uploaded_file.filename}' saved at '{file_location}'"}

@router.put("/{id}",response_model=schemas.MenuItemOut)
async def update_menu_item(id:int, new_menu_item:schemas.MenuItemIn, db: Session = Depends(get_db), current_user:int=Depends(oauth2.get_current_user)):

    menu_item_query = db.query(models.MenuItem).filter(models.MenuItem.id==id)
    menu_item = menu_item_query.first()
    if menu_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Menu item with id: {id} was not found.')

    if menu_item.owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    menu_item_query.update(new_menu_item.dict(),synchronize_session=False)
    db.commit()
    return menu_item_query.first()


@router.get("/by-provider/{id}",response_model=List[schemas.MenuItemOut])
async def get_menu_items_by_provider(id:int, db: Session = Depends(get_db), limit:int = 10,skip:int = 0,search:Optional[str]="",):
    menu_items = db.query(models.MenuItem).filter(models.MenuItem.owner_id==id).all()
    return menu_items

@router.post("/upload-menu-item-pic/{id}")
async def upload_menu_item_pic(id:int,uploaded_file: Optional[UploadFile] = File(None),db: Session = Depends(get_db),current_user:int=Depends(oauth2.get_current_user),):
    BASE_DIR = f"menu_item_pic/"

    menu_item = db.query( models.MenuItem ).filter( models.MenuItem.id == id )
    menu_item_found = menu_item.first()
    if menu_item_found == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Menu Item with id: {id} was not found.')
    if menu_item_found.owner_id != current_user.id:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN,
                             detail=f'Not authorized to perform the requested action.' )

    if uploaded_file == None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail = f'Could not find the file.')
    unique_name_indicator = str(time.time()) + '_' + str(id)
    file_path = BASE_DIR + str(unique_name_indicator) + '_' + str(uploaded_file.filename)

    if menu_item_found.menu_item_pic_url !=None:
        if os.path.isfile( menu_item_found.menu_item_pic_url ):
            os.remove( menu_item_found.menu_item_pic_url )
    new_menu_item_updated = dict()
    new_menu_item_updated['menu_item_pic_url'] = file_path

    menu_item.update(new_menu_item_updated,synchronize_session=False)
    db.commit()

    with open(file_path, "wb+") as file_object:
        file_object.write(uploaded_file.file.read())
    return menu_item.first()

