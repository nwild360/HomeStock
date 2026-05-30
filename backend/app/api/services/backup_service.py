import hashlib
import hmac
import io
import os
import re
import logging
import tempfile
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status

from app.api.schemas import BackupItem
from app.config import get_settings

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(os.environ.get("BACKUP_STORAGE_PATH", "/app/backups"))
FILENAME_RE = re.compile(r"^homestock_\d{4}-\d{2}-\d{2}_\d{6}\.zip$")
MAX_BACKUP_BYTES = 500 * 1024 * 1024  # 500 MB
_PRE_RESTORE_SCHEMA = "homestock_pre_restore"


def _ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _db_env() -> dict:
    s = get_settings()
    return {
        **os.environ,
        "PGPASSWORD": s.POSTGRES_PASSWORD,
        "_DB_HOST": s.POSTGRES_HOST,
        "_DB_PORT": str(s.POSTGRES_PORT),
        "_DB_USER": s.POSTGRES_USER,
        "_DB_NAME": s.POSTGRES_DB,
    }


def _pg_args(env: dict) -> list[str]:
    return [
        "-h", env["_DB_HOST"],
        "-p", env["_DB_PORT"],
        "-U", env["_DB_USER"],
        "-d", env["_DB_NAME"],
    ]


def _run_psql(env: dict, *sql_args: str, timeout: int = 30) -> None:
    """Run psql with the given arguments (-c SQL or -f path). Raises RuntimeError on non-zero exit."""
    result = subprocess.run(
        ["psql", *_pg_args(env), *sql_args],
        env=env,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hmac_of_file(path: str) -> str:
    secret = get_settings().BACKUP_HMAC_SECRET.encode("utf-8")
    h = hmac.new(secret, digestmod=hashlib.sha256)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_checksum(sql_path: str, checksum_path: str | None) -> None:
    """Verify the SQL dump matches the stored checksum. No-op if no checksum file (legacy backup)."""
    if checksum_path is None:
        return
    with open(checksum_path, "r") as f:
        expected = f.read().strip()
    actual = _sha256_of_file(sql_path)
    if actual != expected:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Backup integrity check failed: checksum mismatch. The file may be corrupted.",
        )


def _verify_signature(sql_path: str, signature_path: str | None) -> None:
    """
    Verify the HMAC-SHA256 signature of the SQL dump.

    Both a missing signature file and a mismatched signature are rejected — only
    backups created by this server (which knows BACKUP_HMAC_SECRET) can be restored.
    """
    if signature_path is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Backup signature missing. Only backups created by this server "
                "can be restored. External or manually modified backups are not accepted."
            ),
        )
    with open(signature_path, "r") as f:
        stored = f.read().strip()
    actual = _hmac_of_file(sql_path)
    if not hmac.compare_digest(actual, stored):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Backup signature verification failed: this backup may have been tampered with.",
        )


def list_backups() -> list[BackupItem]:
    _ensure_backup_dir()
    backups = []
    for entry in BACKUP_DIR.iterdir():
        if entry.is_file() and FILENAME_RE.match(entry.name):
            stat = entry.stat()
            backups.append(BackupItem(
                name=entry.name,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                size_bytes=stat.st_size,
            ))
    backups.sort(key=lambda b: b.created_at, reverse=True)
    return backups


def create_backup() -> BackupItem:
    _ensure_backup_dir()
    env = _db_env()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_name = f"homestock_{ts}.zip"
    zip_path = BACKUP_DIR / zip_name

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sql")
    os.close(tmp_fd)

    try:
        result = subprocess.run(
            [
                "pg_dump",
                *_pg_args(env),
                "--schema=homestock",
                "-F", "p",
                "-f", tmp_path,
            ],
            env=env,
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error("pg_dump failed: %s", result.stderr.decode(errors="replace"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup creation failed. Check server logs for details.",
            )

        checksum = _sha256_of_file(tmp_path)
        signature = _hmac_of_file(tmp_path)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_path, arcname="homestock_dump.sql")
            zf.writestr("checksum.sha256", checksum)
            zf.writestr("signature.hmac", signature)

        stat = zip_path.stat()
        return BackupItem(
            name=zip_name,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            size_bytes=stat.st_size,
        )

    except HTTPException:
        zip_path.unlink(missing_ok=True)
        raise
    except subprocess.TimeoutExpired:
        zip_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="pg_dump timed out after 120 seconds.",
        )
    except Exception:
        zip_path.unlink(missing_ok=True)
        logger.exception("Unexpected error during backup creation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup creation failed. Check server logs for details.",
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_backup_path(filename: str) -> Path:
    if not FILENAME_RE.match(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup filename.",
        )
    path = BACKUP_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found.")
    return path


def delete_backup(filename: str) -> None:
    path = get_backup_path(filename)
    path.unlink()


def save_uploaded_backup(filename: str, data: bytes) -> BackupItem:
    if not FILENAME_RE.match(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must match: homestock_YYYY-MM-DD_HHMMSS.zip",
        )
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            if "homestock_dump.sql" not in zf.namelist():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="ZIP must contain homestock_dump.sql",
                )
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is not a valid ZIP archive.",
        )

    _ensure_backup_dir()
    dest = BACKUP_DIR / filename
    if dest.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A backup named {filename} already exists.",
        )

    dest.write_bytes(data)
    stat = dest.stat()
    return BackupItem(
        name=filename,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        size_bytes=stat.st_size,
    )


