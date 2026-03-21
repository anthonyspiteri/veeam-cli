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


def helper_proxy_states(args: dict) -> dict:
    account = args.get("account")
    resp = call_api("/api/v1/backupInfrastructure/proxies/states", pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_sobr_list(args: dict) -> dict:
    account = args.get("account")
    resp = call_api("/api/v1/backupInfrastructure/scaleOutRepositories", pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_managed_server_rescan(args: dict) -> dict:
    server_id = args.get("serverId")
    account = args.get("account")
    if server_id:
        resp = call_api(
            f"/api/v1/backupInfrastructure/managedServers/{server_id}/rescan",
            method="POST", data={}, pretty=False, account=account,
        )
    else:
        resp = call_api(
            "/api/v1/backupInfrastructure/managedServers/rescan",
            method="POST", data={}, pretty=False, account=account,
        )
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_job_create(args: dict) -> dict:
    spec = args.get("spec")
    if not spec:
        raise ValueError("spec is required")
    account = args.get("account")
    resp = call_api("/api/v1/jobs", method="POST", data=spec, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_job_schedule_update(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    schedule = args.get("schedule")
    if not schedule:
        raise ValueError("schedule is required")
    account = args.get("account")

    get_resp = call_api(f"/api/v1/jobs/{job_id}", pretty=False, account=account)
    job = json.loads(get_resp["body"]) if get_resp.get("body") else {}
    job["schedule"] = schedule
    if "storage" in args and args["storage"]:
        job["storage"] = args["storage"]

    put_resp = call_api(f"/api/v1/jobs/{job_id}", method="PUT", data=job, pretty=False, account=account)
    return json.loads(put_resp["body"]) if put_resp.get("body") else {}


def helper_malware_scan(args: dict) -> dict:
    spec = args.get("spec")
    if not spec:
        raise ValueError("spec is required")
    account = args.get("account")
    resp = call_api("/api/v1/malwareDetection/scanBackup", method="POST", data=spec, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_stop(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    resp = call_api(f"/api/v1/jobs/{job_id}/stop", method="POST", data={}, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_enable(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    resp = call_api(f"/api/v1/jobs/{job_id}/enable", method="POST", data={}, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_disable(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    resp = call_api(f"/api/v1/jobs/{job_id}/disable", method="POST", data={}, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_retry(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    resp = call_api(f"/api/v1/jobs/{job_id}/retry", method="POST", data={}, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_clone(args: dict) -> dict:
    job_id = args.get("jobId")
    if not job_id:
        raise ValueError("jobId is required")
    account = args.get("account")
    body: dict = {}
    if args.get("name"):
        body["name"] = args["name"]
    resp = call_api(f"/api/v1/jobs/{job_id}/clone", method="POST", data=body, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


def helper_jobs_states(args: dict) -> dict:
    account = args.get("account")
    params: dict = {}
    for key, param in [
        ("nameFilter", "nameFilter"), ("typeFilter", "typeFilter"),
        ("lastResultFilter", "lastResultFilter"), ("statusFilter", "statusFilter"),
        ("repositoryIdFilter", "repositoryIdFilter"),
        ("lastRunAfterFilter", "lastRunAfterFilter"),
        ("limit", "limit"),
    ]:
        if args.get(key):
            params[param] = args[key]
    if args.get("isHighPriorityJobFilter"):
        params["isHighPriorityJobFilter"] = "true"
    resp = call_api("/api/v1/jobs/states", params=params, pretty=False, account=account)
    return json.loads(resp["body"]) if resp.get("body") else {}


HELPERS = {
    "bakufu_jobs_startByName": {
        "description": "Start a backup job by name and return its session id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Exact job name"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["name"],
        },
        "handler": helper_jobs_start_by_name,
    },
    "bakufu_jobs_lastResult": {
        "description": "Fetch the latest session for a given job id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_last_result,
    },
    "bakufu_sessions_follow": {
        "description": "Poll a session until it reaches a terminal state (Success, Failed, Warning, Stopped).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string", "description": "Veeam session UUID to follow"},
                "intervalMs": {"type": "integer", "description": "Polling interval in milliseconds (default 1000)"},
                "timeoutMs": {"type": "integer", "description": "Maximum wait time in milliseconds (default 600000)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["sessionId"],
        },
        "handler": helper_session_follow,
    },
    "bakufu_sessions_logs": {
        "description": "Fetch log entries for a session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string", "description": "Veeam session UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["sessionId"],
        },
        "handler": helper_session_logs,
    },
    "bakufu_repos_capacity": {
        "description": "Return repository capacity and free space summary for all repositories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
        "handler": helper_repo_capacity,
    },
    "bakufu_repos_addWasabi": {
        "description": "Create a Wasabi object storage repository from a spec object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Full repository creation spec (see Veeam API docs)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["spec"],
        },
        "handler": helper_repo_add_wasabi,
    },
    "bakufu_cloudCredentials_add": {
        "description": "Create a new set of cloud credentials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Cloud credentials creation spec (see Veeam API docs)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["spec"],
        },
        "handler": helper_cloud_credentials_add,
    },
    "bakufu_objectStorage_browse": {
        "description": "Browse object storage resources via the Veeam cloud browser.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Cloud browser request spec (see Veeam API docs)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["spec"],
        },
        "handler": helper_object_storage_browse,
    },
    "bakufu_proxies_states": {
        "description": "Return backup proxy states and task slot utilization for all proxies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
        "handler": helper_proxy_states,
    },
    "bakufu_sobr_list": {
        "description": "List all scale-out backup repositories with performance and capacity tier details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
        "handler": helper_sobr_list,
    },
    "bakufu_managedServers_rescan": {
        "description": "Rescan a specific managed server or all managed servers to refresh component state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "serverId": {"type": "string", "description": "Managed server UUID (omit to rescan all)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
        "handler": helper_managed_server_rescan,
    },
    "bakufu_jobs_create": {
        "description": "Create a new backup job from a full job specification object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Full job creation spec (use bakufu schema CreateJob)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["spec"],
        },
        "handler": helper_job_create,
    },
    "bakufu_jobs_updateSchedule": {
        "description": "Update a job schedule and optionally storage/retention settings. Fetches current config, merges schedule, and PUTs back.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "schedule": {"type": "object", "description": "New schedule object to merge into the job config"},
                "storage": {"type": "object", "description": "Optional updated storage/retention object"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId", "schedule"],
        },
        "handler": helper_job_schedule_update,
    },
    "bakufu_malwareDetection_scan": {
        "description": "Start a malware scan on backup objects using antivirus or YARA rules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Malware scan spec with target backup objects and scan method"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["spec"],
        },
        "handler": helper_malware_scan,
    },
    "bakufu_jobs_stop": {
        "description": "Stop a currently running backup job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_stop,
    },
    "bakufu_jobs_enable": {
        "description": "Re-enable a disabled backup job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_enable,
    },
    "bakufu_jobs_disable": {
        "description": "Disable a backup job from scheduled execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_disable,
    },
    "bakufu_jobs_retry": {
        "description": "Retry the last failed session for a backup job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_retry,
    },
    "bakufu_jobs_clone": {
        "description": "Clone an existing backup job, optionally providing a new name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID to clone"},
                "name": {"type": "string", "description": "Name for the cloned job (optional)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["jobId"],
        },
        "handler": helper_jobs_clone,
    },
    "bakufu_jobs_states": {
        "description": "List jobs with execution state and last-run details, with rich server-side filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nameFilter": {"type": "string", "description": "Filter by job name pattern"},
                "typeFilter": {"type": "string", "description": "Filter by job type e.g. VSphereBackup"},
                "lastResultFilter": {"type": "string", "description": "Filter by last result: Success, Warning, Failed, None"},
                "statusFilter": {"type": "string", "description": "Filter by current status: Running, Inactive, Disabled"},
                "repositoryIdFilter": {"type": "string", "description": "Filter by repository UUID"},
                "lastRunAfterFilter": {"type": "string", "description": "ISO8601 timestamp — return jobs that ran after this"},
                "isHighPriorityJobFilter": {"type": "boolean", "description": "Return high priority jobs only"},
                "limit": {"type": "integer", "description": "Maximum results (default 200)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
        "handler": helper_jobs_states,
    },
}

def workflow_daily_job_health(account, arguments):
    resp = call_api("/api/v1/jobs", pretty=False, account=account)
    jobs = _extract_jobs(json.loads(resp["body"]))
    sessions_resp = call_api("/api/v1/sessions", params={"limit": 500}, pretty=False, account=account)
    sessions = _extract_sessions(json.loads(sessions_resp["body"]))
    # Build map: jobId -> most recent session
    latest: dict = {}
    for s in sessions:
        jid = s.get("jobId")
        if not jid:
            continue
        existing = latest.get(jid)
        if not existing or (s.get("creationTime", "") > existing.get("creationTime", "")):
            latest[jid] = s
    buckets: dict = {"Success": [], "Warning": [], "Failed": [], "Running": [], "None": []}
    for j in jobs:
        jid = j.get("id")
        s = latest.get(jid)
        result = s.get("result") if s else None
        state = s.get("state") if s else None
        if state in {"Starting", "Working"}:
            bucket = "Running"
        elif result in buckets:
            bucket = result
        else:
            bucket = "None"
        buckets[bucket].append({
            "jobId": jid,
            "jobName": j.get("name"),
            "sessionId": s.get("id") if s else None,
            "result": result,
            "state": state,
            "endTime": s.get("endTime") if s else None,
        })
    return {
        "summary": {k: len(v) for k, v in buckets.items()},
        "jobs": buckets,
    }


def workflow_rerun_failed_job(account, arguments):
    job_id = arguments.get("jobId")
    job_name = arguments.get("jobName")
    # Resolve name -> id if needed
    if not job_id and job_name:
        jobs_resp = call_api("/api/v1/jobs", pretty=False, account=account)
        jobs = _extract_jobs(json.loads(jobs_resp["body"]))
        match = next((j for j in jobs if j.get("name") == job_name), None)
        if not match:
            raise ValueError(f"Job not found: {job_name}")
        job_id = match.get("id")
    if not job_id:
        raise ValueError("jobId or jobName is required")
    # Get latest failed session for context
    sessions_resp = call_api("/api/v1/sessions", params={"limit": 200}, pretty=False, account=account)
    sessions = _extract_sessions(json.loads(sessions_resp["body"]))
    job_sessions = [s for s in sessions if s.get("jobId") == job_id]
    job_sessions.sort(key=lambda s: s.get("creationTime") or "", reverse=True)
    last_failed = next((s for s in job_sessions if s.get("result") == "Failed"), None)
    # Start the job
    start_resp = call_api(f"/api/v1/jobs/{job_id}/start", method="POST", data={}, pretty=False, account=account)
    start_data = json.loads(start_resp["body"]) if start_resp.get("body") else {}
    result: dict = {"jobId": job_id, "lastFailed": last_failed, "start": start_data}
    # Optionally follow the new session
    if arguments.get("wait") and start_data.get("id"):
        session_id = start_data["id"]
        interval = int(arguments.get("intervalMs", 2000))
        timeout = int(arguments.get("timeoutMs", 300000))
        start_ts = time.time()
        while True:
            s_resp = call_api(f"/api/v1/sessions/{session_id}", pretty=False, account=account)
            s_data = json.loads(s_resp["body"]) if s_resp.get("body") else {}
            if s_data.get("state") in {"Stopped", "Failed", "Success", "Warning"}:
                result["session"] = s_data
                break
            if (time.time() - start_ts) * 1000 > timeout:
                result["session"] = {"state": "Timeout"}
                break
            time.sleep(interval / 1000.0)
    return result


def workflow_repository_health_review(account, arguments):
    repos_resp = call_api("/api/v1/backupInfrastructure/repositories", pretty=False, account=account)
    repos = json.loads(repos_resp["body"]) if repos_resp.get("body") else {}
    repo_list = repos.get("data", repos) if isinstance(repos, dict) else repos
    states_resp = call_api("/api/v1/backupInfrastructure/repositories/states", pretty=False, account=account)
    states_data = json.loads(states_resp["body"]) if states_resp.get("body") else {}
    states_list = states_data.get("data", []) if isinstance(states_data, dict) else []
    states_map = {s.get("id"): s for s in states_list if s.get("id")}
    health = []
    for r in (repo_list if isinstance(repo_list, list) else []):
        rid = r.get("id")
        state = states_map.get(rid, {})
        capacity = state.get("capacityGB")
        free = state.get("freeSpaceGB")
        used_pct = None
        if capacity and free is not None and capacity > 0:
            used_pct = round((capacity - free) / capacity * 100, 1)
        health.append({
            "id": rid,
            "name": r.get("name"),
            "type": r.get("type"),
            "capacityGB": capacity,
            "freeSpaceGB": free,
            "usedPct": used_pct,
            "isOutOfDate": state.get("isOutOfDate"),
            "isUnavailable": state.get("isUnavailable"),
        })
    return {"repositories": health}


WORKFLOWS = {
    "bakufu_workflows_investigateFailedJob": {
        "description": "Find the latest failed session for a job and return its logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID (provide jobId or jobName)"},
                "jobName": {"type": "string", "description": "Exact job name (provide jobId or jobName)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_createWasabiRepo": {
        "description": "Create a Wasabi repository from cloud credentials and bucket info.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repoSpec": {"type": "object", "description": "Full repository creation spec"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
            "required": ["repoSpec"],
        },
    },
    "bakufu_workflows_capacityReport": {
        "description": "Return a capacity report for all backup repositories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_runSecurityAnalyzer": {
        "description": "Start the Veeam Security and Compliance Analyzer and optionally wait for results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wait": {"type": "boolean", "description": "Wait for the analyzer to finish before returning"},
                "intervalMs": {"type": "integer", "description": "Polling interval in ms when waiting (default 2000)"},
                "timeoutMs": {"type": "integer", "description": "Maximum wait time in ms (default 300000)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_validateImmutability": {
        "description": "Check all object storage repositories for immutability configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_dailyJobHealth": {
        "description": "Summarize job results for the last 24 hours, bucketed by Success, Warning, Failed, Running, and None.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_rerunFailedJob": {
        "description": "Find the latest failed session for a job, start the job again, and optionally wait for completion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID (provide jobId or jobName)"},
                "jobName": {"type": "string", "description": "Exact job name (provide jobId or jobName)"},
                "wait": {"type": "boolean", "description": "Wait for the new session to complete"},
                "intervalMs": {"type": "integer", "description": "Poll interval ms when wait=true (default 2000)"},
                "timeoutMs": {"type": "integer", "description": "Max wait ms when wait=true (default 300000)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_repositoryHealthReview": {
        "description": "List all repositories with capacity utilisation, free space, and availability status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_weeklyJobHealth": {
        "description": "Summarize job results over the last 7 days, bucketed by Success, Warning, Failed, Running, and None.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
    "bakufu_workflows_emergencyStopJob": {
        "description": "Stop a running job by ID or name and return its last session logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobId": {"type": "string", "description": "Veeam job UUID (provide jobId or jobName)"},
                "jobName": {"type": "string", "description": "Exact job name (provide jobId or jobName)"},
                "account": {"type": "string", "description": "Named account to use for authentication"},
            },
        },
    },
}


def run_workflow(name: str, arguments: dict):
    from .api import call_api
    import time
    account = arguments.get("account")

    if name == "bakufu_workflows_investigateFailedJob":
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

    if name == "bakufu_workflows_createWasabiRepo":
        spec = arguments.get("repoSpec")
        if not spec:
            raise ValueError("repoSpec required")
        resp = call_api("/api/v1/backupInfrastructure/repositories", method="POST", data=spec, pretty=False, account=account)
        return json.loads(resp.get("body", "{}")) if resp.get("body") else {}

    if name == "bakufu_workflows_capacityReport":
        resp = call_api("/api/v1/backupInfrastructure/repositories/states", pretty=False, account=account)
        return json.loads(resp.get("body", "{}")) if resp.get("body") else {}

    if name == "bakufu_workflows_runSecurityAnalyzer":
        resp = call_api("/api/v1/securityAnalyzer/start", method="POST", data={}, pretty=False, account=account)
        start = json.loads(resp.get("body", "{}")) if resp.get("body") else {}
        if not arguments.get("wait"):
            return {"start": start}

        interval_ms = int(arguments.get("intervalMs", 2000) or 2000)
        timeout_ms = int(arguments.get("timeoutMs", 300000) or 300000)
        started_at = time.time()
        target_id = start.get("id")
        terminal = {"Stopped", "Failed", "Success", "Warning"}
        latest = {}

        while True:
            last_resp = call_api("/api/v1/securityAnalyzer/lastRun", pretty=False, account=account)
            latest = json.loads(last_resp.get("body", "{}")) if last_resp.get("body") else {}
            state = latest.get("state")
            same_session = bool(target_id) and latest.get("id") == target_id
            if same_session and state in terminal:
                break
            if (time.time() - started_at) * 1000 > timeout_ms:
                return {"start": start, "lastRun": latest, "state": "Timeout"}
            time.sleep(interval_ms / 1000.0)

        bp_resp = call_api("/api/v1/securityAnalyzer/bestPractices", pretty=False, account=account)
        best_practices = json.loads(bp_resp.get("body", "{}")) if bp_resp.get("body") else {}
        return {"start": start, "lastRun": latest, "bestPractices": best_practices}

    if name == "bakufu_workflows_validateImmutability":
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

    if name == "bakufu_workflows_dailyJobHealth":
        return workflow_daily_job_health(account, arguments)

    if name == "bakufu_workflows_rerunFailedJob":
        return workflow_rerun_failed_job(account, arguments)

    if name == "bakufu_workflows_repositoryHealthReview":
        return workflow_repository_health_review(account, arguments)

    if name == "bakufu_workflows_weeklyJobHealth":
        return workflow_weekly_job_health(account, arguments)

    if name == "bakufu_workflows_emergencyStopJob":
        return workflow_emergency_stop_job(account, arguments)

    raise ValueError(f"Unknown workflow: {name}")


def workflow_weekly_job_health(account, arguments):
    """7-day health summary — same logic as daily but fetches more sessions."""
    resp = call_api("/api/v1/jobs", pretty=False, account=account)
    jobs = _extract_jobs(json.loads(resp["body"]))
    sessions_resp = call_api("/api/v1/sessions", params={"limit": 1000}, pretty=False, account=account)
    sessions = _extract_sessions(json.loads(sessions_resp["body"]))
    latest: dict = {}
    for s in sessions:
        jid = s.get("jobId")
        if not jid:
            continue
        existing = latest.get(jid)
        if not existing or (s.get("creationTime", "") > existing.get("creationTime", "")):
            latest[jid] = s
    buckets: dict = {"Success": [], "Warning": [], "Failed": [], "Running": [], "None": []}
    for j in jobs:
        jid = j.get("id")
        s = latest.get(jid)
        result = s.get("result") if s else None
        state = s.get("state") if s else None
        bucket = "Running" if state in {"Starting", "Working"} else (result if result in buckets else "None")
        buckets[bucket].append({
            "jobId": jid,
            "jobName": j.get("name"),
            "sessionId": s.get("id") if s else None,
            "result": result,
            "state": state,
            "endTime": s.get("endTime") if s else None,
        })
    return {
        "window": "7d",
        "summary": {k: len(v) for k, v in buckets.items()},
        "jobs": buckets,
    }


def workflow_emergency_stop_job(account, arguments):
    """Stop a running job and return its last session logs."""
    job_id = arguments.get("jobId")
    job_name = arguments.get("jobName")
    if not job_id and job_name:
        jobs_resp = call_api("/api/v1/jobs", pretty=False, account=account)
        jobs = _extract_jobs(json.loads(jobs_resp["body"]))
        match = next((j for j in jobs if j.get("name") == job_name), None)
        if not match:
            raise ValueError(f"Job not found: {job_name}")
        job_id = match.get("id")
    if not job_id:
        raise ValueError("jobId or jobName is required")
    stop_resp = call_api(f"/api/v1/jobs/{job_id}/stop", method="POST", data={}, pretty=False, account=account)
    stop_data = json.loads(stop_resp["body"]) if stop_resp.get("body") else {}
    sessions_resp = call_api("/api/v1/sessions", params={"limit": 10}, pretty=False, account=account)
    sessions = _extract_sessions(json.loads(sessions_resp["body"]))
    job_sessions = [s for s in sessions if s.get("jobId") == job_id]
    job_sessions.sort(key=lambda s: s.get("creationTime") or "", reverse=True)
    last_session = job_sessions[0] if job_sessions else None
    logs = {}
    if last_session:
        logs_resp = call_api(f"/api/v1/sessions/{last_session['id']}/logs", pretty=False, account=account)
        logs = json.loads(logs_resp["body"]) if logs_resp.get("body") else {}
    return {"jobId": job_id, "stop": stop_data, "lastSession": last_session, "logs": logs}


def run_helper(name: str, arguments: dict):
    """Dispatch a helper by its full key (e.g. 'bakufu_jobs_startByName')."""
    if name not in HELPERS:
        raise ValueError(f"Unknown helper: {name}")
    handler = HELPERS[name]["handler"]
    return handler(arguments)
