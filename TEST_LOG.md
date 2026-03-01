# Test Log

## 2026-03-01 Robustness Sweep

- Timezone: `Asia/Shanghai`
- Window: `2026-03-01 12:44:32 +0800` to `2026-03-01 12:45:19 +0800`
- Commit under test: `6251bc0` (`main`)
- Execution mode: isolated temporary worktree

### Commands and Results

1. `python src/extract_data_test.py` -> PASS
2. `python src/backfill_regression_test.py` -> PASS
3. `python src/stability_test.py` -> PASS
4. `python src/test_glm_integration.py` -> PASS (`Ran 1 test`)
5. `python script_real_stress_test.py` -> PASS
6. `python src/extract_data_test.py` repeated 3 times -> PASS 3/3
7. `python script_real_stress_test.py` repeated 5 times -> PASS 5/5
8. Historical simulation checks:
   - `python src/extract_data.py --date 2026-02-24` -> `last_updated=2026-02-24 00:00:00`, `chart_data[-1].date=2026-02-24`
   - `python src/extract_data.py --date 2026-02-27` -> `last_updated=2026-02-27 00:00:00`, `chart_data[-1].date=2026-02-27`
   - `python src/extract_data.py --date 2026-03-01` -> `last_updated=2026-03-01 00:00:00`, `chart_data[-1].date=2026-03-01`
9. `npm run lint` -> PASS
10. `npm run build` -> PASS

### Notes

- Build emits a non-blocking bundle size warning (`>500 kB`).
- External market/news APIs remain a runtime dependency; current code has fallback behavior and did not fail during this sweep.
