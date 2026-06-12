# ss-topology — Beat Saber 랭크곡/유저 topology 도구 3종

각 디렉토리는 독립적으로 사용 가능 (의존성: python3 표준 라이브러리만).
모든 fetch는 resume 지원 — 중단돼도 재실행하면 이어서 받는다.

## 1. `ss_maps/` — ScoreSaber 곡 분류

★9–11 랭크 난이도 991개 × 맵당 상위 240명의 리더보드 순위로 맵 topology DB를
만들고, 특정 맵과 "유저 서열 패턴"이 유사한 맵을 찾는다.

```bash
cd ss_maps
python3 fetch.py catalog   # ★7.13+ 카탈로그 (180 calls)
python3 fetch.py scores    # 상위 240 스코어 수집 (~19.5k calls, ~80분)
python3 similar.py 313895 20            # DONUT HOLE과 유사한 맵 top 20
python3 similar.py <id> <N> --rebuild   # jsonl에서 topology.db 재빌드
```

- 레이트리밋: 400 req/min → 370/min 토큰버킷으로 제한
- 리더보드 scores 엔드포인트는 12개/페이지 고정 (limit 무시) → 비용의 원인
- 범위 변경: fetch.py 상단 `FETCH_MIN_STAR/FETCH_MAX_STAR/TOP_N`

## 2. `bl_maps/` — BeatLeader 곡 분류

★10–12 랭크맵 648개 × 상위 240명. 동일한 유사도 산식.

```bash
cd bl_maps
python3 fetch.py                  # 카탈로그+스코어 한번에 (~2k calls, ~9분)
python3 similar.py 11c7491 20     # BL DONUT HOLE과 유사한 맵
```

- 레이트리밋: 50 req/10s → 40/10s로 제한
- `count=100` 지원이라 맵당 3페이지로 충분 (SS보다 ~9배 저렴)
- 카탈로그에 BL 공식 acc/pass/tech 레이팅, speed/style 태그 포함

## 3. `ss_users/` — ScoreSaber 유저 분류

전역 상위 3000명 각각의 top-100 pp 곡을 수집 (유저당 1 call).
특정 유저를 주면, **그보다 pp가 높은 유저 중** top pp 곡 구성이 가장 비슷한
유저를 찾고, 그 유저가 했지만 타깃이 안 한 상위 pp 맵(= 다음에 칠 곡 후보)을
보여준다.

```bash
cd ss_users
python3 fetch.py                      # ~3060 calls, ~9분
python3 similar.py <id 또는 이름> 15
```

- 유사도: top-100 곡을 pp 가중 벡터로 보고 cosine + 공통 곡 수

## 유사도 산식 (곡 분류 공통)

- `spear`: 두 맵의 공통 유저들의 순위 순서 일치도 (Spearman)
- `resid`: 유저별 전체 평균 백분위를 뺀 잔차의 상관 — 실력 효과 제거 후
  "이 맵에서 유난히 잘하는 사람"의 패턴 일치도 (acc형/연타형 판별 신호)
- `rbo`: 상위권 가중 리스트 겹침 (참고용)
- `score = 0.5*spear + 0.5*resid`, 각각 `n/(n+25)`로 수축 (n=공통 유저 수)
- 공통 유저 20명 미만 쌍은 제외. n≥50 결과가 신뢰도 높음.
