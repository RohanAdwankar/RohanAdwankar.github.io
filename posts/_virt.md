# How many Agents can I fit on my 7GB PC

Recently I got a new computer so in continuity with my sandbox interest I figured we should take a look at how many sandboxes we can fit into this.

```
rohan@oxroute:~$ fastfetch
                             ....              rohan@oxroute
              .',:clooo:  .:looooo:.           -------------
           .;looooooooc  .oooooooooo'          OS: Ubuntu 26.04.1 LTS (Resolute4
        .;looooool:,''.  :ooooooooooc          Host: 81X8 (IdeaPad 3 15ITL05)
       ;looool;.         'oooooooooo,          Kernel: Linux 7.0.0-38-generic
      ;clool'             .cooooooc.  ,,       Uptime: 2 days, 10 hours, 39 mins
         ...                ......  .:oo,      Packages: 1304 (dpkg), 3 (snap)
  .;clol:,.                        .loooo'     Shell: bash 5.3.9
 :ooooooooo,                        'ooool     Display (BOE0816): 1366x768 in 1]
'ooooooooooo.                        loooo.    Terminal: /dev/pts/0
'ooooooooool                         coooo.    CPU: 11th Gen Intel(R) Core(TM) z
 ,loooooooc.                        .loooo.    GPU: Intel UHD Graphics G4 @ 1.2]
   .,;;;'.                          ;ooooc     Memory: 1.18 GiB / 7.05 GiB (17%)
       ...                         ,ooool.     Swap: 794.90 MiB / 4.00 GiB (19%)
    .cooooc.              ..',,'.  .cooo.      Disk (/): 54.40 GiB / 97.87 GiB 4
      ;ooooo:.           ;oooooooc.  :l.       Local IP (wlp0s20f3): 10.0.0.10/4
       .coooooc,..      coooooooooo.           Battery (L16M2PB2): 97% [AC Conn]
         .:ooooooolc:. .ooooooooooo'           Locale: en_US.UTF-8
           .':loooooo;  ,oooooooooc
               ..';::c'  .;loooo:'

rohan@oxroute:~$
```

As you can see with 7 GiB of RAM you may guess this to be in the dozens but let's apply some optimizations to see how far we can push it.

![736 tenants on a 7 GiB laptop, replayed from real agent sessions at 8x](/img/virt-timelapse.gif)

*What 736 tenants look like on this machine, replayed from real agent sessions at 8x. Each tile is an active tenant: blue ran its last command in a light sandbox and orange in a microVM, and the line and ring tie each terminal to its tile.*

![Each step, and what it bought](/img/virt-ladder.png)

## What a tenant is

A capacity number means nothing without the tenants it was measured against.

