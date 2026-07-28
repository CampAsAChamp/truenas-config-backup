import os
import secrets
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import backup_manager, config, scheduler
from .auth import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    AuthRequired,
    require_dashboard_auth,
    session_cookie_value,
    verify_session,
)
from .config_validation import validate_config
from .datetime_display import format_timestamp, to_iso
from .health import readiness_status
from .version import get_version

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _format_datetime(value):
    return format_timestamp(
        value,
        date_format=config.DISPLAY_DATE_FORMAT,
        clock_format=config.DISPLAY_CLOCK_FORMAT,
        timezone_mode=config.DISPLAY_TIMEZONE_MODE,
        timezone_name=config.DISPLAY_TIMEZONE,
    )


templates.env.filters["format_datetime"] = _format_datetime


def _static_url(path: str) -> str:
    rel_path = path.lstrip("/")
    if config.DEV_MODE:
        file_path = os.path.join(STATIC_DIR, rel_path)
        try:
            cache_key = int(os.stat(file_path).st_mtime)
        except OSError:
            cache_key = get_version()
    else:
        cache_key = get_version()
    return f"/static/{rel_path}?v={cache_key}"


templates.env.globals["static_url"] = _static_url


def _redirect_home(toast: str, msg: str = "") -> RedirectResponse:
    params = {"toast": toast}
    if msg:
        params["msg"] = msg
    return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)


def _safe_next_path(next_path: str | None) -> str:
    if not next_path or not next_path.startswith("/") or next_path.startswith("//"):
        return "/"
    return next_path


def _login_url(next_path: str = "/", error: bool = False) -> str:
    params = {"next": _safe_next_path(next_path)}
    if error:
        params["error"] = "1"
    return f"/login?{urlencode(params)}"


def _set_session_cookie(response: RedirectResponse) -> RedirectResponse:
    response.set_cookie(
        SESSION_COOKIE,
        session_cookie_value(),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


def _clear_session_cookie(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="TrueNAS Config Backup", lifespan=lifespan)


@app.exception_handler(AuthRequired)
async def auth_required_handler(_request: Request, exc: AuthRequired):
    return RedirectResponse(url=_login_url(exc.next_path), status_code=303)


if config.DEV_MODE:
    from .dev_reload import router as dev_reload_router

    app.include_router(dev_reload_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/healthz")
def healthz():
    return PlainTextResponse("OK")


@app.get("/readyz")
def readyz():
    status = readiness_status()
    code = 200 if status["ready"] else 503
    return JSONResponse(status, status_code=code)


@app.get("/login")
def login_page(request: Request, next: str = "/", error: str = ""):
    if verify_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url=_safe_next_path(next), status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "version": get_version(),
            "next_path": _safe_next_path(next),
            "show_error": error == "1",
        },
    )


@app.post("/login")
def login_submit(password: str = Form(...), next: str = Form("/")):
    next_path = _safe_next_path(next)
    if not secrets.compare_digest(
        password.encode("utf-8"),
        config.DASHBOARD_PASSWORD.encode("utf-8"),
    ):
        return RedirectResponse(url=_login_url(next_path, error=True), status_code=303)
    response = RedirectResponse(url=next_path, status_code=303)
    return _set_session_cookie(response)


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    return _clear_session_cookie(response)


@app.get("/", dependencies=[Depends(require_dashboard_auth)])
def dashboard(request: Request):
    next_run = scheduler.next_run_time()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "version": get_version(),
            "dev_mode": config.DEV_MODE,
            "backup_runs": backup_manager.list_backup_runs(),
            "next_run_iso": to_iso(next_run) if next_run else "",
            "settings": {
                "truenas_url": config.TRUENAS_URL,
                "verify_ssl": config.TRUENAS_VERIFY_SSL,
                "cron_schedule": config.CRON_SCHEDULE,
                "retention_count": config.RETENTION_COUNT,
                "include_secret_seed": config.INCLUDE_SECRET_SEED,
            },
            "display_defaults": {
                "dateFormat": config.DISPLAY_DATE_FORMAT,
                "clockFormat": config.DISPLAY_CLOCK_FORMAT,
                "timezoneMode": config.DISPLAY_TIMEZONE_MODE,
                "timezone": config.DISPLAY_TIMEZONE,
            },
        },
    )


@app.post("/run-now", dependencies=[Depends(require_dashboard_auth)])
def run_now():
    success, message = backup_manager.run_backup()
    toast = "backup-success" if success else "backup-failure"
    return _redirect_home(toast, message)


@app.get("/backups/{filename}/download", dependencies=[Depends(require_dashboard_auth)])
def download_backup(filename: str):
    path = backup_manager.backup_path(filename)
    if not path:
        return PlainTextResponse("not found", status_code=404)
    return FileResponse(path, filename=filename, media_type="application/x-tar")


@app.post("/backups/{filename}/delete", dependencies=[Depends(require_dashboard_auth)])
def delete_backup(filename: str):
    safe_name = os.path.basename(filename)
    if backup_manager.delete_backup(filename):
        return _redirect_home("backup-deleted", safe_name)
    return _redirect_home("backup-delete-failed", safe_name)


@app.post("/runs/delete", dependencies=[Depends(require_dashboard_auth)])
def delete_run(timestamp: str = Form(...)):
    if backup_manager.delete_run(timestamp):
        return _redirect_home("run-deleted")
    return _redirect_home("run-delete-failed")