def restore_backup(filename: str) -> None:
    """
    Atomically restore a backup using schema rename/swap so the original data
    is never destroyed until the restore is confirmed successful.

    Flow:
      1. Extract ZIP and verify SHA256 checksum — no live schema touched yet.
      2. Dispose connection pool + terminate active sessions.
      3. Rename homestock → homestock_pre_restore  (original data is safe).
      4. psql -f dump.sql  (dump creates a fresh homestock schema).
      5a. Success → DROP homestock_pre_restore CASCADE.
      5b. Failure → DROP homestock CASCADE +
                    RENAME homestock_pre_restore → homestock  (full rollback).
    """
    path = get_backup_path(filename)
    env = _db_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        # ── Step 1: Extract and verify before touching anything ──────────────
        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()
            if "homestock_dump.sql" not in namelist:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Backup ZIP does not contain homestock_dump.sql",
                )
            zf.extract("homestock_dump.sql", tmpdir)
            checksum_path = None
            if "checksum.sha256" in namelist:
                zf.extract("checksum.sha256", tmpdir)
                checksum_path = os.path.join(tmpdir, "checksum.sha256")
            signature_path = None
            if "signature.hmac" in namelist:
                zf.extract("signature.hmac", tmpdir)
                signature_path = os.path.join(tmpdir, "signature.hmac")

        sql_path = os.path.join(tmpdir, "homestock_dump.sql")
        _verify_checksum(sql_path, checksum_path)
        _verify_signature(sql_path, signature_path)

        # ── Step 2: Clear connections ────────────────────────────────────────
        from app.dependencies.db_session import engine
        engine.dispose()

        try:
            _run_psql(
                env,
                "-c",
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid != pg_backend_pid();",
                timeout=10,
            )
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            logger.warning("pg_terminate_backend warning (non-fatal): %s", e)

        # ── Step 3: Drop any stale temp schema, then rename live schema ──────
        try:
            _run_psql(
                env, "-c", f"DROP SCHEMA IF EXISTS {_PRE_RESTORE_SCHEMA} CASCADE",
                timeout=30,
            )
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            logger.warning("Could not drop stale pre-restore schema (non-fatal): %s", e)

        try:
            _run_psql(
                env, "-c", f"ALTER SCHEMA homestock RENAME TO {_PRE_RESTORE_SCHEMA}",
                timeout=15,
            )
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            logger.error("Schema rename failed — aborting restore: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Restore aborted: could not acquire schema lock. Your data is unchanged.",
            )

        # ── Steps 4 + 5: Restore, then commit or rollback ───────────────────
        try:
            # ON_ERROR_STOP=1: psql exits with code 3 on the first SQL error
            # instead of skipping the bad statement and returning 0.
            _run_psql(env, "-v", "ON_ERROR_STOP=1", "-f", sql_path, timeout=120)

            # Success — drop the safety net
            try:
                _run_psql(
                    env, "-c", f"DROP SCHEMA {_PRE_RESTORE_SCHEMA} CASCADE",
                    timeout=30,
                )
            except (RuntimeError, subprocess.TimeoutExpired) as e:
                # Non-fatal: restore succeeded; the stale schema is just an artifact
                # that will be cleaned up on the next restore attempt.
                logger.warning(
                    "Restore succeeded but could not drop '%s' (non-fatal): %s",
                    _PRE_RESTORE_SCHEMA, e,
                )

            logger.info("✅ Restore complete from %s", filename)

        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            logger.error("Restore failed, rolling back to pre-restore schema: %s", exc)
            try:
                _run_psql(env, "-c", "DROP SCHEMA IF EXISTS homestock CASCADE", timeout=30)
                _run_psql(
                    env, "-c", f"ALTER SCHEMA {_PRE_RESTORE_SCHEMA} RENAME TO homestock",
                    timeout=15,
                )
                logger.info("✅ Rollback complete — original data is intact")
            except (RuntimeError, subprocess.TimeoutExpired) as rollback_exc:
                # The worst possible path: restore failed AND rollback failed.
                # Original data is still in _PRE_RESTORE_SCHEMA — log it prominently.
                logger.critical(
                    "ROLLBACK FAILED. Original data is in schema '%s'. "
                    "Manually run: ALTER SCHEMA %s RENAME TO homestock. Error: %s",
                    _PRE_RESTORE_SCHEMA, _PRE_RESTORE_SCHEMA, rollback_exc,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        f"Restore failed and automatic rollback also failed. "
                        f"Your original data is preserved in the PostgreSQL schema "
                        f"'{_PRE_RESTORE_SCHEMA}'. Run: "
                        f"ALTER SCHEMA {_PRE_RESTORE_SCHEMA} RENAME TO homestock;"
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Restore failed — your original data has been automatically preserved.",
            )

        finally:
            from app.dependencies.db_session import engine
            engine.dispose()
