# 700 agent sandboxes on a 7GB PC

![736 tenants on a 7 GiB laptop, replayed from real agent sessions at 8x](/img/virt-timelapse.gif)

Recently I got a new computer<abbr title="by this i mean someone i know upgraded and i gladly nabbed it">*</abbr> so in continuity with my [other](https://rohanadwankar.github.io/posts/platforms.html) [posts](https://rohanadwankar.github.io/posts/sandbox2.html) on sandboxs I figured we should take a look at how many agent sandboxes we can fit to get an intuition on what these agents sandboxes look like.

Here's the computer we will be playing with!
<pre class="fastfetch"><code class="nohighlight">rohan@oxroute:~$ fastfetch
<span class="c31">                             ....</span>              <span class="c31">rohan</span>@<span class="c31">oxroute</span>
<span class="c31">              .&#x27;,:clooo:  .:looooo:.</span>           -------------
<span class="c31">           .;looooooooc  .oooooooooo&#x27;</span>          <span class="c31">OS</span>: Ubuntu 26.04.1 LTS (Resolute4
<span class="c31">        .;looooool:,&#x27;&#x27;.  :ooooooooooc</span>          <span class="c31">Host</span>: 81X8 (IdeaPad 3 15ITL05)
<span class="c31">       ;looool;.         &#x27;oooooooooo,</span>          <span class="c31">Kernel</span>: Linux 7.0.0-38-generic
<span class="c31">      ;clool&#x27;             .cooooooc.  ,,</span>       <span class="c31">Uptime</span>: 2 days, 10 hours, 39 mins
<span class="c31">         ...                ......  .:oo,</span>      <span class="c31">Packages</span>: 1304 (dpkg), 3 (snap)
<span class="c31">  .;clol:,.                        .loooo&#x27;</span>     <span class="c31">Shell</span>: bash 5.3.9
<span class="c31"> :ooooooooo,                        &#x27;ooool</span>     <span class="c31">Display (BOE0816)</span>: 1366x768 in 1]
<span class="c31">&#x27;ooooooooooo.                        loooo.</span>    <span class="c31">Terminal</span>: /dev/pts/0
<span class="c31">&#x27;ooooooooool                         coooo.</span>    <span class="c31">CPU</span>: 11th Gen Intel(R) Core(TM) z
<span class="c31"> ,loooooooc.                        .loooo.</span>    <span class="c31">GPU</span>: Intel UHD Graphics G4 @ 1.2]
<span class="c31">   .,;;;&#x27;.                          ;ooooc</span>     <span class="c31">Memory</span>: 1.18 GiB / 7.05 GiB (17%)
<span class="c31">       ...                         ,ooool.</span>     <span class="c31">Swap</span>: 794.90 MiB / 4.00 GiB (19%)
<span class="c31">    .cooooc.              ..&#x27;,,&#x27;.  .cooo.</span>      <span class="c31">Disk (/)</span>: 54.40 GiB / 97.87 GiB 4
<span class="c31">      ;ooooo:.           ;oooooooc.  :l.</span>       <span class="c31">Local IP (wlp0s20f3)</span>: 10.0.0.10/4
<span class="c31">       .coooooc,..      coooooooooo.</span>           <span class="c31">Battery (L16M2PB2)</span>: 97% [AC Conn]
<span class="c31">         .:ooooooolc:. .ooooooooooo&#x27;</span>           <span class="c31">Locale</span>: en_US.UTF-8
<span class="c31">           .&#x27;:loooooo;  ,oooooooooc</span>
<span class="c31">               ..&#x27;;::c&#x27;  .;loooo:&#x27;</span>

rohan@oxroute:~$
</code></pre>


For some background on why this is interesting, agent sandboxes are a quickly growing area of interest beccause AI agent require environments to operate it.

Since we have seen a steady increase in the capability of agents to work over longer periods of time we would expect that the amount of compute dedicated to agent sandboxes would increase accordingly.

This growth is so exciting that many believe that in the near future when everyone has consumer agents running roughly 24/7 we don't have enough CPUs to even host that level of [comptue](https://x.com/MTSlive/status/2112699475894669358) experts have even claimed

So clearly it is worthwhile to see what these sandboxes are and what optimizations we can apply.

## Defining the Game 

