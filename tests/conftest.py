"""Keep automated Qt tests independent of desktop focus and accessibility clients."""

import os

# Set before pytest-qt creates QApplication; native UI checks run separately.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
