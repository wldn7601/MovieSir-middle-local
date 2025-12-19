# backend/domains/recommendation/service.py

from sqlalchemy.orm import Session
from sqlalchemy import text

# [중요] 타 도메인 모델 Import
from backend.domains.movie.models import Movie, MovieOttMap, OttProvider
from backend.domains.recommendation.models import MovieLog, MovieClick
from . import schema

def get_hybrid_recommendations(db: Session, user_id: str, req: schema.RecommendationRequest, model_instance):
    """
    1. AI 모델(LightGCN) -> ID 리스트 추출
    2. DB -> 영화 상세 정보 조회
    """
    # 1. AI 모델 예측 (user_id를 int로 변환하거나 매핑 필요할 수 있음)
    # model_instance는 router에서 주입받거나 전역 변수로 로드된 것을 사용
    try:
        # 필터링 후에도 충분한 영화가 남도록 더 많이 요청
        recommended_movie_ids = model_instance.predict(
            user_id, 
            top_k=50,
            available_time=req.available_time,
            preferred_genres=req.genres if req.genres else None,
            preferred_otts=None  # OTT 필터링은 추후 구현 예정
        )
    except Exception as e:
        print(f"AI Model Error: {e}")
        recommended_movie_ids = []

    if not recommended_movie_ids:
        return []

    # 2. DB 조회 (CRUD 역할)
    # AI 모델은 tmdb_id를 반환하므로 tmdb_id로 조회
    movies = db.query(Movie).filter(Movie.tmdb_id.in_(recommended_movie_ids)).all()

    # 순서 보정 (AI가 추천한 순서대로 정렬) - tmdb_id 기준
    movies_map = {m.tmdb_id: m for m in movies}
    results = []
    
    # 필터링 통계
    filtered_counts = {
        'total': len(recommended_movie_ids),
        'not_in_db': 0,
        'adult': 0,
        'passed': 0
    }
    
    for mid in recommended_movie_ids:
        if mid not in movies_map:
            filtered_counts['not_in_db'] += 1
            continue
            
        m = movies_map[mid]
        
        # 성인 콘텐츠만 필터링 (AI 모델이 이미 장르/시간 고려함)
        if req.exclude_adult and m.adult:
            filtered_counts['adult'] += 1
            continue
        
        # ❌ 제거: 런타임 필터링 (AI 모델이 이미 처리)
        # ❌ 제거: 장르 필터링 (Track B는 장르 무시해야 함)
        
        results.append(m)
        filtered_counts['passed'] += 1
    
    # 필터링 통계 출력
    print(f"\n{'='*80}")
    print(f"[Backend Filter] AI 추천: {filtered_counts['total']}개")
    print(f"[Backend Filter] DB 없음: {filtered_counts['not_in_db']}개")
    print(f"[Backend Filter] 성인 제외: {filtered_counts['adult']}개")
    print(f"[Backend Filter] ✅ 최종 결과: {filtered_counts['passed']}개")
    print(f"[Backend Filter] ℹ️  런타임/장르 필터링은 AI 모델에서 처리됨")
    print(f"{'='*80}\n")
            
    return results

def log_click(db: Session, user_id: str, movie_id: int, provider_id: int):
    new_log = MovieClick(user_id=user_id, movie_id=movie_id, provider_id=provider_id)
    db.add(new_log)
    db.commit()

def mark_watched(db: Session, user_id: str, movie_id: int):
    stmt = text("""
        INSERT INTO movie_logs (user_id, movie_id, watched_at)
        VALUES (:uid, :mid, NOW())
        ON CONFLICT (user_id, movie_id) DO UPDATE SET watched_at = NOW()
    """)
    db.execute(stmt, {"uid": user_id, "mid": movie_id})
    db.commit()