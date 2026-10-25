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

## What is a Sandbox

Lots of people will have differing opinions here so for the sake of playing a fair game lets set some base level requirements on what an agent sandbox will need.

1. Isolation Level 

We will assume that tenants can be hostile to each other.
Therefore traditional containerd pods even in seperate namespaces is not sufficient isolation.
<add more>

2. Tenant Activity

Most agent sandboxes don't require all tenants to be 100% active [1]

Also to be honest if we benchmark with all the tenants at full activity to be honest this wouldn't be very fun because we won't be able to do any fun optimizations with baloons and the like.

3. Computational Capability 

We will use opencode as the standard for what the agent sandbox needs to run.
This means the sandbox needs to have internet access and <>.

## How I'm Measuring It

A capacity number means nothing without the tenants it was measured against, so here is what a tenant is.

**The sessions are real.** I gave eight ordinary tasks on a small Python project (explain the repo, fix a failing test, add a function and a test, rename
something, add type hints, write a README section, list the TODOs, add a command line entry point) to opencode, each to up to four of its free models.
Opencode's `bash`, `read`, `write`, `edit`, `glob` and `grep` tools were replaced with wrappers that logged every call: the tool, its arguments, and the
time the model spent thinking before it made the call. That gave 26 usable sessions and 304 tool calls. Opencode has a few more tools (todo lists, subagents, web search), but they touch neither the workspace nor a machine, so they are not part of
what a sandbox has to serve.

**A tenant replays them.** A tenant alternates between being away and handing the agent a task. When it has a task it picks one of the 26 sessions at random, copies the starting project
into its workspace, and replays the recorded calls with their recorded think times between them. The away time is long-tailed, with a mean of two minutes: usually a minute or two, sometimes much longer.
Tenants end up mid-task about 24% of the time, which fits the premise from the start of the post that most tenants are idle. Each tenant also starts at a random point, so they do not all begin together.

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

**Every design gets the same tenants.** All the sandboxes in this post run through one harness and one interface: a command in, an output out, with the workspace kept in step.
The random choices come from a seed, so seed 1 is the same crowd of tenants for every design, and a second seed is a different crowd with the same statistics. A run is six minutes
with a sampler recording free memory, VM count, cpu and disk once a second, and a run is aborted if the machine runs out of memory or disk.

**What counts as a pass.** The target is a p99 of 1.5 seconds of latency added to a call, with no errors. "Added" is the time the call took less the time the same call takes
with one tenant and nothing else going on, which I measured once for every recorded call. Without that, the numbers were dominated by commands that sleep, which take
the same time under every design, so the benchmark measured the commands and not the sandbox. A design passes at a tenant count if most seeds pass, and the count goes up until it does not.

**What this does not measure.** The tenants are coding sessions on a small project, so it says nothing about a sandbox for browsers or for long jobs at full load. Every tenant gets the same 256 MiB, which
is not what the products I compare against use, and the sections below say what each of them does instead.

## Exploring 

In the prior posts the approaches we looked at were vanilla firecracker, firecracker through e2b, and cloud hypervisor.

