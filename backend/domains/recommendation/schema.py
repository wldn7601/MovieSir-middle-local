# backend/domains/recommendation/schema.py

from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    available_time: int = 300  # 이용 가능 시간 (분) - AI 모델이 추천 모드 결정에 사용
    runtime_limit: int = 300   # 개별 영화 최대 런타임 (분)
    genres: List[str] = []
    exclude_adult: bool = True

class ClickLogRequest(BaseModel):
    provider_id: int

class MovieInfo(BaseModel):
    movie_id: int
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    vote_average: Optional[float] = None
    runtime: Optional[int] = None
    genres: Optional[List[str]] = None
    adult: bool
    popularity: Optional[float] = None
    
    class Config:
        from_attributes = True

class OttInfo(BaseModel):
    provider_id: int
    provider_name: str
    url: Optional[str] = None

class MovieDetailResponse(BaseModel):
    info: MovieInfo
    otts: List[OttInfo]
    tag_genome: Optional[dict] = None

class RecommendationResponse(BaseModel):
    results: List[MovieInfo]