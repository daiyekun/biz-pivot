"""阶段四：角色授权（菜单权限树 + 知识库权限）接口冒烟测试。

运行方式（在项目根目录下）：
    python -c "import sys; sys.path.insert(0,'backend'); from tests.test_menu import *; test_menu(); print('阶段四冒烟测试全部通过')"
"""

import time

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core import permission as perm
from app.core.database import SessionLocal
from app.main import app
from app.models.knowledge import SysKnowledgeCategory
from app.models.sys import SysUser


def _admin_headers(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "account": settings.super_admin_account,
            "password": settings.super_admin_password,
        },
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _flatten_codes(nodes: list) -> dict:
    """菜单树扁平化：code -> id"""
    mapping = {}

    def walk(items):
        for n in items:
            if n.get("code"):
                mapping[n["code"]] = n["id"]
            walk(n.get("children", []))

    walk(nodes)
    return mapping


def test_menu() -> None:
    suffix = str(int(time.time() * 1000))
    with TestClient(app) as client:
        headers = _admin_headers(client)

        # ---------- 1. 菜单权限树 ----------
        resp = client.get("/api/v1/menu/tree", headers=headers)
        assert resp.status_code == 200, resp.text
        tree = resp.json()
        id_by_code = _flatten_codes(tree)
        assert "knowledge:upload" in id_by_code
        assert "category:manage" in id_by_code
        assert len(tree) >= 8

        # ---------- 2. 创建测试角色 ----------
        role_name = f"授权角色_{suffix}"
        resp = client.post("/api/v1/role", headers=headers, json={"name": role_name, "state": 0})
        assert resp.status_code == 200, resp.text
        role = resp.json()

        # ---------- 3. 初始无授权 ----------
        resp = client.get(f"/api/v1/menu/role/{role['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["menu_ids"] == []

        # ---------- 4. 保存授权（知识库上传 + 分类管理） ----------
        grant_ids = [id_by_code["knowledge:upload"], id_by_code["category:manage"]]
        resp = client.put(
            f"/api/v1/menu/role/{role['id']}",
            headers=headers,
            json={"menu_ids": grant_ids},
        )
        assert resp.status_code == 200, resp.text
        assert set(resp.json()["menu_ids"]) == set(grant_ids)

        # 非法菜单 ID 应被拒绝
        resp = client.put(
            f"/api/v1/menu/role/{role['id']}",
            headers=headers,
            json={"menu_ids": [999999]},
        )
        assert resp.status_code == 404, resp.text

        # ---------- 5. 回读授权 ----------
        resp = client.get(f"/api/v1/menu/role/{role['id']}", headers=headers)
        assert set(resp.json()["menu_ids"]) == set(grant_ids)

        # ---------- 6. 创建绑定该角色的用户 ----------
        account = f"menuuser_{suffix}"
        resp = client.post(
            "/api/v1/user",
            headers=headers,
            json={
                "name": "授权用户",
                "account": account,
                "password": "User@123",
                "dept_id": 1,
                "role_ids": [role["id"]],
            },
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()

        # ---------- 7. 普通用户登录，动态菜单 ----------
        resp = client.post("/api/v1/auth/login", json={"account": account, "password": "User@123"})
        assert resp.status_code == 200, resp.text
        user_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        resp = client.get("/api/v1/menu/mine", headers=user_headers)
        assert resp.status_code == 200, resp.text
        paths = set(resp.json()["paths"])
        assert "/admin/knowledge" in paths
        assert "/admin/category" in paths
        assert "/admin/dept" not in paths
        assert "/admin/user" not in paths

        # ---------- 8. 普通用户访问授权接口 -> 403 ----------
        assert client.get("/api/v1/menu/tree", headers=user_headers).status_code == 403
        assert client.get(f"/api/v1/menu/role/{role['id']}", headers=user_headers).status_code == 403

        # ---------- 9. 后端功能权限判定（core/permission.py） ----------
        with SessionLocal() as db:
            u = db.query(SysUser).filter(SysUser.account == account).first()
            assert u is not None
            ctx = perm.build_user_context(u, [role["id"]], "/1/")
            assert perm.has_upload_permission(ctx) is True
            assert perm.has_category_permission(ctx) is True
            assert perm.has_menu_permission(ctx, "knowledge:upload") is True
            assert perm.has_menu_permission(ctx, "dept:manage") is False

        # ---------- 10. 清空授权后再校验 ----------
        resp = client.put(
            f"/api/v1/menu/role/{role['id']}",
            headers=headers,
            json={"menu_ids": []},
        )
        assert resp.status_code == 200
        resp = client.get("/api/v1/menu/mine", headers=user_headers)
        assert resp.json()["paths"] == []

        # ---------- 11. 清理 ----------
        assert client.delete(f"/api/v1/user/{user['id']}", headers=headers).status_code == 200
        assert client.delete(f"/api/v1/role/{role['id']}", headers=headers).status_code == 200


def test_menu_access_control() -> None:
    """D1 修复回归：菜单授权后接口真正可用（非仅超管）；D2：可访问分类范围落地。"""
    suffix = str(int(time.time() * 1000))
    with TestClient(app) as client:
        headers = _admin_headers(client)

        menu_tree = client.get("/api/v1/menu/tree", headers=headers).json()
        id_by_code = _flatten_codes(menu_tree)

        # ---------- 创建角色并授权 dept:manage + user:manage ----------
        role = client.post(
            "/api/v1/role", headers=headers,
            json={"name": f"后台角色_{suffix}", "state": 0},
        ).json()
        grant_ids = [id_by_code["dept:manage"], id_by_code["user:manage"]]
        resp = client.put(
            f"/api/v1/menu/role/{role['id']}", headers=headers,
            json={"menu_ids": grant_ids},
        )
        assert resp.status_code == 200, resp.text

        # ---------- D2：可访问分类范围 ----------
        with SessionLocal() as db:
            cat = SysKnowledgeCategory(name=f"分类_{suffix}", pid=0, path="/", sort_order=0, state=0)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            cat.path = f"/{cat.id}/"
            db.commit()
            cat_id = cat.id

        resp = client.put(
            f"/api/v1/menu/role/{role['id']}/categories", headers=headers,
            json={"category_ids": [cat_id]},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["category_ids"] == [cat_id]

        resp = client.get(f"/api/v1/menu/role/{role['id']}/categories", headers=headers)
        assert resp.json()["category_ids"] == [cat_id]

        # 非法分类 ID 拒绝
        resp = client.put(
            f"/api/v1/menu/role/{role['id']}/categories", headers=headers,
            json={"category_ids": [999999]},
        )
        assert resp.status_code == 404, resp.text

        # ---------- 绑定角色的普通用户 ----------
        account = f"adminuser_{suffix}"
        user = client.post(
            "/api/v1/user", headers=headers,
            json={
                "name": "后台用户",
                "account": account,
                "password": "User@123",
                "dept_id": 1,
                "role_ids": [role["id"]],
            },
        ).json()

        uresp = client.post("/api/v1/auth/login", json={"account": account, "password": "User@123"})
        assert uresp.status_code == 200, uresp.text
        uheaders = {"Authorization": f"Bearer {uresp.json()['access_token']}"}

        # ---------- D1：授权菜单接口真实可用 ----------
        paths = set(client.get("/api/v1/menu/mine", headers=uheaders).json()["paths"])
        assert "/admin/dept" in paths and "/admin/user" in paths

        # dept:manage 授权 → /dept/tree 200（修复前为 403）
        assert client.get("/api/v1/dept/tree", headers=uheaders).status_code == 200
        # user:manage 授权 → /user 200
        assert client.get("/api/v1/user", headers=uheaders).status_code == 200
        # 只读角色列表（后台元数据）→ 200
        assert client.get("/api/v1/role", headers=uheaders).status_code == 200
        # 分类树（后台元数据）→ 200
        assert client.get("/api/v1/category/tree", headers=uheaders).status_code == 200

        # 未授权写操作 → 403
        resp = client.post("/api/v1/role", headers=uheaders, json={"name": "越权角色", "state": 0})
        assert resp.status_code == 403, resp.text
        resp = client.post(
            "/api/v1/provider", headers=uheaders,
            json={"name": "越权提供商", "endpoint": "http://x", "model": "m"},
        )
        assert resp.status_code == 403, resp.text
        # 未授权 permission:grant → /menu/tree 403
        assert client.get("/api/v1/menu/tree", headers=uheaders).status_code == 403

        # ---------- 清理 ----------
        assert client.delete(f"/api/v1/user/{user['id']}", headers=headers).status_code == 200
        assert client.delete(f"/api/v1/role/{role['id']}", headers=headers).status_code == 200
        with SessionLocal() as db:
            cat_row = db.get(SysKnowledgeCategory, cat_id)
            if cat_row is not None:
                db.delete(cat_row)
                db.commit()


if __name__ == "__main__":
    test_menu()
    test_menu_access_control()
    print("阶段四冒烟测试全部通过")
