# 17. Authentication

[← Validation history](16-validation-history.md) · [Manual index](README.md) · [Next: Privacy and retention →](18-privacy-and-retention.md)

The software runs in one of two modes, chosen by whoever deployed it. You cannot
switch between them, and you can tell which one you are in at a glance.

| | Open mode | Token mode |
|---|-----------|-----------|
| How you can tell | You can upload straight away | An **API token required** panel sits above the workspace |
| What identifies you | A cookie the server sets on first use | A token you paste in |
| Who shares your runs | Nobody | Everybody holding the same token |
| Across browsers | Each browser is separate | Same token, same runs, any browser |
| Is it authentication? | **No** | Yes, of a sort — see below |

## Open mode

The default, and what a local installation and the public demo both run. There
is no login. On your first request the server sets an `eav_session` cookie in
your browser, and every validation and comparison you create is filed under it.

That cookie is **scoping, not authentication**. It stops one browser session
seeing another's runs, and that is all it claims to do. It does not identify you,
it is not a password, and anyone who obtains its value has your runs.

Practical consequences:

- Clearing cookies, using private browsing, or switching browsers loses access
  to everything you created before. The runs are still on the server; you can no
  longer reach them.
- There is no way to hand a run to a colleague. Send them the exported report
  (chapters [14](14-pdf-report.md) and [15](15-xlsx-report.md)).
- From the command line you must keep the cookie yourself, or every request
  arrives as a new session:

  ```bash
  curl --cookie-jar jar.txt --cookie jar.txt ...
  ```

## Token mode

When the deployment sets one or more shared tokens, every data route requires
one. The page asks for it before anything else:

> **API token required**
> This deployment only answers requests that carry an access token. The token
> stays in this browser.

**Steps:**

1. Paste the token your operator gave you into the field. It is masked as you
   type.
2. Click **Use token**. The button then reads **Update token**, and you can
   replace it at any time.
3. Upload as normal.

Until a valid token is entered, nothing works and the messages are consistent:

| What you do | What you get |
|-------------|--------------|
| Run a validation with no token | **Analysis could not be completed** — A valid bearer token is required. |
| Run a validation with a wrong token | The same message |
| Look at history with a wrong token | **History is unavailable** — A valid bearer token is required. |
| Enter the right token | Everything works, and your token's history appears |

The message is identical for "no token" and "wrong token", which is deliberate:
nothing about the response tells an attacker whether they guessed part of it.

### What a token is and is not

Be clear about this before you rely on it.

- **A token is a shared secret, not a user account.** There are no names, no
  roles, and no record of who did what. Two engineers holding the same token are
  indistinguishable to the software and share one pool of runs.
- **Everyone with the token sees everything created with it.** A run created
  from the command line appeared in a colleague's browser history the moment the
  same token was entered there.
- **Different tokens are completely isolated.** A run created with one token
  answers `Validation not found.` to every other token — the same response as a
  run that does not exist. There is no way to share a single run across tokens.
- **Rotating a token orphans its runs.** They stay in the database and become
  unreachable. Export anything you need before a rotation.
- **The token is stored in your browser** so it survives a reload, in ordinary
  browser storage, unencrypted. On a shared machine, clear it when you finish by
  emptying the field and clicking **Update token**.
- **On plain HTTP a token is readable in transit.** Only use one over HTTPS.

### From the command line

Send it as a bearer token, and no cookie jar is needed — the token is the scope:

```bash
curl --fail-with-body \
  -H "Authorization: Bearer alpha-team-token" \
  -F "file=@sample-data/invalid-register.csv;type=text/csv" \
  http://localhost:8000/api/v1/validations
```

Without it, or with the wrong scheme — `Authorization: Basic ...` — you get HTTP
401 with a `WWW-Authenticate: Bearer` header and:

```json
{"detail": "A valid bearer token is required."}
```

Every data route needs it, including the header inspection that the page runs
when you choose a file, and including report downloads.

## Which mode am I in?

The page tells you: if the token panel is absent, the deployment is open. You can
also ask the server directly, and this one question needs no credentials in
either mode:

```bash
curl http://localhost:8000/api/v1/config
```

```json
{"auth_required": true}
```

`/api/v1/health` is likewise always open, so a monitoring system can check the
service without holding a token. Neither route exposes any stored data.

## What neither mode gives you

There are no user accounts, no roles, no permissions, no audit trail of who
validated what, and no approval workflow. Nothing in the software records a
person. If your process needs "the incoming register was validated by X and
accepted by Y", that record lives in your handover paperwork, with the exported
report attached as the evidence.

---

[← Validation history](16-validation-history.md) · [Manual index](README.md) · [Next: Privacy and retention →](18-privacy-and-retention.md)
