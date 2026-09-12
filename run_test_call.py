"""
End-to-end pipeline smoke test: places one real social check-in call.

Run with: .venv\\Scripts\\python.exe run_test_call.py [resident_id]
"""

import sys

from tools import place_social_checkin_call

if __name__ == "__main__":
    resident_id = sys.argv[1] if len(sys.argv) > 1 else "resident_1"
    place_social_checkin_call(resident_id)
