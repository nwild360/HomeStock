import hashlib
import hmac
import io
import os
import re
import logging
import shutil
import tempfile
import subprocess
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

from app.api.schemas import BackupItem
from app.config import get_settings
from app.dependencies.db_session import engine

logger = logging.getLogger(__name__)

FILENAME_RE = re.compile(r"^homestock_\d{4}-\d{2}-\d{2}_\d{6}\.zip$")
MAX_BACKUP_BYTES = 500 * 1024 * 1024  # 500 MB compressed upload limit
MAX_DECOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB decompressed SQL limit
_PRE_RESTORE_SCHEMA = "homestock_pre_restore"
# Guard: ensure the schema name constant only contains safe identifier characters.
# This prevents any future parameterization of this value from introducing SQL
# injection through the f-string interpolations below.
assert re.match(r"^[a-z][a-z0-9_]{0,62}$", _PRE_RESTORE_SCHEMA), (
    f"_PRE_RESTORE_SCHEMA '{_PRE_RESTORE_SCHEMA}' contains unsafe identifier characters"
)

# Only one restore may run at a time. Non-blocking acquire returns a 409
# immediately rather than queuing a second restore behind a long-running one.
_restore_lock = threading.Lock()

_NONCE_SIZE = 12  # 96-bit nonce for AES-256-GCM


def _resolve_binary(name: str) -> str:
    """Resolve a system binary to its absolute path at module load; fail fast if missing."""
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"Required binary '{name}' not found on PATH. "
            f"Ensure postgresql-client is installed in the container."
        )
    return path


_PSQL = _resolve_binary("psql")
_PG_DUMP = _resolve_binary("pg_dump")


def _backup_dir() -> Path:
    """Return the backup directory path from validated settings."""
    return Path(get_settings().BACKUP_STORAGE_PATH)


def _get_aes_key() -> bytes:
    return bytes.fromhex(get_settings().BACKUP_ENCRYPTION_KEY)


def _encrypt_bytes(data: bytes) -> bytes:
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(_get_aes_key()).encrypt(nonce, data, None)
    return nonce + ciphertext


def _decrypt_bytes(data: bytes) -> bytes:
    try:
        nonce = data[:_NONCE_SIZE]
        ciphertext = data[_NONCE_SIZE:]
        return AESGCM(_get_aes_key()).decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Backup decryption failed. The file may be corrupted, "
                "was created before encryption was enabled, "
                "or was encrypted with a different key."
            ),
        )


def _ensure_backup_dir() -> None:
    _backup_dir().mkdir(mode=0o700, parents=True, exist_ok=True)


