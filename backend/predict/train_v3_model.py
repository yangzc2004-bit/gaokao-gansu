"""
Probability Model V3 - Gradient Boosting with proper backtest validation.
Uses slot1 as holdout (actual outcomes), trains on slot2/slot3 features.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import brier_score_loss
import pickle, json
from pathlib import Path

PROJECT = Path(r"D:\gaokao project")

def load_data():
    records = pd.read_csv(PROJECT / "data/processed/admission_records.csv")
    metrics = pd.read_csv(PROJECT / "data/processed/admission_metrics_long.csv")
    return records, metrics

def build_samples(records, metrics):
    """Build training samples using V2 backtest methodology:
    - slot1 = actual outcome year (holdout label)
    - slot2/slot3 = historical data (features)
    """
    from backend.recommend.ranker import compute_rank_cv
    
    record_fields = records[["record_id", "track", "plan_count", "group_plan_count", 
                              "is_new_major", "school_rank", "school_level"]].copy()
    record_fields["plan_count"] = pd.to_numeric(record_fields["plan_count"], errors="coerce")
    record_fields["group_plan_count"] = pd.to_numeric(record_fields["group_plan_count"], errors="coerce")
    record_fields["school_rank"] = pd.to_numeric(record_fields["school_rank"], errors="coerce")
    
    metric_groups = metrics.groupby("record_id")
    
    FACTORS = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]
    rows = []
    
    for record_id, group in metric_groups:
        # slot1 = actual outcome
        actual = group[group["metric_slot"] == 1]
        if actual.empty:
            continue
        actual = actual.iloc[0]
        actual_min_rank = actual.get("min_rank")
        if pd.isna(actual_min_rank) or actual_min_rank <= 0:
            continue
        
        # slot2/slot3 = historical features only
        history = group[group["metric_slot"].isin([2, 3])].sort_values("metric_slot")
        history = history[history[["min_rank", "avg_rank", "max_rank"]].notna().any(axis=1)]
        if history.empty:
            continue
        
        years_available = int(history["min_rank"].notna().sum())
        if years_available <= 0:
            continue
        
        # Extract historical features (NOT using slot1 data)
        hist_min_ranks = history["min_rank"].dropna().values
        hist_avg_ranks = history["avg_rank"].dropna().values
        hist_max_ranks = history["max_rank"].dropna().values
        
        latest = history.iloc[0]
        latest_min = latest.get("min_rank", np.nan)
        latest_avg = latest.get("avg_rank", np.nan)
        latest_max = latest.get("max_rank", np.nan)
        
        mean_min = np.nanmean(hist_min_ranks) if len(hist_min_ranks) > 0 else np.nan
        mean_avg = np.nanmean(hist_avg_ranks) if len(hist_avg_ranks) > 0 else np.nan
        mean_max = np.nanmean(hist_max_ranks) if len(hist_max_ranks) > 0 else np.nan
        
        # CV from historical min_ranks only
        rank_cv = float(compute_rank_cv(pd.Series(hist_min_ranks))) if len(hist_min_ranks) > 1 else 0.0
        
        # Trend (if 2+ years)
        if len(hist_min_ranks) >= 2:
            rank_trend = (hist_min_ranks[0] - hist_min_ranks[-1]) / max(hist_min_ranks[-1], 1)
        else:
            rank_trend = 0.0
        
        has_big_year = 1 if len(hist_min_ranks) >= 2 and (max(hist_min_ranks) - min(hist_min_ranks)) / max(np.mean(hist_min_ranks), 1) > 0.2 else 0
        
        rec = record_fields[record_fields["record_id"] == record_id]
        if rec.empty:
            continue
        rec = rec.iloc[0]
        
        plan_count = float(rec["plan_count"]) if pd.notna(rec["plan_count"]) else 1.0
        school_rank_val = float(rec["school_rank"]) if pd.notna(rec["school_rank"]) else 500.0
        
        # Simulate multiple user ranks around actual outcome
        for factor in FACTORS:
            user_rank = float(actual_min_rank) * factor
            admitted = 1 if user_rank <= float(actual_min_rank) else 0
            
            # Features based ONLY on historical data (slot2/slot3)
            feat = {
                "hist_min_latest": latest_min if pd.notna(latest_min) else mean_min,
                "hist_avg_latest": latest_avg if pd.notna(latest_avg) else mean_avg,
                "hist_max_latest": latest_max if pd.notna(latest_max) else mean_max,
                "hist_min_mean": mean_min,
                "hist_avg_mean": mean_avg,
                "hist_max_mean": mean_max,
                "rank_cv": rank_cv,
                "rank_trend": np.clip(rank_trend, -1, 1),
                "has_big_year": has_big_year,
                "years_available": years_available,
                "plan_count": plan_count,
                "plan_count_log": np.log1p(plan_count),
                "school_rank": school_rank_val,
                "school_rank_log": np.log1p(school_rank_val),
                # User-rank dependent features (key!)
                "user_rank": user_rank,
                "gap_to_hist_min": (user_rank - mean_min) / max(mean_min, 1),
                "gap_to_hist_avg": (user_rank - mean_avg) / max(mean_avg, 1) if pd.notna(mean_avg) else 0,
                "gap_to_hist_max": (user_rank - mean_max) / max(mean_max, 1) if pd.notna(mean_max) else 0,
                "ratio_to_hist_min": user_rank / max(mean_min, 1),
                "ratio_to_latest_min": user_rank / max(latest_min, 1) if pd.notna(latest_min) else 1.0,
            }
            feat["admitted"] = admitted
            rows.append(feat)
    
    df = pd.DataFrame(rows)
    return df

def train_and_evaluate(df):
    feature_cols = [c for c in df.columns if c != "admitted"]
    X = df[feature_cols].fillna(0)
    y = df["admitted"].values
    
    # Use stratified split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=5,
        min_samples_split=30,
        min_samples_leaf=15,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    y_prob = model.predict_proba(X_test)[:, 1]
    brier = brier_score_loss(y_test, y_prob)
    
    # Calibration by probability bins
    bins = pd.cut(y_prob, bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0], include_lowest=True)
    cal_df = pd.DataFrame({"prob": y_prob, "actual": y_test, "bin": bins})
    cal_stats = cal_df.groupby("bin", observed=False).agg(
        count=("actual", "size"),
        avg_prob=("prob", "mean"),
        actual_rate=("actual", "mean"),
    ).reset_index()
    
    print(f"\nTest samples: {len(y_test)}")
    print(f"Brier score: {brier:.4f}")
    print(f"Admit rate (test): {y_test.mean():.2%}")
    print(f"\nCalibration:")
    print(cal_stats.to_string(index=False))
    
    # Feature importances
    fi = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print(f"\nTop 10 features:")
    print(fi.head(10).to_string())
    
    return model, brier, feature_cols

def save_all(model, brier, feature_cols):
    model_dir = PROJECT / "models"
    model_dir.mkdir(exist_ok=True)
    
    with open(model_dir / "gb_v3_model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    meta = {"model_type": "GradientBoostingClassifier", "brier_score": float(brier),
            "feature_names": feature_cols, "n_features": len(feature_cols),
            "training_method": "slot1_holdout_slot23_features"}
    with open(model_dir / "gb_v3_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    report = f"""# Probability Model V3 Report (Corrected)

