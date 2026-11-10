# W11-W12 T1 공개 이슈 템플릿

CSV와 등록 도구를 관리하는 독립 저장소입니다. 이 저장소에 이슈를 생성하고 필요한 Project 보드에 연결합니다.

- 게시할 공개 저장소: https://github.com/AI-Together-W10-W11-T1/W11-W12-T1-ISSUE-TEMPLATE
- 연결할 Project: https://github.com/orgs/AI-Together-W10-W11-T1/projects/6
- 입력: `common-prd-issues.csv` (Phase 1 34개, Phase 2 24개, 테스트·측정 2개)
- 제목: `[WEEK11-12] CSV 제목` / 본문: CSV의 `content` 값 (현재 모두 공란)

## 한 번에 게시하기

Python 3.9+, Git, GitHub CLI(`gh`)가 필요합니다. `gh`에 로그인한 계정에 조직 저장소 생성·이슈 작성·프로젝트 수정 권한이 있어야 합니다.

이 폴더에서 실행합니다. `publish.py`는 Python 표준 라이브러리만 사용합니다.

```powershell
# GitHub에 접속하거나 변경하지 않고 60개 제목을 확인
python publish.py

# 공개 저장소 생성 → 파일 커밋·업로드 → 이슈 생성 → Project 6번 연결
python publish.py --execute
```

인증과 Project 접근 확인이 실패하면 게시를 중단합니다. 동일 이름의 저장소가 이미 있으면 이 폴더의 origin과 일치할 때만 재실행을 허용합니다. 원격의 기존 작업을 덮어쓰는 강제 push는 하지 않습니다.

부분 실패 후 같은 명령을 실행하면 같은 제목의 기존 이슈(open/closed)를 재사용하고, 누락된 보드 연결을 처리합니다. 성공한 작업은 자동 삭제하지 않습니다. 생성·연결 완료된 이슈 URL이 출력되므로 실패 직전까지의 진행을 확인할 수 있습니다.

업로드 파일은 `.gitignore`, README, 스크립트 3개, `requirements.txt`, `secrets.py.example`, CSV 2개로 제한합니다. `secrets.py`, 토큰, 가상환경은 업로드하지 않습니다.

## 기존 CSV 등록 스크립트

`csv_to_issues.py`도 유지합니다. 별도 사용 시 `python -m pip install -r requirements.txt`로 의존성을 설치하고, `secrets.py.example`을 `secrets.py`로 복사하여 토큰을 설정합니다. 기본 대상은 이 템플릿 저장소입니다.

```powershell
python csv_to_issues.py common-prd-issues.csv --dry-run
python csv_to_issues.py common-prd-issues.csv
```

이 기존 스크립트는 이슈 생성까지만 처리합니다. Project 연결까지 처리하려면 `publish.py --execute`를 사용합니다.

## 다음 프로젝트에서 재사용

새 주차의 CSV와 구분되는 제목으로 새 이슈를 만든 후, 필요한 이슈만 다른 Project에 추가합니다. `publish.py`는 이번 Week 11–12의 60개 등록용입니다. 다른 주차에는 `csv_to_issues.py week13-14_issues_complete.csv`처럼 새 주차 이름의 파일을 사용합니다.

과거의 닫힌 이슈는 새 이슈만 선택해 보드에 추가할 때 함께 추가되지 않습니다. 같은 이슈를 여러 보드에 연결하면 제목·본문·댓글·열림/닫힘은 공유됩니다.

`clear_issues.py`는 설정한 저장소의 모든 이슈를 대상으로 닫기/삭제를 수행하는 원본 도구입니다. 이번 게시 명령은 이 도구를 실행하지 않습니다.
