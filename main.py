from fastapi import FastAPI

from src.routes import auth, users

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth.router, prefix='/project')
app.include_router(users.router, prefix='/project')
