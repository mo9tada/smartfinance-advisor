from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt
import datetime
import os
import subprocess
import threading
import sys
from pathlib import Path
from api.notification_service import create_notification

bp = Blueprint("ingestion", __name__, url_prefix="/api/ingestion")

_lock = threading.Lock()
_max_logs = 1500
_state = {
    "running": False,
    "logs": [],
    "next_log_id": 1,
    "started_at": None,
    "finished_at": None,
    "exit_code": None,
}


def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _append_log(message: str):
    cleaned = (message or "").rstrip("\n")
    if not cleaned:
        return

    with _lock:
        log_line = {
            "id": _state["next_log_id"],
            "timestamp": _utc_now_iso(),
            "message": cleaned,
        }
        _state["next_log_id"] += 1
        _state["logs"].append(log_line)
        if len(_state["logs"]) > _max_logs:
            _state["logs"] = _state["logs"][-_max_logs:]


def _admin_only_guard():
    claims = get_jwt()
    if claims.get("role") != "administrator":
        return jsonify(msg="Administrator access required"), 403
    return None


def _run_pipeline_in_background(app):
    backend_root = Path(__file__).resolve().parents[2]
    pipeline_script = backend_root / "data_pipeline" / "main.py"

    try:
        if not pipeline_script.exists():
            _append_log(f"Pipeline script not found: {pipeline_script}")
            with _lock:
                _state["running"] = False
                _state["finished_at"] = _utc_now_iso()
                _state["exit_code"] = -1
            return

        cmd = [sys.executable, "-u", str(pipeline_script)]
        _append_log(f"Starting ingestion with command: {' '.join(cmd)}")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            cmd,
            cwd=str(backend_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if process.stdout:
            for line in process.stdout:
                _append_log(line)

        exit_code = process.wait()
        if exit_code == 0:
            _append_log("Ingestion completed successfully.")
            with app.app_context():
                create_notification("ingestion", "A data ingestion has been successfully completed by the admin.")
        else:
            _append_log(f"Ingestion failed with exit code: {exit_code}")

        with _lock:
            _state["running"] = False
            _state["finished_at"] = _utc_now_iso()
            _state["exit_code"] = exit_code
    except Exception as e:
        _append_log(f"Unexpected ingestion error: {str(e)}")
        with _lock:
            _state["running"] = False
            _state["finished_at"] = _utc_now_iso()
            _state["exit_code"] = -1


@bp.route("/start", methods=["POST"])
@jwt_required()
def start_ingestion():
    forbidden = _admin_only_guard()
    if forbidden:
        return forbidden

    with _lock:
        if _state["running"]:
            return jsonify(msg="Ingestion already running"), 409

        _state["running"] = True
        _state["logs"] = []
        _state["next_log_id"] = 1
        _state["started_at"] = _utc_now_iso()
        _state["finished_at"] = None
        _state["exit_code"] = None

    app = current_app._get_current_object()
    thread = threading.Thread(target=_run_pipeline_in_background, args=(app,), daemon=True)
    thread.start()

    return jsonify(msg="Ingestion started", started_at=_state["started_at"]), 202


@bp.route("/status", methods=["GET"])
@jwt_required()
def ingestion_status():
    forbidden = _admin_only_guard()
    if forbidden:
        return forbidden

    with _lock:
        last_log_id = _state["logs"][-1]["id"] if _state["logs"] else 0
        return jsonify(
            running=_state["running"],
            started_at=_state["started_at"],
            finished_at=_state["finished_at"],
            exit_code=_state["exit_code"],
            last_log_id=last_log_id,
        ), 200


@bp.route("/logs", methods=["GET"])
@jwt_required()
def ingestion_logs():
    forbidden = _admin_only_guard()
    if forbidden:
        return forbidden

    from_id = request.args.get("from_id", default=0, type=int)

    with _lock:
        lines = [line for line in _state["logs"] if line["id"] > from_id]
        next_from_id = _state["logs"][-1]["id"] if _state["logs"] else from_id
        return jsonify(
            lines=lines,
            next_from_id=next_from_id,
            running=_state["running"],
            exit_code=_state["exit_code"],
            started_at=_state["started_at"],
            finished_at=_state["finished_at"],
        ), 200
