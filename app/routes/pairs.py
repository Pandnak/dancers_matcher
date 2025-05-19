from fastapi import APIRouter, HTTPException
from models import Pair, Dancer, PairResponse
from schemas import StatusType
from db.session import SessionDep
from sqlmodel import select

app = APIRouter(prefix='/pairs', tags=['pairs'])


@app.get("/pairs/")
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

@app.get("/pairs/{pair_id}")
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

@app.delete("/pairs/{pair_id}")
def delete_pair(pair_id: int, session: SessionDep):
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