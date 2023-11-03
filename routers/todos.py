from fastapi import APIRouter, Depends, Request, Form, HTTPException
from typing import Annotated, Optional

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse

from database import engine, SessionLocal, Base
from models import Todos
from pydantic import BaseModel, Field
from .auth import get_current_user

router = APIRouter(
    prefix='/todo',
    tags=['todo']
)

Base.metadata.create_all(bind=engine)


class Todo(BaseModel):
    title: str
    description: Optional[str]
    is_important: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory='templates')

@router.get('/create')
async def add_new_todo(request: Request):
    return templates.TemplateResponse("create.html", {'request': request})


@router.post('/create')
async def create_todo(request: Request,  title: str = Form(...), description: str = Form(default=''), is_important: bool = Form(default=False), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth/login', status_code=status.HTTP_302_FOUND)
    todo_model = Todos()
    todo_model.user_id = user.get('id')
    todo_model.title = title
    todo_model.description = description
    todo_model.is_important = is_important
    todo_model.is_completed = False
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)


@router.get('/delete/{id}')
async def delete_todo(request: Request, id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todos).filter(Todos.id == id).first()
    db.delete(todo_model)
    db.commit()
    return RedirectResponse("/todo", status_code=status.HTTP_302_FOUND)


@router.get('/', response_class=HTMLResponse)
async def read_all_todos(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    todos = db.query(Todos).filter(Todos.user_id==user.get('id')).order_by(Todos.is_important.desc()).order_by(Todos.created_date.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, 'todos': todos})


@router.get('/edit/{id}', response_class=HTMLResponse)
async def edit_todo_page(request: Request, id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    todo_model = db.query(Todos).filter(Todos.id == id).first()
    return templates.TemplateResponse("edit.html", {"request": request, 'todo': todo_model})


@router.post('/edit/{id}')
async def edit_todo(request: Request, id: int, title: str = Form(...), description: str = Form(default=''), is_important: bool = Form(default=False), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    todo_model = db.query(Todos).filter(Todos.id == id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.is_important = is_important
    todo_model.is_completed = False
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)


@router.get('/complete/{id}')
async def complete_todo(request: Request, id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    todo_model = db.query(Todos).filter(Todos.id == id).first()
    todo_model.is_completed = not todo_model.is_completed
    db.commit()
    return RedirectResponse("/todo", status_code=status.HTTP_302_FOUND)


@router.get('/search', response_class=HTMLResponse)
async def search_todo_page(request: Request, query: str = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    print(query)
    todos = db.query(Todos).filter(Todos.title.like('%'+query+'%')).filter(Todos.description.like('%'+query+'%')).order_by(Todos.is_important.desc()).order_by(Todos.created_date.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, 'todos': todos})
