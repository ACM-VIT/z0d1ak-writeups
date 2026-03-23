# acidity

| Field      | Value |
|------------|-------|
| Category   | rev |
| Points     | 283 |
| Solves     | 28 |

## Description

<p>Author: <code>flocto</code></p><p>Make sure you brought your helmet.</p>

## Files

- [acidity.tar.gz](./acidity.tar.gz)

## Writeup

# acidity

Category: rev / misc  
Points at solve time: 347  
Flag: `gigem{RNG_m4nipul4t10n_ftw..._0r_ju5t_br1n6_4_sh0v3l}`

## Challenge setup

The attachment shipped a local ELF called `acidity`, a decoy `flag.txt`, and a helper script. The CTFd page itself did not advertise a remote service, but the provided helper script did:

```python
io = remote("streams.tamuctf.com", 443, ssl=True, sni="acidity")
```

That is straight from `solver-template.py`:

```python
5  io = remote("streams.tamuctf.com", 443, ssl=True, sni="acidity")
```

So the first important takeaway was:

1. The real challenge had a live remote.
2. The local binary was still useful for reversing and tooling.
3. The local `flag.txt` was almost certainly a decoy.

## What the game looks like

The program is a small platformer. You start near the top of a 35x25 board and every frame you get:

```text
Move: [a] left, [d] right, [w] jump, [q] quit
```

The goal tile is `F` at the bottom of the map. Naively this looks like a pathfinding challenge: get to `F`, read the flag, done.

That interpretation is wrong.

## Proving the win condition

Before spending time on map solving, I wanted to verify what actually happens when the player touches `F`.

I built a tiny preload patch in `force_win.c` that NOPs out the conditional branch after the `cmp` against `F`:

```c
28 __attribute__((constructor)) static void init(void) {
29     static const unsigned char nops[6] = {
30         0x90, 0x90, 0x90, 0x90, 0x90, 0x90,
31     };
32     dl_iterate_phdr(find_base_cb, NULL);
33     if (g_base == 0) {
34         return;
35     }
36     patch_bytes((void *)(g_base + 0x1cbde), nops, sizeof(nops));
37 }
```

With that patch loaded, the binary goes straight down the flag-print path and reads `flag.txt`. Locally, that file contained:

```text
gigem{local-test-flag}
```

So the control-flow question was answered:

1. Reaching `F` is the real win condition.
2. The packaged local flag is a decoy.
3. The real flag has to come from the remote.

## The first trap: this is not a fixed map

At first glance you might think the board is deterministic and all you need is a clean BFS over the frames.

That also turned out to be wrong.

The key clue was that different input bytes produced different terrain, even when the visible movement should have been the same. To study that cleanly, I built `hook_script.so` and a Python harness around it.

The important function is `next_scripted_value()` in `hook_script.c`:

```c
107 __attribute__((used)) uint32_t next_scripted_value(void) {
108     uint32_t out = 0;
109     if (script_bytes != NULL && frame_index < script_len) {
110         out = script_bytes[frame_index];
111     }
...
117     frame_index++;
118     return out;
119 }
```

The constructor patches four different input-consumption sites:

```c
246     resume_b06f = (void *)(g_base + 0xb07f);
247     resume_cb90 = (void *)(g_base + 0xcba0);
248     resume_d986 = (void *)(g_base + 0xd996);
249     resume_e9a4 = (void *)(g_base + 0xe9b4);
250     install_skip_hook((void *)(g_base + 0xb06f), hook_b06f, 16);
251     install_skip_hook((void *)(g_base + 0xcb90), hook_cb90, 16);
252     install_skip_hook((void *)(g_base + 0xd986), hook_d986, 16);
253     install_skip_hook((void *)(g_base + 0xe9a4), hook_e9a4, 16);
```

That mattered because the binary was not simply doing “one keypress equals one move.” It was consuming input in a repeating phase pattern, and some of those consumed bytes fed terrain/RNG logic rather than ordinary movement.

## The hidden consume before frame 1

`search_scripted.py` captures the first big modeling insight:

```python
49 def script_hex(actions):
50     # The binary consumes one "current input" before the first visible frame.
51     seq = [""] + actions
52     return "".join("00" if a == "" else f"{ord(a):02x}" for a in seq)
```

There is one hidden consume before the first visible frame. If you do not account for that, every later byte is shifted and the board evolution stops matching reality.

The script also encodes the terrain-byte positions:

```python
126 def insertion_indices(frames):
127     return list(range(2, frames, 4))
```

So once the hidden consume is handled, the interesting bytes land every 4 frames, starting at logical index 2 in the scripted environment.

This is the heart of the challenge:

1. Some frames are normal gameplay frames.
2. Some frames are actually “terrain mutation” frames.
3. The same byte stream drives both.

## Building an offline model

I split the problem into two layers.

### 1. Terrain-byte search

`search_scripted.py` builds a terrain-only action array and merges it with ordinary movement:

```python
130 def terrain_actions_from_genome(genome, frames):
131     actions = [""] * frames
132     for idx, byte in zip(insertion_indices(frames), genome):
133         actions[idx] = byte_action(byte)
134     return actions

137 def merge_actions(terrain_actions, full_action_bytes):
138     ins = set(insertion_indices(len(terrain_actions)))
139     out = terrain_actions[:]
140     for i, value in enumerate(full_action_bytes):
141         if i >= len(out) or i in ins:
142             continue
143         out[i] = byte_action(value)
144     return out
```

This let me ask: “If I choose bytes X, Y, Z on the mutation frames, what board sequence do I get?”

### 2. Exact movement solver

A rough gravity model was not enough, so I wrote `search_exact.py` to match the real movement more closely.

The exact step function keeps track of:

- player position
- jump phase
- falling velocity
- the pending input that gets applied on the next frame

