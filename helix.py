#!/usr/bin/env python3
"""
Helix — A DNA Programming Language Interpreter
Usage:
  python helix.py <file.dna>       Run a .dna file
  python helix.py                  Launch interactive REPL
  python helix.py --help           Show help + codon reference
  python helix.py --ref            Print full codon table
  python helix.py --new <file.dna> Create a new .dna file from a template

To associate .dna files on Windows so you can double-click them:
  python helix.py --install        Register .dna file association (Windows)
  python helix.py --uninstall      Remove .dna file association (Windows)
"""

import sys
import os
import math
import re

# ─────────────────────────────────────────────
#  ANSI COLOURS  (auto-disabled if not a tty)
# ─────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty() and os.name != 'nt' or (
    os.name == 'nt' and os.environ.get('TERM') or
    os.environ.get('COLORTERM') or
    os.environ.get('WT_SESSION')  # Windows Terminal
)

try:
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        USE_COLOR = True
except Exception:
    pass

def col(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

GREEN   = lambda t: col("92", t)
BLUE    = lambda t: col("94", t)
YELLOW  = lambda t: col("93", t)
RED     = lambda t: col("91", t)
CYAN    = lambda t: col("96", t)
GRAY    = lambda t: col("90", t)
BOLD    = lambda t: col("1",  t)
DIM     = lambda t: col("2",  t)

BASE_COLOR = {'A': GREEN, 'C': BLUE, 'G': YELLOW, 'T': RED}

def color_codon(codon):
    return ''.join(BASE_COLOR.get(c, lambda x: x)(c) for c in codon)

# ─────────────────────────────────────────────
#  CODON TABLE  (64 codons = 4³)
# ─────────────────────────────────────────────
# Each entry: (op_name, description)
CODONS = {
    # A__ — Literals / push small values
    'AAA': ('PUSH0',   'push 0'),
    'AAC': ('PUSH1',   'push 1'),
    'AAG': ('PUSH2',   'push 2'),
    'AAT': ('PUSH3',   'push 3'),
    'ACA': ('PUSH4',   'push 4'),
    'ACC': ('PUSH5',   'push 5'),
    'ACG': ('PUSH6',   'push 6'),
    'ACT': ('PUSH7',   'push 7'),
    'AGA': ('PUSH8',   'push 8'),
    'AGC': ('PUSH16',  'push 16'),
    'AGG': ('PUSH32',  'push 32'),
    'AGT': ('PUSH64',  'push 64'),
    'ATA': ('PUSH128', 'push 128'),
    'ATC': ('PUSH256', 'push 256'),
    'ATG': ('PUSHn1',  'push -1'),
    'ATT': ('PUSHn2',  'push -2'),

    # C__ — Arithmetic / bitwise
    'CAA': ('ADD', 'a b → a+b'),
    'CAC': ('SUB', 'a b → a-b'),
    'CAG': ('MUL', 'a b → a*b'),
    'CAT': ('DIV', 'a b → a÷b (integer)'),
    'CCA': ('MOD', 'a b → a mod b'),
    'CCC': ('NEG', 'a → -a'),
    'CCG': ('ABS', 'a → |a|'),
    'CCT': ('INC', 'a → a+1'),
    'CGA': ('DEC', 'a → a-1'),
    'CGC': ('POW', 'a b → a^b'),
    'CGG': ('SQT', 'a → √a'),
    'CGT': ('AND', 'a b → a & b'),
    'CTA': ('ORR', 'a b → a | b'),
    'CTC': ('XOR', 'a b → a ^ b'),
    'CTG': ('NOT', 'a → ~a'),
    'CTT': ('LSH', 'a b → a << b'),

    # G__ — Stack manipulation / control flow
    'GAA': ('DUP',  'duplicate top'),
    'GAC': ('POP',  'discard top'),
    'GAG': ('SWP',  'swap top two'),
    'GAT': ('OVR',  'copy 2nd over top'),
    'GCA': ('ROT',  'rotate top three'),
    'GCC': ('NOP',  'no operation'),
    'GCG': ('JMP',  'jump to label (next token)'),
    'GCT': ('JEZ',  'jump if top == 0'),
    'GGA': ('JNZ',  'jump if top != 0'),
    'GGC': ('JGZ',  'jump if top > 0'),
    'GGG': ('JLZ',  'jump if top < 0'),
    'GGT': ('CAL',  'call subroutine'),
    'GTA': ('RET',  'return from subroutine'),
    'GTC': ('HLT',  'halt program'),
    'GTG': ('NOP2', 'no operation'),
    'GTT': ('NOP3', 'no operation'),

    # T__ — I/O / variables / memory
    'TAA': ('PRN', 'print number'),
    'TAC': ('PRC', 'print char (ASCII)'),
    'TAG': ('INP', 'input → push number'),
    'TAT': ('IRC', 'input → push char code'),
    'TCA': ('SET', 'pop → store in var (next token = name)'),
    'TCC': ('GET', 'load var → push (next token = name)'),
    'TCG': ('CLR', 'clear variable'),
    'TCT': ('DMP', 'dump stack + vars to stderr'),
    'TGA': ('STR', 'print string until next TGA'),
    'TGC': ('LDA', 'pop addr, push mem[addr]'),
    'TGG': ('STA', 'pop addr, pop val, mem[addr]=val'),
    'TGT': ('CMP', 'a b → -1/0/1'),
    'TTA': ('EQL', 'a b → 1 if equal else 0'),
    'TTC': ('NEQ', 'a b → 1 if not equal else 0'),
    'TTG': ('GTH', 'a b → 1 if a > b else 0'),
    'TTT': ('LTH', 'a b → 1 if a < b else 0'),
}

PUSH_VALUES = {
    'PUSH0': 0, 'PUSH1': 1, 'PUSH2': 2, 'PUSH3': 3,
    'PUSH4': 4, 'PUSH5': 5, 'PUSH6': 6, 'PUSH7': 7,
    'PUSH8': 8, 'PUSH16': 16, 'PUSH32': 32, 'PUSH64': 64,
    'PUSH128': 128, 'PUSH256': 256, 'PUSHn1': -1, 'PUSHn2': -2,
}

# ─────────────────────────────────────────────
#  TOKENIZER
# ─────────────────────────────────────────────
def tokenize(source):
    """
    Returns (tokens, labels).
    tokens: list of uppercase strings (codons or label refs)
    labels: dict of label_name → token index
    Lines starting/containing ; are comments.
    A word ending in ':' defines a label.
    """
    tokens = []
    labels = {}

    for line in source.splitlines():
        # strip comments
        line = line.split(';')[0].strip()
        if not line:
            continue
        for part in line.split():
            part = part.upper()
            if part.endswith(':'):
                name = part[:-1]
                labels[name] = len(tokens)
            else:
                tokens.append(part)

    return tokens, labels

# ─────────────────────────────────────────────
#  VIRTUAL MACHINE
# ─────────────────────────────────────────────
class HelixError(Exception):
    pass

class HelixVM:
    MAX_STEPS = 1_000_000

    def __init__(self):
        self.stack = []
        self.vars = {}
        self.mem = [0] * 256
        self.call_stack = []
        self.halted = False
        self.steps = 0
        self.ip = 0

    # ── stack helpers ──
    def push(self, v):
        self.stack.append(int(v))

    def pop(self):
        if not self.stack:
            raise HelixError("Stack underflow")
        return self.stack.pop()

    def peek(self):
        if not self.stack:
            raise HelixError("Stack is empty")
        return self.stack[-1]

    # ── main run loop ──
    def run(self, tokens, labels):
        ip = 0
        while ip < len(tokens) and not self.halted:
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise HelixError("Execution limit reached (possible infinite loop)")

            tok = tokens[ip]
            entry = CODONS.get(tok)

            if entry is None:
                # Unknown token — skip silently (could be a label ref consumed by a jump)
                ip += 1
                continue

            op, _ = entry

            # ── literals ──
            if op in PUSH_VALUES:
                self.push(PUSH_VALUES[op])

            # ── arithmetic ──
            elif op == 'ADD':
                b, a = self.pop(), self.pop(); self.push(a + b)
            elif op == 'SUB':
                b, a = self.pop(), self.pop(); self.push(a - b)
            elif op == 'MUL':
                b, a = self.pop(), self.pop(); self.push(a * b)
            elif op == 'DIV':
                b, a = self.pop(), self.pop()
                if b == 0: raise HelixError("Division by zero")
                self.push(int(a / b))
            elif op == 'MOD':
                b, a = self.pop(), self.pop()
                if b == 0: raise HelixError("Modulo by zero")
                self.push(a % b)
            elif op == 'NEG':
                self.push(-self.pop())
            elif op == 'ABS':
                self.push(abs(self.pop()))
            elif op == 'INC':
                self.push(self.pop() + 1)
            elif op == 'DEC':
                self.push(self.pop() - 1)
            elif op == 'POW':
                b, a = self.pop(), self.pop(); self.push(round(a ** b))
            elif op == 'SQT':
                self.push(round(math.sqrt(abs(self.pop()))))
            elif op == 'AND':
                b, a = self.pop(), self.pop(); self.push(a & b)
            elif op == 'ORR':
                b, a = self.pop(), self.pop(); self.push(a | b)
            elif op == 'XOR':
                b, a = self.pop(), self.pop(); self.push(a ^ b)
            elif op == 'NOT':
                self.push(~self.pop())
            elif op == 'LSH':
                b, a = self.pop(), self.pop(); self.push(a << b)

            # ── stack manipulation ──
            elif op == 'DUP':
                self.push(self.peek())
            elif op == 'POP':
                self.pop()
            elif op == 'SWP':
                b, a = self.pop(), self.pop(); self.push(b); self.push(a)
            elif op == 'OVR':
                b, a = self.pop(), self.pop(); self.push(a); self.push(b); self.push(a)
            elif op == 'ROT':
                c, b, a = self.pop(), self.pop(), self.pop()
                self.push(b); self.push(c); self.push(a)
            elif op in ('NOP', 'NOP2', 'NOP3'):
                pass

            # ── control flow ──
            elif op == 'JMP':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                if label not in labels:
                    raise HelixError(f"Unknown label: {label}")
                ip = labels[label]
                continue
            elif op == 'JEZ':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                v = self.pop()
                if v == 0:
                    if label not in labels: raise HelixError(f"Unknown label: {label}")
                    ip = labels[label]; continue
            elif op == 'JNZ':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                v = self.pop()
                if v != 0:
                    if label not in labels: raise HelixError(f"Unknown label: {label}")
                    ip = labels[label]; continue
            elif op == 'JGZ':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                v = self.pop()
                if v > 0:
                    if label not in labels: raise HelixError(f"Unknown label: {label}")
                    ip = labels[label]; continue
            elif op == 'JLZ':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                v = self.pop()
                if v < 0:
                    if label not in labels: raise HelixError(f"Unknown label: {label}")
                    ip = labels[label]; continue
            elif op == 'CAL':
                ip += 1
                label = tokens[ip] if ip < len(tokens) else None
                if label not in labels: raise HelixError(f"Unknown label: {label}")
                self.call_stack.append(ip + 1)
                ip = labels[label]; continue
            elif op == 'RET':
                if not self.call_stack:
                    raise HelixError("RET with empty call stack")
                ip = self.call_stack.pop(); continue
            elif op == 'HLT':
                self.halted = True; break

            # ── I/O ──
            elif op == 'PRN':
                print(self.pop())
            elif op == 'PRC':
                v = self.pop()
                print(chr(v & 0xFF), end='', flush=True)
            elif op == 'INP':
                try:
                    raw = input(GRAY("? "))
                    self.push(int(raw))
                except (ValueError, EOFError):
                    self.push(0)
            elif op == 'IRC':
                try:
                    raw = input(GRAY("? "))
                    self.push(ord(raw[0]) if raw else 0)
                except EOFError:
                    self.push(0)

            # ── variables ──
            elif op == 'SET':
                ip += 1
                name = tokens[ip] if ip < len(tokens) else None
                if name is None: raise HelixError("SET needs a variable name")
                self.vars[name] = self.pop()
            elif op == 'GET':
                ip += 1
                name = tokens[ip] if ip < len(tokens) else None
                if name is None: raise HelixError("GET needs a variable name")
                self.push(self.vars.get(name, 0))
            elif op == 'CLR':
                ip += 1
                name = tokens[ip] if ip < len(tokens) else None
                if name and name in self.vars:
                    del self.vars[name]

            # ── debug ──
            elif op == 'DMP':
                print(GRAY(f"  [STACK] {self.stack}"), file=sys.stderr)
                print(GRAY(f"  [VARS]  {self.vars}"), file=sys.stderr)

            # ── string literal: TGA ... TGA ──
            elif op == 'STR':
                ip += 1
                parts = []
                while ip < len(tokens):
                    t = tokens[ip]
                    if CODONS.get(t, ('',))[0] == 'STR':
                        break
                    parts.append(t)
                    ip += 1
                print(' '.join(parts))

            # ── memory ──
            elif op == 'LDA':
                addr = self.pop() & 0xFF
                self.push(self.mem[addr])
            elif op == 'STA':
                addr = self.pop() & 0xFF
                val = self.pop()
                self.mem[addr] = val

            # ── comparison ──
            elif op == 'CMP':
                b, a = self.pop(), self.pop()
                self.push(-1 if a < b else (1 if a > b else 0))
            elif op == 'EQL':
                b, a = self.pop(), self.pop(); self.push(1 if a == b else 0)
            elif op == 'NEQ':
                b, a = self.pop(), self.pop(); self.push(1 if a != b else 0)
            elif op == 'GTH':
                b, a = self.pop(), self.pop(); self.push(1 if a > b else 0)
            elif op == 'LTH':
                b, a = self.pop(), self.pop(); self.push(1 if a < b else 0)

            self.ip = ip
            ip += 1

# ─────────────────────────────────────────────
#  PRETTY PRINTER / REFERENCE
# ─────────────────────────────────────────────
def print_banner():
    print(BOLD(GREEN("  ╔══════════════════════════════╗")))
    print(BOLD(GREEN("  ║  ") + BOLD("H E L I X") + GREEN("  .dna interpreter  ║")))
    print(BOLD(GREEN("  ╚══════════════════════════════╝")))
    print(GRAY("  A stack-based language written in DNA\n"))

def print_codon_ref():
    print(BOLD("\nCodon Reference\n"))
    groups = [
        ('A__', 'Literals',    [c for c in CODONS if c[0]=='A']),
        ('C__', 'Arithmetic',  [c for c in CODONS if c[0]=='C']),
        ('G__', 'Stack/Flow',  [c for c in CODONS if c[0]=='G']),
        ('T__', 'I/O & Vars',  [c for c in CODONS if c[0]=='T']),
    ]
    for prefix, title, codons in groups:
        print(BOLD(f"  {YELLOW(prefix)}  {title}"))
        for c in sorted(codons):
            op, desc = CODONS[c]
            print(f"    {color_codon(c)}  {CYAN(op.ljust(8))}  {GRAY(desc)}")
        print()

def print_help():
    print_banner()
    print(BOLD("Usage:"))
    print(f"  {CYAN('python helix.py')} {GREEN('<file.dna>')}      Run a Helix program")
    print(f"  {CYAN('python helix.py')}                  Interactive REPL")
    print(f"  {CYAN('python helix.py')} {GREEN('--ref')}           Print codon reference")
    print(f"  {CYAN('python helix.py')} {GREEN('--new')} {GREEN('<file.dna>')}  Create template .dna file")
    print(f"  {CYAN('python helix.py')} {GREEN('--install')}       Register .dna files (Windows)")
    print(f"  {CYAN('python helix.py')} {GREEN('--uninstall')}     Remove .dna file association")
    print()
    print(BOLD("Quick syntax:"))
    print(f"  {GRAY('; this is a comment')}")
    print(f"  {color_codon('AGT')} {color_codon('AGA')} {color_codon('CAA')} {color_codon('TAA')}    {GRAY('; push 64, push 8, add, print → 72')}")
    print(f"  {GREEN('LOOP:')}                         {GRAY('; define a label')}")
    print(f"  {color_codon('GCG')} {GREEN('LOOP')}               {GRAY('; JMP → LOOP')}")
    print(f"  {color_codon('TCA')} {color_codon('AAC')}            {GRAY('; SET var[AAC] = top of stack')}")
    print(f"  {color_codon('GTC')}                    {GRAY('; HLT')}")
    print()
    print_codon_ref()

# ─────────────────────────────────────────────
#  TEMPLATE
# ─────────────────────────────────────────────
TEMPLATE = """; Helix .dna program
; ─────────────────────────────────────────────
; Each instruction is a 3-letter DNA codon (A/C/G/T)
; Comments start with ;
; Labels end with :   e.g.  LOOP:
;
; A__ = push literals     C__ = arithmetic
; G__ = stack/flow        T__ = I/O & variables
; ─────────────────────────────────────────────

; Print "HI" (H=72, I=73)
; H: 64 + 8 = 72
AGT AGA CAA TAC

; I: 64 + 8 + 1 = 73
AGT AGA CAA AAC CAA TAC

GTC   ; HLT
"""

# ─────────────────────────────────────────────
#  REPL
# ─────────────────────────────────────────────
def repl():
    print_banner()
    print(f"  Type Helix code and press Enter. {GRAY('Blank line = run it.')}")
    print(f"  {GRAY('.help')} for help · {GRAY('.ref')} for codon table · {GRAY('.exit')} to quit\n")

    vm = HelixVM()
    pending = []

    while True:
        try:
            prompt = GRAY("... ") if pending else GREEN(">>> ")
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.strip() == '.exit':
            break
        elif line.strip() == '.help':
            print_help()
            continue
        elif line.strip() == '.ref':
            print_codon_ref()
            continue
        elif line.strip() == '.reset':
            vm = HelixVM()
            print(GRAY("  VM reset."))
            continue
        elif line.strip() == '.stack':
            print(GRAY(f"  Stack: {vm.stack}"))
            continue
        elif line.strip() == '.vars':
            print(GRAY(f"  Vars:  {vm.vars}"))
            continue

        if line.strip() == '' and pending:
            src = '\n'.join(pending)
            pending = []
            tokens, labels = tokenize(src)
            try:
                vm.run(tokens, labels)
                vm.halted = False  # allow further execution in REPL
            except HelixError as e:
                print(RED(f"  Error: {e}"))
        else:
            pending.append(line)

# ─────────────────────────────────────────────
#  FILE ASSOCIATION  (Windows)
# ─────────────────────────────────────────────
def install_windows():
    import subprocess, winreg
    script = os.path.abspath(__file__)
    python = sys.executable

    print(f"Registering .dna files to open with {CYAN(python)} ...")

    # HKCU\Software\Classes\.dna
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                          r"Software\Classes\.dna") as key:
        winreg.SetValue(key, '', winreg.REG_SZ, 'HelixDNA')

    # HKCU\Software\Classes\HelixDNA
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                          r"Software\Classes\HelixDNA") as key:
        winreg.SetValue(key, '', winreg.REG_SZ, 'Helix DNA Program')

    cmd = f'"{python}" "{script}" "%1"'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                          r"Software\Classes\HelixDNA\shell\open\command") as key:
        winreg.SetValue(key, '', winreg.REG_SZ, cmd)

    # Notify shell
    try:
        subprocess.run(['ie4uinit.exe', '-show'], check=False)
    except FileNotFoundError:
        pass

    print(GREEN("  ✓ Done! Double-clicking any .dna file will now run it with Helix."))
    print(GRAY(f"  Command registered: {cmd}"))

