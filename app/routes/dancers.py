from fastapi import APIRouter, HTTPException, status, Depends
from db.session import SessionDep
from sqlmodel import select
from models import Dancer
from auth_handler import get_current_user



app = APIRouter(prefix="/dancers", tags=['dancers'])

@app.post("/", status_code=status.HTTP_201_CREATED)
def create_dancer(dancer: Dancer, session: SessionDep) -> Dancer:
    """
    Создать нового танцора в базе данных.

    Args:
        dancer (Dancer): Объект танцора с данными для создания
        session (SessionDep): Сессия базы данных

    Returns:
        Dancer: Созданный объект танцора с присвоенным ID
    """

    session.add(dancer)
    session.commit()
    session.refresh(dancer)
    return dancer

@app.get("/")
def read_dancers(
    session: SessionDep,
) -> list[Dancer]:
    """
    Получить список всех зарегистрированных танцоров.

    Args:
        session (SessionDep): Сессия базы данных

    Returns:
        list[Dancer]: Список объектов танцоров
    """

    dancers = session.exec(select(Dancer)).all()
    return dancers

@app.get("/{dancer_id}")
def read_dancer(dancer_id: int, session: SessionDep) -> Dancer:
    """
    Получить информацию о танцоре по его ID.

    Args:
        dancer_id (int): Уникальный идентификатор танцора
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если танцор не найден

    Returns:
        Dancer: Объект танцора с запрошенным ID
    """
    dancer = session.get(Dancer, dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    return dancer

@app.put("/{dancer_id}")
def update_dancer(dancer_upd: Dancer, 
                  session: SessionDep,
                  current_user:dict = Depends(get_current_user)
                  ) -> Dancer:
    """
    Полностью обновить информацию о танцоре.
    
    Args:
        dancer_upd (Dancer): Обновленные данные танцора
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если танцор не найден

    Returns:
        Dancer: Обновленный объект танцора
    """
    if not(current_user.dancer_id is None) and current_user.dancer_id != dancer_upd.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No enough right to update dancer. " \
            "User should have an existing dancer_id." \
            "Dancer with dancer_id should exist and be the same delete user_id.",
        )

    dancer = session.query(Dancer).filter(Dancer.id == dancer_upd.id).first()

    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")

    dancer.name = dancer_upd.name
    dancer.age = dancer_upd.age
    dancer.height = dancer_upd.height
    dancer.secret_name = dancer_upd.secret_name
    dancer.sex = dancer_upd.sex
    dancer.level = dancer_upd.level
    dancer.status = dancer_upd.status
    dancer.style = dancer_upd.style

    session.commit()
    session.refresh(dancer)

    return dancer

@app.delete("/{dancer_id}")
def delete_dancer(dancer_id: int, 
                  session: SessionDep,
                  current_user:dict = Depends(get_current_user)):
    """
    Удалить танцора из системы по его ID.
    
    Args:
        dancer_id (int): Уникальный идентификатор танцора
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если танцор не найден

    Returns:
        dict: Результат операции
    """
    if not(current_user.dancer_id is None) and current_user.dancer_id != dancer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No enough right to delete dancer. " \
            "User should have an existing dancer_id." \
            "Dancer with dancer_id should exist and be the same delete user_id.",
        )
    dancer = session.get(Dancer, dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    session.delete(dancer)
    session.commit()
    return {"ok": True}