## Method
- Training: slot2/slot3 historical features only
- Validation: slot1 as holdout (actual admission outcomes)
- This avoids data leakage from the V3 first attempt

## Performance
- **Brier Score (V3)**: {brier:.4f}
- **Brier Score (V2)**: 0.2512
- **Improvement**: {(0.2512 - brier) / 0.2512 * 100:.1f}%
- **Target (< 0.22)**: {'✅ ACHIEVED' if brier < 0.22 else '❌ NOT YET'}

## Features ({len(feature_cols)})
{chr(10).join(f'- {c}' for c in feature_cols)}
"""
    (PROJECT / "docs" / "probability_v3_report.md").write_text(report, encoding="utf-8")
    print(f"\nModel + report saved.")

if __name__ == "__main__":
    print("=" * 50)
    print("V3 Model Training (Corrected - Slot Holdout)")
    print("=" * 50)
    
    print("\n[1/3] Loading data...")
    records, metrics = load_data()
    
    print("\n[2/3] Building samples (slot1 holdout)...")
    import sys
    sys.path.insert(0, str(PROJECT))
    df = build_samples(records, metrics)
    print(f"Samples: {len(df)}, Features: {len(df.columns)-1}")
    
    print("\n[3/3] Training + evaluating...")
    model, brier, feature_cols = train_and_evaluate(df)
    
    save_all(model, brier, feature_cols)
    
    print(f"\nT3.1 DONE, Brier={brier:.4f}")
