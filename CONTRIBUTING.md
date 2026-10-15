# Contributing

Thanks for helping keep the list accurate. Hostnames and service routing change often, so both new entries and corrections are valuable.

## Adding or changing a row

1. Edit [`data/ai_services.csv`](data/ai_services.csv).
   - **Order matters: the first matching row wins.** Put a specific name above any wildcard that would also match it (`api.x.ai` above `*.x.ai`). Keep a vendor's rows together.
   - Use a wildcard only where the vendor documents a family of names, or where you have seen several. Prefer exact names.
   - Set `role` (see the README) and `counts_as_usage` to match: `1` only for `app`, `api` and `agent`. Prefer exact names; keep each vendor's `*.` catch-all last with role `other`.
   - `source` is the vendor's documentation URL. If the vendor publishes none (for example, a name seen in your own DNS logs), leave it blank and describe the evidence in the pull request: what the client was doing, such as "desktop app sign-in".
   - Set `confidence` (see the README): `documented` when the vendor states the role (needs `source`), `evidence` when DNS answers or the server's responses show it (say what in `notes`), `hostname` when only the name suggests it, `low` when even that is a weak guide.
   - No commas or double quotes in any field. Use `;` in notes.
2. Add at least one line to [`tests/match_cases.csv`](tests/match_cases.csv) per new pattern (hostname, expected service and role). Add a negative case (empty service and role) when a wildcard could catch unrelated names.
3. Run `python3 scripts/validate.py` (Python 3.9+, no dependencies). It checks:
   - the schema, including that `counts_as_usage` matches `role`;
   - duplicates;
   - rows that can never match because an earlier row catches them first;
   - every test case.

## What belongs here

- Generative-AI applications, APIs, coding assistants, AI browsers and cloud AI platforms that people reach directly.
- Not general cloud or CDN endpoints, unless they are specific to an AI service.
- Not organisation-specific policy, such as allow/deny or watch-list flags. Keep that in your own copy, in an extra column joined on `host_pattern`.

## Privacy

Never include internal hostnames, IP addresses, usernames or log excerpts in issues or pull requests. "Seen from a macOS desktop client on 2026-10-14" is enough context.

## License of contributions

By submitting a contribution you agree that it is licensed under [CC BY 4.0](LICENSE), the same license as the rest of the repository.
