from __future__ import annotations

from fastapi import FastAPI

from backend.models.schemas import UserProfile
from backend.recommend.engine import recommend_for_frontend


app = FastAPI(title="甘肃高考志愿推荐系统")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend")
def recommend_api(profile: UserProfile) -> dict:
    return recommend_for_frontend(
        "data/processed/admission_records.csv",
        "data/processed/admission_metrics_long.csv",
        "configs/policy_rules.gansu.json",
        "configs/region_dict.gansu.json",
        profile,
    )
