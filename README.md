# helix

**helix**, also known as **dna**, is a programming language based on dna. it uses only the characters `A`, `C`, `G`, and `T` for instructions, making source code resemble a dna sequence.

helix is a small, stack-based language similar to assembly. programs are made from 3-character instructions called **codons**.

function and package support are planned for future versions.

---

# how to code in helix

each instruction in helix is exactly **3 characters** long and can contain only:

```text
A C G T
```

instructions can be placed next to each other with spaces:

```text
AGT AAC CAA TAC
```

comments begin with `;` and continue until the end of the line:

```text
; this is a comment
AGT AAC CAA TAC
```

you can also use comments to explain individual instructions:

```text
AGT ; push 64
AAC ; push 1
CAA ; add
TAC ; print character
```

---

# the stack

helix uses a **stack** to store values.

values are pushed onto the stack using literal instructions:

```text
AAC
```

this pushes `1`:

```text
[1]
```

another value can then be pushed:

```text
AAC AAG
```

result:

```text
[1, 2]
```

operators generally consume values from the top of the stack and push their result back.

for example:

```text
AAC AAG CAA
```

means:

```text
push 1
push 2
add
```

result:

```text
[3]
```

the notation `a b → result` means that `a` and `b` are consumed from the stack and replaced with `result`.

---

# instructions

## A__ - literals

these instructions push constant values onto the stack.

```text
AAA  PUSH0     push 0
AAC  PUSH1     push 1
AAG  PUSH2     push 2
AAT  PUSH3     push 3
ACA  PUSH4     push 4
ACC  PUSH5     push 5
ACG  PUSH6     push 6
ACT  PUSH7     push 7
AGA  PUSH8     push 8
AGC  PUSH16    push 16
AGG  PUSH32    push 32
AGT  PUSH64    push 64
ATA  PUSH128   push 128
ATC  PUSH256   push 256
ATG  PUSHn1    push -1
ATT  PUSHn2    push -2
```

these are useful for constructing larger numbers with arithmetic:

```text
AGT AGC CAA
```

pushes `64`, pushes `16`, then adds them:

```text
80
```

---

# C__ - arithmetic

arithmetic instructions operate on values at the top of the stack.

```text
CAA  ADD       a b → a + b
CAC  SUB       a b → a - b
CAG  MUL       a b → a * b
CAT  DIV       a b → a ÷ b
CCA  MOD       a b → a mod b
CCC  NEG       a → -a
CCG  ABS       a → |a|
CCT  INC       a → a + 1
CGA  DEC       a → a - 1
CGC  POW       a b → a ^ b
CGG  SQT       a → √a
CGT  AND       a b → a & b
CTA  ORR       a b → a | b
CTC  XOR       a b → a ^ b
CTG  NOT       a → ~a
CTT  LSH       a b → a << b
```

division is integer division.

example:

```text
AGC AAG CAA
```

results in:

```text
18
```

---

# G__ - stack and flow control

these instructions manipulate the stack or control program execution.

```text
GAA  DUP       duplicate top value
GAC  POP       discard top value
GAG  SWP       swap top two values
GAT  OVR       copy 2nd over top
GCA  ROT       rotate top three values

GCC  NOP       no operation

GCG  JMP       jump to label
GCT  JEZ       jump if top == 0
GGA  JNZ       jump if top != 0
GGC  JGZ       jump if top > 0
GGG  JLZ       jump if top < 0

GGT  CAL       call subroutine
GTA  RET       return from subroutine

GTC  HLT       halt program

GTG  NOP2      no operation
GTT  NOP3      no operation
```

## stack manipulation

### DUP

```text
AAC GAA
```

stack:

```text
[1]
```

after `GAA`:

```text
[1, 1]
```

### POP

```text
AAC GAC
```

the `1` is discarded, leaving an empty stack.

### SWP

if the stack is:

```text
[1, 2]
```

then:

```text
GAG
```

produces:

```text
[2, 1]
```

### OVR

if the stack is:

```text
[1, 2]
```

then:

```text
GAT
```

copies the second value over the top, producing:

```text
[1, 2, 1]
```

---

# T__ - i/o and variables

```text
TAA  PRN       print number
TAC  PRC       print character
TAG  INP       input → push number
TAT  IRC       input → push character code

TCA  SET       pop → store in var
TCC  GET       load var → push
TCG  CLR       clear variable
TCT  DMP       dump stack + vars to stderr

TGA  STR       print string until next TGA

TGC  LDA       pop addr, push mem[addr]
TGG  STA       pop addr, pop val, mem[addr]=val

TGT  CMP       a b → -1/0/1
TTA  EQL       a b → 1 if equal else 0
TTC  NEQ       a b → 1 if not equal else 0
TTG  GTH       a b → 1 if a > b else 0
TTT  LTH       a b → 1 if a < b else 0
```

---

# variables

variables can be stored using `TCA` and loaded using `TCC`.

the instruction immediately following `TCA` or `TCC` is used as the variable name.

for example:

```text
AAC TCA ONEHUND
```

