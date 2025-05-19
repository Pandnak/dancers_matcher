from fastapi import APIRouter, HTTPException, Depends
from models import Pair, Dancer, PairResponse
from schemas import StatusType
from db.session import SessionDep
from sqlmodel import select
from auth_handler import get_current_user
from fastapi import status

app = APIRouter(prefix='/pairs', tags=['pairs'])


@app.get("/")
def read_pairs(session: SessionDep) -> list[PairResponse]:
    """
    Получить список всех существующих пар.

    Args:
        session (SessionDep): Сессия базы данных

    Returns:
        list[PairResponse]: Список пар с полной информацией о танцорах
    """

    pairs = session.exec(select(Pair)).all()
    return [PairResponse(
        id=pair.id,
        dancer1=session.get(Dancer, pair.dancer1_id),
        dancer2=session.get(Dancer, pair.dancer2_id),
        created_at=pair.created_at
    ) for pair in pairs]

@app.get("/{pair_id}")
def read_pair(pair_id: int, session: SessionDep) -> PairResponse:
    """
    Получить информацию о паре по её ID.
    
    Args:
        pair_id (int): Уникальный идентификатор пары
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если пара не найдена

    Returns:
        PairResponse: Объект пары с информацией о танцорах
    """

    pair = session.get(Pair, pair_id)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    return PairResponse(
        id=pair.id,
        dancer1=session.get(Dancer, pair.dancer1_id),
        dancer2=session.get(Dancer, pair.dancer2_id),
        created_at=pair.created_at
    )

@app.delete("/{pair_id}")
def delete_pair(pair_id: int, 
                session: SessionDep,
                current_user: dict = Depends(get_current_user)):
    """
    Удалить пару и обновить статусы танцоров.
    
    После удаления пары:
    - Проверяет участие танцоров в других парах
    - Обновляет статусы на IN_SEARCH если пар больше нет
    
    Args:
        pair_id (int): Уникальный идентификатор пары
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если пара не найдена

    Returns:
        dict: Результат операции
    """

    pair = session.get(Pair, pair_id)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    if current_user.user_type == "DANCER": 
        if not(current_user.dancer_id is None) and \
            current_user.dancer_id != pair.dancer1_id and \
            current_user.dancer_id != pair.dancer2_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No enough right to delete pair. " \
                "User should be on of participant of pair or admin." 
            )
    else:

        # Получаем связанных танцоров
        dancer1 = session.get(Dancer, pair.dancer1_id)
        dancer2 = session.get(Dancer, pair.dancer2_id)

        # Удаляем пару
        session.delete(pair)

        # Проверяем другие существующие пары
        dancer1_pairs = session.exec(
            select(Pair).where(
                (Pair.dancer1_id == dancer1.id) |
                (Pair.dancer2_id == dancer1.id)
            )
        ).all()

        dancer2_pairs = session.exec(
            select(Pair).where(
                (Pair.dancer1_id == dancer2.id) |
                (Pair.dancer2_id == dancer2.id)
            )
        ).all()

        # Обновляем статусы если нужно
        if not dancer1_pairs and dancer1.status == StatusType.IN_PAIR:
            dancer1.status = StatusType.IN_SEARCH
            session.add(dancer1)

        if not dancer2_pairs and dancer2.status == StatusType.IN_PAIR:
            dancer2.status = StatusType.IN_SEARCH
            session.add(dancer2)

        session.commit()
        return {"ok": True}
