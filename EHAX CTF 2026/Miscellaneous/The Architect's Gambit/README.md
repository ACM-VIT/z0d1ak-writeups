# The Architect's Gambit

| Field      | Value |
|------------|-------|
| Category   | Miscellaneous |
| Points     | 475 |
| Solves     | 37 |

## Description

`author:CyC`

The Architect has constructed a game of impossible Nim - where the rules bend under incomprehensible mechanics and the game state hides behind ciphers. Standard theory won't save you. Only those who master both decryption and combinatorial analysis may prevail.

You must win a series of Nim rounds against The Architect's engine.

`nc 20.244.7.184 41337`

Clarification on Answer Binding Format: For those writing solvers, the HMAC formula uses colons for concatenation, a 0-based round index, and takes the first 8 hex characters: msg = f"{session_nonce}:{round_idx}:{answer}" (everything is ASCII, no raw hex bytes are decoded).

## Writeup

### Flag

```text
EH4X{4rch173c7s_g4mb17_cryp70_n1m_w4rf4r3}
```

### Executive Summary

This challenge is a 10-round Nim variant split into three phases. Rounds 1-7 require decrypting hidden pile states and returning authenticated answers. Rounds 8-10 are interactive commit/reveal rounds. The solve path is:

1. Solve PoW.
2. Recover each round state (AES-ECB in phase 1, AES-CBC in phase 2).
3. Run a game solver on the decoded piles.
4. Send answers with the exact HMAC binding format.
5. For phase 3, use `PLAY`, read revealed `STATE`, and iteratively send winning commit/reveal moves.

### Vulnerability Analysis

The challenge combines cryptographic wrappers with a deterministic impartial game:

- The game state is recoverable every round if decryption and parsing are done correctly.
- The answer-binding HMAC is strict about formatting and indexing; many wrong solves fail here.
- In phase 3, the service reveals plaintext state after `PLAY`, so no oracle break is needed.

Critical correctness details:

- Round index is 0-based in the HMAC message.
- HMAC message format is exactly `session_nonce:round_idx:answer`.
- Illegal moves are those that do not reduce total stones.
- Drain destination updates must be saturating (`min(MAX_VAL, current + drain)`).

### Exploit Strategy

Use DFS + memoization over game states to classify winning/losing positions.

Transition model:

- Choose pile `i`, remove `k` where `1 <= k <= min(limit, pile[i])`.
- Add drained value to destination pile:
  - Phase 1: `drain = floor(k/2)`
  - Phase 2/3: `drain = gf256_mul(k, weight) % k`
- Reject transitions that do not decrease total stones.

A state is winning if at least one legal move reaches a losing state.

### Implementation

Protocol handling by phase:

1. **PoW**: find nonce such that `SHA256(prefix + nonce)` starts with required zeros.
2. **Phase 1 (rounds 1-3)**:
   - Decrypt `ENCRYPTED_PILES` with given AES-ECB key.
   - Parse pile values and solve.
   - Send `WIN`/`LOSE` answer with HMAC suffix.
3. **Phase 2 (rounds 4-7)**:
   - Parse `ENCODED_PILES` as `IV:CT`.
   - Derive key as `SHA256(f"{session_nonce}:{round_idx}")[:16]`.
   - Validate using `KEY_CHECK`, decrypt AES-CBC, solve, respond with HMAC.
4. **Phase 3 (rounds 8-10)**:
   - Send `PLAY`.
   - Parse `STATE: [...]`.
   - For each move: compute winning move, commit with `sha256(f"{pile},{take},{nonce}")`, then `REVEAL`.

### Execution & Results

The full automation consistently cleared all 10 rounds and printed the final flag.

