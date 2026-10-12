"""Generate the illustrative screen textures used by scene_flarevm.py.

Needs Pillow (run with the system Python, not the bpy venv):
    python3 blender/make_textures.py
The content is generic assembly and hex-dump styling, not output from any real sample.
"""
import os
import random

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

BG = "#0B0E12"
ADDR = "#6B7686"
MNEM = "#E8A33D"
OPER = "#E9E6E0"
NOTE = "#7FB6D9"
DIM = "#3A4350"

random.seed(7)


def disasm(path, w=1024, h=4096, size=26):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, size)
    fb = ImageFont.truetype(BOLD, size)
    ins = [
        ("push", "ebp"), ("mov", "ebp, esp"), ("sub", "esp, 0x40"), ("mov", "eax, [ebp+0x8]"),
        ("xor", "ecx, ecx"), ("lea", "edx, [eax+0x10]"), ("call", "sub_401180"), ("test", "eax, eax"),
        ("jz", "short loc_401046"), ("mov", "[ebp-0x4], eax"), ("push", "0x0"), ("push", "offset aKernel32"),
        ("call", "ds:GetModuleHandleA"), ("cmp", "dword ptr [ebp-0x4], 0"), ("jnz", "loc_40105C"),
        ("add", "esp, 0x8"), ("mov", "esi, [ebp+0xC]"), ("movzx", "eax, byte ptr [esi]"), ("inc", "esi"),
        ("shl", "eax, 2"), ("pop", "ebp"), ("retn", ""), ("nop", ""), ("int3", ""),
    ]
    notes = ["; arg_0", "; loop counter", "; check return value", "; resolve import", "; local buffer", ""]
    y = 18
    addr = 0x401000
    line_h = int(size * 1.55)
    n = 0
    while y < h - line_h:
        if n % 11 == 0:
            d.text((24, y), "loc_%X:" % addr, font=fb, fill=OPER)
            y += line_h
        op, args = random.choice(ins)
        d.text((24, y), "%08X" % addr, font=f, fill=ADDR)
        d.text((24 + size * 9, y), op, font=f, fill=MNEM)
        d.text((24 + size * 16, y), args, font=f, fill=OPER)
        note = random.choice(notes)
        if note and args:
            d.text((24 + size * 33, y), note, font=f, fill=NOTE)
        addr += random.choice((1, 2, 3, 5, 6))
        y += line_h
        n += 1
    img.save(path, optimize=True)


def card_pe(path, w=720, h=480):
    img = Image.new("RGB", (w, h), "#10151C")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline="#2A3441", width=3)
    f = ImageFont.truetype(FONT, 30)
    fb = ImageFont.truetype(BOLD, 34)
    d.text((32, 24), "PE HEADER", font=fb, fill=MNEM)
    d.line([(32, 78), (w - 32, 78)], fill="#2A3441", width=2)
    rows = [("machine", "x86"), ("sections", "5"), ("entry point", "0x1A40"), ("subsystem", "console"),
            ("imports", "kernel32.dll"), ("", "user32.dll"), ("compiled", "[timestamp]")]
    y = 100
    for k, v in rows:
        d.text((32, y), k, font=f, fill=ADDR)
        d.text((290, y), v, font=f, fill=OPER)
        y += 50
    img.save(path, optimize=True)


def card_hex(path, w=720, h=480):
    img = Image.new("RGB", (w, h), "#10151C")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline="#2A3441", width=3)
    f = ImageFont.truetype(FONT, 25)
    fb = ImageFont.truetype(BOLD, 34)
    d.text((32, 24), "STRINGS AND BYTES", font=fb, fill=MNEM)
    d.line([(32, 78), (w - 32, 78)], fill="#2A3441", width=2)
    y = 98
    off = 0
    for r in range(9):
        bs = [random.randrange(256) for _ in range(8)]
        hexs = " ".join("%02X" % b for b in bs)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in bs)
        d.text((32, y), "%04X" % off, font=f, fill=ADDR)
        d.text((120, y), hexs, font=f, fill=OPER)
        d.text((560, y), asc, font=f, fill=NOTE)
        y += 40
        off += 8
    img.save(path, optimize=True)


if __name__ == "__main__":
    disasm(os.path.join(OUT, "disasm.png"))
    card_pe(os.path.join(OUT, "card_pe.png"))
    card_hex(os.path.join(OUT, "card_hex.png"))
    print("textures written to", OUT)
