# ss-topology — Beat Saber 랭크곡/유저 topology 도구 3종

각 디렉토리는 독립적으로 사용 가능 (의존성: python3 표준 라이브러리만).
모든 fetch는 resume 지원 — 중단돼도 재실행하면 이어서 받는다.

## 1. `ss_maps/` — ScoreSaber 곡 분류

랭크 난이도 중 별점 높은 순 3600개는 맵당 상위 240명의 리더보드 순위로
맵 topology DB를 만들고, 3600곡 이후 모든 랭크곡은 1페이지(상위 12명)를
저장해 기본 rank10 분석이 가능하게 한다.

```bash
cd ss_maps
python3 fetch.py catalog             # 전체 ranked 카탈로그
python3 fetch.py scores              # 상위 3600개 맵의 상위 240 스코어 수집
python3 fetch.py scores-rest-page1   # 3600곡 이후 랭크곡의 상위 12 스코어 수집
python3 similar.py 313895 20            # DONUT HOLE과 유사한 맵 top 20
python3 similar.py 313895 20 --playlist=out.bplist  # 결과를 플레이리스트로 저장
python3 similar.py <id> <N> --rebuild   # jsonl에서 topology.db 재빌드
python3 analyze_rank10_bins.py --output data/rank10_top10pct_pp450.md
```

- 레이트리밋: 400 req/min → 기본 20 req/10s 토큰버킷으로 여유 있게 제한
- 리더보드 scores 엔드포인트는 12개/페이지 고정 (limit 무시) → 비용의 원인
- 카탈로그 갱신 시 `created_date`, `ranked_date`, `qualified_date`,
  `loved_date`를 함께 저장
- 범위 변경: 환경변수 `SS_MAPS_MAP_LIMIT`, `SS_MAPS_TOP_N`,
  `SS_MAPS_RATE_PER_WINDOW`, `SS_MAPS_RATE_WINDOW`, `SS_MAPS_WORKERS`
- `analyze_rank10_bins.py`는 `leaderboards.json`, `map_scores.jsonl`,
  `map_scores_tail12.jsonl`을 읽고 0.1성 bin 안에서 10등 정확도가 상위
  10%이며 10등 pp가 450 이상인 곡을 정리한다. `--min-stars`,
  `--max-stars`, `--pp-min`, `--format csv|json|markdown`으로 범위를 조절한다.

## 2. `bl_maps/` — BeatLeader 곡 분류

BeatLeader 랭크 난이도 중 별점 높은 순 2000개 × 상위 240명. 동일한 유사도 산식.

```bash
cd bl_maps
python3 fetch.py                  # 카탈로그+스코어 한번에, resume 지원
python3 similar.py 11c7491 20     # BL DONUT HOLE과 유사한 맵
```

- 레이트리밋: 50 req/10s → 40/10s로 제한
- `count=100` 지원이라 맵당 3페이지로 충분 (SS보다 ~9배 저렴)
- 카탈로그에 BL 공식 acc/pass/tech 레이팅, speed/style 태그 포함
- 범위 변경: 환경변수 `BL_MAPS_MAP_LIMIT`, `BL_MAPS_TOP_N`,
  `BL_MAPS_RATE_MAX`, `BL_MAPS_RATE_WINDOW`, `BL_MAPS_WORKERS`

## 3. `ss_users/` — ScoreSaber 유저 분류

전역 상위 3000명 각각의 top-100 pp 곡을 수집 (유저당 1 call).
특정 유저를 주면, **그보다 pp가 높은 유저 중** top pp 곡 구성이 가장 비슷한
유저들을 찾는다. 추천 맵은 표시된 유사 유저 중 2명 이상에게 반복 등장하고,
그 곡을 가진 비교 유저 모두가 타깃의 ScoreSaber `+1PP` 기준보다 높은 raw PP를
기록했으며, 타깃의 현재 top-100에는 없는 곡만 보여준다.

```bash
cd ss_users
python3 fetch.py                      # ~3060 calls, resume 지원
python3 similar.py <id 또는 이름> 15
```

- 유사도: top-100 곡을 pp 가중 벡터로 보고 cosine + 공통 곡 수
- Farm picks: ScoreSaber v2 프로필의 최신 `stats.plusOnePP`를 조회하고,
  반복 인원 수와 비교 유저들의 최저 raw PP 순으로 후보를 정렬
- 범위 변경: 환경변수 `SS_USERS_N_PLAYERS`, `SS_USERS_TOP_SCORES`,
  `SS_USERS_RATE_PER_MIN`, `SS_USERS_WORKERS`

## 전체 데이터 수집

ScoreSaber 곡별 유저 분포와 유저별 top pp 데이터를 기본 정책으로 한번에 받으려면:

```bash
./fetch_data.sh
```

기본값은 `SS_MAPS_MAP_LIMIT=2000`, `SS_MAPS_TOP_N=240`,
`SS_MAPS_RATE_PER_MIN=180`, `SS_USERS_N_PLAYERS=3000`,
`SS_USERS_TOP_SCORES=100`, `SS_USERS_RATE_PER_MIN=180`이다.

## 유사도 산식 (곡 분류 공통)

- `spear`: 두 맵의 공통 유저들의 순위 순서 일치도 (Spearman)
- `resid`: 유저별 전체 평균 백분위를 뺀 잔차의 상관 — 실력 효과 제거 후
  "이 맵에서 유난히 잘하는 사람"의 패턴 일치도 (acc형/연타형 판별 신호)
- `rbo`: 상위권 가중 리스트 겹침 (참고용)
- `score = 0.5*spear + 0.5*resid`, 각각 `n/(n+25)`로 수축 (n=공통 유저 수)
- 공통 유저 20명 미만 쌍은 제외. n≥50 결과가 신뢰도 높음.
