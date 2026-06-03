import os

# Force the testing environment before the app boots so it loads `.env.testing`
# (SQLite). The framework only auto-detects "testing" once PYTEST_CURRENT_TEST is
# set, which is too late — the Application boots at import time.
os.environ.setdefault("APP_ENV", "testing")

# Ensure the application is booted (env loaded, providers registered) before tests
# import models/controllers.
from bootstrap.application import app  # noqa: E402,F401
