from fastapi import FastAPI
from db.db import init_db
from routes import (dancers,
                    requests,
                    pairs,
                    auth,
                    recomendations)

app = FastAPI(title="FastAPI dancers' matcher",
              description="This server allows dancres to find pair for ballroom dancing.",
              version="1.0.0",
              contact={
               'name': 'Andrew Pervunetskikh',
               'url': 'https://github.com/Pandnak',
               'email': 'pervunetskikh.aa@phystech.edu'   
              })

app.include_router(dancers.app)
app.include_router(requests.app)
app.include_router(pairs.app)
app.include_router(auth.app)
app.include_router(recomendations.app)

@app.on_event("startup")
def on_startup():
    init_db()
