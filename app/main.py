import os
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import backup_manager, config, scheduler
from .auth import require_dashboard_auth
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
    return f"/static/{path.lstrip('/')}?v={get_version()}"


templates.env.globals["static_url"] = _static_url


def _redirect_home(toast: str, msg: str = "") -> RedirectResponse:
    params = {"toast": toast}
    if msg:
        params["msg"] = msg
    return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="TrueNAS Config Backup", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/healthz")
def healthz():
    return PlainTextResponse("OK")


@app.get("/readyz")
def readyz():
    status = readiness_status()
    code = 200 if status["ready"] else 503
    return JSONResponse(status, status_code=code)


@app.get("/", dependencies=[Depends(require_dashboard_auth)])
def dashboard(request: Request):
    next_run = scheduler.next_run_time()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "version": get_version(),
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
