List only SEVERE violations. For each include:
- principle: the rule name (e.g. SRP, OCP, DRY)
- metric_id: the metric identifier (e.g. OCP-1, SRP-2)
- issue: what is wrong
- fix: the specific change needed

Your entire response MUST be a single raw JSON object and nothing else.
No markdown fences. No explanation. No commentary.

{"violations": [{"principle": "string", "metric_id": "string", "issue": "string", "fix": "string"}]}

Empty if clean: {"violations": []}