```python
19 @dataclass(frozen=True)
20 class ExactState:
21     x: int
22     y: int
23     jump_idx: int
24     fall_v: int
25     pending: str
```

And the simulator applies the real jump arc:

```python
16 JUMP_SEQ = (-2, -1, 0, 1, 2)
...
49 def exact_step(board_next, state: ExactState, next_pending: str):
...
55     dx = -1 if pending == "a" else 1 if pending == "d" else 0
...
62     if jump_idx >= 0:
63         delta = JUMP_SEQ[jump_idx]
...
66     elif pending == "w" and grounded:
67         delta = JUMP_SEQ[0]
```

`evaluate_mods()` then explores all legal movement choices on non-mutation frames while keeping the terrain bytes fixed:

```python
115 def evaluate_mods(mods, frames=103):
...
140     for t in range(len(boards) - 1):
141         nxt = {}
142         choices = [terrain_actions[t]] if t in ins else SEARCH_ACTIONS
...
147                 if acid.board_char(raw[t + 1], ns.x, ns.y) == "F":
148                     return {
149                         "found": True,
```

At this point I had a real workflow:

1. Choose mutation bytes.
2. Capture the resulting board sequence offline.
3. Run an exact search for the best movement path through those boards.

## What the search found

This search did not find a complete win immediately, but it did get very close.

The best branch I had for a long time was this mutation set in the exact/hooked environment:

```text
10=d5, 34=69, 38=ef, 42=88, 50=b1, 54=e1
```

That branch consistently got the player into the flag pocket, but still not onto `F`.

I also saved a live transcript of the best near-win run in `remote_best_offset_minus2.txt`. The end of that transcript clearly shows the problem:

```text
####.###########.###..########.####
################@##################
###################################
###################################
#################F#################
```

The solver was reaching the pocket but still landing one tile short.

This is why the challenge felt miserable for so long: once the model is “almost right,” the remaining error is not obvious. You are not debugging a giant failure. You are debugging one wrong late-game step.

## Why the exact solver still missed the solve

The offline tools were accurate enough to find the correct family of terrain bytes, but not accurate enough to finish the live run.

The missing piece was terminal behavior.

I ended up with three different environments:

1. `LocalGame` in `solve.py`, which talks to the process over plain pipes.
2. `PtyGame` in `pty_probe.py`, which runs the binary under a pseudo-terminal.
3. `RemoteGame` in `pty_probe.py`, which talks to the real TLS service.

Those paths do not behave identically.

Relevant code from `pty_probe.py`:

```python
41 class PtyGame:
...
52         self.proc = subprocess.Popen(
53             ["docker", "exec", "-it", self.container, "./acidity"],
54             stdin=slave,
55             stdout=slave,
56             stderr=slave,
57             close_fds=True,
58         )
```

```python
98 class RemoteGame:
99     def __init__(self, host: str, port: int, sni: str):
...
108         ctx = ssl._create_unverified_context()
109         raw = socket.create_connection((self.host, self.port))
110         self.sock = ctx.wrap_socket(raw, server_hostname=self.sni)
```

Once I had the near-win terrain schedule, I stopped trusting the exact solver for the last move and started probing PTY and remote runs directly.

That was the correct pivot.

## The final step

The accepted solve came from treating the exact solver’s best branch as a seed, then probing late-game suffix inputs directly against the PTY/remote path.

The important insight was:

1. The terrain-byte branch was already good enough.
2. The offline exact model still missed a terminal-sensitive late input.
3. The last fix was not “find a whole new map.”
4. The last fix was “find the one live suffix move the offline model is still missing.”

The solving notes for the accepted run recorded the winning remote byte schedule as:

```text
9:0xd5, 33:0x69, 37:0xef, 41:0x88, 49:0xb1, 53:0xe1, 94:a, 100:d
```

The exact solver had already found the terrain part of that structure. The live probing added the crucial late `d`.

One practical note: the last step was sensitive to PTY/remote behavior, which is exactly why I had to use `pty_probe.py` instead of trusting the pipe-based offline model. So I treat the accepted schedule above as the solving note for the successful run, not as a promise that every stripped-down harness will replay it identically without the same terminal semantics.

This also matches the challenge theme and the final flag: the solve was about manipulating the board-generation / RNG path with carefully placed raw bytes, not about platforming skill.

## Submission and verification

The final flag was:

```text
gigem{RNG_m4nipul4t10n_ftw..._0r_ju5t_br1n6_4_sh0v3l}
```

## TL;DR

The intended difficulty was not “beat a hard platformer.” It was:

1. Notice the hidden remote in the attachment.
2. Verify that touching `F` really prints `flag.txt`.
3. Notice that input bytes affect terrain generation.
4. Model the hidden pre-frame consume and the repeating mutation slots.
5. Build an offline searcher to find promising terrain-byte schedules.
6. Stop trusting the pipe-based exact model for the very last step.
7. Probe PTY / remote behavior directly to recover the final live suffix.

That is why the flag is:

```text
gigem{RNG_m4nipul4t10n_ftw..._0r_ju5t_br1n6_4_sh0v3l}
```

## Files I used

- [solver-template.py](./extracted/solver-template.py): hidden remote endpoint
- [force_win.c](./artifacts/force_win.c): patch confirming the `F -> flag.txt` control path
- [hook_script.c](./artifacts/hook_script.c): input-hooking and scripted-byte injection
- [search_scripted.py](./artifacts/search_scripted.py): terrain-byte schedule model
- [search_exact.py](./artifacts/search_exact.py): exact-ish movement solver
- [pty_probe.py](./artifacts/pty_probe.py): PTY and remote probing harness
- [remote_best_offset_minus2.txt](./artifacts/remote_best_offset_minus2.txt): saved near-win remote transcript



