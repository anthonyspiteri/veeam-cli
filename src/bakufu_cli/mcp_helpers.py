from __future__ import annotations

import json
import time
from typing import Any

from .api import call_api


def _extract_jobs(data: dict) -> list[dict]:
    if isinstance(data, dict):
        return data.get("data", []) or []
    return []


def _extract_sessions(data: dict) -> list[dict]:
    if isinstance(data, dict):
        return data.get("data", []) or []
    return []


def helper_jobs_start_by_name(args: dict) -> dict:
    name = args.get("name")
    if not name:
        raise ValueError("name is required")
    account = args.get("account")

    jobs_resp = call_api("/api/v1/jobs", pretty=False, account=account)
    jobs = _extract_jobs(json.loads(jobs_resp["body"]))
    match = next((j for j in jobs if j.get("name") == name), None)
    if not match:
        raise ValueError(f"Job not found: {name}")

    job_id = match.get("id")
    start_resp = call_api(f"/api/v1/jobs/{job_id}/start", method="POST", data={}, pretty=False, account=account)
    return {"job": match, "start": json.loads(start_resp["body"]) if start_resp.get("body") else {}}


def helper_jobs_last_result(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    resp = call_api("/api/v1/sessions", params={"limit": 200}, pretty=False, account=account)
    sessions = _extract_sessions(json.loads(resp["body"]))
    filtered = [s for s in sessions if s.get("jobId") == job_id]
    filtered.sort(key=lambda s: s.get("creationTime") or "", reverse=True)
    return {"latest": filtered[0] if filtered else None}


def helper_session_follow(args: dict) -> dict:
    session_id = args.get("sessionId")
    if not session_id:
        raise ValueError("sessionId is required")
    interval = int(args.get("intervalMs", 1000))
    timeout = int(args.get("timeoutMs", 600000))
    account = args.get("account")

    start = time.time()
    while True:
        resp = call_api(f"/api/v1/sessions/{session_id}", pretty=False, account=account)
        data = json.loads(resp["body"]) if resp.get("body") else {}
        state = data.get("state")
        if state in {"Stopped", "Failed", "Success", "Warning"}:
            return data
        if (time.time() - start) * 1000 > timeout:
            return {"state": "Timeout", "session": data}
        time.sleep(interval / 1000.0)


def helper_session_logs(args: dict) -> dict:
    session_id = args.get("sessionId")
    if not session_id:
        raise ValueError("sessionId is required")
    account = args.get("account")
    resp = call_api(f"/api/v1/sessions/{session_id}/logs", pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_repo_capacity(args: dict) -> dict:
    account = args.get("account")
    resp = call_api("/api/v1/backupInfrastructure/repositories/states", pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_repo_add_wasabi(args: dict) -> dict:
    # Expects full repository spec in args["spec"]
    spec = args.get("spec")
    if not spec:
        raise ValueError("spec is required")
    account = args.get("account")
    resp = call_api("/api/v1/backupInfrastructure/repositories", method="POST", data=spec, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_cloud_credentials_add(args: dict) -> dict:
    spec = args.get("spec")
    if not spec:
        raise ValueError("spec is required")
    account = args.get("account")
    resp = call_api("/api/v1/cloudCredentials", method="POST", data=spec, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_object_storage_browse(args: dict) -> dict:
    spec = args.get("spec")
    if not spec:
        raise ValueError("spec is required")
    account = args.get("account")
    resp = call_api("/api/v1/cloudBrowser", method="POST", data=spec, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


HELPERS = {
    "bakufu.jobs.startByName": {
        "description": "Start a job by name and return session id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "account": {"type": "string"},
            },
            "required": ["name"],
        },
        "handler": helper_jobs_start_by_name,
    },
    "bakufu.jobs.lastResult": {
        "description": "Fetch latest session for a job id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string"},
                "account": {"type": "string"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_last_result,
    },
    "bakufu.sessions.follow": {
        "description": "Poll a session until completion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "intervalMs": {"type": "integer"},
                "timeoutMs": {"type": "integer"},
                "account": {"type": "string"},
            },
            "required": ["sessionId"],
        },
        "handler": helper_session_follow,
    },
    "bakufu.sessions.logs": {
        "description": "Fetch session logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "account": {"type": "string"},
            },
            "required": ["sessionId"],
        },
        "handler": helper_session_logs,
    },
    "bakufu.repos.capacity": {
        "description": "Summarize repository capacity and free space.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {"type": "string"}},
        },
        "handler": helper_repo_capacity,
    },
    "bakufu.repos.addWasabi": {
        "description": "Create a Wasabi repository from spec.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object"},
                "account": {"type": "string"},
            },
            "required": ["spec"],
        },
        "handler": helper_repo_add_wasabi,
    },
    "bakufu.cloudCredentials.add": {
        "description": "Create cloud credentials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object"},
                "account": {"type": "string"},
            },
            "required": ["spec"],
        },
        "handler": helper_cloud_credentials_add,
    },
    "bakufu.objectStorage.browse": {
        "description": "Browse object storage resources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object"},
                "account": {"type": "string"},
            },
            "required": ["spec"],
        },
        "handler": helper_object_storage_browse,
    },
}

