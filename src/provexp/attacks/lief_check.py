"""
Whether LIEF can rebuild a file, checked once per original binary before the attacks that rebuild through LIEF.

secml-malware's GAMMA attacks (section injection, API injection) parse the file with LIEF, add sections or imports, and
rebuild it (`write_to_bytes`) on every query, always starting from the original file. On some malformed files LIEF's
rebuild runs away: it pads the output to a garbage section offset (outputs of 2 GiB or more), fails to allocate, or
crashes in the parser (session 76: 38 of 40 files lost to OOM-killed workers fail here, 40 of 40 controls pass). Inside a
worker pool such a file kills its worker and stalls the pool. Checking the original once, in a separate process with a
memory cap and a timeout, finds these files before the attack runs; the LIEF-based attacks are then not applicable to
them, which is reported apart from attack failures.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from itertools import islice
import json
import resource
import subprocess
import sys
from typing import Iterable
from typing import Optional

__all__ = ["DOS_ATTACKS", "LIEF_ATTACKS", "MAX_OUTPUT", "dos_header_extensible", "lief_round_trip", "lief_round_trips"]


# The toolkit attacks that rebuilt the file through LIEF (secml-malware's c_gamma_sections_evasion, c_gammapi_evasion)
# until session 103; our writers make their edits since (provexp.attacks.toolkit.gamma_start gates them). Kept to read
# the earlier runs' lief_check.parquet.
LIEF_ATTACKS = ("gamma_sections", "gamma_api")

# The toolkit attacks that extend the DOS header (secml-malware's shift_pe_header_by: CBlackBoxContentDOSExtensionProblem
# and CBlackBoxFormatExploitEvasionProblem). They insert bytes where the PE header starts; on a file whose PE header
# starts inside the DOS header (e_lfanew below 0x40, a known trick of tiny executables) that is in front of the
# e_lfanew field itself, and no parser reads the result (session 85: 45 of 79,121 outputs). Such a file has no DOS
# header to extend, so these attacks are not applicable to it.
DOS_ATTACKS = ("dos_extend", "format_exploit")
DOS_HEADER_SIZE = 0x40

# NOTE: the largest rebuilt output the attacks accept. GAMMA holds each query's output as a list of Python ints and a
# CArray, ~140 bytes of memory per output byte (session 76: 7.1 GB peak on a 51 MB output, several minutes per run).
# 64 MiB (16x the 4,000,000-byte input limit) keeps a run under ~10 GB; legitimate outputs seen so far reach 51 MB, the
# runaway ones 2 GiB.
MAX_OUTPUT = 64 * 2**20


################################################################################
# The checks
################################################################################


def dos_header_extensible(data: bytes) -> bool:
    """Whether the DOS header can be extended: the PE header starts past it (e_lfanew >= 0x40)."""
    if len(data) < DOS_HEADER_SIZE:
        return False
    return int.from_bytes(data[0x3C:0x40], "little") >= DOS_HEADER_SIZE

def lief_round_trip(data: bytes, memory_cap: int = 8 * 2**30, timeout: float = 120.0) -> Optional[str]:
    """Run GAMMA's two LIEF rebuilds on `data` in a separate process; None if both succeed, else the reason.

    The child parses the file, adds one 4 KiB data section and rebuilds it (section injection), then parses it again,
    adds one import and rebuilds it with the import table (API injection), under an address-space cap.

    Args:
        data: The file the attack starts from (the original, or the escaped file).
        memory_cap: The child's address-space limit, in bytes.
        timeout: Seconds before the child is killed.

    Returns:
        None when LIEF rebuilds the file, else one of `crash: ...`, `memory`, `timeout`, `output: <bytes>`, `error: ...`.
    """
    if memory_cap <= 0 or timeout <= 0:
        raise ValueError(f"memory_cap and timeout must be positive, got {memory_cap} and {timeout}.")
    try:
        proc = subprocess.run([sys.executable, "-m", "provexp.attacks.lief_check", str(memory_cap)], input=data,
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout"
    if proc.returncode < 0:
        return f"crash: signal {-proc.returncode}"
    out = proc.stdout.decode(errors="replace").strip().splitlines()
    if proc.returncode != 0 or not out:
        err = proc.stderr.decode(errors="replace")
        if "MemoryError" in err or "bad_alloc" in err:
            return "memory"
        return f"error: {(err.strip().splitlines() or ['exit ' + str(proc.returncode)])[-1][:160]}"
    result = json.loads(out[-1])
    if result.get("error"):
        return f"error: {result['error'][:160]}"
    size = max(result["sections"], result["imports"])
    if size > MAX_OUTPUT:
        return f"output: {size}"
    return None


def lief_round_trips(files: Iterable[bytes], workers: int) -> list[Optional[str]]:
    """`lief_round_trip` on each file, `workers` at a time (threads, each waiting on its own child process).

    The files are drawn from `files` a chunk at a time, so a generator keeps only a few of them in memory.

    Args:
        files: The files the attacks start from, each checked once.
        workers: Checks running at once.

    Returns:
        One result per file, in order (None: LIEF rebuilds it).
    """
    if workers < 1:
        raise ValueError(f"workers must be >= 1, got {workers}.")
    out: list[Optional[str]] = []
    it = iter(files)
    with ThreadPoolExecutor(workers) as pool:
        while chunk := list(islice(it, 4 * workers)):
            out.extend(pool.map(lief_round_trip, chunk))
    return out


def _child(memory_cap: int) -> None:
    """The child: read the file from stdin, rebuild it as both GAMMA attacks do, print the output sizes as JSON."""
    resource.setrlimit(resource.RLIMIT_AS, (memory_cap, memory_cap))
    import lief

    lief.logging.disable()
    data = sys.stdin.buffer.read()
    pe = lief.PE.parse(list(data))
    if pe is None:
        print(json.dumps({"error": "LIEF could not parse the file"}), flush=True)
        return
    section = lief.PE.Section()
    section.name = "check"
    section.content = list(b"\x00" * 4096)
    pe.add_section(section)
    sections = len(pe.write_to_bytes())
    pe = lief.PE.parse(bytes(data))
    if pe is None:
        print(json.dumps({"error": "LIEF could not parse the file"}), flush=True)
        return
    found = [lib for lib in pe.imports if lib.name.lower() == "kernel32.dll"]
    lib = found[0] if found else pe.add_import("kernel32.dll")
    lib.add_entry("GetTickCount")
    config = lief.PE.Builder.config_t()
    config.imports = True
    imports = len(pe.write_to_bytes(config))
    print(json.dumps({"sections": sections, "imports": imports}), flush=True)


if __name__ == "__main__":
    _child(int(sys.argv[1]))
