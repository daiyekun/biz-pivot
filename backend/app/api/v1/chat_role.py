"""智能聊天角色管理接口（sys_chat_role）。

阶段一：提供聊天角色的增删改查能力；会话创建时须先选择聊天角色（阶段五生效）。
鉴权：chat_role:manage 菜单权限（超管全量）。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_menu_permission
from app.config import constants
from app.core.database import get_db
from app.schemas.chat_role_schema import ChatRoleCreate, ChatRoleOut, ChatRoleUpdate
from app.services.chat_role_service import ChatRoleService

router = APIRouter(
    prefix="/chat-role",
    tags=["聊天角色"],
    dependencies=[Depends(require_menu_permission(constants.MENU_CODE_CHAT_ROLE))],
)

_service = ChatRoleService()


@router.get("/list", response_model=list[ChatRoleOut])
def list_chat_roles(db: Session = Depends(get_db)):
    return _service.list_roles(db)


@router.post("", response_model=ChatRoleOut)
def create_chat_role(payload: ChatRoleCreate, db: Session = Depends(get_db)):
    return _service.create_role(db, payload)


@router.put("/{role_id}", response_model=ChatRoleOut)
def update_chat_role(role_id: int, payload: ChatRoleUpdate, db: Session = Depends(get_db)):
    return _service.update_role(db, role_id, payload)


@router.delete("/{role_id}")
def delete_chat_role(role_id: int, db: Session = Depends(get_db)):
    _service.delete_role(db, role_id)
    return {"message": "删除成功"}
