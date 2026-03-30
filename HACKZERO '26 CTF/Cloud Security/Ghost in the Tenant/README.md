# Ghost in the Tenant

| Field    | Value          |
| -------- | -------------- |
| Category | Cloud Security |
| Points   | 500            |
| Solves   | 39             |

## Description

The vault stands in plain sight, yet remains silent.
An instance exists within the same boundary, but not all identities are equal.
Access is not denied, it is simply misplaced.
Become what the vault expects, and it may answer.

Challenge credentials:

```
Client Id: 3874eff6-1931-4b95-8ff0-a697a8fd47b1
Tenant Id: 07cb5c87-9226-4baf-9293-15e53e7f634f
Client Secret: REDACTED_AZURE_CLIENT_SECRET
```

Flag Format:
`hackzero{}`

## Writeup

The hint said:

- the vault is visible
- access is "misplaced"
- an instance in the same boundary has the right identity

That sounded like: my provided app identity can see infrastructure, but the Key Vault access policy is tied to a different principal (likely a VM managed identity).

I authenticated as the service principal using OAuth client credentials (I didn’t have Azure CLI locally, so I used direct REST calls).

I confirmed I had access to one subscription:

- `d7f5ab5f-aa83-4abb-9f23-09051c0f24a1`

I listed Key Vaults in the subscription and found:

- Vault: `HackZero`
- URI: `https://hackzero.vault.azure.net/`

Its access policies contained two object IDs:

- `3e0baaff-f74e-4fdf-8b4d-af7852affd83` (broad permissions)
- `21b81251-3f4c-4f06-ad62-6e678fe0878b` (secret `get`/`list`)

My logged-in app’s object ID was different:

- `73dd20a7-60c6-4046-ade4-9fbd1151c6fc`

So the vault permissions were not for my app directly.

Using ARM I enumerated RBAC and found my principal had `Virtual Machine Contributor` on VM `ctf`. Inspecting that VM revealed a system-assigned managed identity with principalId `21b81251-3f4c-4f06-ad62-6e678fe0878b` — an exact match to the vault access policy.

Because of the VM role, I used the ARM `runCommand` API to execute a small script on `ctf` that called the IMDS endpoint:

```
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
```

The returned access token (for the VM's managed identity) was used to call the Key Vault Secrets API. I listed secrets and examined versions of `flag` (several versions contained decoys such as `THIS_IS_FAKE_FLAG`); one older version matched the CTF format and contained the real flag.

Summary: the provided service principal could manage the VM but not read secrets; the VM's managed identity held Key Vault permissions. Pivoting via `runCommand` -> IMDS -> Key Vault allowed retrieval of the `flag`.

### Flag

```
hackzero{8bc7ff831fdb83fdd07432cf89b6c059}
```
