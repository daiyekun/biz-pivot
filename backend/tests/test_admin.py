"""阶段三：系统菜单初始化 + 后台管理（部门/用户/角色）接口冒烟测试。

运行方式（在项目根目录下）：
    python -c "import sys; sys.path.insert(0,'backend'); from tests.test_admin import *; test_admin(); print('阶段三冒烟测试全部通过')"
"""

import time

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.sys import SysDepartment, SysUserRole


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


def test_admin() -> None:
    suffix = str(int(time.time() * 1000))
    with TestClient(app) as client:
        headers = _admin_headers(client)

        # ---------- 1. 部门树 ----------
        resp = client.get("/api/v1/dept/tree", headers=headers)
        assert resp.status_code == 200, resp.text
        tree = resp.json()
        assert isinstance(tree, list)
        root = tree[0] if tree else None
        assert root is not None and root["is_company"] == 1

        # ---------- 2. 新增子部门 / 二级部门 ----------
        resp = client.post(
            "/api/v1/dept",
            headers=headers,
            json={"pid": root["id"], "name": f"测试部门A_{suffix}", "sort_order": 1},
        )
        assert resp.status_code == 200, resp.text
        dept_a = resp.json()
        assert dept_a["pid"] == root["id"]
        assert dept_a["path"].startswith(root["path"])
        assert dept_a["company_id"] == root["id"]

        resp = client.post(
            "/api/v1/dept",
            headers=headers,
            json={"pid": dept_a["id"], "name": f"测试部门B_{suffix}", "sort_order": 1},
        )
        assert resp.status_code == 200, resp.text
        dept_b = resp.json()

        # ---------- 3. 修改部门（改名） ----------
        resp = client.put(
            f"/api/v1/dept/{dept_a['id']}",
            headers=headers,
            json={"name": f"测试部门A改_{suffix}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["name"] == f"测试部门A改_{suffix}"

        # ---------- 4. 防循环嵌套：把 A 移到自己的子部门 B 下 ----------
        resp = client.put(
            f"/api/v1/dept/{dept_a['id']}",
            headers=headers,
            json={"pid": dept_b["id"]},
        )
        assert resp.status_code == 200, resp.text  # BizError -> HTTP 200 业务码非 0
        assert resp.json()["code"] != 0

        # ---------- 5. 删除有下级的部门应被拒绝 ----------
        resp = client.delete(f"/api/v1/dept/{dept_a['id']}", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["code"] != 0

        # ---------- 6. 角色 CRUD ----------
        resp = client.post(
            "/api/v1/role",
            headers=headers,
            json={"name": f"测试角色_{suffix}", "desc": "阶段三冒烟", "state": 0},
        )
        assert resp.status_code == 200, resp.text
        role = resp.json()

        resp = client.get("/api/v1/role", headers=headers, params={"keyword": f"测试角色_{suffix}"})
        assert resp.status_code == 200, resp.text
        page = resp.json()
        assert page["total"] >= 1

        resp = client.get("/api/v1/role/all", headers=headers)
        assert resp.status_code == 200
        assert any(r["id"] == role["id"] for r in resp.json())

        # ---------- 7. 用户 CRUD（归属部门必填 + 绑定角色） ----------
        account = f"tuser_{suffix}"
        resp = client.post(
            "/api/v1/user",
            headers=headers,
            json={
                "name": "测试用户",
                "account": account,
                "password": "User@123",
                "dept_id": dept_b["id"],
                "role_ids": [role["id"]],
                "phone": "13800000000",
            },
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()
        assert user["role_ids"] == [role["id"]]

        # 重复账号 -> 409
        resp = client.post(
            "/api/v1/user",
            headers=headers,
            json={
                "name": "重复",
                "account": account,
                "password": "User@123",
                "dept_id": dept_b["id"],
            },
        )
        assert resp.status_code == 409

        # 分页筛选
        resp = client.get("/api/v1/user", headers=headers, params={"account": account})
        assert resp.status_code == 200, resp.text
        page = resp.json()
        assert page["total"] >= 1
        assert any(u["account"] == account for u in page["records"])

        # 按部门筛选
        resp = client.get("/api/v1/user", headers=headers, params={"dept_id": dept_b["id"]})
        assert resp.status_code == 200
        assert any(u["account"] == account for u in resp.json()["records"])

        # 修改用户
        resp = client.put(
            f"/api/v1/user/{user['id']}",
            headers=headers,
            json={"name": "测试用户改", "phone": "13900000000"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["name"] == "测试用户改"

        # 重置密码
        resp = client.put(
            f"/api/v1/user/{user['id']}/password",
            headers=headers,
            json={"password": "NewPass@123"},
        )
        assert resp.status_code == 200, resp.text

        # 禁用后无法登录
        resp = client.put(f"/api/v1/user/{user['id']}/state", headers=headers, json={"state": 1})
        assert resp.status_code == 200, resp.text
        resp = client.post("/api/v1/auth/login", json={"account": account, "password": "NewPass@123"})
        assert resp.status_code == 401

        # 启用
        resp = client.put(f"/api/v1/user/{user['id']}/state", headers=headers, json={"state": 0})
        assert resp.status_code == 200

        # 删除用户
        resp = client.delete(f"/api/v1/user/{user['id']}", headers=headers)
        assert resp.status_code == 200, resp.text

        # ---------- 8. 角色删除校验：绑定已删用户仍应允许删除（软删用户不计绑定） ----------
        resp = client.delete(f"/api/v1/role/{role['id']}", headers=headers)
        assert resp.status_code == 200, resp.text

        # ---------- 9. 清理部门 ----------
        resp = client.delete(f"/api/v1/dept/{dept_b['id']}", headers=headers)
        assert resp.status_code == 200, resp.text
        resp = client.delete(f"/api/v1/dept/{dept_a['id']}", headers=headers)
        assert resp.status_code == 200, resp.text


def test_soft_delete_and_guards() -> None:
    """B1：软删后重建同名账号/角色不冲突；删用户清 sys_user_role；禁用部门不可挂用户。"""
    suffix = str(int(time.time() * 1000))
    with TestClient(app) as client:
        headers = _admin_headers(client)

        # 角色软删后重建同名
        role_name = f"RB_{suffix}"
        resp = client.post("/api/v1/role", headers=headers, json={"name": role_name, "state": 0})
        assert resp.status_code == 200, resp.text
        role_id = resp.json()["id"]
        assert client.delete(f"/api/v1/role/{role_id}", headers=headers).status_code == 200
        resp = client.post("/api/v1/role", headers=headers, json={"name": role_name, "state": 0})
        assert resp.status_code == 200, resp.text
        client.delete(f"/api/v1/role/{resp.json()['id']}", headers=headers)

        # 账号软删后重建同名
        account = f"ub_{suffix}"
        resp = client.post(
            "/api/v1/user", headers=headers,
            json={"name": "u", "account": account, "password": "User@123", "dept_id": 1},
        )
        assert resp.status_code == 200, resp.text
        uid = resp.json()["id"]
        assert client.delete(f"/api/v1/user/{uid}", headers=headers).status_code == 200

        with SessionLocal() as db:
            assert db.query(SysUserRole).filter(SysUserRole.user_id == uid).count() == 0

        resp = client.post(
            "/api/v1/user", headers=headers,
            json={"name": "u2", "account": account, "password": "User@123", "dept_id": 1},
        )
        assert resp.status_code == 200, resp.text
        client.delete(f"/api/v1/user/{resp.json()['id']}", headers=headers)

        # 禁用部门不可挂用户
        resp = client.post("/api/v1/dept", headers=headers, json={"pid": 1, "name": f"dd_{suffix}"})
        assert resp.status_code == 200, resp.text
        dept_id = resp.json()["id"]
        with SessionLocal() as db:
            dept = db.get(SysDepartment, dept_id)
            dept.state = 1
            db.commit()
        resp = client.post(
            "/api/v1/user", headers=headers,
            json={"name": "x", "account": f"x_{suffix}", "password": "User@123", "dept_id": dept_id},
        )
        assert resp.status_code == 404, resp.text
        with SessionLocal() as db:
            dept = db.get(SysDepartment, dept_id)
            db.delete(dept)
            db.commit()


if __name__ == "__main__":
    test_admin()
    test_soft_delete_and_guards()
    print("阶段三冒烟测试全部通过")
