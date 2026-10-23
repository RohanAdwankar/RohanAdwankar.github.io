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

My first instinct was to start with e2b but it recommends 4+ cores and 8GB minimum RAM so my old boy is disqualified on both counts. [https://github.com/e2b-dev/runtime/blob/main/DEV-LOCAL.md]

So lets proceed with the others and toss in Kata containers for the k8s fans.

### Naaive Firecracker

### Cloud Hypervisor

### Kata Containers

### Firecracker Tricked Out 

## Past 600

Ok so this is all very cool but there's something that you are probably also starting to clue in on.

## Routing Graunlarity

Everytie

## Footnotes

[1] I believe sandboxes for RL may be different where they just run for long amoutns of time at full activity. This was focused more on agents involved with the real world (humans, other agents) where there is more latency and periods of inactivity than simulations.
