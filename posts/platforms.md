# The box an agent runs in 

One awesome product evolution is that agents (Claude Code, Instinct, Poke, etc) are moving off our local computers so that we can use them on our phones.
Ultimately this is great for the customer because that means the agent companies provide us with VMs for them to run on! Here's some notes on how the major platforms work based on looking around on [ws-term](https://github.com/RohanAdwankar/ws-term).

## Claude Code on Your Phone

Claude Code's box is its own **Firecracker microVM** a KVM guest with its
own kernel, booted straight into an init written in Rust:

```
$ cat /proc/cmdline
... rdinit=/process_api ... --listen-vsock-port 2024
$ uname -r
6.18.5-fc-v20                 # -fc- = Firecracker; a custom-built guest kernel
$ ps -o comm -p 1
process_api                   # PID 1 is not systemd — it's a Rust/Tokio binary
```

`process_api` is PID 1 and the host's control agent living
inside your VM: it mounts the disks, then listens on **vsock port 2024** so the
host can drive the session from outside. That's the platform's defining trait —
**the operator lives inside your tenant space**, and a lot of engineering goes into
sealing it off (PID 1 is non-dumpable, `/proc/1/mem` is denied even with
`CAP_SYS_PTRACE`, your shell is missing `CAP_SYS_RESOURCE`).

The disks split cleanly into *yours* (writable, persistent) and *theirs*
(read-only, shared):

```
$ lsblk -o NAME,SIZE,RO,MOUNTPOINT
vda   256G  0  /                    # yours: writable, survives reclaim
vdc   341M  1  /opt/claude-code     # theirs: the 324 MB `claude` harness (Bun)
vdd  45.6M  1  /opt/env-runner      # theirs: the task launcher
vde/vdf ... 1  /mnt/skills/...      # theirs: skills
```

The **harness** is the thing running your tool calls and is a 324 MB compiled Bun
binary on a read-only disk. The model runs elsewhere, inference goes out as **Server-Sent Events over HTTPS/2** (not a WebSocket) to `/v1/messages`, through an egress gateway that is 443-only and
MITM'd (`CN = Egress Gateway ... (production)`), with `api.anthropic.com` pinned
in `/etc/hosts`. There is no inbound at all (`192.0.2.2`, an RFC-5737 test
address). Auth is a **host-minted OAuth token**, cached root-only on disk and
rotated per boot.

Lifecycle is host-driven and measured from the inside: **~430 ms** to init,
**~6.4 s** to the harness process. Spin-up is triggered by an inbound message
(the host wakes the VM over vsock and runs `--session-mode resume`); spin-down is
idle reclaim decided by the host. When it's reclaimed, the *processes* die but
`vda` detaches intact and reattaches on the next cold boot — which is why the
conversation feels continuous even though the compute was destroyed.

```mermaid
flowchart TB
  user(["your keystrokes"]) -->|http post| ingress["session-ingress"]
  ingress --> pa
  hostctl(["host control plane"]) -->|vsock port 2024| pa
  subgraph vm["Firecracker microVM"]
    pa["process_api, pid 1, Rust"] --> harness["claude, 324 MB Bun harness"]
    vda[("vda (rw), yours, persists")] --- harness
    ro[("vdc/vdd/vde/vdf (ro), theirs")] --- harness
  end
  harness -->|inference over SSE| gw["egress gateway, 443, mitm, api.anthropic.com"]
```

---

## Instinct

Instinct is a new startup which launched recently and it does some very nice things on the memory side which gives that feel of it being a real assistant rather than a chatbot.

```
$ hostname
e2b.local
$ cat /.e2b
n038afjvewg7jnc9pwdz
```

