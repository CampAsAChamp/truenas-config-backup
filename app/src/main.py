import logging
import os
import secrets
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

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
from .datetime_display import TIMEZONE_LABELS, TIMEZONE_OPTIONS, format_timestamp, to_iso
from .health import readiness_status
from .log_reader import tail_log_entries
from .logging_setup import clear_logs, configure_logging
from .settings import validate_settings
from .settings_store import PersistedSettings, seed_if_missing, update_persisted
from .version import get_display_version, get_version

logger = logging.getLogger("truenas_config_backup")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
BRAND_ASSETS = {"logo.svg", "logo.png"}

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


def _asset_location(rel_path: str) -> tuple[str, str]:
    if rel_path in BRAND_ASSETS:
        return "/brand", os.path.join(DOCS_DIR, rel_path)
    return "/static", os.path.join(STATIC_DIR, rel_path)


def _static_url(path: str) -> str:
    rel_path = path.lstrip("/")
    base, file_path = _asset_location(rel_path)
    if config.DEV_MODE:
        try:
            cache_key = int(os.stat(file_path).st_mtime)
        except OSError:
            cache_key = get_version()
    else:
        cache_key = get_version()
    return f"{base}/{rel_path}?v={cache_key}"


templates.env.globals["static_url"] = _static_url


class SettingsUpdate(BaseModel):
    cron_schedule: str = ""
    retention_count: int = Field(ge=0)
    include_secret_seed: bool = True
    include_pool_keys: bool = False
    include_root_authorized_keys: bool = False
    notify_webhook_url: str = ""
    notify_on_success: bool = False


def _redirect_home(toast: str, msg: str = "", page: int | None = None) -> RedirectResponse:
    params = {"toast": toast}
    if msg:
        params["msg"] = msg
    if page is not None and page > 1:
        params["page"] = str(page)
    return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)


