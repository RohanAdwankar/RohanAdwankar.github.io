# An eBPF Sandbox Offloader

Idea: run an agent's function inside a sandbox, then move it to a faster state when it is safe to do so.

## The problem

A sandbox is slow because every call crosses a boundary.
Syscalls get filtered, copied and logged.
Most functions an agent runs are pure and small.
Those functions do not need the full boundary on every call.

## The idea

Take a function and watch what it does in the sandbox.
If it only touches memory it owns, it is safe to run faster.
Offload it to a cheaper state, such as in-kernel eBPF or a warm snapshot.
If it ever does something unexpected, fall back to the full sandbox.

## Design sketch

1. Wrap a function so its calls go through a small runner.
2. Trace its syscalls with eBPF tracepoints during the first runs.
3. Build a profile of allowed syscalls and memory use.
4. Once the profile is stable, load an eBPF program that enforces it.
5. Run later calls on the fast path with the profile enforced.
6. On any violation, kill the call and rerun it in the full sandbox.

## Open questions

What counts as a safe function?
How many traced runs make a profile trustworthy?
Can eBPF alone run the function, or does it only enforce the profile?
How much faster is the fast path in practice?

## Next steps

Pick a language for the runner.
Write a tracer with one tracepoint.
Measure the cost of the full sandbox on a trivial function.