conceptually means:

```text
push 1
set ONEHUND
```

and:

```text
TCC ONEHUND
```

loads the value back onto the stack.

variables can be useful for avoiding repeated calculations:

```text
AGT AGC CAA TCA TOTAL
```

this calculates `64 + 16` and stores the result as `TOTAL`.

---

# comparisons

comparison instructions return either `1` or `0`, making them useful with conditional jumps.

## EQL

```text
AAC AAC TTA
```

checks:

```text
1 == 1
```

result:

```text
1
```

## NEQ

```text
AAC AAG TTC
```

checks:

```text
1 != 2
```

result:

```text
1
```

## GTH

```text
AAG AAC TTG
```

checks:

```text
2 > 1
```

result:

```text
1
```

## LTH

```text
AAC AAG TTT
```

checks:

```text
1 < 2
```

result:

```text
1
```

---

# conditional execution

comparison instructions can be combined with conditional jumps.

the conditional jump instructions are:

```text
GCT  JEZ   jump if top == 0
GGA  JNZ   jump if top != 0
GGC  JGZ   jump if top > 0
GGG  JLZ   jump if top < 0
```

for example:

```text
; if the result is zero, jump
GCT LABEL
```

---

# memory

helix provides a simple memory system.

## LDA

`LDA` loads a value from memory.

```text
TGC
```

operation:

```text
address → mem[address]
```

## STA

`STA` stores a value in memory.

```text
TGG
```

operation:

```text
address, value → mem[address] = value
```

memory addresses are integer values.

---

# input and output

## print number

```text
TAA
```

prints the number at the top of the stack.

example:

```text
AGC TAA
```

prints:

```text
16
```

## print character

```text
TAC
```

prints the value at the top of the stack as an ascii character.

for example:

```text
AGT AAC CAA TAC
```

breakdown:

```text
AGT  push 64
AAC  push 1
CAA  add
TAC  print character
```

`64 + 1 = 65`, and ascii character `65` is `A`.

output:

```text
A
```

---

# character input

`TAT` reads a character and pushes its ascii value onto the stack.

```text
TAT
```

to immediately print the character:

```text
TAT TAC
```

---

# strings

strings can be printed using `TGA`.

a string starts with `TGA` and ends at the next `TGA`.

for example:

```text
TGA hello world TGA
```

prints:

```text
hello world
```

this provides a more convenient way to print text than constructing every ascii value manually.

---

# subroutines

helix supports subroutines using `GGT` and `GTA`.

```text
GGT
```

calls a subroutine.

```text
GTA
```

returns from the current subroutine.

this allows frequently used code to be reused without duplicating it.

---

# complete instruction reference

```text
A__  LITERALS
AAA  PUSH0
AAC  PUSH1
AAG  PUSH2
AAT  PUSH3
ACA  PUSH4
ACC  PUSH5
ACG  PUSH6
ACT  PUSH7
AGA  PUSH8
AGC  PUSH16
AGG  PUSH32
AGT  PUSH64
ATA  PUSH128
ATC  PUSH256
ATG  PUSHn1
ATT  PUSHn2

C__  ARITHMETIC
CAA  ADD
CAC  SUB
CAG  MUL
CAT  DIV
CCA  MOD
CCC  NEG
CCG  ABS
CCT  INC
CGA  DEC
CGC  POW
CGG  SQT
CGT  AND
CTA  ORR
CTC  XOR
CTG  NOT
CTT  LSH

G__  STACK / FLOW
GAA  DUP
GAC  POP
GAG  SWP
GAT  OVR
GCA  ROT
GCC  NOP
GCG  JMP
GCT  JEZ
GGA  JNZ
GGC  JGZ
GGG  JLZ
GGT  CAL
GTA  RET
GTC  HLT
GTG  NOP2
GTT  NOP3

T__  I/O / VARIABLES
TAA  PRN
TAC  PRC
TAG  INP
TAT  IRC
TCA  SET
TCC  GET
TCG  CLR
TCT  DMP
TGA  STR
TGC  LDA
TGG  STA
TGT  CMP
TTA  EQL
TTC  NEQ
TTG  GTH
TTT  LTH
```

---

# example programs

## print the letter A

```text
AGT AAC CAA TAC
```

## print a number

```text
AGG TAA
```

output:

```text
32
```

## increment a number

```text
AAG CCT TAA
```

output:

```text
3
```

## hello world

```text
TGA hello world! TGA
```

---

# design philosophy

helix is intentionally small.

instead of having a large collection of keywords, syntax rules, and special characters, the language uses a fixed **3-character codon system**:

```text
AAA
AAC
AAG
...
TTT
```

there are exactly **64 possible codons**, since each position has four possible bases:

```text
4 × 4 × 4 = 64
```

the four bases are:

```text
A
C
G
T
```

the instruction groups are organized by their first base:

```text
A = literals
C = arithmetic
G = stack / flow
T = i/o / variables
```

this gives helix a compact instruction set while keeping programs visually similar to dna sequences.
