import base64
import codecs

# Can you find the flag?
# Hint: sometimes things aren't what they appear to be...

_phantom = "dHZ0cnp7dHUwZmdfMWFfZ3UzX2Z1M3l5fQ=="

def reveal():
    step1 = base64.b64decode(_phantom).decode()
    step2 = codecs.decode(step1, "rot13")
    return step2

if __name__ == "__main__":
    print("Nothing to see here...")
