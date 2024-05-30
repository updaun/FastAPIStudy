import time
import typing
import re

import jwt

from fastapi.params import Header
from jwt import PyJWTError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from common import config, consts
from common.config import conf
from models import UserToken

from utils.date_utils import D


class AccessControl:
    def __init__(
        self,
        app: ASGIApp,
        except_path_list: typing.Sequence[str] = None,
        except_path_regex: str = None,
    ) -> None:
        if except_path_list is None:
            except_path_list = ["*"]
        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regex = except_path_regex

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope=scope)
        headers = Headers(scope=scope)
        request.state.req_time = D.datetime()
        request.state.start = time.time()
        request.state.inspect = None
        request.state.user = None
        request.state.is_admin_access = None
        ip_from = (
            request.headers["x-forwarded-for"]
            if "x-forwarded-for" in request.headers.keys()
            else None
        )

        if (
            await self.url_pattern_check(request.url.path, self.except_path_regex)
            or request.url.path in self.except_path_list
        ):
            return await self.app(scope, receive, send)

        if request.url.path.startswith("/api"):
            # api 인경우 헤더로 토큰 검사
            if "Authorization" in request.headers.keys():
                request.state.user = await self.token_decode(
                    access_token=request.headers.get("Authorization")
                )
                # 토큰 없음
            else:
                if "Authorization" not in request.headers.keys():
                    response = JSONResponse(
                        status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED")
                    )
                    return await response(scope, receive, send)
        else:

            if "Authorization" not in request.cookies.keys():
                response = JSONResponse(
                    status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED")
                )
                return await response(scope, receive, send)

            request.state.user = await self.token_decode(
                access_token=request.cookies.get("Authorization")
            )

        request.state.req_time = D.datetime()
        res = await self.app(scope, receive, send)
        return res

    @staticmethod
    async def url_pattern_check(path, pattern):
        result = re.match(pattern, path)
        if result:
            return True
        return False

    @staticmethod
    async def token_decode(access_token):
        """
        :param access_token:
        :return:
        """
        try:
            access_token = access_token.replace("Bearer ", "")
            payload = jwt.decode(
                access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM]
            )
        except PyJWTError as e:
            print(e)
            # Raise Error
        return payload
