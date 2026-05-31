# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업:
- **G. 로그 월별 분리** — `daily-2026-05.log` 식으로 누적 (3개 wrapper 미구현)
- **H. dead code 정리** — `_build_ticker_block` 미사용 제거

> E(Moat Daily 단축)·F(펀더멘털 yfinance 교체 + 폴백)는 평가에서 정합 완료 확인되어 제거됨.

---

## G. 로그 월별 분리

### 배경

현재 wrapper들이 단일 파일에 무한 append (`daily.log`, `daily-launchd.log`, `rollup.log`, `token-refresh.log`). 회전 없음. 월 경계로 파일을 갈라 누적하고 싶음: `daily-2026-05.log`, `daily-2026-06.log` …

### G.1 방식 — plist 수정 없이 wrapper에서 처리

각 wrapper 상단(`cd` 직후, 토큰 주입/echo 이전)에 월별 파일로 **전체 출력 리다이렉트**:

```bash
mkdir -p automation/logs
MONTH="$(date +%Y-%m)"
exec >> "automation/logs/daily-$MONTH.log" 2>&1
```

- `exec >> ... 2>&1` 이후 모든 wrapper echo + python 출력이 월별 파일 하나로 감 → 기존 `daily.log` + `daily-launchd.log` 이원화가 **단일 월별 파일로 통합**.
- 따라서 `daily_moat.sh` 끝의 `... | tee -a automation/logs/daily.log` 파이프 **제거**, `"$PYTHON" automation/src/daily_moat.py` 만 실행 (pipefail 우려도 사라짐).
- plist `StandardOutPath`/`StandardErrorPath`는 그대로 둠 — `exec` 이후엔 거의 빈 채로 남고, exec 이전 치명적 실패(bash 기동 실패 등)만 잡는 안전망. plist 편집 불필요.

### G.2 적용 대상 wrapper

| wrapper | 월별 파일명 |
|---------|-------------|
| `automation/cron/daily_moat.sh` | `daily-$MONTH.log` |
| `automation/cron/rollup.sh` | `rollup-$MONTH.log` (기존 `tee -a rollup.log` 제거) |
| `automation/cron/refresh_token.sh` | `token-refresh-$MONTH.log` (기존 `LOG=` 고정경로를 월별로) |

각 wrapper 동일 패턴 적용. `refresh_token.sh`는 `LOG` 변수를 `automation/logs/token-refresh-$(date +%Y-%m).log`로 바꾸거나 동일 `exec` 패턴으로 통일.

### G.3 기존 로그 / gitignore

- 기존 `daily.log`/`daily-launchd.log`/`rollup.log`/`token-refresh.log`는 그대로 둠(건드리지 않음). 새 쓰기만 월별로.
- `.gitignore`의 `automation/logs/`가 `*-YYYY-MM.log` 전부 커버 → 추가 설정 불필요.

### G.4 검증 (수정 세션 후)

1. `bash automation/cron/daily_moat.sh` 수동 1회 → `automation/logs/daily-2026-05.log` 생성·기록 확인(wrapper 헤더 + python 출력 한 파일에).
2. plist 발사(`launchctl start com.moat-journal.daily`) 후에도 월별 파일에 정상 적재 확인.
3. 월 경계 자동 분리는 `date +%Y-%m`이 보장(다음 달 첫 실행 시 새 파일).

---

## H. dead code 정리

평가에서 발견: `automation/src/daily_moat.py`의 `_build_ticker_block`(현 :133 부근)이 E 단축 이후 어디서도 호출되지 않음 (`build_summary_chunks`·`build_detail` 모두 자체 라인 빌드). 미사용 함수 제거.

- `_build_ticker_block` 삭제. 이 함수에서만 쓰이고 다른 데서 안 쓰이는 헬퍼가 있으면 같이 정리 (단 `_normalize_lines`·`_top_n`은 `build_detail`에서 사용 중 → 유지).

G·H 모두 처리되면 종결, todo 비우기.