I recorded 26 real [opencode](https://opencode.ai) sessions: eight ordinary tasks on a small Python project (explain the repo, fix a failing test, add a function and a test, rename something, add type hints, write a README section, list the TODOs, add a command line entry point), each given to up to four of opencode's free models, with its tool calls logged along with how long the model thought before each one. That is 304 tool calls.

A simulated tenant alternates between being away (long-tailed, mean two minutes) and handing the agent a task. When it has a task it picks a recorded session at random, copies the starting project into its workspace and replays the calls with their recorded think times. Tenants are mid-task about 24% of the time, which matches how people use these things.

```
tenant:
  sleep(random start)
  loop until the run ends:
      session = random recorded session
      workspace = fresh copy of the starting project
      for call in session:
          sleep(call.think_ms)                  # the model thinking, as recorded
          run call against this tenant's sandbox
      sleep(away_time)                          # lognormal, mean 120 s
```

Every design gets the same tenants, because the random choices come from a seed. A run is six minutes. A design **passes** at N tenants if the p99 of the latency it *adds* to a call stays under 1.5 seconds, with no errors and no out-of-memory abort. "Added" is a call's time less the time the same call takes with one tenant on the machine, which keeps commands that simply sleep from drowning out the sandbox. Each count runs on two seeds, and a design **holds** N if both pass.

"Hostile" means each tenant needs its own kernel boundary, so the baseline is a microVM per tenant: Firecracker v1.17.0, a 1 vCPU, 256 MiB guest, a 6.1 kernel, and an 800 MiB ext4 image with bash and python3.

## Step 1: a VM per tenant, kept up

This is the whole VM:

```
PUT /boot-source     {"kernel_image_path": "vmlinux-6.1.128",
                      "boot_args": "console=ttyS0 reboot=k panic=1 pci=off sandroute.workspace=/work sandroute.port=5000"}
PUT /drives/rootfs   {"path_on_host": "rootfs.ext4", "is_root_device": true, "is_read_only": true}
PUT /machine-config  {"vcpu_count": 1, "mem_size_mib": 256}
PUT /vsock           {"guest_cid": 3, "uds_path": "v.sock"}
PUT /actions         {"action_type": "InstanceStart"}
```

Boot one per tenant, never turn them off. A small agent in each guest runs commands over vsock, and the host keeps the workspace in sync.

**48 tenants.** At 64 the machine runs out of memory. Each VM costs about 113 MiB of host memory even when it does nothing, almost half of the 256 MiB it was given, because the guest kernel and the agent touch most of what they have. The latency is excellent (p99 of 20 ms) because every VM is already there. The limit is purely memory, and so are the next two steps.

## Step 2: kill idle VMs, cold boot on the next command

Most tenants are idle most of the time, so don't keep their VMs. After 30 seconds without a command, kill the VM, and boot a fresh one on the next command. The disk, which here means the workspace on the host, is the only thing that persists. This is, as far as I can tell from the box, how Claude Code does it.

**64 tenants**, up from 48. At 96 the machine still runs out of memory. The VMs that are up are not cheaper (about 100 MiB each), there are just fewer of them. And the latency is where it hurts: about 1 call in 11 wakes a VM, and a cold boot of a guest kernel costs 1.2 seconds, so the p99 sits at 1.2 s even with only 64 tenants. The design works by paying latency to save memory, and it only goes up a little.

## Step 3: boot once, restore everyone from one snapshot

Booting is the expensive part, and every boot does the same work. So boot one VM, wait for the agent to come up, pause it, and write out its memory. Every tenant's VM is then *restored* from that single file with the memory mapped copy on write, so a VM only holds the pages it has changed.

```
# once: boot a VM, wait for the agent, then
PATCH /vm               {"state": "Paused"}
PUT   /snapshot/create  {"snapshot_type": "Full", "snapshot_path": "pristine.snap", "mem_file_path": "pristine.mem"}

# per tenant, on a fresh firecracker process, instead of the boot calls above:
PUT   /snapshot/load    {"snapshot_path": "pristine.snap",
                         "mem_backend": {"backend_type": "File", "backend_path": "pristine.mem"},
                         "resume_vm": true}
```

Two things have to be true for this to work. The root drive must be read-only, because restoring over an image another VM has since written corrupts the filesystem (the restored guest's cached ext4 metadata no longer matches the disk). And the snapshot has to be taken *while the workspace is empty*, because the host owns the workspace and pushes it in on every wake.

**176 tenants** kept up, at about 27 MiB each instead of 113. A restore takes tens of milliseconds, so at this point a VM is cheap enough to restore on demand, which is the next step.

## Step 4: release idle VMs, and throw away the ones that hold nothing

Now the combination: release a VM after a short idle window and restore the shared snapshot on the next command. A window of 5 seconds turned out to be best.

The question is what to do with the VM when you release it. The naive answer is to snapshot its memory to disk so it can resume exactly. That works, and it cost me: at about 400 tenants the machine was writing 11 to 13 GiB of session snapshots and running out of disk bandwidth.

The better answer is that most guests hold nothing worth saving. The workspace is on the host and gets pushed back in. If the guest also holds nothing outside the workspace and `/tmp`, the VM can simply be killed, and the next wake restores the shared snapshot, with no disk written at all:

```
release():
  if a command is in flight:                      keep the VM
  live = guest.busy()                             # a server the agent backgrounded, a cron
  if live or the probe failed:                    keep the VM, look again later
  if guest.state() shows no change outside the workspace and /tmp:
      kill the VMM                                # nothing written
  else:
      pause + /snapshot/create into this tenant's own slot
```

Two details made that work. `/tmp` is a second synced area, kept on the host while the guest is gone, so a test run that writes scratch files doesn't make the guest look dirty. And a guest that really did install something (a `pip install`, say) keeps its snapshot, in two alternating slots so a failed write never destroys the last good one.

**640 tenants**, from 176, and the machine now runs out of *cpu* and not memory. Resident VMs at the peak are 228, each costing about 8 MiB. The tail is where the cost is: a woken call takes a median of 115 ms and the p99 for all calls is 1.3 s, because 640 tenants produced 4,590 wakes in a six minute run.

## Step 5: don't use a VM for most commands

Looking at what the tenants run, 224 of 304 recorded calls (74%) never needed a machine at all: they are the file tools (`read`, `edit`, `write`, `glob`, `grep`), and shell commands like `ls`, `cat` and `sed`. Only 80 of the 136 shell commands ran code, and 8 of the 26 sessions never needed a VM once. Yet every design above gives each of them a whole VM, or pays to wake one.

So send each call to the cheapest place that is still safe for it. The command line is parsed with a real bash grammar (tree-sitter). A command stays in a light sandbox only if every name in it is one the sandbox carries, and nothing in it asks about the machine or reaches outside the workspace:

```
for name in command_names(line):
    if name has a '/':               return VM    # a binary at some path
    if name in ALWAYS_VM:            return VM    # python3, gcc, node, npm, cargo, chromium, ...
    if name in MACHINE_QUERIES:      return VM    # which, env, ps, uname, curl, kill, ...
if line names a path outside the workspace:  return VM
if line reads $PATH:                 return VM
if any name is not a known utility:  return VM
return LIGHT
```

`which chromium` in a cheap shell would say "not installed" about the shell and not about the machine, and a real model concluded exactly that, which is why machine questions always go to the VM.

The light sandbox is [bubblewrap](https://github.com/containers/bubblewrap) plus a seccomp filter, with no VM:

```
bwrap --unshare-all --unshare-user --disable-userns --cap-drop ALL --seccomp 3 \
      --die-with-parent --new-session --clearenv \
      --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
      --proc /proc --dev /dev --tmpfs /tmp \
      --bind $WORKSPACE /work --chdir /work \
      bash -c "$COMMAND"
```

The only writable things are the tenant's workspace and a private `/tmp`; there is no network namespace to join and the filter has no socket calls. The filter is the Docker default profile's 299 allowed calls, with `clone3` answered "not implemented" and `clone` with any namespace flag refused. A command costs about 6 ms, against 2.4 ms bare and 7.5 ms in a warm VM.

**736 tenants**, from 640. That is a smaller step than the others, and it is worth explaining why. At its limit the released design runs 19,353 calls and 4,590 wakes in a six minute run. With routing, oxroute runs 22,328 calls and 1,777 wakes, at 43% mean cpu against 51%. Routing removed most of the wakes. But the limit is not set by the average, it is set by bursts: when many tenants start a turn at once, the wakes and the Python test runs they cause queue on four threads, and the p99 passes 1.5 seconds while the machine is half idle. The 26% of calls that still need a VM, mostly `python3`, are real work that no design avoids.

The light tier does something else that no VM does: its cost does not grow with the host process. The orchestrator starts each command with `posix_spawn` and not `fork`, because a fork copies the parent's page tables, and with hundreds of tenants the parent is hundreds of megabytes. A command costs about 7 ms whatever the size of the host process.

## Other steps, and what didn't matter

- **Warming Python into the snapshot.** Whatever sits in the guest's page cache when the snapshot is taken is shared by every VM restored from it, so the init script imports Python's common standard library before the snapshot. A wake that runs `python3 -m unittest` then costs 161 ms of cpu instead of 530.
- **A balloon with free page reporting**, the technique Muse is described to use. A guest that allocated and freed 120 MB went from 184 MiB back to 64 MiB in three seconds. In an earlier rough run it took the kept-up design from 128 tenants to about 150, and it does nothing for the released designs, which run out of cpu first.
- **Telling the sandbox when a turn ends** lets it release the VM at once, instead of waiting out the idle window. In an earlier rough run that halved the number of resident VMs. It needs a harness that can say when a turn ends, so it is not in the numbers above.
- **Telling it when a turn starts** so the VM wakes during the model's thinking time. A blind prewarm cost more cpu than it saved, because a third of the sessions never need a VM. It would need a predictor.

## The same tenants on other people's designs

![Latency added to a call at each design's limit](/img/virt-latency.png)

The same replay, run against designs from other systems: Kata Containers (a VM per pod, driven through Kubernetes) holds 40 tenants, gVisor with pods deleted when idle holds 80 (192 kept up, in an earlier rough run), and a Cloud Hypervisor VM at the size Muse is described to use, 2 vCPU and 8 GiB with a balloon, holds 16. Those are not slower designs. They are designs for tenants that hold state: an always-on VM that keeps its working set is a good deal for a personal agent, and the wrong one for a machine full of mostly idle coding sessions.

## Try it yourself

The usual way to show a sandbox API is to start a hundred of them at once, each writing a file and reading it back. Here is that job in sandroute:

```rust
async fn run_single_sandbox(idx: usize) -> anyhow::Result<()> {
    // Create an isolated sandbox
    let sandbox = Sandroute::create().await?;
    let random = format!("{idx}-{:x}", SystemTime::now().duration_since(UNIX_EPOCH)?.as_nanos());

    // Write a file inside the sandbox
    sandbox.write_file("random.txt", &random).await?;

    // Read it back with a command
    let res = sandbox.run("cat random.txt", None).await?;
    println!("Sandbox {idx}: {}", res.stdout.trim());
    sandbox.close().await
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Spin up the sandboxes simultaneously
    let tasks: Vec<_> = (0..100).map(|i| tokio::spawn(run_single_sandbox(i))).collect();
    for t in tasks { t.await??; }
    Ok(())
}
```

It is `examples/hundred.rs` in the [repo](https://github.com/RohanAdwankar/sandroute), and you run it with `cargo run --release --example hundred 100` once the VM image is built. The `close()` is explicit because Rust cannot await in a destructor.

To have something to compare against I ran the same job on [microsandbox](https://github.com/superradcompany/microsandbox), an open source runtime that starts a microVM per sandbox from a Python (or Rust) SDK, with nothing to install but KVM. It looks like this:

```python
async def run_single_sandbox(idx: int):
    # Spin up an isolated microVM asynchronously
    sandbox = await Sandbox.create(f"bench-{idx}", image="python", cpus=1, memory=256)
    try:
        random_str = uuid.uuid4().hex

        # Write file inside sandbox
        await sandbox.fs.write("/tmp/random.txt", random_str.encode())

        # Read or verify back
        res = await sandbox.exec("cat", ["/tmp/random.txt"])
        print(f"Sandbox {idx}: {res.stdout_text.strip()}")
    finally:
        await sandbox.stop_and_wait()
        await Sandbox.remove(f"bench-{idx}")
```

All three, on the same laptop, a hundred sandboxes at once, each with a 256 MiB guest:

| | the read runs in | time | host memory used |
|---|---|---|---|
| microsandbox | a microVM (`cat`) | 8.6 s | 4.6 GiB |
| sandroute | a microVM (`python3`) | 2.0 s | 242 MiB |
| sandroute | the light sandbox (`cat`) | 0.8 s | 23 MiB |

Microsandbox boots a fresh microVM for every sandbox, and it is quick for that: ten sandboxes took 0.8 s. A hundred of them fill the machine, and the 4.6 GiB they hold is where the 100 or so a 7 GiB laptop can hold comes from. Sandroute restores every VM from one shared snapshot, so a VM costs about 2 MiB at a hundred and 4.4 MiB at seven hundred, and a command that only touches files does not need one. That is the whole trick of this post, and it is also why this is not a fair fight about boot speed: microsandbox is doing the honest thing, and the comparison is what the shared snapshot and the light sandbox buy.

Past a hundred, the sandroute version keeps going:

| sandboxes | the read runs in | time | host memory used |
|---|---|---|---|
| 700 | the light sandbox (`cat`) | 5.4 s | 589 MiB |
| 700 | a microVM (`python3`) | 18.5 s | 3.1 GiB |

Every one of those sandboxes is isolated from the others and from the host. Seven hundred microVMs restored from a shared snapshot in 18.5 seconds, holding 3.1 GiB, is about 4.4 MiB each. Microsandbox is where this laptop stops it. A hundred sandboxes at once work. At 110 the machine runs out of memory while most of the sandboxes are still starting: free memory fell to 259 MiB, then 293 MiB at 120 and 284 MiB at 130 (where 34 of the 130 had finished), and I stopped each run there (the same rule the capacity benchmark uses, under 300 MiB free) rather than let the kernel start killing things. That is a ceiling of about 100 sandboxes at once, and sandroute does seven hundred on the same machine, seven times as many, in 18.5 seconds.

![130 sandboxes started at once, microsandbox next to sandroute](/img/virt-exhaustion.gif)

*130 sandboxes started at once. Microsandbox's memory climbs to the limit before most have finished and the run is stopped with 34 done; sandroute finishes all 130 in 3.4 s.*

One caveat on how to read that. Microsandbox starts all of its VMs at the same moment here, which is what the job asks for, and a smaller number would work if they were started a few at a time. A hundred at once is the usual way to show a sandbox API, so it is the fair one to run.

## What is left

The next step is the 26% of calls that still need a VM. Most of them are `python3`, and running Python in the light tier would be the biggest remaining win, but it widens the kernel surface a hostile tenant can reach (a script can make any allowed system call) and a script that needs the network or `pip` would fail without telling anyone, so I have not done it. After that: a cheaper wake (about 110 ms of cpu today), a limit on how many VMs restore at once so a burst of turns doesn't thrash four threads, and a predictor that wakes a VM only for turns that will need one.

The code and every raw result are in the [sandroute repo](https://github.com/RohanAdwankar/sandroute).
