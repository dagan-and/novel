#!/usr/bin/env python3
"""
publish.py — 변환 3종 + git commit & push 자동 실행

사용법:
  python3 publish.py          # 변환 + 커밋 + 푸시
  python3 publish.py --dry    # 변환만, git 건너뜀
"""

import os, re, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
EPISODES_DIR = os.path.join(BASE, 'episodes')

DRY = '--dry' in sys.argv


# ── 유틸 ──────────────────────────────────────────────────────────────

def run(cmd, check=True):
    print('$ ' + ' '.join(cmd))
    result = subprocess.run(cmd, cwd=BASE)
    if check and result.returncode != 0:
        print(f'오류: {" ".join(cmd)} 실패 (exit {result.returncode})')
        sys.exit(result.returncode)
    return result.returncode


def git_status_lines():
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=BASE,
                       capture_output=True, text=True)
    return r.stdout.splitlines()


# ── 에피소드 목록 수집 ────────────────────────────────────────────────

def all_episode_names():
    """episodes/ 안의 ep.NNN[_a].md 목록 (정렬)"""
    names = []
    for f in sorted(os.listdir(EPISODES_DIR)):
        if not f.endswith('.md'):
            continue
        base = f.replace('.md', '')
        if re.match(r'^ep\.\d+(_a)?$', base):
            names.append(base)
    return names


def new_or_modified_episodes():
    """git status 기준 신규·수정된 에피소드 이름 목록"""
    eps = []
    for line in git_status_lines():
        m = re.search(r'episodes/(ep\.\d+(?:_a)?)\.md', line)
        if m:
            eps.append(m.group(1))
    return sorted(set(eps))


def build_commit_message(changed_eps):
    """변경된 에피소드 목록으로 커밋 메시지 생성"""
    if not changed_eps:
        return 'Update HTML conversion and settings'

    nums = sorted(set(int(re.search(r'\d+', e).group()) for e in changed_eps))
    if len(nums) == 1:
        ep_part = f'ep.{nums[0]:03d}'
    else:
        ep_part = f'ep.{nums[0]:03d}~{nums[-1]:03d}'

    return f'Add {ep_part} with HTML conversion and updates'


# ── 변환 ──────────────────────────────────────────────────────────────

def step_convert_episodes():
    print('\n[ 1/3 ] 에피소드 HTML 변환')
    ep_names = all_episode_names()
    if not ep_names:
        print('  변환할 에피소드 없음')
        return
    run([sys.executable, 'convert_html.py'] + ep_names)


def step_convert_profiles():
    print('\n[ 2/3 ] 캐릭터 프로필 HTML 변환')
    run([sys.executable, 'convert_profiles.py'])


def step_convert_setting():
    print('\n[ 3/3 ] 세계관·관계망·인덱스 HTML 변환')
    run([sys.executable, 'convert_setting.py'])


# ── git ───────────────────────────────────────────────────────────────

def step_git_push(msg):
    print('\n[ git ] 커밋 & 푸시')

    run(['git', 'add', '-A'])

    # staged 변경사항이 없으면 커밋 건너뜀
    rc = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE).returncode
    if rc == 0:
        print('  변경사항 없음 — 커밋 건너뜀')
        return

    run(['git', 'commit', '-m', msg])
    run(['git', 'push', 'origin', 'main'])


# ── 메인 ──────────────────────────────────────────────────────────────

def main():
    print('=' * 54)
    print('  다시 만나는 관계들 — 발행 스크립트')
    print('=' * 54)

    # git push 전에 변경 목록 미리 수집 (add 전이어야 정확)
    changed_eps = new_or_modified_episodes()
    commit_msg  = build_commit_message(changed_eps)

    step_convert_episodes()
    step_convert_profiles()
    step_convert_setting()

    if DRY:
        print('\n--dry 모드: git 건너뜀')
    else:
        step_git_push(commit_msg)
        print(f'\n✓ 완료: {commit_msg}')


if __name__ == '__main__':
    main()
