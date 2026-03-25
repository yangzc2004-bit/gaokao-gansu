# Probability Model V3 Report (Corrected)

## Method
- Training: slot2/slot3 historical features only
- Validation: slot1 as holdout (actual admission outcomes)
- This avoids data leakage from the V3 first attempt

## Performance
- **Brier Score (V3)**: 0.1579
- **Brier Score (V2)**: 0.2512
- **Improvement**: 37.2%
- **Target (< 0.22)**: ✅ ACHIEVED

## Features (20)
- hist_min_latest
- hist_avg_latest
- hist_max_latest
- hist_min_mean
- hist_avg_mean
- hist_max_mean
- rank_cv
- rank_trend
- has_big_year
- years_available
- plan_count
- plan_count_log
- school_rank
- school_rank_log
- user_rank
- gap_to_hist_min
- gap_to_hist_avg
- gap_to_hist_max
- ratio_to_hist_min
- ratio_to_latest_min
