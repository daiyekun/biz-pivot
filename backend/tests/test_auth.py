"""阶段二：登录鉴权体系 接口冒烟测试。

运行方式（在 backend 目录下）：
    python -m tests.test_auth
"""

from fastapi.testclient import TestClient

from app.config import constants
from app.config.settings import settings
from app.core import auth as auth_core
from app.core.database import SessionLocal
from app.main import app
from app.models.sys import SysUser


def _make_user(account: str, state: int = constants.STATE_NORMAL) -> int:
    with SessionLocal() as db:
        slot, pwd = auth_core.make_password("User@123")
        user = SysUser(
            name="测试账号",
            account=account,
            pwd=pwd,
            slot=slot,
            dept_id=1,
            company_id=1,
            state=state,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def _cleanup(user_id: int) -> None:
    with SessionLocal() as db:
        user = db.get(SysUser, user_id)
        if user is not None:
            db.delete(user)
            db.commit()


def test_login_and_auth() -> None:
    with TestClient(app) as client:
        # 1. 公开接口（健康检查）无需登录
        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 200

        # 2. 未登录访问受保护接口 -> 401
        resp = client.get("/api/v1/provider/list")
        assert resp.status_code == 401

        # 3. 错误密码 -> 401
        resp = client.post(
            "/api/v1/auth/login",
            json={"account": settings.super_admin_account, "password": "wrong-pass"},
        )
        assert resp.status_code == 401

        # 4. 超级管理员正确登录
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "account": settings.super_admin_account,
                "password": settings.super_admin_password,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["access_token"] and data["refresh_token"]
        assert data["user"]["account"] == settings.super_admin_account
        assert data["user"]["is_super"] is True

        token = data["access_token"]
        refresh_token = data["refresh_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 5. refresh token 不能当 access token 访问受保护接口（A1 type 隔离）
        resp = client.get(
            "/api/v1/provider/list",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert resp.status_code == 401

        # 6. 登录后访问受保护接口
        resp = client.get("/api/v1/provider/list", headers=headers)
        assert resp.status_code == 200

        # 7. 当前用户资料
        resp = client.get("/api/v1/auth/profile", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["account"] == settings.super_admin_account

        # 8. 刷新 Token
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200, resp.text
        new_token = resp.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # 9. 普通用户访问后台管理接口 -> 403（A2 超管拦截）
        uid = _make_user("__t_normal__")
        try:
            resp = client.post(
                "/api/v1/auth/login",
                json={"account": "__t_normal__", "password": "User@123"},
            )
            assert resp.status_code == 200, resp.text
            normal_headers = {
                "Authorization": f"Bearer {resp.json()['access_token']}"
            }
            resp = client.get("/api/v1/provider/list", headers=normal_headers)
            assert resp.status_code == 403
            resp = client.post(
                "/api/v1/chat-role",
                headers=normal_headers,
                json={"name": "越权角色", "temperature": 0.7},
            )
            assert resp.status_code == 403
        finally:
            _cleanup(uid)

        # 10. 禁用账号禁止登录
        uid = _make_user("__t_disabled__", state=constants.STATE_DISABLED)
        try:
            resp = client.post(
                "/api/v1/auth/login",
                json={"account": "__t_disabled__", "password": "User@123"},
            )
            assert resp.status_code == 401
            assert "禁用" in resp.json()["message"]
        finally:
            _cleanup(uid)

        # 11. 登出后 access token 彻底失效
        resp = client.post("/api/v1/auth/logout", headers=new_headers)
        assert resp.status_code == 200
        resp = client.get("/api/v1/auth/profile", headers=new_headers)
        assert resp.status_code == 401


if __name__ == "__main__":
    test_login_and_auth()
    print("阶段二鉴权冒烟测试全部通过")
