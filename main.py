import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from src.routes import (auth,
                        users,
                        tags,
                        cloud_image,
                        ratings,
                        comments)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory='templates')
BASE_DIR = pathlib.Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse, description="Main Page")
async def root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "FAST_image_App"})


app.include_router(auth.router, prefix='/project')
app.include_router(users.router, prefix='/project')
app.include_router(tags.router, prefix='/project')
app.include_router(cloud_image.router, prefix='/project')
app.include_router(ratings.router, prefix='/project')
app.include_router(comments.router, prefix='/project')