WORKFLOWS = {
    "bakufu.workflows.investigateFailedJob": {
        "description": "Find latest failed session for a job and return logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string"},
                "jobName": {"type": "string"},
                "account": {"type": "string"},
            },
        },
    },
    "bakufu.workflows.createWasabiRepo": {
        "description": "Create Wasabi repo from cloud credentials and bucket info.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repoSpec": {"type": "object"},
                "account": {"type": "string"},
            },
            "required": ["repoSpec"],
        },
    },
    "bakufu.workflows.capacityReport": {
        "description": "Return repository capacity report.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {"type": "string"}},
        },
    },
    "bakufu.workflows.runSecurityAnalyzer": {
        "description": "Start Security & Compliance Analyzer and return session.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {"type": "string"}},
        },
    },
    "bakufu.workflows.validateImmutability": {
        "description": "Check object storage repositories for immutability settings.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {"type": "string"}},
        },
    },
}


def run_workflow(name: str, arguments: dict):
    from .api import call_api
    account = arguments.get("account")

    if name == "bakufu.workflows.investigateFailedJob":
        job_id = arguments.get("jobId")
        job_name = arguments.get("jobName")
        if not job_id and not job_name:
            raise ValueError("jobId or jobName required")
        if not job_id and job_name:
            jobs_resp = call_api("/api/v1/jobs", pretty=False, account=account)
            jobs = json.loads(jobs_resp.get("body", "{}")).get("data", [])
            match = next((j for j in jobs if j.get("name") == job_name), None)
            if not match:
                raise ValueError(f"Job not found: {job_name}")
            job_id = match.get("id")
        sessions_resp = call_api("/api/v1/sessions", params={"limit": 200}, pretty=False, account=account)
        sessions = json.loads(sessions_resp.get("body", "{}")).get("data", [])
        failed = [s for s in sessions if s.get("jobId") == job_id and s.get("result", {}).get("result") == "Failed"]
        failed.sort(key=lambda s: s.get("creationTime") or "", reverse=True)
        latest = failed[0] if failed else None
        logs = {}
        if latest and latest.get("id"):
            logs_resp = call_api(f"/api/v1/sessions/{latest['id']}/logs", pretty=False, account=account)
            logs = json.loads(logs_resp.get("body", "{}")) if logs_resp.get("body") else {}
        return {"latestFailed": latest, "logs": logs}

    if name == "bakufu.workflows.createWasabiRepo":
        spec = arguments.get("repoSpec")
        if not spec:
            raise ValueError("repoSpec required")
        resp = call_api("/api/v1/backupInfrastructure/repositories", method="POST", data=spec, pretty=False, account=account)
        return json.loads(resp.get("body", "{}")) if resp.get("body") else {}

    if name == "bakufu.workflows.capacityReport":
        resp = call_api("/api/v1/backupInfrastructure/repositories/states", pretty=False, account=account)
        return json.loads(resp.get("body", "{}")) if resp.get("body") else {}

    if name == "bakufu.workflows.runSecurityAnalyzer":
        resp = call_api("/api/v1/securityAnalyzer/start", method="POST", data={}, pretty=False, account=account)
        return json.loads(resp.get("body", "{}")) if resp.get("body") else {}

    if name == "bakufu.workflows.validateImmutability":
        resp = call_api("/api/v1/backupInfrastructure/repositories", pretty=False, account=account)
        data = json.loads(resp.get("body", "{}")) if resp.get("body") else {}
        repos = data.get("data", [])
        immutability = []
        for repo in repos:
            bucket = repo.get("bucket") or {}
            imm = bucket.get("immutability") if isinstance(bucket, dict) else None
            if imm:
                immutability.append({"id": repo.get("id"), "name": repo.get("name"), "immutability": imm})
        return {"immutability": immutability}

    raise ValueError(f"Unknown workflow: {name}")
