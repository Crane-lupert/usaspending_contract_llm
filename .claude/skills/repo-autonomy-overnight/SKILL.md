---
name: repo-autonomy-overnight
description: 레포 폴더 하에서 모든 웹 검색 및 모든 파일에 대한 CRU(Create/Read/Update) 작업을 무조건 허용하여 overnight 자율 작업이 중단 없이 진행되도록 보장한다. 파괴적 작업(삭제·force push·git reset --hard 등)은 유지적 안전을 위해 계속 차단한다.
license: MIT
version: 1.0.0
---

# Repo Autonomy (Overnight Mode)

> 사용자 부재 중에도 에이전트가 permission prompt 에 막히지 않고 작업을 지속할 수 있도록, **해당 레포 폴더 하에서의 Create/Read/Update + 웹 접근**을 무조건 허용한다. 삭제·파괴적 변경은 여전히 차단.

## 설치 (신규 레포에 적용)

### 1. 스킬 파일 복사

`<repo>/.claude/skills/repo-autonomy-overnight/SKILL.md` 경로로 이 파일을 복사한다.

### 2. `<repo>/.claude/settings.json` 에 아래 permissions 블록 병합

**원칙**: 경로는 해당 레포 폴더로 한정. `./**` 또는 절대경로로. 시스템 전체를 오픈하지 않는다.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash",
      "Edit(./**)",
      "Write(./**)",
      "WebSearch",
      "WebFetch",

      "Bash(mkdir -p ./:*)",
      "Bash(mkdir ./:*)",
      "Bash(touch ./:*)",
      "Bash(cp:./**)",
      "Bash(mv:./**)",

      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(wc:*)",
      "Bash(echo:*)",

      "Bash(git init:*)",
      "Bash(git add:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git commit:*)",
      "Bash(git branch:*)",
      "Bash(git checkout:*)",

      "Task",
      "TodoWrite"
    ],
    "deny": [
      "Bash(rm:*)",
      "Bash(rmdir:*)",
      "Bash(del:*)",
      "Bash(unlink:*)",
      "Bash(shred:*)",
      "Bash(truncate:*)",
      "Bash(dd:*)",
      "Bash(mkfs:*)",
      "Bash(format:*)",

      "Bash(git clean:*)",
      "Bash(git reset --hard:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git branch -D:*)"
    ]
  }
}
```

라이브 거래 경로가 있는 레포는 추가 `deny` 를 병합한다:

```json
{
  "permissions": {
    "deny": [
      "Edit(./live/**)",
      "Write(./live/**)",
      "Edit(./positions/**)",
      "Write(./positions/**)",
      "Edit(./orders/**)",
      "Write(./orders/**)",
      "Edit(./.env.live)",
      "Write(./.env.live)",
      "Edit(./.env.prod)",
      "Write(./.env.prod)"
    ]
  }
}
```

> Claude Code 의 deny 규칙은 allow 보다 우선. 즉 `Write(./**)` 이 있어도 `Write(./live/**)` 차단이 먼저 적용된다.

### 3. (선택) PreToolUse hook 병행

권한 JSON 으로 막히지 않는 조건부 로직(예: 매니페스트 기반 동적 차단)은 `.claude/hooks/` 스크립트로 보강.

## 사용 조건 (언제 이 스킬을 레포에 설치해야 하는가)

다음 중 하나라도 해당하면 **설치 권장**:
- 장시간 overnight 자율 작업 가능성이 있음
- 대량 파일 일괄 생성/수정 작업(매니페스트·배치)
- sub-agent 병렬 작업이 잦음
- 사용자가 자리를 비우는 빈도가 높음

설치 **금지** 경우:
- 라이브 주문 집행 코드만 다루는 순수 실전 레포 (`live-only` 성격) — CRU 허용이 사고 경로가 될 수 있음
- 외부 비밀(시크릿) 다수 포함 레포

## 안전 경계 (절대 깨지 않음)

- **파괴적 Bash 는 여전히 deny**: `rm`, `rmdir`, `del`, `unlink`, `shred`, `truncate`, `dd`, `mkfs`, `format`
- **git 파괴적 옵션 deny**: `git clean`, `git reset --hard`, `git push --force`, `git branch -D`
- **레포 외부 경로 CRU 금지**: `Edit(./**)`, `Write(./**)` 는 레포 루트 하위만 허용. 외부는 별도 승인.
- **라이브 경로 deny 병행 원칙**: 실거래가 있는 레포는 `live/`, `positions/`, `orders/`, `.env.live` 등을 추가 deny 로 묶는다.

## 검증 체크리스트

신규 레포에 적용 후 다음을 확인:

- [ ] `.claude/settings.json` 에 permissions.allow / deny 가 병합됐다
- [ ] `Edit(./**)` / `Write(./**)` 가 허용돼 있다
- [ ] `WebSearch` / `WebFetch` 가 허용돼 있다
- [ ] 파괴적 Bash deny 리스트가 유지돼 있다
- [ ] 라이브 경로가 있다면 추가 deny 가 병합됐다
- [ ] 메타-하네스 레포(`d:\vscode\meta-harness`) 는 이미 적용돼 있다 (확인만)
- [ ] `targets.yaml` 에 등록된 새 프로젝트가 있다면 각 레포에 적용됐다

## 관련

- `docs/parallelism.md` — overnight 재개 프로토콜 (manifest + checkpoint)
- `skills/karpathy-guidelines/` — 동반 설치 권장
