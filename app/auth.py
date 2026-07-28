import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from . import config

security = HTTPBasic(auto_error=False)


def require_dashboard_auth(
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> None:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not secrets.compare_digest(
        credentials.password.encode("utf-8"),
        config.DASHBOARD_PASSWORD.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
