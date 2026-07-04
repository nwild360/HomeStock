# HomeStock MCP Server — Configuration Guide

HomeStock exposes its inventory operations to AI agents via the [Model Context Protocol](https://modelcontextprotocol.io). This document covers everything needed to configure the feature: the in-app settings, authentication options, and a full walkthrough for setting up a Keycloak client that can talk to the MCP server.

## Overview

| | |
|---|---|
| Endpoint | `https://<your-homestock>/mcp` (also served on the backend port directly, e.g. `:8000/mcp`) |
| Transport | Streamable HTTP (stateless, JSON responses) |
| Tools | 14 — items list/get/create/update/adjust-stock/delete, categories CRUD, units CRUD |
| Default state | Disabled |
| Toggle | Settings → Integrations → MCP Server |
| Auth | OAuth 2.1 (Keycloak, recommended) and/or per-user API keys (fallback) |
| Discovery | RFC 9728 metadata at `/.well-known/oauth-protected-resource` |

Every MCP request must be authenticated. Actions are attributed to a HomeStock user: OAuth tokens are mapped through the same JIT-provisioning path as SSO logins (`oidc_sub`), and API keys belong to the user who created them.

## In-app settings

Settings → Integrations → MCP Server → Configure:

| Setting | Meaning |
|---|---|
| **Enable MCP Server** | Master toggle. When off, `/mcp` returns 404 for everyone. Applies immediately, no restart. |
| **Server URL (OAuth audience)** | The canonical public URL of the MCP endpoint as agents reach it (e.g. `https://homestock.example.com/mcp`). When set, every OAuth token **must** carry this value in its `aud` claim (RFC 8707 resource check — blocks tokens minted for other services from being replayed here). Leave blank only if you cannot add audience mappers; that weakens validation to issuer + introspection only. |
| **Required scope** | OAuth scope that must be present in the token (default `mcp:tools`). Blank = no scope check. Blank this if your realm models MCP access with client **roles** instead of scopes. |
| **Allow API Key Auth** | Accept `hs_live_` personal API keys (Settings → API Keys) as `Authorization: Bearer` or `X-API-Key`. Off by default. Useful for headless agents or instances without Keycloak. |

Enabling requires at least one viable auth method: SSO/OIDC configured, or API keys allowed.

## How token validation works

For each request with a non-`hs_live_` bearer token, the backend:

1. **Introspects** the token at Keycloak (RFC 7662), using the same confidential client configured in Settings → SSO / OIDC. This delegates signature, issuer, expiry, and revocation checking to Keycloak.
2. **Checks the audience**: the token's `aud` must contain the configured Server URL (skipped if Server URL is blank).
3. **Checks the scope**: the token's `scope` must include the Required scope (skipped if blank).
4. **Maps the identity**: the token's `sub` is resolved to a HomeStock user (JIT-provisioned on first use, same as SSO login).

Verified tokens are cached in-memory for up to 60 seconds (bounded by token expiry) to avoid one Keycloak round trip per tool call.

## Keycloak setup

Prerequisite: HomeStock SSO/OIDC is configured and enabled (Settings → SSO / OIDC) with a **confidential** client — call it `<homestock-client>` below. The MCP server reuses that client's credentials for token introspection.

### Step 1 — Audience mappers (required)

Tokens presented to the MCP server need **two** audience values:

| Audience value | Why |
|---|---|
| `<homestock-client>` (the OIDC client id) | Keycloak ≥ 26.6.2 refuses to introspect a token for a client that is not in the token's `aud` — introspection returns `{"active": false}` even for perfectly valid tokens. |
| Your Server URL, e.g. `https://homestock.example.com/mcp` | HomeStock's own resource/audience check (must match the Server URL setting exactly). |

> ⚠️ **One mapper = one audience.** Keycloak's Audience mapper has both an "Included Client Audience" dropdown and an "Included Custom Audience" text field, but if both are filled **only the client audience is emitted** — the custom value is silently ignored. You must create **two separate mappers**:
>
> 1. *Audience* mapper — Included Client Audience: `<homestock-client>`, custom field empty, "Add to access token" ON.
> 2. *Audience* mapper — Included Client Audience: empty, Included Custom Audience: `https://homestock.example.com/mcp`, "Add to access token" ON.

Where to put the mappers:

- **Shared across many agent clients**: create a client scope (e.g. `mcp:tools`, see Step 2) and add both mappers under that scope's **Mappers** tab, then attach the scope to each agent client.
- **Single client**: add both mappers under the client's own *dedicated* scope (Clients → your client → Client scopes → `<client>-dedicated` → Mappers).

If you run separate dev/prod HomeStock instances, add one custom-audience mapper per instance URL — `aud` is an array and all values coexist.

### Step 2 — Scope or roles (authorization granularity)

Pick one model:

**Scope-based (default):** create a client scope named `mcp:tools` (Client scopes → Create; Protocol: OpenID Connect; **"Include in token scope" ON**), attach it to each agent client as **Default** (Default matters: client-credentials mints don't request optional scopes), and keep the Required scope setting at `mcp:tools`. Putting the Step 1 mappers inside this scope makes it a one-stop "MCP access" grant.

**Role-based:** if your realm uses client roles (e.g. `mcp.homestock.write`) for authorization conventions instead, blank the Required scope setting. Audience enforcement remains the access control: only clients you've given the audience mappers can reach the server. (HomeStock does not currently evaluate `resource_access.*.roles` server-side.)

### Step 3 — The agent client itself

**Interactive agents (Claude Code, Claude Desktop, VS Code — browser login):**

- Pre-register a **public** client: Client authentication OFF, Standard flow ON, Valid redirect URIs covering the client's loopback callback (e.g. `http://localhost:*/callback` in dev), PKCE enforced by the client.
- Or enable **Dynamic Client Registration**: Clients → Client registration → Trusted Hosts policy — add the connecting hosts and review "Client URIs Must Match". Anonymous DCR is rejected with `Policy 'Trusted Hosts' rejected request` until the host is trusted.
- Attach the `mcp:tools` scope (or the two mappers) per Steps 1–2.
- Connect with: `claude mcp add --transport http homestock https://<your-homestock>/mcp` — the client discovers Keycloak via the 401 challenge + `/.well-known/oauth-protected-resource` and opens a browser for login.

**Machine-to-machine agents (headless, client-credentials):**

- Confidential client: Client authentication ON, Service accounts roles ON, Standard flow OFF.
- Attach the `mcp:tools` scope (or the two mappers) per Steps 1–2.
- Mint tokens from the token endpoint with `grant_type=client_credentials` and send as `Authorization: Bearer <token>`. Tokens are short-lived — re-mint per run rather than caching.
- On first use, HomeStock JIT-provisions a user named after the service account (e.g. `service-account-<client-id>`) so actions stay attributable.

### Troubleshooting

Backend log lines (`docker-compose logs -f backend`) map directly to causes:

| Log message | Cause / fix |
|---|---|
| `MCP OAuth rejected: inactive token` | Token expired **or** Keycloak's introspection audience rule — ensure the `<homestock-client>` client-audience mapper from Step 1 exists. |
| `MCP OAuth rejected: audience [...] does not cover <url>` | The custom-audience mapper is missing/wrong, or the Server URL setting doesn't exactly match the mapped value. Remember: one audience per mapper. |
| `MCP OAuth rejected: missing required scope` | Scope not attached as Default to the client, "Include in token scope" off, or you're using role-based access — blank the Required scope setting. |
| `MCP OAuth rejected: OIDC is not configured` | Settings → SSO / OIDC is disabled or incomplete. |
| HTTP 404 from `/mcp` | Feature toggle is off. |
| HTTP 401 `API key auth is disabled` | Key presented while Allow API Key Auth is off. |

Decode a minted token (e.g. at jwt.io or `base64 -d` on the middle segment) and confirm `aud` contains **both** values and `scope` contains the required scope before suspecting the server.

## API key fallback

With **Allow API Key Auth** on, agents may authenticate with a personal key from Settings → API Keys instead of OAuth:

```bash
claude mcp add --transport http homestock https://<your-homestock>/mcp \
  --header "Authorization: Bearer hs_live_..."
```

Keys are long-lived bearer credentials — prefer OAuth where possible, keep keys scoped to one agent each, and revoke them in the UI when retired.

## Quick smoke test

```bash
TOKEN=...   # OAuth access token or hs_live_ API key

curl -s https://<your-homestock>/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

A healthy, enabled server returns the 14-tool list. (The server is stateless — no `initialize` handshake or session id is required for testing.)
