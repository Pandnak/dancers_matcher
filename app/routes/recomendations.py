from typing import List
import numpy as np
from fastapi import HTTPException, Query, APIRouter
from models import Dancer
from db.session import SessionDep
from sqlmodel import select
from schemas import StatusType

app = APIRouter(prefix='/recomendations', tags=['recomendations'])


LEVEL_ORDER = {
    "S": 8,
    "M": 7,
    "A": 6,
    "B": 5,
    "C": 4,
    "D": 3,
    "E": 2,
    "N": 1,
}

def get_level_value(level: str | None) -> int:
    if not level:
        return 0
    return LEVEL_ORDER.get(level.upper(), 0)

@app.get("/base/{dancer_id}", response_model=List[Dancer])
def get_basic_recommendations(
    dancer_id: int,
    session: SessionDep
) -> List[Dancer]:
    """
    Get basic partner recommendations based on compatibility rules.
    
    Recommends dancers who:
    - Have opposite sex
    - Share the same dance style
    - Have similar skill level (±1 level)
    - Are currently in 'IN_SEARCH' status
    
    Args:
        dancer_id (int): ID of the dancer seeking recommendations
        session (SessionDep): Database session dependency
        
    Returns:
        List[Dancer]: List of compatible dancers ordered by basic compatibility
        
    Raises:
        HTTPException: 404 if dancer not found
    """

    dancer = session.get(Dancer, dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")

    # Basic filters
    current_level = get_level_value(dancer.level)

    # Query compatible dancers
    query = select(Dancer).where(
        Dancer.id != dancer_id,
        Dancer.sex != dancer.sex.value,
        Dancer.status == StatusType.IN_SEARCH,
        Dancer.style == dancer.style
    )

    eligible_dancers = session.exec(query).all()

    # Filter by level similarity
    recommended = []
    for dancer in eligible_dancers:
        dancer_level = get_level_value(dancer.level)
        if abs(dancer_level - current_level) <= 1:
            recommended.append(dancer)

    return recommended

@app.get("/knn/{dancer_id}", response_model=List[Dancer])
def get_knn_recommendations(
    dancer_id: int,
    session: SessionDep,
    k: int = Query(default=5, ge=1, le=20)
) -> List[Dancer]:
    """
    Get K-nearest neighbors recommendations with compatibility filtering.
    
    First applies basic compatibility filters, then uses KNN algorithm to find
    the most similar dancers based on:
    - Skill level (numeric mapping)
    - Age
    - Height
    
    Features are normalized before distance calculation.
    
    Args:
        dancer_id (int): ID of the dancer seeking recommendations
        session (SessionDep): Database session dependency
        k (int, optional): Number of neighbors to return. Between 1-20. Defaults to 5.
        
    Returns:
        List[Dancer]: Top K most similar compatible dancers ordered by similarity
        
    Raises:
        HTTPException: 
            404 if dancer not found
            400 if dancer's age or height information is missing
            
    Notes:
        Requires dancer to have both age and height specified in their profile
        Uses Euclidean distance on normalized features
        Starts with basic compatibility-filtered candidates
    """

    current_dancer = session.get(Dancer, dancer_id)
    if not current_dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")

    if not current_dancer.age or not current_dancer.height:
        raise HTTPException(
            status_code=400,
            detail="Age and height required for KNN recommendations"
        )

    # Get base recommendations
    base_recommendations = get_basic_recommendations(dancer_id, session)

    # Prepare feature vectors
    features = []
    valid_dancers = []

    for dancer in base_recommendations:
        if dancer.age and dancer.height and dancer.level:
            level_val = get_level_value(dancer.level)
            features.append([level_val, dancer.age, dancer.height])
            valid_dancers.append(dancer)

    if not features:
        return []

    # Prepare current dancer's features
    current_features = np.array([
        get_level_value(current_dancer.level),
        current_dancer.age,
        current_dancer.height
    ])

    # Normalize features
    features_array = np.array(features)
    normalized = (features_array - features_array.mean(axis=0)) / (features_array.std(axis=0) + 1e-8)
    current_normalized = (current_features - features_array.mean(axis=0)) / (features_array.std(axis=0) + 1e-8)

    # Calculate distances
    distances = np.linalg.norm(normalized - current_normalized, axis=1)

    # Get top K indices
    sorted_indices = np.argsort(distances)
    top_k_indices = sorted_indices[:k]

    return [valid_dancers[i] for i in top_k_indices]
