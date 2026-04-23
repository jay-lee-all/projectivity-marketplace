---
project: {{slug}}
customer_org: {{customer_org_english}}
customer_org_ko: {{customer_org_korean}}
lead_pm: {{lead_pm}}
linear_project: {{linear_project_name}}
linear_ticket_prefix: {{linear_ticket_prefix}}
when_created: {{now_kst_date}}
---

# {{linear_project_name}}

{{description}}

## Channels

- Slack (internal): {{internal_slack_name}} ({{internal_slack_id}})
- Slack (external customer): {{external_slack_name}} ({{external_slack_id}})

## Team

- Lead PM: {{lead_pm}}
- Engineering: TBD
- Customer-side: see `core/contacts.yaml`

## Scope

TBD — curation will fill this as decisions land.

## Links

- Linear: {{linear_project_name}}

---

Scaffold substitutes `{{placeholders}}` from the elicitation answers. Rules:

- If a field is blank, drop the line entirely (not the section header).
- For fields that are expected-but-unknown (Engineering roster, Scope), leave the literal `TBD` so the PM sees the gap at a glance.
- Frontmatter fields with no value should be omitted (not left as `null` or empty string).
