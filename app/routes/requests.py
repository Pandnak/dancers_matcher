from fastapi import APIRouter, status, HTTPException, Depends
from models import Dancer, Request, Pair
from schemas import RequestCreate, RequestUpdate, RequestStatus, StatusType
from db.session import SessionDep
from sqlmodel import select
from auth_handler import get_current_user


app = APIRouter(prefix="/requests", tags=['requests'])

@app.post("/", status_code=status.HTTP_201_CREATED)
def create_request(request: RequestCreate,
                   session: SessionDep,
                   current_user: dict = Depends(get_current_user)) -> Request:
    """
    Создать новый запрос на партнерство между танцорами.

    Args:
        request (RequestCreate): Данные для создания запроса
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если отправитель или получатель не найдены

    Returns:
        Request: Созданный объект запроса
    """
    # Check if sender exists
    sender = session.get(Dancer, request.sender_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender dancer not found")

    if not(current_user.dancer_id is None) and current_user.dancer_id != sender.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No enough right to create request. " \
            "User should have an existing dancer_id." \
            "Dancer with dancer_id should exist.",
        )

    # Check if receiver exists
    receiver = session.get(Dancer, request.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver dancer not found")

    # Create new request
    db_request = Request(**request.dict(), status=RequestStatus.PENDING)
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


@app.get("/")
def read_requests(
    session: SessionDep,
) -> list[Request]:
    """
    Получить список всех запросов на партнерство.

    Args:
        session (SessionDep): Сессия базы данных

    Returns:
        list[Request]: Список объектов запросов
    """

    requests = session.exec(select(Request)).all()
    return requests

@app.get("/{request_id}")
def read_request(request_id: int, session: SessionDep) -> Request:
    request = session.get(Request, request_id)
    """
    Получить информацию о запросе по его ID.

    Args:
        request_id (int): Уникальный идентификатор запроса
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если запрос не найден

    Returns:
        Request: Объект запроса с указанным ID
    """
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@app.put("/{request_id}")
def update_request(
    request_id: int,
    request_update: RequestUpdate,
    session: SessionDep,
    current_user: dict = Depends(get_current_user),
) -> Request:
    """
    Обновить статус запроса на партнерство.

    При принятии запроса (ACCEPTED):
    - Проверяет возможность создания пары
    - Создает новую пару
    - Обновляет статусы танцоров

    Args:
        request_id (int): ID обновляемого запроса
        request_update (RequestUpdate): Новый статус запроса
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если запрос не найден
        HTTPException: 400 при нарушении условий создания пары

    Returns:
        Request: Обновленный объект запроса
    """

    db_request = session.get(Request, request_id)
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Обновляем статус
    db_request.status = request_update.status

    # Если запрос принят - обновляем статусы танцоров
    if db_request.status == RequestStatus.ACCEPTED:
        sender = session.get(Dancer, db_request.sender_id)
        receiver = session.get(Dancer, db_request.receiver_id)

        if sender.status != StatusType.IN_SEARCH or receiver.status != StatusType.IN_SEARCH:
            raise HTTPException(
                status_code=400,
                detail="Both dancers must be in 'in-search' status."
            )

        if sender.id == receiver.id:
            raise HTTPException(
                status_code=400,
                detail="You can send a request to yourself. Both dancers must have different id number."
            )

        if sender.sex == receiver.sex:
            raise HTTPException(
                status_code=400,
                detail="Both dancers must be of different genders."
            )

        # Проверка существующих пар
        existing_pair = session.exec(
            select(Pair).where(
                (Pair.dancer1_id.in_([sender.id, receiver.id])) |
                (Pair.dancer2_id.in_([sender.id, receiver.id]))
            )
        ).first()

        if existing_pair:
            raise HTTPException(
                status_code=400,
                detail="One or both dancers are already in a pair"
            )

        # Создаем новую пару
        new_pair = Pair(dancer1_id=sender.id, dancer2_id=receiver.id)
        session.add(new_pair)

        # Обновляем статусы танцоров
        sender.status = StatusType.IN_PAIR
        receiver.status = StatusType.IN_PAIR
        session.add(sender)
        session.add(receiver)

    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request

@app.delete("/{request_id}")
def delete_request(request_id: int, 
                   session: SessionDep, 
                   current_user: dict = Depends(get_current_user)):
    """
    Удалить запрос на партнерство.

    Args:
        request_id (int): Уникальный идентификатор запроса
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если запрос не найден

    Returns:
        dict: Результат операции
    """
    if current_user.user_type == "DANCER":
        if not(current_user.dancer_id is None) and current_user.dancer_id != request_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No enough right to delete request. " \
                "User should have an existing dancer_id." \
                "Dancer with dancer_id should exist and be the same delete user_id.",
            )
    else:
        request = session.get(Request, request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        session.delete(request)
        session.commit()
        return {"ok": True}