def uninstall_windows():
    import winreg

    def del_tree(root, path):
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        subkey = winreg.EnumKey(key, 0)
                        del_tree(root, path + '\\' + subkey)
                    except OSError:
                        break
            winreg.DeleteKey(root, path)
        except FileNotFoundError:
            pass

    del_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\HelixDNA")
    del_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\.dna")
    print(GREEN("  ✓ .dna file association removed."))

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def run_file(path):
    if not os.path.exists(path):
        print(RED(f"Error: file not found: {path}"), file=sys.stderr)
        sys.exit(1)
    if not path.lower().endswith('.dna'):
        print(YELLOW(f"Warning: file does not have a .dna extension: {path}"), file=sys.stderr)

    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()

    tokens, labels = tokenize(source)

    # Brief header when running a file (suppress if output is piped)
    if sys.stdout.isatty():
        name = os.path.basename(path)
        print(GRAY(f"helix: running {name} ({len(tokens)} tokens, {len(labels)} labels)"))

    vm = HelixVM()
    try:
        vm.run(tokens, labels)
    except HelixError as e:
        print(RED(f"\nRuntime error: {e}"), file=sys.stderr)
        print(GRAY(f"  step {vm.steps}, stack: {vm.stack}"), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(GRAY("\n^C"), file=sys.stderr)
        sys.exit(130)


def main():
    args = sys.argv[1:]

    if not args:
        repl()
        return

    cmd = args[0]

    if cmd in ('--help', '-h', '-?', '/?'):
        print_help()

    elif cmd == '--ref':
        print_codon_ref()

    elif cmd == '--new':
        if len(args) < 2:
            print(RED("Usage: python helix.py --new <filename.dna>"))
            sys.exit(1)
        path = args[1]
        if not path.lower().endswith('.dna'):
            path += '.dna'
        if os.path.exists(path):
            print(RED(f"File already exists: {path}"))
            sys.exit(1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE)
        print(GREEN(f"  ✓ Created {path}"))

    elif cmd == '--install':
        if os.name != 'nt':
            print(RED("--install only works on Windows."))
            print("On Linux/macOS, add this to your shell config:")
            print(CYAN(f"  alias helix='python3 {os.path.abspath(__file__)}'"))
            print("Then: xdg-mime or 'open with' in your file manager.")
            sys.exit(1)
        try:
            install_windows()
        except Exception as e:
            print(RED(f"Failed: {e}"))
            sys.exit(1)

    elif cmd == '--uninstall':
        if os.name != 'nt':
            print(RED("--uninstall only works on Windows."))
            sys.exit(1)
        try:
            uninstall_windows()
        except Exception as e:
            print(RED(f"Failed: {e}"))
            sys.exit(1)

    elif cmd.startswith('-'):
        print(RED(f"Unknown option: {cmd}"))
        print(f"Try: {CYAN('python helix.py --help')}")
        sys.exit(1)

    else:
        # Treat as file path
        run_file(cmd)


if __name__ == '__main__':
    main()
