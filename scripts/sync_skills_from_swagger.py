import json
import re
import shutil
from pathlib import Path
from typing import Optional, List

root = Path(__file__).resolve().parents[1]
schemas_dir = root / 'schemas'
swagger_candidates = sorted(
    schemas_dir.glob('swagger*.json'),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
swagger_path = swagger_candidates[0] if swagger_candidates else (root / 'swagger_v1.3.json')
skills_dir = root / 'skills'
docs_path = root / 'docs' / 'skills.md'

swagger = json.loads(swagger_path.read_text())


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def normalize_description(text: str, fallback: str) -> str:
    if not text:
        return fallback
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text or fallback


def humanize(name: str) -> str:
    return name.replace('-', ' ').replace('_', ' ').strip().title()


def default_prompt_for(category: str, name: str, description: str) -> str:
    if category == 'Persona':
        return f"Use {name} guidance to execute backup operations with concise status, risks, and next actions."
    if category == 'Recipe':
        return f"Run {name} and summarize outcome with evidence and follow-up commands."
    if category == 'Helper':
        return f"Use {name} to perform this backup task and return structured JSON."
    return f"Use {name} for Veeam API operations and return structured JSON."


def yaml_quote(value: str) -> str:
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f"\"{escaped}\""


def skill_frontmatter(name: str, description: str, category: str, requires_skills: Optional[List[str]] = None) -> str:
    requires_skills = requires_skills or []
    lines = [
        '---',
        f'name: {yaml_quote(name)}',
        'version: "1.0.0"',
        f'description: {yaml_quote(description)}',
        'metadata:',
        '  openclaw:',
        f'    category: {yaml_quote(category.lower())}',
        '    requires:',
        '      bins:',
        '        - "bakufu"',
        '      skills:',
    ]
    if requires_skills:
        for req in requires_skills:
            lines.append(f'        - {yaml_quote(req)}')
    else:
        lines.append('        - "bakufu-shared"')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


helper_profiles = {
    'bakufu-jobs-start-by-name': {
        'requires': ['bakufu-jobs', 'bakufu-sessions'],
        'commands': ['bakufu jobs list --pretty', 'bakufu workflows investigateFailedJob --job-name "<name>"'],
        'instructions': [
            'Resolve the exact job name before start to avoid launching the wrong workload.',
            'Capture returned session identifiers for follow-up checks.',
            'Immediately verify resulting session state and logs if state is non-success.',
        ],
        'tips': [
            'Use account override for multi-tenant environments.',
            'Prefer name-based start in operator runbooks where IDs are unstable.',
        ],
    },
    'bakufu-jobs-last-result': {
        'requires': ['bakufu-jobs', 'bakufu-sessions'],
        'commands': ['bakufu jobs list --pretty', 'bakufu sessions show <session-id> --pretty'],
        'instructions': [
            'Resolve the latest session for the target job before escalation.',
            'Use session state and result together; state alone is not enough.',
            'Escalate repeated warnings as operational debt before they become failures.',
        ],
        'tips': [
            'Track trends across runs, not just the latest result.',
            'Attach session IDs in incident summaries.',
        ],
    },
    'bakufu-session-follow': {
        'requires': ['bakufu-sessions'],
        'commands': ['bakufu sessions show <session-id> --pretty', 'bakufu sessions logs <session-id> --pretty'],
        'instructions': [
            'Poll active sessions until terminal state before reporting completion.',
            'Stop polling only on terminal states or timeout.',
            'Pull logs automatically for failed or warning outcomes.',
        ],
        'tips': [
            'Use shorter intervals for incident response, longer for background checks.',
            'Persist timeout outcomes for retry analysis.',
        ],
    },
    'bakufu-session-logs': {
        'requires': ['bakufu-sessions'],
        'commands': ['bakufu sessions logs <session-id> --pretty'],
        'instructions': [
            'Filter to failed/warning records first to reduce noise.',
            'Correlate task errors with infrastructure objects before remediation.',
            'Retain raw log JSON as evidence for audits and postmortems.',
        ],
        'tips': [
            'Use logs with session summary; each alone is incomplete.',
            'Capture exact error text and object IDs in tickets.',
        ],
    },
    'bakufu-repo-capacity': {
        'requires': ['bakufu-repositories'],
        'commands': ['bakufu workflows capacityReport', 'bakufu run Repositories GetAllRepositories --pretty'],
        'instructions': [
            'Assess free space and growth patterns before approving policy expansion.',
            'Highlight repositories near threshold with concrete remediation.',
            'Cross-check capacity anomalies against recent job/session behavior.',
        ],
        'tips': [
            'Include capacity snapshots in weekly operations reports.',
            'Treat sudden free-space drops as incident candidates.',
        ],
    },
    'bakufu-repo-add-wasabi': {
        'requires': ['bakufu-repositories', 'bakufu-cloud-browser', 'bakufu-cloud-credentials-add'],
        'commands': ['bakufu workflows createWasabiRepo --spec @repo.json'],
        'instructions': [
            'Validate credentials, region, bucket, and folder before creation.',
            'Confirm immutability and retention settings align with policy.',
            'Verify repository health after create before assigning jobs.',
        ],
        'tips': [
            'Keep repository specs versioned for repeatable provisioning.',
            'Use dedicated credentials for principle-of-least-privilege.',
        ],
    },
    'bakufu-cloud-credentials-add': {
        'requires': ['bakufu-credentials', 'bakufu-cloud-browser'],
        'commands': ['bakufu call /api/v1/cloudCredentials --method POST --json @creds.json --pretty'],
        'instructions': [
            'Scope credentials to required buckets and operations only.',
            'Test credential access with object storage browse before production use.',
            'Rotate credentials with change tracking and validation checks.',
        ],
        'tips': [
            'Separate read-only and management credentials where possible.',
            'Document ownership and rotation schedule for every secret.',
        ],
    },
    'bakufu-object-storage-browse': {
        'requires': ['bakufu-cloud-browser'],
        'commands': ['bakufu call /api/v1/cloudBrowser --method POST --json @browse.json --pretty'],
        'instructions': [
            'Use browse to validate target paths before repository create/update.',
            'Confirm bucket and folder paths exactly match policy expectations.',
            'Capture discovered object hierarchy for provisioning evidence.',
        ],
        'tips': [
            'Avoid manual path assumptions in scripted onboarding.',
            'Use browse output to preflight automation specs.',
        ],
    },
}


def _default_helper_profile(name: str) -> dict:
    return {
        'requires': ['bakufu-shared'],
        'commands': ['bakufu --help', 'bakufu run <Tag> <OperationId> --pretty'],
        'instructions': [
            'Use this helper to perform focused task execution with structured output.',
            'Confirm prerequisites and identifiers before issuing writes.',
            'Capture resulting IDs and state for downstream workflows.',
        ],
        'tips': [
            'Prefer helper commands before low-level operation calls.',
            'Attach raw JSON when handing off to other operators.',
        ],
    }


recipe_workflow_map = {
    'recipe-investigate-failed-job': 'investigateFailedJob',
    'recipe-rerun-failed-job': 'investigateFailedJob',
    'recipe-capacity-report': 'capacityReport',
    'recipe-create-wasabi-repo': 'createWasabiRepo',
    'recipe-security-analyzer-run': 'runSecurityAnalyzer',
    'recipe-validate-immutability': 'validateImmutability',
}


def _recipe_profile(name: str) -> dict:
    workflow = recipe_workflow_map.get(name)
    commands = ['bakufu jobs list --pretty', 'bakufu sessions show <session-id> --pretty']
    if workflow:
        commands.insert(0, f'bakufu workflows {workflow}')
    return {
        'requires': ['bakufu-shared', 'bakufu-jobs', 'bakufu-sessions'],
        'commands': commands,
        'instructions': [
            'Start with the highest-level workflow/command for this recipe.',
            'Collect identifiers (job/session/repository) and keep them in every step.',
            'Escalate to targeted `bakufu run` calls when additional detail is required.',
        ],
        'tips': [
            'Keep recipe outputs concise: status, evidence, and next action.',
            'Store raw JSON artifacts for repeatability and auditing.',
        ],
    }


services = [
    {
        'name': 'bakufu-shared',
        'description': 'Common auth, config, and Swagger-driven endpoint conventions.',
        'tag': 'Shared',
    }
]

for tag in swagger.get('tags', []):
    if not isinstance(tag, dict):
        continue
    tag_name = tag.get('name')
    if not tag_name:
        continue
    if tag_name.startswith('Section'):
        continue
    services.append(
        {
            'name': f"bakufu-{slugify(tag_name)}",
            'description': normalize_description(tag.get('description', ''), f'Operations for {tag_name}.'),
            'tag': tag_name,
        }
    )

helpers = [
    {'name': 'bakufu-jobs-start-by-name', 'description': 'Start a job by name and return session details.'},
    {'name': 'bakufu-jobs-last-result', 'description': 'Get latest job session result and status.'},
    {'name': 'bakufu-session-follow', 'description': 'Poll a session until terminal state.'},
    {'name': 'bakufu-session-logs', 'description': 'Fetch session logs and surface failures.'},
    {'name': 'bakufu-repo-capacity', 'description': 'Summarize repository capacity and free space.'},
    {'name': 'bakufu-repo-add-wasabi', 'description': 'Create a Wasabi object storage repository.'},
    {'name': 'bakufu-cloud-credentials-add', 'description': 'Create cloud credentials for S3-compatible storage.'},
    {'name': 'bakufu-object-storage-browse', 'description': 'Browse object storage regions, buckets, and folders.'},
    {'name': 'bakufu-job-by-name', 'description': 'Resolve a job id from a job name.'},
    {'name': 'bakufu-session-last-failed', 'description': 'Find the most recent failed session for a job.'},
    {'name': 'bakufu-repo-immutability-summary', 'description': 'Summarize immutability settings across repositories.'},
    {'name': 'bakufu-security-analyzer-last-run', 'description': 'Get the latest Security Analyzer run state and findings.'},
]

personas = [
    {'name': 'persona-backup-admin', 'description': 'Design and govern backup infrastructure and policy.'},
    {'name': 'persona-backup-operator', 'description': 'Run daily backup operations and resolve failed jobs.'},
    {'name': 'persona-security-admin', 'description': 'Operate security analyzer, malware detection, and hardening controls.'},
    {'name': 'persona-dr-operator', 'description': 'Validate restore readiness and execute DR runbooks.'},
    {'name': 'persona-auditor', 'description': 'Collect compliance evidence and produce operational audit summaries.'},
]

recipes = [
    {'name': 'recipe-investigate-failed-job', 'description': 'Find the latest failed job session and collect logs.'},
    {'name': 'recipe-rerun-failed-job', 'description': 'Start a failed job again and monitor session completion.'},
    {'name': 'recipe-daily-job-health', 'description': 'Summarize success, warning, and failed jobs in the last 24 hours.'},
    {'name': 'recipe-weekly-job-health', 'description': 'Generate a weekly trend summary of job results.'},
    {'name': 'recipe-capacity-report', 'description': 'Produce repository capacity, free-space, and usage report.'},
    {'name': 'recipe-validate-immutability', 'description': 'Verify object storage immutability settings and retention posture.'},
    {'name': 'recipe-create-wasabi-repo', 'description': 'Create Wasabi credentials and repository mapping.'},
    {'name': 'recipe-repository-rescan', 'description': 'Rescan repositories and capture result states.'},
    {'name': 'recipe-repository-online-check', 'description': 'List repositories and flag offline or out-of-date states.'},
    {'name': 'recipe-security-analyzer-run', 'description': 'Run Security Analyzer and summarize findings.'},
    {'name': 'recipe-security-analyzer-schedule-review', 'description': 'Inspect Security Analyzer schedule configuration.'},
    {'name': 'recipe-best-practices-review', 'description': 'Collect and summarize best-practice compliance results.'},
    {'name': 'recipe-malware-events-review', 'description': 'Review recent malware detection events and statuses.'},
    {'name': 'recipe-malware-scan-start', 'description': 'Start malware scan workflow and track completion.'},
    {'name': 'recipe-license-posture', 'description': 'Summarize installed license and consumption posture.'},
    {'name': 'recipe-config-backup-run', 'description': 'Start configuration backup and validate outcome.'},
    {'name': 'recipe-config-backup-policy-review', 'description': 'Review configuration backup policy and schedule.'},
    {'name': 'recipe-proxy-health-review', 'description': 'List backup proxies and validate operational readiness.'},
    {'name': 'recipe-managed-server-health', 'description': 'List managed servers and identify unavailable hosts.'},
    {'name': 'recipe-protection-group-rescan', 'description': 'Rescan protection group entities and capture upgrade status.'},
    {'name': 'recipe-job-session-export', 'description': 'Export recent job session records for reporting.'},
    {'name': 'recipe-audit-four-eyes-events', 'description': 'Collect authorization events for four-eyes audit evidence.'},
    {'name': 'recipe-restore-point-coverage', 'description': 'Summarize restore-point availability by workload.'},
    {'name': 'recipe-restore-readiness-check', 'description': 'Validate restore paths, mount servers, and key dependencies.'},
    {'name': 'recipe-dr-failover-readiness', 'description': 'Review replica and failover objects for DR readiness.'},
    {'name': 'recipe-dr-failback-status', 'description': 'Inspect failback sessions and unresolved states.'},
    {'name': 'recipe-session-sla-breach', 'description': 'Identify sessions breaching defined completion thresholds.'},
    {'name': 'recipe-encryption-posture', 'description': 'Review encryption and KMS configuration coverage.'},
    {'name': 'recipe-traffic-rules-review', 'description': 'Capture network traffic rule configuration for operations review.'},
    {'name': 'recipe-auditor-monthly-pack', 'description': 'Build a monthly compliance evidence pack for auditors.'},
]

catalog = {
    'services': [{'name': s['name'], 'description': s['description']} for s in services],
    'helpers': helpers,
    'personas': personas,
    'recipes': recipes,
}

persona_profiles = {
    'persona-backup-admin': {
        'title': 'Backup Admin',
        'mission': 'Own backup architecture, governance, and platform reliability.',
        'requires': [
            'bakufu-repositories',
            'bakufu-jobs',
            'bakufu-session-logs',
            'bakufu-repo-capacity',
            'bakufu-repo-immutability-summary',
        ],
        'focus': [
            'Repository strategy, capacity, and immutability posture',
            'Policy consistency, schedule quality, and operational guardrails',
            'Infrastructure health across proxies, managed servers, and mount paths',
        ],
        'workflows': [
            'capacityReport',
            'validateImmutability',
            'createWasabiRepo',
        ],
        'recipes': [
            'recipe-capacity-report',
            'recipe-validate-immutability',
            'recipe-repository-online-check',
            'recipe-proxy-health-review',
            'recipe-managed-server-health',
        ],
        'instructions': [
            'Start each operational review with capacity and immutability posture before approving policy changes.',
            'Use job and session views to verify policy outcomes, then drill into logs only for non-success states.',
            'Prefer workflow-level commands first; use `bakufu run` only for unsupported edge operations.',
            'Track infrastructure bottlenecks (proxy/repository/mount server) and report concrete remediation actions.',
        ],
        'tips': [
            'Keep repository growth and free-space checks in every weekly platform review.',
            'Treat immutability and encryption findings as blockers for compliance sign-off.',
            'Record session IDs in change notes so issues are reproducible and auditable.',
        ],
    },
    'persona-backup-operator': {
        'title': 'Backup Operator',
        'mission': 'Run day-to-day backup operations and recover quickly from failures.',
        'requires': [
            'bakufu-jobs',
            'bakufu-session-last-failed',
            'bakufu-session-follow',
            'bakufu-session-logs',
            'bakufu-jobs-last-result',
        ],
        'focus': [
            'Job success rates, warning triage, and rerun hygiene',
            'Session-level troubleshooting with task logs',
            'Daily and weekly job-health reporting',
        ],
        'workflows': [
            'investigateFailedJob',
            'capacityReport',
        ],
        'recipes': [
            'recipe-investigate-failed-job',
            'recipe-rerun-failed-job',
            'recipe-daily-job-health',
            'recipe-weekly-job-health',
            'recipe-job-session-export',
        ],
        'instructions': [
            'Start with `investigateFailedJob` when a job degrades, then pull logs for failed tasks only.',
            'Rerun failed jobs only after identifying likely root cause and confirming dependencies are online.',
            'Escalate recurring warnings into weekly reports with timestamps and affected objects.',
            'Maintain a clear handoff summary with job name, session id, result, and next action.',
        ],
        'tips': [
            'Use job-name based workflows for faster triage when IDs are not available.',
            'Focus first on latest failed session to reduce noise from old historical warnings.',
            'Prefer concise status updates: what failed, why, what changed, what is next.',
        ],
    },
    'persona-security-admin': {
        'title': 'Security Admin',
        'mission': 'Protect backup data and enforce security/compliance controls.',
        'requires': [
            'bakufu-security',
            'bakufu-malware-detection',
            'bakufu-security-analyzer-last-run',
            'bakufu-repo-immutability-summary',
            'bakufu-encryption',
        ],
        'focus': [
            'Security Analyzer runs and remediation visibility',
            'Malware event monitoring and scan execution',
            'Encryption/KMS and four-eyes audit evidence',
        ],
        'workflows': [
            'runSecurityAnalyzer',
            'validateImmutability',
        ],
        'recipes': [
            'recipe-security-analyzer-run',
            'recipe-best-practices-review',
            'recipe-malware-events-review',
            'recipe-encryption-posture',
            'recipe-audit-four-eyes-events',
        ],
        'instructions': [
            'Run Security Analyzer before control reviews and summarize critical findings first.',
            'Correlate malware events with backup sessions and affected repositories before remediation.',
            'Validate encryption and key management coverage for all protected storage tiers.',
            'Produce four-eyes event evidence for policy exceptions and sensitive changes.',
        ],
        'tips': [
            'Treat repeated best-practice failures as control design issues, not one-off incidents.',
            'Capture timestamps and object IDs in every security report for traceability.',
            'Keep analyzer and malware outcomes in the same evidence packet for audits.',
        ],
    },
    'persona-dr-operator': {
        'title': 'DR Operator',
        'mission': 'Validate recoverability and execute failover/failback runbooks safely.',
        'requires': [
            'bakufu-restore',
            'bakufu-replicas',
            'bakufu-failover',
            'bakufu-failback',
            'bakufu-restore-points',
        ],
        'focus': [
            'Restore readiness and restore-point coverage',
            'Replica failover preparedness and dependency checks',
            'Failback monitoring and unresolved-state closure',
        ],
        'workflows': [
            'investigateFailedJob',
        ],
        'recipes': [
            'recipe-restore-readiness-check',
            'recipe-restore-point-coverage',
            'recipe-dr-failover-readiness',
            'recipe-dr-failback-status',
            'recipe-session-sla-breach',
        ],
        'instructions': [
            'Validate restore readiness before failover execution windows begin.',
            'Use restore-point coverage checks to confirm SLA alignment for critical workloads.',
            'Monitor failover and failback sessions to closure; document unresolved dependencies.',
            'Escalate immediately when readiness checks show missing recovery paths.',
        ],
        'tips': [
            'Run readiness checks on a schedule, not only during incidents.',
            'Keep failover/failback evidence together for post-incident review.',
            'Prioritize workloads by business criticality when time is constrained.',
        ],
    },
    'persona-auditor': {
        'title': 'Auditor',
        'mission': 'Collect evidence and produce compliance-ready backup audit summaries.',
        'requires': [
            'bakufu-sessions',
            'bakufu-session-logs',
            'bakufu-security',
            'bakufu-license',
            'bakufu-repositories',
        ],
        'focus': [
            'Evidence collection for backup, security, and compliance controls',
            'Traceable session/activity history for control attestation',
            'Monthly and period-based reporting packs',
        ],
        'workflows': [
            'capacityReport',
            'validateImmutability',
        ],
        'recipes': [
            'recipe-audit-four-eyes-events',
            'recipe-auditor-monthly-pack',
            'recipe-job-session-export',
            'recipe-license-posture',
            'recipe-traffic-rules-review',
        ],
        'instructions': [
            'Gather evidence from operational, security, and capacity domains before finalizing reports.',
            'Validate that findings include timestamps, IDs, and source objects for audit traceability.',
            'Use recurring report structures so monthly packs are comparable across periods.',
            'Escalate missing or contradictory evidence before issuing attestation statements.',
        ],
        'tips': [
            'Keep raw JSON artifacts attached to summary reports for verification.',
            'Cross-check control evidence between sessions, logs, and security analyzer outputs.',
            'Separate observations from recommendations to keep reports objective.',
        ],
    },
}

# Clean and rebuild skills directory.
if skills_dir.exists():
    for child in skills_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
else:
    skills_dir.mkdir(parents=True)

(skills_dir / 'skills.json').write_text(json.dumps(catalog, indent=2))


def write_skill(name: str, description: str, category: str) -> None:
    target = skills_dir / name
    target.mkdir(parents=True, exist_ok=True)
    (target / 'agents').mkdir(parents=True, exist_ok=True)

    display_name = humanize(name)
    short_description = description if len(description) <= 140 else description[:137] + '...'
    default_prompt = default_prompt_for(category, name, description)
    agent_yaml = (
        f"display_name: {yaml_quote(display_name)}\n"
        f"short_description: {yaml_quote(short_description)}\n"
        f"default_prompt: {yaml_quote(default_prompt)}\n"
    )
    (target / 'agents' / 'openai.yaml').write_text(agent_yaml)

    profile = persona_profiles.get(name)
    if category == 'Persona' and profile:
        frontmatter = skill_frontmatter(name, description, category, profile['requires'])
        requires_line = ', '.join([f"`{item}`" for item in profile['requires']])
        focus_lines = '\n'.join([f"- {item}" for item in profile['focus']])
        workflow_lines = '\n'.join(
            [f"- `bakufu workflows {item}`" for item in profile['workflows']]
        )
        recipe_lines = '\n'.join([f"- `{item}`" for item in profile['recipes']])
        instruction_lines = '\n'.join([f"- {item}" for item in profile['instructions']])
        tips_lines = '\n'.join([f"- {item}" for item in profile['tips']])
        content = f"""{frontmatter}# {profile['title']}

PREREQUISITE: Load the following utility skills to operate as this persona: {requires_line}

{description}

## Relevant Workflows

{workflow_lines}

## Primary Focus Areas
{focus_lines}

## Instructions
{instruction_lines}

## Recommended Recipes
{recipe_lines}

## Tips
{tips_lines}

## Mission
- {profile['mission']}
"""
    else:
        if category == 'Service':
            service_requires = ['bakufu-shared']
            frontmatter = skill_frontmatter(name, description, category, service_requires)
            content = f"""{frontmatter}# {humanize(name)}

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

{description}

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "{humanize(name).replace('Bakufu ', '')}"`
- `bakufu run <Tag> <OperationId> --params '{{}}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
"""
        elif category == 'Helper':
            profile = helper_profiles.get(name, _default_helper_profile(name))
            frontmatter = skill_frontmatter(name, description, category, profile['requires'])
            requires_line = ', '.join([f"`{item}`" for item in profile['requires']])
            command_lines = '\n'.join([f"- `{item}`" for item in profile['commands']])
            instruction_lines = '\n'.join([f"- {item}" for item in profile['instructions']])
            tips_lines = '\n'.join([f"- {item}" for item in profile['tips']])
            content = f"""{frontmatter}# {humanize(name)}

PREREQUISITE: Load the following utility skills first: {requires_line}

{description}

## Relevant Commands

{command_lines}

## Instructions
{instruction_lines}

## Tips
{tips_lines}
"""
        elif category == 'Recipe':
            profile = _recipe_profile(name)
            frontmatter = skill_frontmatter(name, description, category, profile['requires'])
            requires_line = ', '.join([f"`{item}`" for item in profile['requires']])
            command_lines = '\n'.join([f"- `{item}`" for item in profile['commands']])
            instruction_lines = '\n'.join([f"- {item}" for item in profile['instructions']])
            tips_lines = '\n'.join([f"- {item}" for item in profile['tips']])
            content = f"""{frontmatter}# {humanize(name)}

PREREQUISITE: Load the following utility skills first: {requires_line}

{description}

## Relevant Commands

{command_lines}

## Instructions
{instruction_lines}

## Tips
{tips_lines}
"""
        else:
            frontmatter = skill_frontmatter(name, description, category)
            content = f"""{frontmatter}# {name}

Purpose: {description}

Category: {category}

## Inputs
- Veeam backup server target and account context
- Required identifiers for entities (job/session/repository/etc.)

## Output
- Structured JSON suitable for CLI and MCP consumers

## Execution Pattern
1. Resolve auth context with `bakufu auth token`.
2. Use dynamic operation (`bakufu run`) or helper/workflow command.
3. Return concise summary plus raw JSON when needed.
"""
    (target / 'SKILL.md').write_text(content)


for item in catalog['services']:
    write_skill(item['name'], item['description'], 'Service')
for item in catalog['helpers']:
    write_skill(item['name'], item['description'], 'Helper')
for item in catalog['personas']:
    write_skill(item['name'], item['description'], 'Persona')
for item in catalog['recipes']:
    write_skill(item['name'], item['description'], 'Recipe')

def add_table(lines_ref: list[str], title: str, summary: str, section_name: str):
    def entry_meta(entry_name: str, entry_desc: str) -> tuple[str, str]:
        if section_name == 'services':
            return ('service', 'bakufu-shared')
        if section_name == 'helpers':
            profile = helper_profiles.get(entry_name, _default_helper_profile(entry_name))
            return ('helper', ', '.join(profile['requires']))
        if section_name == 'recipes':
            profile = _recipe_profile(entry_name)
            return ('recipe', ', '.join(profile['requires']))
        if section_name == 'personas':
            profile = persona_profiles.get(entry_name, {})
            requires = profile.get('requires', ['bakufu-shared'])
            return ('persona', ', '.join(requires))
        return ('skill', 'bakufu-shared')

    lines_ref.append(f'## {title}')
    lines_ref.append('')
    lines_ref.append(summary)
    lines_ref.append('')
    lines_ref.append('| Skill | Version | Category | Requires | Description |')
    lines_ref.append('|-------|---------|----------|----------|-------------|')
    for entry in catalog[section_name]:
        category, requires = entry_meta(entry['name'], entry['description'])
        lines_ref.append(
            f"| [{entry['name']}](../skills/{entry['name']}/SKILL.md) | 1.0.0 | {category} | `{requires}` | {entry['description']} |"
        )
    lines_ref.append('')


lines = [
    '# Skills Index',
    '',
    '> Auto-generated by `python scripts/sync_skills_from_swagger.py`. Do not edit manually.',
    '',
    f'Total skills: **{len(catalog["services"]) + len(catalog["helpers"]) + len(catalog["personas"]) + len(catalog["recipes"])}**',
    '',
]

add_table(lines, 'Services', 'Core Veeam Backup & Replication API skills.', 'services')
add_table(lines, 'Helpers', 'Shortcut commands for common operations.', 'helpers')
add_table(lines, 'Personas', 'Role-based skill bundles.', 'personas')
add_table(lines, 'Recipes', 'Multi-step task sequences with real commands.', 'recipes')

docs_path.write_text('\n'.join(lines))
print('skills regenerated')
