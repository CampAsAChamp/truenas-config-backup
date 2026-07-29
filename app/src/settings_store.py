import json
import os
from typing import Any

from pydantic import BaseModel, Field

from .settings import Settings, load_settings_from_env


class PersistedSettings(BaseModel):
    cron_schedule: str | None = None
    retention_count: int | None = Field(default=None, ge=0)
    include_secret_seed: bool | None = None
    include_pool_keys: bool | None = None
    include_root_authorized_keys: bool | None = None
    notify_webhook_url: str | None = None
    notify_on_success: bool | None = None


def settings_file_path(config_dir: str) -> str:
    return os.path.join(config_dir, "settings.json")


def from_settings(s: Settings) -> PersistedSettings:
    return PersistedSettings(
        cron_schedule=s.backup.cron_schedule,
        retention_count=s.backup.retention_count,
        include_secret_seed=s.backup.include_secret_seed,
        include_pool_keys=s.backup.include_pool_keys,
        include_root_authorized_keys=s.backup.include_root_authorized_keys,
        notify_webhook_url=s.notify.webhook_url,
        notify_on_success=s.notify.on_success,
    )


def load_persisted(config_dir: str) -> PersistedSettings | None:
    path = settings_file_path(config_dir)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return PersistedSettings.model_validate(data)


def save_persisted(config_dir: str, data: PersistedSettings) -> None:
    os.makedirs(config_dir, exist_ok=True)
    path = settings_file_path(config_dir)
    with open(path, "w") as f:
        json.dump(data.model_dump(exclude_none=True), f, indent=2)
        f.write("\n")


def seed_if_missing(config_dir: str, s: Settings) -> None:
    if os.path.exists(settings_file_path(config_dir)):
        return
    try:
        save_persisted(config_dir, from_settings(s))
    except OSError:
        return


def merge_persisted(base: Settings, persisted: PersistedSettings) -> Settings:
    backup = base.backup.model_copy(
        update={
            k: v
            for k, v in {
                "cron_schedule": persisted.cron_schedule,
                "retention_count": persisted.retention_count,
                "include_secret_seed": persisted.include_secret_seed,
                "include_pool_keys": persisted.include_pool_keys,
                "include_root_authorized_keys": persisted.include_root_authorized_keys,
            }.items()
            if v is not None
        }
    )
    notify = base.notify.model_copy(
        update={
            k: v
            for k, v in {
                "webhook_url": persisted.notify_webhook_url,
                "on_success": persisted.notify_on_success,
            }.items()
            if v is not None
        }
    )
    return base.model_copy(update={"backup": backup, "notify": notify})


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    base = load_settings_from_env(environ)
    persisted = load_persisted(base.config_dir)
    if persisted is None:
        return base
    return merge_persisted(base, persisted)


def update_persisted(config_dir: str, updates: dict[str, Any]) -> PersistedSettings:
    current = load_persisted(config_dir) or PersistedSettings()
    merged = current.model_copy(update=updates)
    save_persisted(config_dir, merged)
    return merged


def persisted_to_api_dict(p: PersistedSettings) -> dict[str, Any]:
    return p.model_dump(exclude_none=True)