My first instinct was to start with e2b but it recommends 4+ cores and 8GB minimum RAM so my old boy is disqualified on both counts. [https://github.com/e2b-dev/infra/blob/main/DEV-LOCAL.md]

So lets proceed with the others and toss in Kata containers for the k8s fans.

### Naaive Firecracker

Every number in this section was taken on the machine above with the same recorded agent sessions replayed against
each tenant: 26 real opencode sessions (8 small Python tasks run by 4 free models, 304 tool calls), with the model's think time kept. A design "passes" at a
tenant count if the p99 of the latency it adds to a call stays under 1.5 s, with no errors and no out of memory.
The numbers marked rough were taken while I was also using the machine, so they are good to about 5%.

**The config.** Firecracker v1.17.0, a 6.1.128 guest kernel built MMIO-only (`CONFIG_PCI` is off, which matters in the
next section; Claude Code's Firecracker kernel does have PCI, so a recent Firecracker is not necessarily MMIO-only), and an 800 MiB ext4 image with bash, python3, coreutils and pip copied in. This is the whole VM:

```
PUT /boot-source     {"kernel_image_path": "vmlinux-6.1.128",
                      "boot_args": "console=ttyS0 reboot=k panic=1 pci=off sandroute.workspace=/work sandroute.port=5000"}
PUT /drives/rootfs   {"path_on_host": "rootfs.ext4", "is_root_device": true, "is_read_only": true}
PUT /machine-config  {"vcpu_count": 1, "mem_size_mib": 256}
PUT /vsock           {"guest_cid": 3, "uds_path": "v.sock"}
PUT /actions         {"action_type": "InstanceStart"}
```

The root is read-only with a tmpfs overlay on top, so one image backs every VM. A small agent in the guest runs
commands over vsock, and the host keeps the workspace and syncs it in.

#### Vanilla

One VM per tenant, cold booted, never released, no balloon.

Cold booted and kept up, the machine holds 48 tenants (both seeds, p99 20 ms) and runs out of memory at 64. Each VM costs about 113 MiB of host memory, which is nearly half of what its 256 MiB guest was given: the guest kernel and the agent are mostly touched memory. The same VM restored from one shared snapshot costs about 27 MiB, passes 176 tenants (both seeds), and runs out of memory at 192, which is a trick and not vanilla.

#### The way Claude Code does it

What the first post found: Firecracker, a Rust PID 1 (`process_api`) listening on vsock port 2024, one writable 256 GB disk that
outlives the VM plus read-only disks for the harness. A message wakes the VM, and when it is idle the host reclaims it: the
processes die and the disk is kept. A second look inside a box (this time with a probe that dumps the VM's configuration) adds the rest:

```
kernel   6.18.44-fc-v153 (builder@sandboxing), custom, not an Ubuntu kernel; CONFIG_PCI=y, VMGENID, VIRTIO_BALLOON, VIRTIO_MEM, ZSWAP
cmdline  mitigations=auto,no_guest_host,no_guest_guest deferred_init=lazy dhash_entries=131072 ihash_entries=65536
         console=ttyS0 reboot=k panic=1 nomodule random.trust_cpu=1 ipv6.disable=1 swiotlb=noforce psi=1 rdinit=/process_api
cpu      4 vCPU, one thread per core, a generic Xeon @ 2.80GHz under KVM
memory   16 GiB (MemTotal 16477348 kB), no swap, 0 hugepages, THP madvise, shmem THP never
balloon  virtio_balloon: free_page_reporting=1, stats_vq=1, deflate_on_oom=1, no free page hinting, page_reporting_order=9
disks    vda 256G ext4 rw, discard (reserved so only about 30 GiB is usable); five small read-only disks: rclone, claude-code,
         env-runner and two skills trees. Measured: 517 MB/s write, 1.6 GB/s read, about 4300 synchronous 4K writes a second
boot     1.82 s to /process_api as init (the first post measured 430 ms); a cold boot with a new boot id
```

How 16 GiB per tenant is affordable. At boot the kernel brings up only 3.2 of the 16 GiB (`Memory: 3214224K/16776824K`), because
of `deferred_init=lazy`, so the host does not have to back all of it. The balloon hands freed pages back, and at idle the guest holds
about 0.5 GiB, 310 MB of it the `claude` process. `swiotlb=noforce` skips a bounce buffer the kernel would otherwise allocate in a
guest with more than 4 GB, and the two hash table sizes are capped so they do not grow with RAM. None of these matter much at 256 MiB.

What this does and does not show about snapshots. The one wake observed was a cold boot onto the kept disk: a new boot id, a dmesg
starting from zero, and files in `/tmp` from the earlier session still there because `/tmp` is on `vda`. The kernel has VMGENID built in,
so it could be restored from a snapshot, and one wake does not show whether it ever is. It is one observation.

Here that is the `reclaim` design: release an idle VM by killing it, and cold boot the next one. It passes 64 tenants on both seeds and runs out of memory at 96 on both. Even at 64 its p99 is 1.2 s, because every wake is a cold boot of a whole guest kernel.
A first test of keeping a disk and cold booting instead of writing memory snapshots, on this machine: oxroute with every idle VM killed
and cold booted ran out of memory with 78 VMs resident, where the restore design held 239. A cold booted VM costs about 123 MiB against
about 37 for one restored from a shared snapshot. The approach suits a host with memory to spare.

#### The way Instinct does it

E2B Firecracker, 2 vCPU, 1.9 GB RAM, 29 GB disk, Ubuntu 22.04 with a desktop, about 1.3 s to the desktop, and a timeout
with either a cold boot or a snapshot resume. I do not know which Instinct uses.

Here that is the `suspend` design, with its VM sized 2 vCPU and 1900 MiB. I did not measure it at that size. At my own 1 vCPU and 256 MiB
it passes 640 tenants with a 5 second idle window (both seeds, p99 1.3 s) and fails at 704 on cpu.

### Cloud Hypervisor

Cloud Hypervisor is Firecracker's sibling: both are Rust VMMs on KVM built from the same rust-vmm crates. The difference
that matters here is that it has PCI and a balloon with free page reporting, which is how Muse stays affordable.

**The config I booted** (v54.0, the build Kata ships). It needs a kernel with PCI, so my Firecracker kernel does not work and this
uses Kata's 6.18.56. The same rootfs image boots under it and my agent comes up in about 0.2 s of guest time:

```
cloud-hypervisor \
  --kernel vmlinux.container \
  --disk path=rootfs.ext4,readonly=on,image_type=raw \
  --cmdline "console=ttyS0 root=/dev/vda ro rootfstype=ext4 panic=1 sandroute.workspace=/work sandroute.port=5000" \
  --cpus boot=1 --memory size=256M --vsock cid=3,socket=v.sock
```

#### Vanilla

The line above, one VM per tenant, cold booted, kept up, no balloon. I did not run it at capacity; in a small test eight idle ones cost about 167 MiB each, against about 113 for Firecracker cold booted.

#### The way Muse does it

From the second post, from inside the box: a Cloud Hypervisor microVM with 2 vCPU and 8 GB allocated, a stock Ubuntu
`7.0.0-26-generic` kernel, and four virtio-blk disks (a read-only btrfs root, a dm-crypt overlay for scratch, a dm-verity tools
image, and a 100 GB LUKS2 volume for the user). Its balloon has free page reporting, so an idle one costs its working set of
about 2 GB and not 8. It also has a virtio-rng, a vsock channel back to the VMM for readiness, and a systemd-nspawn container
inside it. New ones are pre-booted, and one takes about 40 s to become ready.

What I do not know: the Cloud Hypervisor version and its full command line, whether guest memory is backed by huge pages or
shared, how the balloon is sized, how the host is configured, or how many of these a host runs.

Cloud Hypervisor at 2 vCPU and 8 GiB with the balloon on, pre-booted and kept up. It does not have Muse's four-disk layout, only the one read-only root.
On this machine it holds 16 tenants (both seeds, p99 41 ms) and runs out of memory at 32. Each costs about 370 MiB of host memory, well under its 8 GiB because the balloon hands back what the guest does not use.
That is the price of keeping a rich, always-on VM per user: it is a good deal for a personal agent that holds state, and the wrong one for a seven gigabyte machine full of mostly idle coding sessions.

#### Optimized variant

The same VM with the balloon turned on and, as under Firecracker, restored from one shared snapshot instead of cold booted. Cloud Hypervisor v54's
`memory_restore_mode=CopyOnWrite` maps the snapshot's memory file copy on write, so many VMs share one file and a VM only holds the pages it has touched.
Two restored from one snapshot held 14 MiB each. The calls are:

```
PUT /api/v1/vm.create    {..., "balloon": {"size": 0, "deflate_on_oom": true, "free_page_reporting": true}}
PUT /api/v1/vm.pause
PUT /api/v1/vm.snapshot  {"destination_url": "file:///snap/pristine"}      # once, with an empty workspace
# per tenant, on a fresh cloud-hypervisor process:
PUT /api/v1/vm.restore   {"source_url": "file:///snap/pristine", "memory_restore_mode": "CopyOnWrite"}
PUT /api/v1/vm.resume
```

I did not run these at capacity, so the numbers in this post for the snapshot designs are Firecracker's.

### Kata Containers

Kata runs each pod in its own VM and lets Kubernetes drive it, so it is the answer to "I want VMs but I want to keep my cluster".
I ran it through the real Kubernetes interface: `crictl` against containerd 2.4.1 with Kata 4.3.1, Cloud Hypervisor as the
VMM (v54.0), a 6.18.56 guest kernel, and the `python:3.13-slim` image, with the workspace shared into the guest over virtio-fs.

#### Vanilla

Kata's own defaults are a 2048 MiB guest, 1 vCPU, and no free page reporting. On the untouched defaults it is borderline at 32 tenants: one seed passed and the other ran out of memory.

#### Optimized variant

Two changes to Kata's shipped Cloud Hypervisor config, made with `sed` so the diff from vanilla is exactly this:

```
sed -e 's/^default_memory = .*/default_memory = 256/' \
    -e 's/^reclaim_guest_freed_memory = false/reclaim_guest_freed_memory = true/' \
    configuration-clh.toml > kata-clh.toml
```

A 256 MiB guest like the Firecracker ones, and `reclaim_guest_freed_memory`, which turns on free page reporting. A pod per tenant with the
guest at 256 MiB and the reporting off held 48 to 52 tenants in an earlier, rough run. Each pod costs about 154 MiB of host memory idle, because Kata boots a fresh
guest kernel and agent for every pod where Firecracker restores a shared snapshot. Pods deleted when idle (`kata-cold`) hold 48 as well, because every wake boots a VM.
With reporting on, a pod that allocated and freed 150 MB goes from 259 MiB to 161 MiB, and stays at 259 with it off. I also tried a 128 MiB guest, which was
worse (186 MiB a pod), and virtio-fs with no cache, which would not boot. The final run, with reporting on, passes 40 tenants on both seeds (p99 0.33 s) and runs out of memory at 56 on both, so the limit is between 40 and 56 and I cannot say reporting moved it.

### gVisor

Not in the plan, but it is the other way people isolate hostile tenants, so I ran it: gVisor (`runsc`, release 20261019,
systrap platform) as a runtime in the same containerd. It has no VM and no guest kernel. A kept pod costs about 40 MiB of host
memory and boots in under 200 ms. In an earlier, rough run a kept pod held 192 tenants and ran out of cpu there. Deleting idle pods does not help, because creating them costs more cpu than it saves: in the final run it passes 80 on both seeds and 112 on one of two (p99 1.05 s and 1.60 s).

### Firecracker Tricked Out

Four things on top of the naive config.

1. **Restore from one shared snapshot.** The first VM is booted once and snapshotted with an empty workspace, and every tenant's
   VM is restored from that single file (memory mapped copy on write, the root image shared). A resident VM then holds only the
   pages it has touched, about 27 MiB, instead of its whole 256.

   ```
   # once: boot a VM, wait for the agent, then
   PATCH /vm               {"state": "Paused"}
   PUT   /snapshot/create  {"snapshot_type": "Full", "snapshot_path": "pristine.snap", "mem_file_path": "pristine.mem"}

   # per tenant, on a fresh firecracker process, instead of the boot calls above:
   PUT   /snapshot/load    {"snapshot_path": "pristine.snap",
                            "mem_backend": {"backend_type": "File", "backend_path": "pristine.mem"},
                            "resume_vm": true}
   ```

   The root drive has to be read-only. Restoring over an image that another VM has since written corrupts the filesystem, because the
   restored guest's cached ext4 metadata no longer matches the disk. The snapshot's file name includes a hash of the workspace path (the
   agent's root is baked into guest memory), the kernel and the image, so a rebuilt image never restores a stale snapshot.
2. **Release idle VMs, and throw away the ones with nothing to keep.** After an idle window the VM is released. The agent asks the
   guest whether it holds anything the workspace does not, and if not the VM is simply killed, which writes nothing, and the next
   command restores the shared snapshot. If it does hold something, such as an installed package, the whole VM is snapshotted.

   ```
   release():
     if a command is in flight:                      keep the VM
     live = guest.busy()                             # a server the agent backgrounded, a cron
     if live or the probe failed:                    keep the VM, look again later
     if guest.state() shows no change outside the workspace and /tmp:
         kill the VMM                                # nothing written; the next command restores the shared snapshot
     else:
         pause + /snapshot/create into this tenant's slot (two slots, alternating, so a failed write never destroys the last good one)
   ```
3. **A balloon with free page reporting**, the same technique as Muse. In the guest it hands back memory the guest has freed:
   a VM that allocated 120 MB and freed it went from 184 MiB back to 64 MiB in 3 seconds. In an earlier rough run it took the kept design from
   128 tenants to about 150, and I did not rerun that. It does nothing for the released designs, which run out of cpu first.

```
PUT /balloon  {"amount_mib": 0, "deflate_on_oom": true, "free_page_reporting": true}
```
plus `page_reporting.page_reporting_order=3` on the guest command line.

4. **Warm the interpreter into the snapshot.** Whatever is in the guest's page cache when the snapshot is taken is in every VM restored from it. The init script
   loads Python's commonly used standard library and a few shell utilities before the agent starts:

   ```
   chroot "$R" /usr/bin/python3 -c 'import unittest, json, re, os, sys, subprocess, pathlib, argparse, collections, typing, shutil, tempfile, io, itertools, functools, textwrap, datetime, logging, asyncio'
   chroot "$R" /bin/bash -c 'ls / >/dev/null; grep -q . /etc/passwd; sed -n 1p /etc/passwd >/dev/null'
   ```

   Without it a restored VM reads Python from the virtual disk on its first command. A wake followed by `python3 -m unittest` cost 530 ms of cpu and 307 ms of wall time; with it, 161 ms and 116 ms.
   I found this by accident: my first rewrite of the guest agent was a static binary, where the old one was a Python program that kept Python warm in every snapshot without anyone noticing. The same 560 tenants went from a p99 of 0.5 s to 4.6 s.

Final run, two seeds each, on the idle machine. A design holds N tenants if both seeds passed at N:

| design | holds | what runs out |
|---|---|---|
| one VM each, cold booted, kept up | 48 | memory |
| one VM each, restored from the shared snapshot, kept up | 176 | memory |
| released after 5 s idle, every command in the VM | 640 | cpu |
| released after 30 s idle, file-only commands in the light tier (oxroute) | 736 | cpu |

The released designs wrote no session snapshots at all in the final run: a guest that holds nothing outside the workspace and `/tmp` is killed and the next wake restores the shared snapshot, so there is no disk to run out of.

![Tenants one 7 GiB machine serves, by design](/img/virt-capacity.png)

## What a command costs in each tier

Before the routing part, here is what routing is choosing between. This is the same command run 60 times in each place, in a project of 300 small files, on the machine above.

| command | host, nothing around it | light sandbox | Firecracker, warm |
|---|---|---|---|
| `ls` | 2.4 ms | 6.0 ms | 7.5 ms |
| `cat` a file | 2.1 ms | 5.7 ms | 7.2 ms |
| `grep -rn` over 300 files | 2.8 ms | 6.9 ms | 8.1 ms |
| `find` and sort | 3.9 ms | 7.1 ms | 9.1 ms |
| `python3` start | 10.2 ms | 13.4 ms | 14.3 ms |
| `python3`, 85 ms of cpu | 82.1 ms | 85.3 ms | 86.3 ms |

The light sandbox is the file-only tier: bubblewrap builds a fresh set of namespaces for the command and a seccomp filter limits what it can ask the kernel. That adds about 3.5 ms.
This is the whole command line around each one (the seccomp program arrives on file descriptor 3):

```
bwrap --unshare-all --unshare-user --disable-userns --cap-drop ALL --seccomp 3 \
      --die-with-parent --new-session --clearenv \
      --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
      --proc /proc --dev /dev --tmpfs /tmp \
      --bind $WORKSPACE /work --chdir /work \
      bash -c "$COMMAND"
```

The only writable things are the tenant's workspace and a private `/tmp`. There is no network namespace to join and the filter has no socket calls. The filter is the Docker default
profile's 299 allowed calls, with `clone3` answered "not implemented" (so a program falls back to `clone`, whose flags can be checked) and `clone` with any namespace flag refused.
A warm VM adds only 1 to 2 ms more than the light sandbox, and 85 ms of cpu inside it took 86.3 ms. What a command in a warm VM pays is a vsock round trip and a sync, where the host walks the workspace
and reports what changed before the command and the guest reports back after it. A wake, meaning a released VM restored from the shared snapshot and then running one command through the whole path, is about 90 ms.

So a warm VM is not slow, and sending file commands to the light tier does not make them much faster once the VM is up. The saving is everything around the VM: the 90 ms wake, the cpu it burns, and the memory a resident VM holds. That is what routing is trying not to pay.

## Past 600

Ok so this is all very cool but there's something that you are probably also starting to clue in on.

Of the 304 calls the tenants make, 168 are the file tools (`read`, `edit`, `write`, `glob`, `grep`) and 56 of the 136 shell commands only touch files, `ls` and `cat` and `sed`. That is 224 of 304
calls, 74%, that never needed a machine at all, and 8 of the 26 sessions never needed one once. Everything above gives such a call a whole VM anyway, and the designs that release VMs when idle pay to restore one for it.
Those designs run out of cpu, not memory, at about 640 tenants, because every release and wake is work (a VM killed and restored, a snapshot mapped, a sync). Taking the calls that need no machine out of that path is the whole idea.

So sandroute sends each call to the cheapest place that is still safe for it. Here is how it works, in the order a call meets it.

### 1. Decide where the command runs

The command line is parsed with a real bash grammar (tree-sitter), not matched with patterns, so pipelines, `$(...)`, heredocs and `&&` chains all give up the command names inside them.
A command stays in the light tier only if every name is one the light tier carries, and nothing in it asks about the machine or reaches outside the workspace:

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

The machine queries matter more than they look. `which chromium` run in a cheap shell would say "not installed" about the shell and not about the machine, and a real model concluded exactly that.
The file tools skip the parsing: they always go to the light tier.

### 2. Run it in the light tier

The light tier is the `bwrap` command line from the cost section: a fresh set of namespaces, a seccomp filter, the workspace as the only writable thing. It starts with `posix_spawn` and not `fork`, because a
fork copies the parent's page tables and the cost of a launch then grows with the size of the process that is serving hundreds of tenants. A command costs about 7 ms whatever size the host process is.

### 3. Wake a VM when a command needs one

The first command that needs a machine finds none and boots one. The VM is the shared-snapshot restore from the Firecracker section, so a wake, including the sync and one command, takes about 90 ms and the VM holds only the pages it touches:

```
run(command):
    if classify(command) == LIGHT:  return bwrap_exec(command)
    if the VM is not up:            boot()          # restore the shared snapshot, or resume this tenant's own
    return vm.exec(command)
```

### 4. Keep the workspace in step

The host owns the workspace, so both tiers see the same files. Around every command in the VM the host pushes what changed on its side and pulls what the command changed:

```
vm.exec(command):
    push_changes()                  # walk the host workspace, send files whose size or mtime changed
    result = agent.exec(command)    # the guest agent also walks its tree before and after
    apply(result.report)            # write what the command created, changed or deleted back to the host
```

That walk is the 6 to 7 ms a warm VM costs over the light tier. A file changed on both sides since the last exchange is a conflict, and the VM's version wins.

### 5. Hand the VM back

After an idle window with no VM command, the VM is released, as in the `release()` flow shown earlier. It is kept if anything is still alive inside it, such as a server the agent started in the background. If the guest holds
nothing outside the workspace and `/tmp`, it is killed outright, which writes nothing. Otherwise it is snapshotted into this tenant's own slot and resumed next time.

### 6. Hints

The harness can say when a turn ends, and releasing then instead of waiting out the window halves the number of VMs resident at any moment. It can also say when a turn starts, so the VM wakes while the model is still thinking
about its first command. Both are optional, and the numbers in this post use the idle window alone unless a series says otherwise.

### What it buys

On the same tenants and the same machine, the design that releases VMs and sends everything to them holds 640 tenants. With the routing in front it holds 736, and both run out of cpu and not memory.
That is 15% more, which is less than I expected, so here is what the run says. At 640 tenants the released design does about 19,000 calls and 4,600 wakes in a six minute run; oxroute at 736 does about 22,000 calls
and 1,800 wakes, with a lower mean cpu (43% against 51%). Routing removed most of the wakes and the cpu they cost, and the limit moved by only 15% because it is set by bursts and not the mean: when many tenants
start a turn together, the wakes and the Python test runs they cause queue on four threads, and the p99 passes 1.5 s while the average machine is still half idle. The 26% of calls that still need a VM
(mostly `python3`) are real work that no design avoids.

The latency each call pays at those limits:

![Latency added to a call at each design's limit](/img/virt-latency.png)

Every design sits under the 1.5 s target at its limit by construction, so the chart shows what the limit costs. The kept-up designs are fast (a p99 of 20 to 35 ms) because their VMs are always there, and they stop for lack of memory. The released designs pay a wake on the unlucky calls, so their p95 and p99 climb toward the target while the median stays in single digits of milliseconds, and they stop for lack of cpu. The Claude Code style design pays a cold boot of about 1.2 s on every wake, and oxroute pays a wake on far fewer calls.

Against what the other setups give on this machine (the chart above), the picture is bigger: 736 tenants against 176 for a kept-up Firecracker VM per tenant, 64 for the way Claude Code is described to work, 40 for Kata
and 16 for the way Muse is configured. Most of that comes from restoring one shared snapshot and throwing a VM away when it holds nothing, and the routing is the last 15% on top.

## Routing Graunlarity

Everytie

## Footnotes

[1] I believe sandboxes for RL may be different where they just run for long amoutns of time at full activity. This was focused more on agents involved with the real world (humans, other agents) where there is more latency and periods of inactivity than simulations.
