from dataclasses import asdict

import uvicorn
from fastapi import FastAPI

from database.conn import db
from common.config import conf
from routes import index, auth



def create_app():
    """
    앱 함수 실행
    :return:
    """

    c = conf()

    app = FastAPI()

    conf_dict = asdict(c)

    # 데이터베이스 이니셜라이즈
    db.init_app(app, **conf_dict)

    # 레디스 이니셜라이즈
    # 미들웨어 정의
    # 라우터 정의
    app.include_router(index.router)
    app.include_router(auth.router, tags=["Authentication"], prefix="/auth")
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=conf().PROJ_RELOAD)
