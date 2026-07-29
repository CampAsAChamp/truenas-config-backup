#!/usr/bin/env python3
"""Capture docs/dashboard.png from a seeded local app instance.

Steps:
1. Create temp backup/config dirs and seed demo data with --force.
2. Start uvicorn on a free local port with pinned screenshot env vars.
3. Log in via Playwright with a frozen clock and fixed timezone.
4. Screenshot the dashboard and write docs/dashboard.png.
5. Stop uvicorn and remove temp data.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "dashboard.png"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed-local-data.py"

SCREENSHOT_PASSWORD = "screenshot"
SCREENSHOT_TIME = datetime(2026, 7, 28, 22, 24, 0, tzinfo=timezone.utc)
VIEWPORT = {"width": 1280, "height": 900}
HEALTH_POLL_INTERVAL_SEC = 0.25
HEALTH_TIMEOUT_SEC = 30


def log_step(message: str) -> None:
    print(f"[*] {message}", file=sys.stderr)


def find_free_port() -> int:
    """Return an ephemeral TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def build_server_env(backup_dir: Path, config_dir: Path) -> dict[str, str]:
    """Build env for a deterministic, production-like screenshot server."""
    env = os.environ.copy()
    env.update(
        {
            "DASHBOARD_PASSWORD": SCREENSHOT_PASSWORD,
            "TRUENAS_URL": "https://192.168.1.50",
            "TRUENAS_VERIFY_SSL": "false",
            "DISPLAY_TIMEZONE_MODE": "manual",
            "DISPLAY_TIMEZONE": "America/Los_Angeles",
            "DEV_MODE": "false",
            "BACKUP_DIR": str(backup_dir),
            "CONFIG_DIR": str(config_dir),
        }
    )
    return env


def seed_data(env: dict[str, str]) -> None:
    """Seed backup files and history into temp dirs."""
    subprocess.run(
        [sys.executable, str(SEED_SCRIPT), "--force"],
        check=True,
        cwd=REPO_ROOT,
        env=env,
    )


def start_server(env: dict[str, str], port: int) -> subprocess.Popen[bytes]:
    """Start uvicorn without reload; caller must terminate the process."""
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def wait_for_health(base_url: str, proc: subprocess.Popen[bytes]) -> None:
    """Poll /healthz until the server responds or the process exits."""
    deadline = time.monotonic() + HEALTH_TIMEOUT_SEC
    health_url = f"{base_url}/healthz"

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            raise RuntimeError(f"uvicorn exited before becoming ready:\n{stderr}")

        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(HEALTH_POLL_INTERVAL_SEC)

    raise TimeoutError(f"Server did not become ready within {HEALTH_TIMEOUT_SEC}s")


def capture_screenshot(base_url: str, output_path: Path) -> None:
    """Log in and save a full-page dashboard screenshot."""
    from playwright.sync_api import sync_playwright

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            timezone_id="America/Los_Angeles",
            viewport=VIEWPORT,
        )
        context.clock.install(time=SCREENSHOT_TIME)
        page = context.new_page()

        page.goto(f"{base_url}/login", wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        page.fill('input[name="password"]', SCREENSHOT_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{base_url}/", wait_until="networkidle")

        page.wait_for_selector(".backup-table tbody tr")
        page.wait_for_function(
            "() => document.getElementById('display-preview')?.textContent?.length > 0"
        )

        page.screenshot(path=str(output_path), full_page=True)

        browser.close()


def stop_server(proc: subprocess.Popen[bytes]) -> None:
    """Terminate uvicorn and wait briefly for a clean exit."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main() -> None:
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory(prefix="dashboard-screenshot-") as temp_dir:
        temp_root = Path(temp_dir)
        backup_dir = temp_root / "backups"
        config_dir = temp_root / "config"
        env = build_server_env(backup_dir, config_dir)

        log_step("Seeding demo backup data")
        seed_data(env)

        log_step(f"Starting app on {base_url}")
        server = start_server(env, port)
        try:
            wait_for_health(base_url, server)
            log_step(f"Capturing screenshot to {OUTPUT_PATH}")
            capture_screenshot(base_url, OUTPUT_PATH)
        finally:
            log_step("Stopping app")
            stop_server(server)

    log_step("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_step(f"Failed: {exc}")
        sys.exit(1)
