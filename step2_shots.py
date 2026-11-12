import subprocess
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(".")
SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

TESTS = [
    (i, "tests/test_rules.py") for i in range(1, 8)
] + [
    (i, "tests/test_checks.py") for i in range(8, 13)
]

def run_test(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def make_image(filename, title, command, output, passed):
    lines = [
        "SMART CRM - MEKONG MOBILE",
        "TEST EVIDENCE - DOCKER EXECUTION LOG",
        "",
        "Source: Actual Docker command output",
        f"Command: {command}",
        f"Result: {'PASS' if passed else 'FAIL'}",
        "",
        *output.splitlines()
    ]

    font = ImageFont.load_default()
    width = 1500
    line_height = 19
    height = max(260, 35 + len(lines) * line_height)

    img = Image.new("RGB", (width, height), (24, 26, 32))
    draw = ImageDraw.Draw(img)

    y = 18
    for index, line in enumerate(lines):
        if index == 4:
            color = (80, 220, 130) if passed else (255, 90, 90)
        else:
            color = (230, 233, 240)

        draw.text((20, y), line[:190], fill=color, font=font)
        y += line_height

    img.save(SHOTS / filename)

results = []

# 1. Chạy từng test riêng biệt
for number, test_file in TESTS:
    test_name = f"TC{number:02d}"
    command = [
        "docker", "compose", "exec", "-T", "pipeline",
        "python", "-m", "pytest", "-v", test_file,
        "-k", test_name
    ]

    result = run_test(command)
    output = (result.stdout + "\n" + result.stderr).strip()
    passed = result.returncode == 0 and "1 passed" in output

    status = "PASS" if passed else "FAIL"
    filename = f"verified_{status}_TC-{number:02d}.png"

    make_image(
        filename,
        test_name,
        " ".join(command),
        output,
        passed
    )

    results.append((test_name, passed, output))
    print(f"{test_name}: {status}")

# 2. Chạy toàn bộ test suite
command = [
    "docker", "compose", "exec", "-T", "pipeline",
    "python", "-m", "pytest", "-v"
]
result = run_test(command)
output = (result.stdout + "\n" + result.stderr).strip()

passed = (
    result.returncode == 0
    and "12 passed" in output
    and "failed" not in output.lower()
)

make_image(
    f"verified_{'PASS' if passed else 'FAIL'}_pytest_all.png",
    "FULL TEST SUITE",
    " ".join(command),
    output,
    passed
)

# 3. Báo cáo tổng kết
summary = "\n".join(
    f"{name}: {'PASS' if ok else 'FAIL'}"
    for name, ok, _ in results
)

summary += (
    f"\n\nIndividual tests: {sum(ok for _, ok, _ in results)}/12 PASS"
    f"\nFull suite: {'PASS' if passed else 'FAIL'}"
)

make_image(
    f"verified_{'PASS' if passed and all(x[1] for x in results) else 'FAIL'}_summary.png",
    "TEST SUMMARY",
    "Docker pytest execution",
    summary,
    passed and all(x[1] for x in results)
)

print("\n========== FINAL RESULT ==========")
print(summary)
print(f"\nEvidence folder: {SHOTS.resolve()}")