For this to be useful/educational we need to have a benchmark which roughly reflects agent behavior.

So to start I recorded 26 real [opencode](https://opencode.ai) agent sessions where the agent is doing things like explaining a repo, fixing a failing test, adding a command line entry point, etc.).
You can find these session files [here](https://github.com/RohanAdwankar/sandroute/tree/main/bench/traces)

A simulated tenant alternates between being away (long-tailed, mean two minutes) and handing the agent a task to replicate the user behavior of periodically checking your phone and texting muse.
When it has a task it picks a recorded session at random, copies the starting project into its workspace and replays the calls with their recorded think times.
Tenants are mid-task about 24% of the time, which is my relatively arbitary but nor unreasonable guess for their activity.

Every design gets the same tenants, because the random choices come from a seed.
A run is six minutes.
A design **passes** at N tenants if the p99 of the latency it *adds* to a call stays under 1.5 seconds, with no errors and no out-of-memory abort. "Added" is a call's time less the time the same call takes with one tenant on the machine (helpful for example for commands that simply sleep).
Each count runs on two seeds, and a design **holds** N if both pass.

## Level 1: Cold Boots 

Let's start off with a standard Firecracker MicroVM.

```
PUT /boot-source     {"kernel_image_path": "vmlinux-6.1.128",
                      "boot_args": "console=ttyS0 reboot=k panic=1 pci=off sandroute.workspace=/work sandroute.port=5000"}
PUT /drives/rootfs   {"path_on_host": "rootfs.ext4", "is_root_device": true, "is_read_only": true}
PUT /machine-config  {"vcpu_count": 1, "mem_size_mib": 256}
PUT /vsock           {"guest_cid": 3, "uds_path": "v.sock"}
PUT /actions         {"action_type": "InstanceStart"}
```

Boot one per tenant without never turning them off.

This gets us to ~48 tenants with the machine running out of memory at 64.

Each VM costs about 113 MiB of host memory even when it does nothing, almost half of the 256 MiB it was given, because the guest kernel and the agent touch most of what they have.

The latency is excellent (p99 of 20 ms) because every VM is already there.

So next since we are limited by memory, we can start optimize out that.

![48 tenants, each in its own VM that stays up. Memory is already at 3.6 GiB.](/img/virt-level1.gif)

## Level 2: Idle Killing

Most tenants are idle most of the time, so don't keep their VMs.

After 30 seconds without a command, kill the VM, and boot a fresh one on the next command.

Then when a new message is sent the VM boots again and the disk reattaches.

This tactic allows use to grow from 48 to 64 tenants, and at 96 the machine runs out of memory.

One downside is that now about 1 call in 11 wakes a VM, and a cold boot of a guest kernel costs 1.2 seconds, so the p99 sits at 1.2 s even with only 64 tenants.

![64 tenants. Idle VMs are killed, and each tenant's next command waits for a cold boot.](/img/virt-level2.gif)

## Level 3: Snapshots 

Booting is the expensive, and most boots are doing the same work.

So now we can boot one VM, wait for the agent to come up, pause it, and write out its memory.

Every tenant's VM is then restored from that single file with the memory mapped copy on write, so a VM only holds the pages it has changed.

```
# once: boot a VM, wait for the agent, then
PATCH /vm               {"state": "Paused"}
PUT   /snapshot/create  {"snapshot_type": "Full", "snapshot_path": "pristine.snap", "mem_file_path": "pristine.mem"}

# per tenant, on a fresh firecracker process, instead of the boot calls above:
PUT   /snapshot/load    {"snapshot_path": "pristine.snap",
                         "mem_backend": {"backend_type": "File", "backend_path": "pristine.mem"},
                         "resume_vm": true}
```

Two things have to be true for this to work.

The root drive must be read-only, because restoring over an image another VM has since written corrupts the filesystem (the restored guest's cached ext4 metadata no longer matches the disk).

And the snapshot has to be taken *while the workspace is empty*, because the host owns the workspace and pushes it in on every wake.

One more trick, whatever sits in the guest's page cache when the snapshot is taken is shared by every VM restored from it, so the init script imports Python's common standard library before the snapshot.
A wake that runs `python3 -m unittest` then costs 161 ms of cpu instead of 530.

This boost us a ton up to 176 tenants at about 27 MiB each instead of 113.

Since these restore in tens of milliseconds, a VM is cheap enough to restore on demand, so now bring back Level 2's killing: release a VM after a short idle window and restore the shared snapshot on the next command.
A window of 5 seconds turned out to be best.

The question is what to do with the VM when you release it.
The naive answer is to snapshot its memory to disk so it can resume exactly.
That works, and it cost me: at about 400 tenants the machine was writing 11 to 13 GiB of session snapshots and running out of disk bandwidth.

The better answer is that most guests hold nothing worth saving.
The workspace is on the host and gets pushed back in.
If the guest also holds nothing outside the workspace and `/tmp`, the VM can simply be killed, and the next wake restores the shared snapshot, with no disk written at all:

Two details made that work.
`/tmp` is a second synced area, kept on the host while the guest is gone, so a test run that writes scratch files doesn't make the guest look dirty.
And a guest that really did install something (a `pip install`, say) keeps its snapshot, in two alternating slots so a failed write never destroys the last good one.

**640 tenants**, from 176, and the machine now runs out of *cpu* and not memory.
Resident VMs at the peak are 228, each costing about 8 MiB.
The tail is where the cost is: a woken call takes a median of 115 ms and the p99 for all calls is 1.3 s, because 640 tenants produced 4,590 wakes in a six minute run.

![576 tenants, shown below its limit of 640 because recording the run adds load. VMs come and go as tenants start and stop turns.](/img/virt-level3.gif)

## Level 4: Routing 

Thus far we have optimizing by configuring the VM but lets do some out of the box thinking (obligatory[this should be a hyperlink which when clicked plays the budum tiss sound for a pun]) and see how we can offload the neccesity of the VM.

Looking at what the agents are running, 224 of 304 recorded calls (74%) never needed a real comptuer they are the file tools (`read`, `edit`, `write`, `glob`, `grep`), and shell commands like `ls`, `cat` and `sed`.

Only 80 of the 136 shell commands ran code, and 8 of the 26 sessions never needed a VM once.

Thinking back to how people use agents this makes a lot of sense.
Even though there are spurts of activity when actually programming which require a VM (eg. browser use, compilation) for a large segement of operations the agent just needs to read parts of their codebase / memory files and retrieve the asnwer.

Therefore if we can selectively route querires ligher sandbox we can satisfy agent requests in then we can increase the percentage of commands which dont require rewaking the VM.
This routing system was the intuion behind oxroute[add link].
In this case for the light sandbox I chose [bubblewrap](https://github.com/containers/bubblewrap) plus a seccomp filter, with no VM:

```
bwrap --unshare-all --unshare-user --disable-userns --cap-drop ALL --seccomp 3 \
      --die-with-parent --new-session --clearenv \
      --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
      --proc /proc --dev /dev --tmpfs /tmp \
      --bind $WORKSPACE /work --chdir /work \
      bash -c "$COMMAND"
```

The only writable things are the tenant's workspace and a private `/tmp`; there is no network namespace to join and the filter has no socket calls.
The filter is the Docker default profile's 299 allowed calls, with `clone3` answered "not implemented" and `clone` with any namespace flag refused.
A command costs about 6 ms, against 2.4 ms bare and 7.5 ms in a warm VM.
The light tier also does something nice, its cost does not grow with the host process.
The orchestrator starts each command with `posix_spawn` and not `fork`, because a fork copies the parent's page tables, and with hundreds of tenants the parent is hundreds of megabytes.
A command costs about 6ms whatever the size of the host process.

This routing approach generates a 100 tenant boost up to 736 tenants.
This is great but perhaps a smaller boost then you may expect due to the profile of the benchmark workload.
Compare the two designs at the point where each one stops passing.
Level 3 (restoring a VM on every command that needs one) handles 640 tenants, who make 19,353 calls in a six minute run and wakes a VM 4,590 times, using 51% of the cpu on average.
Level 4 (running file commands outside a VM) handles 736 tenants, who make 22,328 calls and wake a VM only 1,777 times, using 43% of the cpu.
Routing removed most of the wakes.
But the tenant limit is set by bursts, not the average.
When many tenants start a turn at the same moment, there are more wakes and Python test runs than the four cpu threads can run at once, so some calls wait their turn, and the p99 passes 1.5 seconds while the machine is half idle.
The 26% of calls that still need a VM, mostly `python3`, are real work that no design avoids at the peaks, but depending on the profile of the peaking the tenant gains could be seen as more or less.

![736 tenants on a 7 GiB laptop, replayed from real agent sessions at 8x](/img/virt-timelapse.gif)

![Each step, and what it bought](/img/virt-ladder.png)

![Latency added to a call at each level's limit](/img/virt-latency.png)

## Try it yourself

Here is the script to start 100 sandboxes in sandroute:

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

It is `examples/hundred.rs` in the [repo](https://github.com/RohanAdwankar/sandroute), and you run it with `cargo run --release --example hundred 100` once the VM image is built.
The `close()` is explicit because Rust cannot await in a destructor.

To see the L4 speed benefit you can run the equivalent with [microsandbox](https://github.com/superradcompany/microsandbox):

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

Sandroute would normally run a `cat` in the light sandbox, so the second row reads the file with Python, which it does not route to the light sandbox, to make sure the read runs in a microVM like microsandbox's does.
Microsandbox boots a fresh microVM for every sandbox, with nothing shared between them.

That takes 8.6 s for a hundred and holds 4.6 GiB, which is where the 100 or so a 7 GiB laptop can hold comes from.
Sandroute restores every VM from one shared snapshot, so a hundred take 2.0 s and 242 MiB, and a command that only touches files does not need a VM at all.

Past a hundred, the sandroute version keeps going, while at 110 microsandbox starts failing.

| sandboxes | the read runs in | time | host memory used |
|---|---|---|---|
| 700 | the light sandbox (`cat`) | 5.4 s | 589 MiB |
| 700 | a microVM (`python3`) | 18.5 s | 3.1 GiB |


![130 sandboxes started at once, microsandbox next to sandroute](/img/virt-exhaustion.gif)

Microsandbox starts all of its VMs at the same moment here, which is what the job asks for, and a smaller number would work if they were started a few at a time.

## What is left

The next step is the 26% of calls that still need a VM.
Most of them are `python3`, and running Python in the light tier would be the biggest remaining win, but it widens the kernel surface a hostile tenant can reach (a script can make any allowed system call) and a script that needs the network or `pip` would fail without telling anyone, so I have not done it.
After that: a cheaper wake (about 110 ms of cpu today), a limit on how many VMs restore at once so a burst of turns doesn't thrash four threads, and a predictor that wakes a VM only for turns that will need one.

Ideas I tried or have not tried yet:

- **A balloon with free page reporting**, the technique Muse is described to use.
  A guest that allocated and freed 120 MB went from 184 MiB back to 64 MiB in three seconds.
  In an earlier rough run it took the kept-up design from 128 tenants to about 150, and it had minimal impact on the released designs, which run out of cpu first.
  A balloon pays off most for long running agents, whose VMs stay up and keep freed memory they never hand back, and these tenants are mostly idle with VMs that are released within seconds.
  For a more diverse set of workloads with longer running agents it could be worth turning on.
- **Telling the sandbox when a turn ends** lets it release the VM at once, instead of waiting out the idle window.
  In an earlier rough run that halved the number of resident VMs.
  It needs a harness that can say when a turn ends, so it is not in the numbers above.
- **Telling it when a turn starts** so the VM wakes during the model's thinking time.
  A blind prewarm cost more cpu than it saved, because a third of the sessions never need a VM.
  It would need a predictor.
- **Other designs, untuned.** The same replay, run against designs from other systems as they come, without the optimizations above: Kata Containers (a VM per pod, driven through Kubernetes) holds 40 tenants, gVisor with pods deleted when idle holds 80 (192 kept up, in an earlier rough run), and a Cloud Hypervisor VM at the size Muse is described to use, 2 vCPU and 8 GiB with a balloon, holds 16.
  Those are not slower designs.
  They are designs for tenants that hold state: an always-on VM that keeps its working set is a good deal for a personal agent, and the wrong one for a machine full of mostly idle coding sessions.
  These numbers show what the optimizations are worth more than what the hypervisors are worth, since only Firecracker got them; running the same steps on another hypervisor would be the fair comparison.


The code and every raw result are in the [sandroute repo](https://github.com/RohanAdwankar/sandroute).
