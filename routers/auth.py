from typing import Annotated, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Response, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from database import Base, engine, SessionLocal
from models import User
from datetime import timedelta, datetime

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

templates = Jinja2Templates(directory="templates")
bcrypt_context = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto'
)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

SECRET_KEY = '02b76ea8b2bffc60f9b2055f15717449cd378de0e6914e76ff1ac4bd4f4ef0a99d8223bbde8a3653408184005afdead61c82fbbef9af151d28d325c70e405b69f4a9ad0074ef9bcc1a9b63103f503e44'


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('username')
        self.password = form.get('password')


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username==username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, timedelta: timedelta):
    encode = {
        'sub': username,
        'id': user_id,
        'exp': datetime.utcnow() + timedelta,
    }
    return jwt.encode(encode, SECRET_KEY, "HS256")


async def get_current_user(request: Request):
    try:
        token = request.cookies.get('access_token')
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            return None
        return {'username': username, 'id': user_id}
    except JWTError:
        return None


@router.post('/token', response_model=Token)
async def get_token(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    response.set_cookie(key='access_token', value=token, httponly=True)
    return True


@router.get('/')
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@router.post('/')
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url='/todo', status_code=status.HTTP_302_FOUND)

        validate_token = await get_token(response, form_data=form, db=db)

        if not validate_token:
            return templates.TemplateResponse('login.html', context={'request': request,'msg': 'user not found'})
        return response
    except HTTPException:
        return templates.TemplateResponse('login.html', context={'request': request,'msg': 'Unknown error'})


@router.get('/logout')
async def logout(request: Request):
    response = templates.TemplateResponse('login.html', context={'request': request, 'msg': 'Logout successful!'})
    response.delete_cookie(key='access_token')
    return response


@router.get('/register')
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', context={'request': request})


@router.post('/register')
async def register(request: Request, name: str = Form(...), surname: str = Form(...), username: str = Form(...), password: str = Form(...), password2: str = Form(...), db: Session = Depends((get_db))):
    msgs = []

    if not db.query(User).filter(User.username==username).first():
        if password == password2:
            user = User(name=name,
                        surname=surname,
                        username=username,
                        hashed_password=bcrypt_context.hash(SECRET_KEY, 'bcrypt', password))
            db.add(user)
            db.commit()
            return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)
        else: msg = 'Passwords are not similar!'
    else: msg = 'This username is exist!'
    return templates.TemplateResponse('register.html', context={'request': request, 'msg': msg})