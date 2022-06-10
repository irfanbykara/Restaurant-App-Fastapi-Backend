from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import trial,auth, provider,menu_items,consumer,opportunity,like
from fastapi import Body
# from celery_worker import create_task
from fastapi.responses import JSONResponse
from .database import db_session,get_db
from sqlalchemy.orm import Session
from fastapi_utils.session import FastAPISessionMaker
from fastapi_utils.tasks import repeat_every
from .database import sessionmaker
from . import models
from datetime import datetime

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trial.router)
app.include_router(auth.router)
app.include_router(provider.router)
app.include_router(opportunity.router)
app.include_router(like.router)
app.include_router(menu_items.router)
app.include_router(consumer.router)

def unactivate_expired_opportunities(db: Session) -> None:
    # Getting the current date and time
    dt = datetime.now()

    # getting the timestamp
    ts = datetime.timestamp( dt )
    # db.query(models.Opportunity).filter(models.Opportunity.is_active==True,models.Opportunity.end_day<ts).update({models.Opportunity.is_active:True},synchronize_session=False)
    # db.commit()



@app.on_event("startup")
@repeat_every(seconds=10)  # 1 hour
def startup_task() -> None:
    print('Called on startup...')
    try:
        with sessionmaker.context_session() as db:
            unactivate_expired_opportunities(db=db)
    except Exception as e:
        print('An error occured')
        print(e)


@app.get("/")
async def root():
    return {'message':'Welcome to Venga Backend root!'}