Instinct doesn't run its own hypervisor. `e2b.local` means this is a rented
[E2B](https://e2b.dev) sandbox — "sandbox-as-a-service," a throwaway Ubuntu box
you hand an agent so it has a computer:

```
Ubuntu 22.04.5, 2 vCPU, 1.9 GB RAM, 29 GB disk, up ~30 min, user sandbox (uid 1001)
```

So if the box is disposable, where does the agent's memory live? In a directory
called `/memory` — and this is the platform's defining idea:

```
$ cat /memory/README.md
Persistent memory for [[rohan-adwankar]]
$ ls /memory
entities/  comms/  timeline/  workstreams/  knowledge/
$ git -C /memory log --format='%an <%ae>' -1
Instinct Agent <agent@instinct.com>
```

The agent's memory is a **git repo of Markdown files** with `[[wiki-links]]`,
navigated by `grep`. The `timeline/` *coarsens* over time (raw → hourly → daily →
weekly, like human memory), and the agent is literally the **git author** — it
doesn't call a memory API, it writes Markdown and commits it as itself.

The durable layer is that repo, pushed to **S3**, keyed by a per-user id — and
stored not as files but as a single **git bundle**, which is a great little gotcha:

```
$ git -C /memory remote -v
origin  s3://instinct-prod-agent-memory/filesystem-memory/user-01M1VW7...
$ aws s3 ls s3://.../user-01M1VW7.../ --recursive
  HEAD
  refs/heads/main/<sha>.bundle     # the ENTIRE vault, packed — `ls` after sync looks empty
```

Auth is **short-lived STS credentials**, not long-lived keys — so a leaked
sandbox self-heals when the token lapses:

```
$ cat /etc/instinct-aws-creds
export AWS_ACCESS_KEY_ID='ASIA…'     # ASIA prefix + session token = temporary STS
...                                   # (values redacted — live secrets)
# role: instinct-sandbox-observations-role
```

```mermaid
flowchart TB
  subgraph box["E2B sandbox (rented, disposable)"]
    agent["Instinct Agent (agent@instinct.com)"] -->|writes and commits| mem["/memory, a Markdown vault git repo"]
    creds["/etc/instinct-aws-creds, short-lived STS"]
  end
  mem -->|git push| store
  creds -->|authorizes git push| store
  subgraph store["S3 (durable, per-user)"]
    vault[("instinct-prod-agent-memory, the vault")]
    obs[("instinct-prod-observations, raw firehose")]
  end
```

*Durable thing = a git repo in S3. The machine is throwaway.*

Using a git repo for this is quite nice the default structure seems to be like this:
```
  ~/instinct-vault/..         │󰫎  24 󰲡 Vault
    .git                    │   23
    comms                   │   22 Persistent memory for 󱗖 rohan-adwankar. Markdown + wiki-links, navigated by grep. Start here, then jump
      chat                  │   21
         rohan-adwankar--inst│   20 Who Rohan is, what he is working on, and what is connected live in entities/, workstreams/, and knowled
    entities                │   19
      people                │󰫎  18  󰲣 Layout
         rohan-adwankar.md   │   17
      projects              │   15 README.md
         ws-term.md          │   14 timeline/     chronological record, coarsening upward: raw/ → hourly/ → daily/ → weekly/ → monthly/
    knowledge               │   13 entities/     people/ projects/ — the nouns of Rohan's world, one file each
      decisions             │   12 comms/        chat/ email/ meetings/ — one file per thread, named <who>--<topic>--<date>.md
         x-account-signup-dec│   11 workstreams/  active/ completed/ someday/ — units of work; status: frontmatter matches the subdirectory
      preferences           │   10 knowledge/    facts/ procedures/ preferences/ decisions/
        instinct            │    8
           autonomy.md       │    7 knowledge/preferences/instinct/ holds how Rohan wants the assistant itself to behave — autonomy, drafti
           iteration-style.md│    6
    timeline                │󰫎   5  󰲣 Conventions
      daily                 │    4
         2026-09-06.md       │    3 ● Every file has frontmatter with id, type, and aliases. [[id]] resolves to id.md or id/_index.md.
    workstreams             │    2 ● Entity and knowledge files are updated in place and read as current state, never as a log. History li
      active                │    1 ● Files that outgrow one page are promoted to a directory with an _index.md carrying the original id.
         dragon-game-asset.md│  25  - Timeline and comms hold events and conversations; entities hold durable properties only.
         startup-idea-search.│~
    󰂺 README.md               │~
~                             │~
~                             │~

:!tmux capture-pane -pS - | pbcopy
```

Now Claude Code's harness in the VM is open source and the same as normal but how about Instinct?

```
$ ps -eo args | grep -E 'agent-exec|tools'
agent-exec-server --port 8080                    # Go — runs the bash/code it's sent
tools __internal_daemon --socket /tmp/.tools/bridge.sock \
      --base-url https://api.instinct.com/-/api/graphql/tool-execute   # Rust
$ strings /usr/local/bin/tools /usr/local/bin/agent-exec-server \
    | grep -iE 'anthropic|openai|/v1/messages|x-api-key|claude|gpt|model'
                                                 # → nothing. no model listed
```

So seems like no inference calls anywhere on the box. Claude Code seals the *operator*
inside the guest; Instinct doesn't put the brain in the guest at all. The sandbox
is a pure **execution surface**: `agent-exec-server` runs whatever bash the backend
hands it, and every tool call — Gmail, the cloud browser, a payment — leaves as a
**GraphQL request to `api.instinct.com`**, executed server-side. The `--base-url`
is a runtime argument, not compiled in.

For the actual tool surface rather than MCPs seems like Instinct uses a CLI for all tools:

```
sandbox@e2b:~/ws-term-v1$ tools --help | wc
     90    1466   10891
sandbox@e2b:~/ws-term-v1$ tools --help
Tools CLI

You are a task agent. Your parent (the main agent) spawned you for a focused job. When the job is done, report back to your parent and hold. Your parent owns task-agent cleanup.

Your direct-execute traits:
  - work - integrations, files, web page fetching
....

Run `tools --help` for the current surface.

USAGE
  tools <command-path> [options]
  tools help [<path>...]

....

Built-ins (no help read needed): help, async wait, async list.

EXECUTABLE (you can call these directly)
  agent_message        namespace (1 action)   Send messages to other agents.
  browser_guidance     namespace (3 actions)  Search per-config website guidance and this user's past outcomes before browser navigation, and record how a config performed after an attempt. Missing guidance is normal and means unknown, not supported or blocked.
  cloud_browser        namespace (27 actions) Drive a cloud-hosted Chrome lease with the user's saved logins. Use for agent-driven web tasks (order food, book rides, compare prices, fetch receipts) that need real authenticated capability on real sites. A task agent acquires its own `lease_id` with `tools cloud_browser_scheduler acquire` and drives it here.

....

DELEGATED (only callable by the other role)
  account              namespace (2 actions) Read the user's Instinct account profile.
  feedback             namespace (3 actions) Submit product feedback and respond to team follow-ups.
  generate_referral_link action                Ask the main agent to get the member's reusable referral link and current lifetime allowance.
  revoke_referral_link action                Ask the main agent to revoke the member's reusable referral link.
  speak                action                Generate a WAV speech file from a transcript, optional director's notes, and a voice.

UNAVAILABLE (does not apply to this role)
  steer_voice_agent    action     Send an answer or context into the user's active live voice session.
```

The tool surface is the tell that this box isn't a coding sandbox at all —
`tools --help` lists ~50 namespaces (Gmail, Notion, Slack, Stripe payments, a
credential vault), but the one that reveals the design is the **cloud browser**:

```
$ tools --help | grep -iE 'cloud_browser|vault'
cloud_browser            (27)  Drive a cloud-hosted Chrome lease with the user's saved logins.
cloud_browser_scheduler  (4)   acquire, list, release, extend leases
vault                    (7)   Manage, fill, and import the user's stored credentials
```

When Instinct orders food or books a flight "as you," it does **not** open a
browser on this sandbox. It *leases* one from a separate pool of cloud browsers,
each carrying your saved profile — cookies and logins — and drives it through the
same `api.instinct.com` bridge:

```
tools cloud_browser_scheduler acquire      # → lease_id, on a browser "config" (a profile)
tools cloud_browser <action>               # click / type / read / screenshot that Chrome
```

You can read the whole model off how leases behave: each profile has exactly **one
write lease** (the only session allowed to save new logins), up to five run at
once, and releasing a lease "saves its cookies first, so the next lease loads
them." That persistence is the point — your browser identity is a **third durable
thing**, sitting server-side next to the S3 vault and the observations index, kept
so a disposable box can borrow it for one task and hand it back. Two details let
it sign in without a secret ever touching the box:

- **Scout before navigating.** `tools browser_guidance search` returns curated
  per-site notes plus *your own* past outcomes per profile (`config-a: success`,
  `config-b: blocked`) — a risk prior, not a verdict.
- **Secrets go through the Vault, never chat.** `tools vault fill` types a stored
  credential straight into the page; when the vault lacks one, `tools vault
  request` mints a link *you* fill (`app.instinct.com/vault/fill?t=…`). One-time
  codes it reads itself from your connected Gmail or Outlook.

```mermaid
flowchart TB
  ta["task agent, off-box"] -->|acquire lease| sched["cloud_browser_scheduler"]
  sched --> cb
  ta -->|click, type, read| cb["cloud browser with your saved profile"]
  vault[("Vault, your secrets, server-side")] -->|fill| cb
  cb -->|"logged in as you"| sites(["Amazon, Uber, airlines, and more"])
  box["disposable E2B box"] -->|"issues tools calls, holds no cookies"| cb
```

*The sandbox never holds a cookie or a password. Like the model, your logged-in
browser lives off the box — leased per task, persisted per profile.* (The box does
boot its own throwaway desktop — `Xvfb :99` + xfce + noVNC, hence the wallpaper you see when you open the VM —
but that's the stock E2B template, not the browser Instinct drives as you.)

---

## Summary

| | **Claude Code** | **Instinct** |
|---|---|---|
| Isolation primitive | Own Firecracker microVM | Rented E2B sandbox |
| Who runs the hypervisor | The platform | E2B (third party) |
| What's durable | The machine (`vda` block volume) | A git repo in S3 |
| Memory model | Conversation state on disk | Markdown vault, git-versioned, agent-authored |
| Credentials | Host-minted OAuth, on disk, rotated | Short-lived STS, role-scoped |
| Backing store | Local virtio-block | S3, keyed by per-user id |
| Harness location | On the box — 324 MB Bun binary | Off the box — backend only; the box holds two execution shims |
| How the model is reached | SSE → `/v1/messages` via egress gateway | Never from the box — GraphQL to `api.instinct.com`, server-side |


This was pretty fun to take a peak, I'll keep recording my notes down as new platforms come around! It's very useful to track how the end applications are progressing to understand how the general infra will develop. Like the rest of these notes I'll try to keep documenting other products and what infra they are using under the hood.
