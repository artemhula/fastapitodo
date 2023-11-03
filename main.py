from starlette import status
from starlette.responses import RedirectResponse

from routers import todos, auth
from fastapi import FastAPI

app = FastAPI()
app.include_router(auth.router)
app.include_router(todos.router)


@app.get('/')
async def show_index():
    return RedirectResponse('/todo', status_code=status.HTTP_302_FOUND)