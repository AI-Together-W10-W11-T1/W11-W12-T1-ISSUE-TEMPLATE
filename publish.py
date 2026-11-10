"""공개 템플릿 저장소 생성 → CSV 이슈 생성 → Project 연결. 기본은 로컬 미리보기."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OWNER = "AI-Together-W10-W11-T1"
REPO = f"{OWNER}/W11-W12-T1-ISSUE-TEMPLATE"
PROJECT = "6"
CSV = ROOT / "common-prd-issues.csv"


def run(*args, data=None, check=True):
    # 현재 게시 폴더만 이번 프로세스에서 신뢰한다. gh가 호출하는 Git에도 전달되며
    # 사용자 전역 설정은 변경하지 않는다. 기존 명령별 설정이 있으면 뒤에 추가한다.
    env = os.environ.copy()
    index = int(env.get("GIT_CONFIG_COUNT", "0"))
    env["GIT_CONFIG_COUNT"] = str(index + 1)
    env[f"GIT_CONFIG_KEY_{index}"] = "safe.directory"
    env[f"GIT_CONFIG_VALUE_{index}"] = ROOT.as_posix()
    result = subprocess.run(args, cwd=ROOT, input=data, capture_output=True,
                            text=True, encoding="utf-8", env=env)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def gh_json(*args):
    return json.loads(run("gh", *args).stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="GitHub에 실제 게시")
    args = parser.parse_args()
    with CSV.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["title", "content"]:
            raise ValueError("CSV 헤더는 title,content여야 합니다.")
        rows = list(reader)
    titles = [f"[WEEK11-12] {row['title'].strip()}" for row in rows]
    if not rows or any(not row["title"].strip() for row in rows):
        raise ValueError("이슈 목록 또는 제목이 비어 있습니다.")
    if len(set(titles)) != len(titles):
        raise ValueError("CSV에 중복 제목이 있습니다.")
    print(f"대상: {REPO} / Project {PROJECT} / {len(rows)}개")
    if not args.execute:
        for title in titles:
            print(title)
        print("미리보기 완료. 실제 게시: python publish.py --execute")
        return

    # 인증·프로젝트 접근을 먼저 확인한다. 실패하면 원격 생성에 진입하지 않는다.
    run("gh", "api", "--method", "GET", "user")
    gh_json("project", "view", PROJECT, "--owner", OWNER, "--format", "json")
    probe = run("gh", "api", "--method", "GET", f"repos/{REPO}", check=False)
    exists = probe.returncode == 0
    if not exists and "HTTP 404" not in probe.stderr:
        raise RuntimeError(probe.stderr.strip())
    origin = None
    if (ROOT / ".git").exists():
        remote = run("git", "remote", "get-url", "origin", check=False)
        if remote.returncode == 0:
            origin = remote.stdout.strip()
    allowed = {f"https://github.com/{REPO}.git", f"https://github.com/{REPO}",
               f"git@github.com:{REPO}.git"}
    # 기존 원격 저장소는 이 폴더의 origin이 일치하는 재실행일 때만 사용한다.
    if exists and origin not in allowed:
        raise RuntimeError("같은 이름의 저장소가 이미 존재합니다. 덮어쓰지 않고 중단합니다.")
    if origin and origin not in allowed:
        raise RuntimeError("origin이 등록 대상과 다릅니다.")
    if exists and json.loads(probe.stdout)["private"]:
        raise RuntimeError("기존 저장소가 비공개입니다. 공개 설정을 변경하지 않고 중단합니다.")
    if not (ROOT / ".git").exists():
        run("git", "init", "-b", "main")
    # 명시한 배포 파일만 포함한다. 실제 토큰 설정과 로컬 환경은 업로드하지 않는다.
    files = [".gitignore", "README.md", "requirements.txt", "secrets.py.example",
             "csv_to_issues.py", "clear_issues.py", "publish.py",
             "common-prd-issues.csv", "week11-12_issues_complete.csv"]
    tracked = run("git", "ls-files").stdout.splitlines()
    if set(tracked) - set(files):
        raise RuntimeError("허용 목록 외 추적 파일이 있습니다. 업로드 전에 확인하세요.")
    run("git", "add", "--", *files)
    pending = run("git", "diff", "--cached", "--quiet", check=False)
    if pending.returncode == 1:
        run("git", "commit", "-m", "Prepare W11-W12 issue templates and publisher")
    elif pending.returncode:
        raise RuntimeError(pending.stderr)
    if not exists:
        run("gh", "repo", "create", REPO, "--public", "--source", str(ROOT),
            "--remote", "origin")
    run("git", "push", "-u", "origin", "HEAD:main")

    # 전체 상태 조회가 성공한 뒤 생성한다. 재실행 시 같은 제목은 재사용한다.
    pages = gh_json("api", "--method", "GET", f"repos/{REPO}/issues",
                    "-f", "state=all", "-f", "per_page=100", "--paginate", "--slurp")
    existing = {item["title"]: item["html_url"] for page in pages for item in page
                if "pull_request" not in item}
    items = gh_json("project", "item-list", PROJECT, "--owner", OWNER,
                    "--format", "json", "--limit", "10000")
    linked = {item.get("content", {}).get("url") for item in items["items"]}
    for row, title in zip(rows, titles):
        url = existing.get(title)
        if not url:
            payload = json.dumps({"title": title, "body": row["content"] or ""})
            result = run("gh", "api", "--method", "POST", f"repos/{REPO}/issues",
                         "--input", "-", data=payload)
            url = json.loads(result.stdout)["html_url"]
            existing[title] = url
        if url not in linked:
            run("gh", "project", "item-add", PROJECT, "--owner", OWNER, "--url", url)
            linked.add(url)
        print(f"확인 완료: {url} {title}", flush=True)

    items = gh_json("project", "item-list", PROJECT, "--owner", OWNER,
                    "--format", "json", "--limit", "10000")
    urls = {item.get("content", {}).get("url") for item in items["items"]}
    if any(existing[title] not in urls for title in titles):
        raise RuntimeError("일부 이슈의 보드 연결을 확인하지 못했습니다. 재실행하세요.")
    print(f"완료: https://github.com/{REPO} / {len(titles)}개를 Project {PROJECT}에 등록")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(f"중단: {error}", file=sys.stderr)
        sys.exit(1)
