# Half Dust Half Deity

| Field    | Value  |
| -------- | ------ |
| Category | Stegno |
| Points   | 250    |
| Solves   | 53     |

## Description

A poet once said we are two things at once, the ground beneath our feet and the sky above our heads. They left this poem behind as proof.
Read every word. Then read between them.

flag format: hackzero{}

## Files

- [poetry.txt](./poetry.txt)

## Writeup

i read the poem once normally and nothing obvious popped out so that usually means the text itself is just a cover

then i noticed weird invisible unicode stuff between words not normal spaces so i dumped the file and checked the hidden chars there were 5 repeating codepoints u200b u200d u202a u202d u2063

after that the pattern made sense because the hidden chars were coming in blocks of 7 and since ascii fits inside 5^7 i treated each 7 char block like a base 5 number

i mapped them as
u200b = 0
u200d = 1
u202a = 2
u202d = 3
u2063 = 4

decoding all the blocks gave

Where am I

and then the actual flag

### Flag

```
flag: hackzero{9e82e9e902fb1b437230df2e66586433}
```
