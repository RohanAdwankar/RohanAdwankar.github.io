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

TODO(final run): capacity of cold booted VMs (series `fc-vanilla`). So far only a small test: eight idle tenants cost about 123 MiB each cold booted. What is measured at capacity is the same VM restored from one shared snapshot instead, which is a trick and not vanilla: it costs about 37 MiB each, passes 128 tenants (two seeds), and at 160 the machine runs out of memory.

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

Here that is the `reclaim` design: release an idle VM by killing it, and cold boot the next one. TODO(final run), series `fc-claude`.
A first test of keeping a disk and cold booting instead of writing memory snapshots, on this machine: oxroute with every idle VM killed
and cold booted ran out of memory with 78 VMs resident, where the restore design held 239. A cold booted VM costs about 123 MiB against
about 37 for one restored from a shared snapshot. The approach suits a host with memory to spare.

#### The way Instinct does it

E2B Firecracker, 2 vCPU, 1.9 GB RAM, 29 GB disk, Ubuntu 22.04 with a desktop, about 1.3 s to the desktop, and a timeout
with either a cold boot or a snapshot resume. I do not know which Instinct uses.

Here that is the `suspend` design, with its VM sized 2 vCPU and 1900 MiB. TODO(final run), series `fc-instinct`. At my own 1 vCPU and 256 MiB
it passes 416 tenants with a 5 second idle window (rough, two seeds), and fails at 432 on cpu and disk.

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

TODO(final run), series `ch-vanilla`: the line above, one VM per tenant, cold booted, kept up, no balloon. The backend is built and boots; in a
small test eight idle ones cost about 167 MiB each, against 123 for Firecracker cold booted.

#### The way Muse does it

From the second post, from inside the box: a Cloud Hypervisor microVM with 2 vCPU and 8 GB allocated, a stock Ubuntu
`7.0.0-26-generic` kernel, and four virtio-blk disks (a read-only btrfs root, a dm-crypt overlay for scratch, a dm-verity tools
image, and a 100 GB LUKS2 volume for the user). Its balloon has free page reporting, so an idle one costs its working set of
about 2 GB and not 8. It also has a virtio-rng, a vsock channel back to the VMM for readiness, and a systemd-nspawn container
inside it. New ones are pre-booted, and one takes about 40 s to become ready.

What I do not know: the Cloud Hypervisor version and its full command line, whether guest memory is backed by huge pages or
shared, how the balloon is sized, how the host is configured, or how many of these a host runs.

TODO(final run), series `ch-muse`: Cloud Hypervisor at 2 vCPU and 8 GiB with the balloon on, pre-booted and kept up. It does not yet have
Muse's four-disk layout, only the one read-only root.

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

TODO(final run), series `ch-snapshot`, `ch-suspend` and `ch-oxroute`.

### Kata Containers

Kata runs each pod in its own VM and lets Kubernetes drive it, so it is the answer to "I want VMs but I want to keep my cluster".
I ran it through the real Kubernetes interface: `crictl` against containerd 2.4.1 with Kata 4.3.1, Cloud Hypervisor as the
VMM (v54.0), a 6.18.56 guest kernel, and the `python:3.13-slim` image, with the workspace shared into the guest over virtio-fs.

#### Vanilla

Kata's own defaults are a 2048 MiB guest, 1 vCPU, and no free page reporting. TODO(final run), series `kata-vanilla`, on the untouched defaults.

#### Optimized variant

Two changes to Kata's shipped Cloud Hypervisor config, made with `sed` so the diff from vanilla is exactly this:

```
sed -e 's/^default_memory = .*/default_memory = 256/' \
    -e 's/^reclaim_guest_freed_memory = false/reclaim_guest_freed_memory = true/' \
    configuration-clh.toml > kata-clh.toml
```

