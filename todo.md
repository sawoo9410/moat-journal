# Todo — 구현 명세

> 수정 세션은 이 파일을 읽고 구현한다. 이 파일 수정 금지.

남은 작업: **E. Moat Daily 단축 — 종합평가만 송출**.

---

## E. Moat Daily 메시지 단축

### 배경

현재 Moat Daily 요약 메시지는 종목당 호재(≤3) + 악재(≤3) + Valuation + 종합평가까지 모두 포함 → 종목당 ~24줄, 5종목 청크면 한 메시지 ~7KB로 Telegram 4096자 한도 초과 → `_split_message`가 다시 쪼개 가독성 저하.

월간 .md 파일에는 풀 기록(호재/악재/Valuation/종합평가) 보존이 가치 있음. **텔레그램 매일 요약에만 단축 적용**, 깊이는 일요일 detail로.

### E.1 변경 명세

| 항목 | 변경 |
|------|------|
| `companies/{TICKER}/{YYYY}/{YYYY-MM}.md` (월간 기록) | **변경 없음** — 호재/악재/Valuation/종합평가 풀 기록 유지 |
| Moat Daily 메시지 (매일) | **종합평가만** per ticker |
| 일요일 detail 메시지 | **변경 없음** — 호재 ≤5 + 악재 ≤5 + valuation + 종합평가 풀 유지 |
| 청크 크기 | **유지** (`summary_chunk_size: 5`, [!] 5종목씩) |

### E.2 메시지 포맷 (예상)

```
Moat Daily — 2026-05-15 (1/N)

━ GOOGL ━
호재는 Waymo 트립 +92%·검색 점유율 유지·AI 인프라 수요 확장이고, 악재는 FY26 capex $180~190B로 ROIC 분모 팽창·DOJ 항소 장기화·주가 +16.7% 선반영이며, 결과적으로 Castle 외벽은 견고하지만 ROIC 품질 erosion이 thesis 가정보다 빨라 추가매수보다 매출 기여도 확인이 우선인 악재 우위.

━ MCD ━
{종합평가}

[... 최대 5종목]
```

마지막 메시지 끝에 `안정: {티커 쉼표 나열}` 한 줄 추가.

### E.3 코드 수정 범위 — `automation/src/daily_moat.py`

#### `build_summary` 재작성

현재 호재/악재/Valuation/종합평가 블록을 모두 출력 → **종합평가만** 출력하도록 단순화.

```python
def build_summary_chunk(date: str, results: list[dict], chunk_idx: int, chunk_total: int, append_stable: list[str] | None = None) -> str:
    header = f"Moat Daily — {date} ({chunk_idx}/{chunk_total})"
    lines = [header, ""]
    for r in results:
        ticker = r["ticker"]
        comment = r["parsed"]["comment"].strip()
        if not comment:
            continue
        lines.append(f"━ {ticker} ━")
        lines.append(comment)
        lines.append("")
    if append_stable:
        lines.append(f"안정: {', '.join(append_stable)}")
    return "\n".join(lines).rstrip() + "\n"
```

호재/악재 컷 함수(`_top_n`), Valuation 압축 로직 등은 build_summary 경로에서 제거 (build_detail에는 유지).

#### `main()` 청크 송출 로직

[!] 종목(comment 있는 종목)을 `summary_chunk_size`(=5)로 분할 → 각 청크 `build_summary_chunk` 호출 → telegram_bot.send_message.

```python
flagged = [r for r in results if r.get("flag")]
stable = [r["ticker"] for r in results if not r.get("flag") and not r.get("error")]
chunk_size = cfg["schedule"].get("summary_chunk_size", 5)
chunks = [flagged[i:i+chunk_size] for i in range(0, len(flagged), chunk_size)] or [[]]
total = len(chunks)
for idx, chunk in enumerate(chunks, start=1):
    append_stable = stable if idx == total else None
    msg = build_summary_chunk(date, chunk, idx, total, append_stable=append_stable)
    telegram_bot.send_message(msg)
```

[!] 종목 0개 (전 종목 안정)이면 청크 1개 빈 chunk + 안정 라인만 송출.

### E.4 프롬프트 — 변경 없음

`automation/prompts/daily.md`는 현재대로 유지. 호재/악재/Valuation/종합평가 4개 섹션 모두 생성. 단지 텔레그램 송출 시점에 종합평가만 골라 보낼 뿐, **월간 .md 파일에는 풀 기록 그대로 저장**.

### E.5 검증 절차 (수정 세션 후)

1. `launchctl start com.moat-journal.daily` 1회 발사
2. 텔레그램 확인:
   - Moat Daily 메시지가 종목별 `━ TICKER ━ {종합평가}` 블록만 (호재/악재 bullet, Valuation 없음)
   - [!] 종목 5개 이상이면 청크 헤더 `(i/N)` 표시
   - 마지막 청크에만 `안정: ...` 라인
   - 한 메시지가 4096자 미만 (청크가 다시 분할되지 않음)
3. 월간 .md 파일은 그대로 풀 기록 보존 확인
4. 일요일이 아니면 detail 메시지 송출 없음 확인

문제 없으면 E 종결, todo 비우기.
