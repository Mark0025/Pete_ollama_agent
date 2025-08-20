import os
import glob
from datetime import datetime
from loguru import logger

LOGDIR = os.path.join(os.path.dirname(__file__), '../tests/TestLogs')
os.makedirs(LOGDIR, exist_ok=True)
logger.add(os.path.join(LOGDIR, "whats_working.log"), rotation="1 MB", retention="10 days", level="INFO")

DEV_MAN_DIR = os.path.join(os.path.dirname(__file__), '../DEV_MAN')
OUTPUT_PATH = os.path.join(DEV_MAN_DIR, 'whats_working.md')

# Find latest pytest_output.txt and testlog.txt
def find_latest(pattern):
    files = glob.glob(os.path.join(LOGDIR, pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

pytest_log = find_latest('pytest_output.txt')
testlog = find_latest('testlog.txt')

summary = []
if pytest_log:
    with open(pytest_log) as f:
        for line in f:
            if 'PASSED' in line or 'FAILED' in line or 'ERROR' in line:
                summary.append(line.strip())
if testlog:
    with open(testlog) as f:
        for line in f:
            if 'PASSED' in line or 'FAILED' in line or 'ERROR' in line:
                summary.append(line.strip())

# Parse summary into table
rows = []
for line in summary:
    if 'PASSED' in line:
        status = '✅'
    elif 'FAILED' in line or 'ERROR' in line:
        status = '❌'
    else:
        status = '❓'
    parts = line.split()
    test_name = parts[0] if parts else 'Unknown'
    desc = ' '.join(parts[1:])
    rows.append((test_name, status, desc))

# Write whats_working.md
with open(OUTPUT_PATH, 'w') as f:
    f.write(f"# 🟢 What's Working: Automated Test Summary\n")
    f.write(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
    f.write("| Test | Status | Description |\n")
    f.write("|------|--------|-------------|\n")
    for test, status, desc in rows:
        f.write(f"| {test} | {status} | {desc} |\n")
    f.write("\n---\n")
    f.write("Logs: See tests/TestLogs/whats_working.log for details.\n")
logger.success(f"Updated whats_working.md with {len(rows)} test results.")
print(f"[green]Updated whats_working.md with {len(rows)} test results.") 