A 256 MiB guest like the Firecracker ones, and `reclaim_guest_freed_memory`, which turns on free page reporting. A pod per tenant with the
guest at 256 MiB and the reporting off holds 48 to 52 tenants (rough). Each pod costs about 154 MiB of host memory idle, because Kata boots a fresh
guest kernel and agent for every pod where Firecracker restores a shared snapshot. Pods deleted when idle (`kata-cold`) hold 48 as well, because every wake boots a VM.
With reporting on, a pod that allocated and freed 150 MB goes from 259 MiB to 161 MiB, and stays at 259 with it off. I also tried a 128 MiB guest, which was
worse (186 MiB a pod), and virtio-fs with no cache, which would not boot. TODO(final run) on the capacity with reporting on.

### gVisor

Not in the plan, but it is the other way people isolate hostile tenants, so I ran it: gVisor (`runsc`, release 20261019,
systrap platform) as a runtime in the same containerd. It has no VM and no guest kernel. A kept pod costs about 40 MiB of host
memory and boots in under 200 ms. It holds 192 tenants (two seeds) and runs out of cpu there. Deleting idle pods does not help,
because creating them costs more cpu than it saves: it holds 96. All rough.

### Firecracker Tricked Out

Three things on top of the naive config, each measured on its own.

1. **Restore from one shared snapshot.** The first VM is booted once and snapshotted with an empty workspace, and every tenant's
   VM is restored from that single file (memory mapped copy on write, the root image shared). A resident VM then holds only the
   pages it has touched, about 35 MiB, instead of its whole 256.

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
   a VM that allocated 120 MB and freed it went from 184 MiB back to 64 MiB in 3 seconds. It adds to the kept design (128 tenants
   to about 150) and does nothing for the released ones, which run out of cpu first.

```
PUT /balloon  {"amount_mib": 0, "deflate_on_oom": true, "free_page_reporting": true}
```
plus `page_reporting.page_reporting_order=3` on the guest command line.

| design (rough) | holds | what runs out |
|---|---|---|
| one VM each, kept up | 128 | memory |
| one VM each, kept up, with the balloon | about 150 | memory |
| one VM each, released after 5 s idle | 416 | cpu and disk |

The disk is real: the released design wrote 11 to 13 GiB of session snapshots at its limit.

## What a command costs in each tier

Before the routing part, here is what routing is choosing between. This is the same command run 60 times in each place, in a project of 300 small files, on the machine above.

| command | host, nothing around it | light sandbox | Firecracker, warm |
|---|---|---|---|
| `ls` | 4.7 ms | 6.5 ms | 11.6 ms (p95 22.6) |
| `cat` a file | 4.5 ms | 6.2 ms | 11.3 ms |
| `grep -rn` over 300 files | 5.0 ms | 7.2 ms | 13.4 ms (p95 27.1) |
| `find` and sort | 6.0 ms | 7.5 ms | 14.3 ms |
| `python3` start | 12.5 ms | 13.9 ms | 18.0 ms |
| `python3`, 85 ms of cpu | 84.0 ms | 85.7 ms | 89.7 ms |

The light sandbox is the file-only tier: bubblewrap builds a fresh set of namespaces for the command and a seccomp filter limits what it can ask the kernel. That adds about 1.7 ms.
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
A warm VM adds 6 to 7 ms. That is not the VM being slower at the work, since 85 ms of cpu inside it took 89.7 ms, about 5% more. It is the fixed price of getting a command in and out:
a vsock round trip, and a sync where the host walks the workspace and reports what changed before the command and the guest reports back after it. The spikes in the p95 are a sync with
something to carry. A wake, meaning a released VM restored from the shared snapshot and then running one command through the whole path, is about 95 ms.

So a command that only reads or searches files costs about twice as much in the VM as in the light tier, a few milliseconds either way. That is nothing for one command and it is the whole
story at 600 tenants, because those few milliseconds, the wakes behind them and the memory a resident VM holds are what the routing is trying not to pay.

## Past 600

Ok so this is all very cool but there's something that you are probably also starting to clue in on.

## Routing Graunlarity

Everytie

## Footnotes

[1] I believe sandboxes for RL may be different where they just run for long amoutns of time at full activity. This was focused more on agents involved with the real world (humans, other agents) where there is more latency and periods of inactivity than simulations.
