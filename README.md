# AI Service Indicators

A community-maintained list of DNS hostnames for generative-AI applications and APIs, for measuring **observed AI-service access** from DNS, proxy or firewall logs.

Each row maps a hostname pattern to a service, vendor, category and role, so you can tell chat use from API calls, agents, sign-in, CDN, telemetry and plain website visits. Where a vendor publishes the hostname, the row links to that page.

> **A DNS lookup shows a device contacted a service, not that anyone submitted a prompt.** Report results as observed access, count distinct devices rather than queries, and remember that devices are not people.

## The data

[`data/ai_services.csv`](data/ai_services.csv)

| Column | Meaning |
|---|---|
| `host_pattern` | Lowercase hostname; `*` matches any run of characters, including dots |
| `service` | Product, e.g. `ChatGPT`, `Codex`, `OpenAI API`, `GitHub Copilot`; a vendor name (`OpenAI`) for names shared across its products |
| `vendor` | Company operating the service |
| `category` | `Chat assistant`, `Coding assistant`, `AI platform` (APIs and cloud model hosting), `AI browser`, `Research`, `Creative` |
| `role` | What the hostname does; see below |
| `counts_as_usage` | `1` for `app`, `api` and `agent` roles; `0` otherwise |
| `source` | Vendor documentation or application URL; blank where the vendor publishes none |
| `confidence` | How the role was established; see below |
| `notes` | Interpretation caveats |

### Roles

| `role` | Meaning | Usage? |
|---|---|---|
| `app` | The interactive product: web app, its live-response and voice endpoints, mobile and desktop app backends, coding-assistant service endpoints | yes |
| `api` | Public programmatic inference endpoint | yes |
| `agent` | Coding-agent, connector and MCP endpoints | yes |
| `portal` | Developer console (keys, billing) | no |
| `web` | Marketing site, docs, help, status, community, email links | no |
| `auth` | Sign-in, SSO, bot checks | no |
| `cdn` | Static assets, user content, CDN alias (CNAME) targets | no |
| `telemetry` | Analytics, metrics, experiments and feature flags | no |
| `download` | Installers and updates | no |
| `other` | A vendor's catch-all for subdomains not yet classified; review these rather than count them | no |

### Confidence

| `confidence` | The role comes from |
|---|---|
| `documented` | The vendor's documentation, linked in `source` |
| `evidence` | DNS answers or the server's own responses, described in `notes` (for example a CNAME to a billing or help-desk provider, or a redirect) |
| `hostname` | The hostname alone |
| `low` | The hostname or weak evidence; treat as a hypothesis |

`confidence` describes the role. A `source` on a catch-all or `hostname` row shows that the domain belongs to the vendor, not what each subdomain does. Corrections backed by vendor documentation are especially welcome.

Using `role`, you can tell, for example, ChatGPT chat (`chatgpt.com`, `ws.chatgpt.com`) apart from OpenAI API calls (`api.openai.com`), Codex agents (`codex-cloud-backend.chatgpt.com`), and someone reading `openai.com` or `help.openai.com`.

No field contains a comma or quote, so any CSV reader, `awk -F,`, or a SIEM lookup can load the file as-is.

### Matching rules

1. Lowercase the queried hostname and strip any trailing dot.
2. Try rows **in file order**; the **first** matching row wins. Specific names come before their wildcard catch-alls (`api.openai.com` before `*.openai.com`).
3. A pattern matches the **whole** hostname: `*.chatgpt.com` matches `ab.chatgpt.com` but not `fakechatgpt.com` or `chatgpt.com.example.net`. Apex domains are listed separately.
4. A hostname matching no row is not in scope.

These are the semantics of a Splunk `WILDCARD` lookup with `max_matches=1`.

## How to interpret results

- **Report by `role`, not by domain.** Telemetry and experiment names (for example `ab.chatgpt.com`) fire on page load and are often queried by more devices than the app itself. There is no blanket "all `openai.com` = ChatGPT" rule.
- **An API hostname identifies the service contacted, not the application, person, model or billing account behind it.** `api.anthropic.com`, for example, is used by Claude Code as well as by custom applications.
- **A usage role shows that a service was in use on a device, not what the person did with it.** DNS cannot show whether someone generated an image, ran an agent or only opened the app.
- **Some vendor names are reached from other companies' websites.** `bzr.openai.com`, for example, is OpenAI's ad-measurement pixel, embedded in advertisers' sites, and is queried by devices that never use ChatGPT.
- **Keep non-usage roles out of usage counts.** `auth`, `cdn`, `telemetry` and `web` names can corroborate activity, but browsers prefetch them, and they are reached by people who never use the product.
- **Count distinct devices per service per day or week, not queries.** Caching, retries, background refresh and prefetching distort query counts.
- **Classify the name the client asked for**, not CDN alias (CNAME) targets in the response.

### Coverage gaps

DNS-based measurement misses:

- off-network devices;
- clients using encrypted DNS (DoH/DoT) to outside resolvers;
- locally run models;
- AI features embedded in other SaaS products, which share the host application's hostnames;
- calls made from a vendor's backend.

Some services (OpenRouter, Azure AI Foundry, Bedrock, Vertex AI) front many models, and DNS cannot tell which model was used.

## Using it

Implement the matching rules above. For each pattern, a regex of `^` + the pattern with `*` replaced by `.*` (everything else escaped) + `$` is enough. In Splunk, load the CSV as a lookup with `match_type = WILDCARD(host_pattern)` and `max_matches = 1`.

On high-volume DNS indexes, filter on indexed terms before classifying: `python3 scripts/splunk_terms.py` prints a keyword filter that covers every pattern.

## Contributing

New services, endpoints and corrections are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Every change must pass `python3 scripts/validate.py`, which also runs automatically on pull requests.

## License

[CC BY 4.0](LICENSE)
