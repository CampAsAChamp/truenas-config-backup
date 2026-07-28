import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import backup_manager, config, history, scheduler
from .version import get_version

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="TrueNAS Config Backup", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/healthz")
def healthz():
    return PlainTextResponse("OK")


@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "version": get_version(),
            "backups": backup_manager.list_backups(),
            "history": history.read_all()[:20],
            "next_run": scheduler.next_run_time(),
            "settings": {
                "truenas_url": config.TRUENAS_URL,
                "verify_ssl": config.TRUENAS_VERIFY_SSL,
                "cron_schedule": config.CRON_SCHEDULE,
                "retention_count": config.RETENTION_COUNT,
                "include_secret_seed": config.INCLUDE_SECRET_SEED,
            },
        },
    )


@app.post("/run-now")
def run_now():
    backup_manager.run_backup()
    return RedirectResponse(url="/", status_code=303)


@app.get("/backups/{filename}/download")
def download_backup(filename: str):
    path = backup_manager.backup_path(filename)
    if not path:
        return PlainTextResponse("not found", status_code=404)
    return FileResponse(path, filename=filename, media_type="application/x-tar")


@app.post("/backups/{filename}/delete")
def delete_backup(filename: str):
    backup_manager.delete_backup(filename)
    return RedirectResponse(url="/", status_code=303)
