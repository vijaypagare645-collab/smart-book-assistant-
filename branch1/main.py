from fastapi import FastAPI,Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static",StaticFiles(directory = "branch1/static"),name="static")
templates = Jinja2Templates(directory='branch1/templates')

@app.get('/')
def home(request:Request):
    return templates.TemplateResponse(request=request, name='index.html',context={'data':'i am from templates'})