def _clamp_page(page: int, total_runs: int, page_size: int) -> int:
    if page < 1:
        return 1
    if total_runs == 0:
        return 1
    total_pages = max(1, (total_runs + page_size - 1) // page_size)
    return min(page, total_pages)


def _pagination_context(page: int, page_size: int, total_runs: int) -> dict:
    page = _clamp_page(page, total_runs, page_size)
    total_pages = max(1, (total_runs + page_size - 1) // page_size) if total_runs else 1
    showing_from = (page - 1) * page_size + 1 if total_runs else 0
    showing_to = min(page * page_size, total_runs)
    return {
        "page": page,
        "page_size": page_size,
        "total_runs": total_runs,
        "total_pages": total_pages,
        "showing_from": showing_from,
        "showing_to": showing_to,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


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
    configure_logging()
    logger.info("application starting")
    validate_config()
    seed_if_missing(config.CONFIG_DIR, config.settings)
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

app.mount("/brand", StaticFiles(directory=DOCS_DIR), name="brand")
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
            "version_display": get_display_version(dev_mode=config.DEV_MODE),
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
def dashboard(request: Request, page: int = 1):
    page_size = config.DASHBOARD_PAGE_SIZE
    offset = (max(page, 1) - 1) * page_size
    backup_runs, total_runs = backup_manager.list_backup_runs_page(
        offset=offset,
        limit=page_size,
    )
    pagination = _pagination_context(page, page_size, total_runs)
    next_run = scheduler.next_run_time()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "version_display": get_display_version(dev_mode=config.DEV_MODE),
            "dev_mode": config.DEV_MODE,
            "backup_runs": backup_runs,
            "pagination": pagination,
            "next_run_iso": to_iso(next_run) if next_run else "",
            "settings": {
                "truenas_url": config.TRUENAS_URL,
                "verify_ssl": config.TRUENAS_VERIFY_SSL,
                "cron_schedule": config.CRON_SCHEDULE,
                "retention_count": config.RETENTION_COUNT,
                "include_secret_seed": config.INCLUDE_SECRET_SEED,
                "include_pool_keys": config.INCLUDE_POOL_KEYS,
                "include_root_authorized_keys": config.INCLUDE_ROOT_AUTHORIZED_KEYS,
                "notify_webhook_url": config.NOTIFY_WEBHOOK_URL,
                "notify_on_success": config.NOTIFY_ON_SUCCESS,
            },
            "display_defaults": {
                "dateFormat": config.DISPLAY_DATE_FORMAT,
                "clockFormat": config.DISPLAY_CLOCK_FORMAT,
                "timezoneMode": config.DISPLAY_TIMEZONE_MODE,
                "timezone": config.DISPLAY_TIMEZONE,
            },
            "display_config": {
                "timezoneOptions": list(TIMEZONE_OPTIONS),
                "timezoneLabels": TIMEZONE_LABELS,
            },
        },
    )


@app.get("/help/restore", dependencies=[Depends(require_dashboard_auth)])
def restore_help(request: Request):
    return templates.TemplateResponse(
        request,
        "restore_help.html",
        {
            "version_display": get_display_version(dev_mode=config.DEV_MODE),
            "dev_mode": config.DEV_MODE,
            "settings": {
                "include_secret_seed": config.INCLUDE_SECRET_SEED,
                "include_pool_keys": config.INCLUDE_POOL_KEYS,
                "include_root_authorized_keys": config.INCLUDE_ROOT_AUTHORIZED_KEYS,
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
def delete_run(timestamp: str = Form(...), page: int = Form(1)):
    if backup_manager.delete_run(timestamp):
        total_runs = backup_manager.list_backup_runs_page(offset=0, limit=1)[1]
        redirect_page = _clamp_page(page, total_runs, config.DASHBOARD_PAGE_SIZE)
        offset = (redirect_page - 1) * config.DASHBOARD_PAGE_SIZE
        page_runs, _ = backup_manager.list_backup_runs_page(
            offset=offset,
            limit=config.DASHBOARD_PAGE_SIZE,
        )
        if redirect_page > 1 and not page_runs:
            redirect_page = max(1, redirect_page - 1)
        return _redirect_home("run-deleted", page=redirect_page if redirect_page > 1 else None)
    return _redirect_home("run-delete-failed", page=page if page > 1 else None)


@app.get("/api/logs", dependencies=[Depends(require_dashboard_auth)])
def api_logs(limit: int = config.LOG_TAIL_LIMIT):
    clamped = max(1, min(limit, config.LOG_TAIL_LIMIT))
    return {"entries": tail_log_entries(clamped)}


@app.post("/api/logs/clear", dependencies=[Depends(require_dashboard_auth)])
def api_clear_logs():
    clear_logs()
    return {"ok": True}


@app.get("/api/settings/next-run", dependencies=[Depends(require_dashboard_auth)])
def api_next_run(cron_schedule: str = ""):
    cron_schedule = cron_schedule.strip()
    if not cron_schedule:
        return {"next_run_iso": ""}
    try:
        next_run = scheduler.next_run_for_cron(cron_schedule)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"next_run_iso": to_iso(next_run) if next_run else ""}


@app.post("/api/settings", dependencies=[Depends(require_dashboard_auth)])
def api_update_settings(body: SettingsUpdate):
    try:
        persisted = PersistedSettings(
            cron_schedule=body.cron_schedule,
            retention_count=body.retention_count,
            include_secret_seed=body.include_secret_seed,
            include_pool_keys=body.include_pool_keys,
            include_root_authorized_keys=body.include_root_authorized_keys,
            notify_webhook_url=body.notify_webhook_url,
            notify_on_success=body.notify_on_success,
        )
        validate_settings(
            config.settings.model_copy(
                update={
                    "backup": config.settings.backup.model_copy(
                        update={
                            "cron_schedule": persisted.cron_schedule or "",
                            "retention_count": persisted.retention_count or 8,
                            "include_secret_seed": persisted.include_secret_seed
                            if persisted.include_secret_seed is not None
                            else True,
                            "include_pool_keys": persisted.include_pool_keys or False,
                            "include_root_authorized_keys": (persisted.include_root_authorized_keys or False),
                        }
                    ),
                    "notify": config.settings.notify.model_copy(
                        update={
                            "webhook_url": persisted.notify_webhook_url or "",
                            "on_success": persisted.notify_on_success or False,
                        }
                    ),
                }
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    update_persisted(config.CONFIG_DIR, body.model_dump())
    config.reload_settings()
    scheduler.reload()
    next_run = scheduler.next_run_time()
    return {"ok": True, "next_run_iso": to_iso(next_run) if next_run else ""}
