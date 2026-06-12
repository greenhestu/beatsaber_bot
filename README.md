# beatsaber_bot

[![BSCK](https://img.shields.io/badge/BSCK-282b30.svg?logo=discord&style=for-the-badge)](https://discord.gg/SEFBZrG)

Beat Saber 플레이어를 위한 한국어 Discord 봇.
[ScoreSaber](https://scoresaber.com) 프로필을 Discord 계정에 연동해서 PP/랭킹을
조회하고, 등록된 유저의 PP 변동을 **매일 기록**해 전적 조회·그래프·유저 간
비교 기능을 제공한다.

## 주요 기능 (명령어)

접두사는 `!`. 모든 명령은 한글/영문 축약형을 함께 지원한다.

| 명령어 | 축약형 | 설명 |
|---|---|---|
| `!등록 <스코어세이버 주소>` | `!r` | 내 Discord 계정에 ScoreSaber 프로필 연동 (재등록 가능) |
| `!검색 <닉네임>` | `!s` | 닉네임으로 ScoreSaber 검색, 상위 5명 중 이모지 반응으로 골라 등록 |
| `!타등록 <discord_id> <주소>` | `!or` | 다른 사람의 계정을 대신 등록 |
| `!추가 <스코어세이버 주소>` | `!a` | 일일 PP 기록 대상에 추가 (다음 날부터 기록) |
| `!내정보` | `!i` | 내 프로필 embed — 세계/국내 랭킹, PP, 랭크곡 평균 정확도, 오늘 얻은 PP |
| `!타정보 <discord_id>` | `!oi` | 등록된 다른 유저의 프로필 embed |
| `!내전적 [개수] [csv\|txt]` | `!h` | 일자별 PP·랭킹·증가량 기록 출력 (기본 20개, 파일로 저장 가능) |
| `!그래프 [개수]` | `!g` | PP 변화 그래프 PNG (pchip 보간, 기본 최근 20개) |
| `!비교 [개수] - 주소1,주소2,...` | `!c` | 최대 7명의 PP 변화를 한 그래프에 비교 |
| `!랭킹 [국가코드]` | | ScoreSaber 전체/국가 랭킹 링크 |
| `!곡추천 <리더보드 주소\|id> [개수]` | `!rec` | ScoreSaber 랭크곡 추천 — 리더보드 유저 서열이 유사한 곡 |
| `!블곡추천 <리더보드 주소\|id> [개수]` | `!blrec` | BeatLeader 랭크곡 추천 (위와 동일 방식) |
| `!유저추천 [스코어세이버 주소] [개수]` | `!urec` | 나(또는 지정 유저)보다 pp 높은 유저 중 top곡 구성이 비슷한 유저 + farm 후보곡 |

## 구조

```
discord_bot.py      # 엔트리포인트 — 봇 명령 정의·입력 파싱·응답 (discord.py 1.7)
bot_command_set.py  # 명령 구현 — ScoreSaber API 조회, 전적 파일 읽기, matplotlib 그래프
kr_ranker.py        # [일일 배치] 한국 랭킹 1~100위의 PP/순위를 기록
added_user.py       # [일일 배치] !추가 로 등록된 유저(Added_User_List.txt)의 PP를 기록
userdata.bin        # Discord ID → ScoreSaber ID 매핑 (pickle dict)
Added_User_List.txt # 일일 기록 대상 유저 목록 (한 줄당 ScoreSaber ID)
gulim.ttc           # 그래프 한글 렌더링용 굴림 폰트
history.txt         # 전적 기록 파일 예시
```

### 데이터 흐름

1. `kr_ranker.py`와 `added_user.py`를 **매일 1회**(예: cron, 새벽 5:30) 실행하면
   유저별 전적이 `data/PP_text/<scoresaber_id>.txt`에 한 줄씩 누적된다:
   ```
   2020-9-17, 4855.24, Rank: 76, Name: <닉네임>
   ```
   매월 1일에는 `nextmonth` 구분선이 들어간다. 같은 날 중복 실행은 자동 스킵.
2. 봇의 `!내전적`/`!그래프`/`!비교`는 이 텍스트 파일을 읽어 증가량 계산·시각화만
   수행한다 (조회 시 ScoreSaber 호출 없음). `!내정보`/`!검색`만 실시간 API 조회.

## 설치 및 실행

```bash
pip install discord.py==1.7.3 requests beautifulsoup4 matplotlib scipy numpy

# 1. 봇 토큰: 레포 루트에 token.txt 생성, 첫 줄에 토큰 입력 (# 뒤는 주석으로 무시)
# 2. 폰트: gulim.ttc를 /usr/share/fonts/에 복사 (그래프 한글용)
# 3. 데이터 디렉토리 생성
mkdir -p data/PP_text

# 봇 실행
python3 discord_bot.py

# 일일 기록 (crontab 예시 — 매일 05:30)
# 30 5 * * * cd /path/to/beatsaber_bot && python3 kr_ranker.py && python3 added_user.py
```

`token.txt`, `data/`, `graph.png` 등 런타임 산출물은 `.gitignore`에 포함되어 있다.

## 곡/유저 추천 (`recommend/`)

리더보드 **topology** 기반 추천 기능. 곡 추천은 "두 곡의 리더보드에 공통으로
등장하는 유저들의 순위 순서가 얼마나 일치하는가"(Spearman 순위상관 + 실력
효과를 제거한 잔차 상관)로 유사도를 계산한다 — 같은 부류(acc형/연타형/테크형)
유저가 상위권에 오는 곡끼리 묶인다. 유저 추천은 top-100 pp곡을 위치 가중
(0.965^i) cosine으로 비교해, 나보다 pp 높은 유저 중 베스트 곡 구성이 가장
비슷한 유저와 그 유저의 farm 곡(내가 아직 안 친 고pp 곡)을 보여준다.

```
recommend/
├── ss_maps/   # ScoreSaber 곡 추천 — ★9–11 랭크 991곡 × 리더보드 상위 240명
├── bl_maps/   # BeatLeader 곡 추천 — ★10–12 랭크 648곡 × 상위 240명
└── ss_users/  # ScoreSaber 유저 추천 — 전역 상위 3000명 × top-100 pp곡
```

### 데이터 준비 (최초 1회 + 주기 갱신)

추천 데이터는 용량 문제로 git에 포함되지 않는다 (`recommend/*/data/` gitignore).
봇 명령은 **로컬 데이터만 읽으므로 조회 시 API 호출이 없다.** 수집 스크립트는
각 사이트의 레이트리밋(ScoreSaber 400req/min, BeatLeader 50req/10s) 아래로
자동 페이싱되며, 중단돼도 재실행하면 이어받는다.

```bash
cd recommend/ss_maps  && python3 fetch.py catalog && python3 fetch.py scores  # ~80분
cd recommend/bl_maps  && python3 fetch.py                                     # ~9분
cd recommend/ss_users && python3 fetch.py                                     # ~9분
```

수집 범위(별 구간, 인원수)와 유사도 산식 세부는 `recommend/README.md` 참고.
갱신 주기는 주 1회면 충분하다 (갱신 시 기존 `data/*.jsonl` 삭제 후 재수집).

## 참고 / 제한사항

- 봇 상태 메시지대로 **오전 5:30~40은 일일 기록 시간**이라 응답이 느릴 수 있다.
- `bot_command_set.py`/`added_user.py`의 프로필 조회는 구버전
  `new.scoresaber.com/api` 엔드포인트를 사용한다. 현재는
  `scoresaber.com/api`로 통합되었으므로 (`kr_ranker.py`는 이미 신버전 사용)
  동작하지 않으면 URL을 교체해야 한다.
- `requirements.txt`는 운영 머신의 `pip freeze` 전체 덤프라 실제 필요한 패키지는
  위 설치 명령의 6개뿐이다.
- 한국/일본 유저에게는 한국어, 그 외에는 영어로 프로필을 출력한다.

## TODO

- `/` (슬래시) 명령어 지원
- log 메시지 파일로 보관하기

## License

MIT © 2021 greenhestu
