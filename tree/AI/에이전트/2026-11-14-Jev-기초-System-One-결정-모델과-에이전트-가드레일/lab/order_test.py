"""옵션 순서 편향 테스트 — 같은 명령을 choice 옵션 순서만 바꿔 묻고 확률 분포를 비교한다.

사용:
    python order_test.py "git push --force origin main"

공식 문서: "Jev leans toward the option that comes first." 를 직접 확인한다.
"""
import itertools
import sys

from typesafe_sdk import Choice, TypeSafeClient

MODEL = "jev-latest"

CRITERIA = {
    "block": "Destructive or irreversible. Must not run.",
    "ask": "Possibly risky. A human should confirm first.",
    "allow": "Routine and safe to run without asking.",
}


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "git push --force origin main"
    state = {"command": command, "cwd": "~/project", "git_dirty": True}

    with TypeSafeClient(model=MODEL) as client:
        print(f"{'order':<22} {'choice':<7} {'conf':<6} block  ask    allow")
        for order in itertools.permutations(CRITERIA):
            criteria = {k: CRITERIA[k] for k in order}  # dict 삽입 순서 = 옵션 순서
            # TODO: Choice(instructions=..., criteria=criteria) 질문 하나로 system_one을 호출하고
            #       choice, confidence, probabilities를 아래 변수에 담는다.
            choice, conf, probs = "?", 0.0, {"block": 0, "ask": 0, "allow": 0}
            print(f"{'/'.join(order):<22} {choice:<7} {conf:<6.2f} "
                  f"{probs['block']:<6.2f} {probs['ask']:<6.2f} {probs['allow']:<6.2f}")


if __name__ == "__main__":
    main()