def _db_env() -> dict:
    s = get_settings()
    return {
        "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "HOME": os.environ.get("HOME", "/root"),
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
        [_PSQL, *_pg_args(env), *sql_args],
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


def list_backups() -> list[BackupItem]:
    _ensure_backup_dir()
    backups = []
    for entry in _backup_dir().iterdir():
        if entry.is_file() and FILENAME_RE.match(entry.name):
            stat = entry.stat()
            backups.append(BackupItem(
                name=entry.name,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                size_bytes=stat.st_size,
            ))
    backups.sort(key=lambda b: b.created_at, reverse=True)
    return backups[:100]  # cap response; oldest beyond 100 are still on disk


def create_backup() -> BackupItem:
    _ensure_backup_dir()
    env = _db_env()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    zip_name = f"homestock_{ts}.zip"
    zip_path = _backup_dir() / zip_name

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sql")
    os.close(tmp_fd)

    try:
        result = subprocess.run(
            [
                _PG_DUMP,
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

        with open(tmp_path, "rb") as f:
            encrypted_sql = _encrypt_bytes(f.read())

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("homestock_dump.sql.enc", encrypted_sql)
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
    path = _backup_dir() / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found.")
    return path


def delete_backup(filename: str) -> None:
    path = get_backup_path(filename)
    path.unlink(missing_ok=True)


def save_uploaded_backup(filename: str, data: bytes) -> BackupItem:
    if not FILENAME_RE.match(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must match: homestock_YYYY-MM-DD_HHMMSS.zip",
        )

    # Validate structure and that the encrypted SQL is decryptable with our key.
    # Uploaded backups must be ZIPs produced by this server (or another instance
    # sharing the same BACKUP_ENCRYPTION_KEY). Saved as-is; no re-encryption.
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            if "homestock_dump.sql.enc" not in zf.namelist():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Backup ZIP must contain homestock_dump.sql.enc",
                )
            member_info = zf.getinfo("homestock_dump.sql.enc")
            if member_info.file_size > MAX_DECOMPRESSED_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Backup SQL dump exceeds maximum allowed size (2 GB).",
                )
            _decrypt_bytes(zf.read("homestock_dump.sql.enc"))
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is not a valid ZIP archive.",
        )

    _ensure_backup_dir()
    dest = _backup_dir() / filename
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
      1. Extract ZIP, decrypt SQL, verify checksum + HMAC in memory — schema untouched.
      2. Dispose connection pool + terminate active sessions.
      3. Rename homestock → homestock_pre_restore  (original data is safe).
      4. psql -f dump.sql  (dump creates a fresh homestock schema).
      5a. Success → DROP homestock_pre_restore CASCADE.
      5b. Failure → DROP homestock CASCADE +
                    RENAME homestock_pre_restore → homestock  (full rollback).
    """
    if not _restore_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A restore is already in progress. Please wait for it to complete.",
        )
    try:
        _restore_locked(filename)
    finally:
        _restore_lock.release()


def _restore_locked(filename: str) -> None:
    """Inner restore logic — must only be called while _restore_lock is held."""
    path = get_backup_path(filename)
    env = _db_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        # ── Step 1: Extract, decrypt, verify — schema untouched throughout ──
        try:
            with zipfile.ZipFile(path, "r") as zf:
                namelist = zf.namelist()
                if "homestock_dump.sql.enc" not in namelist:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Backup ZIP does not contain homestock_dump.sql.enc",
                    )
                member_info = zf.getinfo("homestock_dump.sql.enc")
                if member_info.file_size > MAX_DECOMPRESSED_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Backup SQL dump exceeds maximum allowed size (2 GB).",
                    )
                encrypted_sql = zf.read("homestock_dump.sql.enc")
                stored_checksum = (
                    zf.read("checksum.sha256").decode().strip()
                    if "checksum.sha256" in namelist else None
                )
                stored_signature = (
                    zf.read("signature.hmac").decode().strip()
                    if "signature.hmac" in namelist else None
                )
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Backup file is not a valid ZIP archive.",
            )

        plaintext_sql = _decrypt_bytes(encrypted_sql)

        # Verify integrity and authenticity entirely in memory before writing
        # to disk or touching the live schema — no unverified bytes hit disk.
        if stored_checksum is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Backup integrity data missing: checksum not found.",
            )
        actual_checksum = hashlib.sha256(plaintext_sql).hexdigest()
        if actual_checksum != stored_checksum:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Backup integrity check failed: checksum mismatch. The file may be corrupted.",
            )
        if stored_signature is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Backup signature missing. Only backups created by this server "
                    "can be restored. External or manually modified backups are not accepted."
                ),
            )
        secret = get_settings().BACKUP_HMAC_SECRET.encode("utf-8")
        h = hmac.new(secret, digestmod=hashlib.sha256)
        h.update(plaintext_sql)
        if not hmac.compare_digest(h.hexdigest(), stored_signature):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Backup signature verification failed: this backup may have been tampered with.",
            )

        # Both checks passed — write the verified plaintext to disk
        sql_path = os.path.join(tmpdir, "homestock_dump.sql")
        with open(sql_path, "wb") as f:
            f.write(plaintext_sql)

        # ── Step 2: Clear connections ────────────────────────────────────────
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

        # ── Step 3: Atomically drop any stale schema and rename live schema ──
        # Single transaction eliminates the window where the stale schema is
        # gone but the rename hasn't happened yet, which would leave no safety
        # net if the process was killed between those two separate calls.
        try:
            _run_psql(
                env,
                "-c",
                f"BEGIN; "
                f"DROP SCHEMA IF EXISTS {_PRE_RESTORE_SCHEMA} CASCADE; "
                f"ALTER SCHEMA homestock RENAME TO {_PRE_RESTORE_SCHEMA}; "
                f"COMMIT;",
                timeout=45,
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

            logger.info("Restore complete from %s", filename)

        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            logger.error("Restore failed, rolling back to pre-restore schema: %s", exc)
            try:
                _run_psql(env, "-c", "DROP SCHEMA IF EXISTS homestock CASCADE", timeout=30)
                _run_psql(
                    env, "-c", f"ALTER SCHEMA {_PRE_RESTORE_SCHEMA} RENAME TO homestock",
                    timeout=15,
                )
                logger.info("Rollback complete — original data is intact")
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
                        "Restore failed and automatic rollback also failed. "
                        "Your original data is preserved in a recovery schema. "
                        "Contact your administrator or check server logs for recovery instructions."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Restore failed — your original data has been automatically preserved.",
            )

        finally:
            engine.dispose()
