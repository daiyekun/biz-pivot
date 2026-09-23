"""模型提供商设置接口（sys_provider）。

阶段一：提供多模型提供商的配置能力（增删改查）。
鉴权：provider:manage 菜单权限（超管全量）。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_menu_permission
from app.config import constants
from app.core.database import get_db
from app.schemas.provider_schema import ProviderCreate, ProviderOut, ProviderUpdate
from app.services.provider_service import ProviderService

router = APIRouter(
    prefix="/provider",
    tags=["模型提供商"],
    dependencies=[Depends(require_menu_permission(constants.MENU_CODE_PROVIDER))],
)

_service = ProviderService()


@router.get("/list", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return _service.list_providers(db)


@router.post("", response_model=ProviderOut)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)):
    return _service.create_provider(db, payload)


@router.put("/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: int, payload: ProviderUpdate, db: Session = Depends(get_db)):
    return _service.update_provider(db, provider_id, payload)


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    _service.delete_provider(db, provider_id)
    return {"message": "删除成功"}
