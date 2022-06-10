from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import schemas, database, models, oauth2


router = APIRouter(
    prefix="/likes",
    tags=['Likes']
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def like(like: schemas.LikeBase, db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):

    if current_user.is_provider:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Not authorized the perform this action...')

    provider = db.query(models.User).filter(models.User.id == like.provider_id,models.User.is_provider==True).first()
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Provider with id: {like.provider_id} does not exist")

    like_query = db.query(models.Like).filter(models.Like.provider_id == like.provider_id, models.Like.consumer_id == current_user.id)

    found_like = like_query.first()
    if (like.dir == 1):
        if found_like:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Consumer {current_user.id} has alredy liked on provider {like.provider_id}")
        new_like = models.Like(provider_id=like.provider_id, consumer_id=current_user.id)
        db.add(new_like)
        db.commit()
        return {"message": "successfully added vote"}
    else:
        if not found_like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Like does not exist")

        like_query.delete(synchronize_session=False)
        db.commit()
        return {"message": "Successfully deleted like"}
