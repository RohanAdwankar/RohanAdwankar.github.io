# intuition through destruction

A common sentiment when I talk to people is that engineering with agents just feels so... not like engineering.
It feels very wishy washy where sure there are cool techniques but it's very hard to get an intuition on how much the different pieces matter.
This matter is made worse by the fact that every couple weeks all the ideas change.
So back to when learning other systems lets start ripping out components and seeing how our perf changes.

Let's begin with choosing an agent.

The most popular open source one seems to be openclaw so that may be a good choice.

It was where a lot of different techniques were popularized, and you can clearly see the influence in style to how proprietary harnesses work.

```
<show the muse sandbox content vs openclaw sandbox contents>
```

So lets take a look at the repo.

```
 % git clone https://github.com/openclaw/openclaw.git
Cloning into 'openclaw'...
remote: Enumerating objects: 2118623, done.
remote: Counting objects: 100% (4606/4606), done.
remote: Compressing objects: 100% (1760/1760), done.
fatal: write error: No space left on device.66 GiB | 35.27 MiB/s
fatal: fetch-pack: invalid index-pack output
```

Actually on second thought maybe its not in the cards. <footnote>[just being tongue in cheek here, I use openclaw at work so I'm just choosing something else I haven't used so its more entertaining]

The thing is that if you look at the internals of the agent we see a lot of calls are to a library called pi-agent-core.

So it may be easier to spin out on that instead.

```
pi % git ls-files | xargs cat | wc -l
  483642
pi % ls packages
agent  ai  chord  client  codemode  coding-agent  durable  env
evals  mcp  protocol  server  telemetry  tui
```

Ok cool half a million lines is going to be a lot easier to proceed from than 10M+ but still a tad too much to read for an afternoon so like any other system lets start stripping out the things which dont move the needle on the core perf <footnote>[to be clear here I'm not saying that it is necessarily unreasonable, this is just for learning purposes].

## An Aside on Evals

Now like I mentioned our goal here is from a system programming perspective to get an intuition on what moves the perf.

One of the harder things about evals for agents is that theres a lot of moving parts so its basically impossible to have an eval that is all 3 of: comprehensive (evaluates all the features), fast (I can test the impact of removing a part), and cheap (without spending too much to evaluate).

For the purpose of this experiment I'll be using the terminal bench released solutions and Nemotron Ultra since its the best one free on OpenRouter.

## Cutting

So out with all the skill files, nix configuration things, tui, evals, telemetry, and most of the stuff in the repo aside from the core.

```
<the diff of cutting these things>
```

And to baseline our approach lets see what that did:

```
<result of running the benchmark>
```

## Cutting more

TODO: not run yet. Each round below needs a line count and a benchmark score.

| Round | What was cut | Lines | Pass rate |
|---|---|---|---|
| 0 | full repo | 483642 | TODO |
| 1 | skills, nix, tui, evals, telemetry | TODO | TODO |
| 2 | TODO | TODO | TODO |
| 3 | TODO | under 10000 | TODO |

## What moved the needle

TODO: write after the numbers exist.
