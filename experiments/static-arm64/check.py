#!/usr/bin/env python3
"""Reproduce the isolated static AArch64 proof and C-ABI integration experiment.

    python3 experiments/static-arm64/check.py /tmp/sigil-static-new

Requires native AArch64 Linux, gcc/binutils, git, and elan/lake on PATH.
The work directory must be new. Builds and downloaded sources stay there.
The pinned historical Lean toolchain belongs to this experiment alone.
"""
import argparse
import ctypes
from pathlib import Path
import platform
import random
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
LNSYM = "5c05220ff970e3bdd7813ad0c9ef3741522c8b92"
URL = "https://github.com/leanprover/LNSym"
# Packaging overlay only: no instruction semantics or upstream proofs change.
# The upstream package also fetches ELF/documentation dependencies unused here.
LAKEFILE = """import Lake
open Lake DSL
package lnsym
lean_lib Arm
lean_lib Specs
lean_lib Tactics
lean_lib Probe
"""
ALLOWED = "[propext, Classical.choice, Quot.sound]"


def run(args, cwd, timeout=300):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    assert result.returncode == 0, f"command failed: {args}\n{result.stdout}\n{result.stderr}"
    return result.stdout


def artifact_statement(data):
    # Only numeric literals enter Lean, so artifact contents cannot inject source.
    return ("import Probe\n"
            f"theorem artifact_matches : ({list(data)} : List Nat) = SigilStatic.codeBytes := by decide\n"
            "#print axioms artifact_matches\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    assert platform.system() == "Linux" and platform.machine() == "aarch64", "native AArch64 Linux required"
    work = args.work.resolve()
    work.mkdir()  # A fresh, persistent experiment directory; never overwrite a prior run.
    model = work / "LNSym"
    run(["git", "init", "-q", str(model)], work)
    run(["git", "remote", "add", "origin", URL], model)
    run(["git", "fetch", "--depth=1", "origin", LNSYM], model)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], model)
    assert run(["git", "rev-parse", "HEAD"], model).strip() == LNSYM
    (model / "lakefile.lean").write_text(LAKEFILE)
    (model / "lake-manifest.json").unlink()
    shutil.copyfile(HERE / "Probe.lean", model / "Probe.lean")
    print(run(["lake", "build", "Probe"], model, timeout=900), end="")
    audit = run(["lake", "env", "lean", "--trust=0", "Probe.lean"], model)
    assert "warning:" not in audit
    assert audit.strip().splitlines() == [
        f"'SigilStatic.muladd_word_state' depends on axioms: {ALLOWED}",
        f"'SigilStatic.muladd_word_exact' depends on axioms: {ALLOWED}",
    ], audit
    print(audit, end="")

    library = work / "libsigil_static_probe.so"
    run(["gcc", "-shared", "-nostdlib", "-Wl,--build-id=none,-z,noexecstack,-z,now",
         str(HERE / "muladd.S"), "-o", str(library)], work)
    raw = work / "text.bin"
    # Extract the final linked artifact, not just the assembler's object file.
    run(["objcopy", "-O", "binary", "--only-section=.text", str(library), str(raw)], work)
    data = raw.read_bytes()
    (model / "Artifact.lean").write_text(artifact_statement(data))
    answer = run(["lake", "env", "lean", "--trust=0", "Artifact.lean"], model)
    assert answer.strip() == "'artifact_matches' does not depend on any axioms", answer
    print("Final library .text bytes:", data.hex(" "))
    print(answer, end="")

    # A corrupted artifact must fail the same kernel-checked byte binding.
    assert data, "empty .text"
    corrupted = bytes([data[0] ^ 1]) + data[1:]
    (model / "Corrupt.lean").write_text(artifact_statement(corrupted))
    result = subprocess.run(["lake", "env", "lean", "--trust=0", "Corrupt.lean"], cwd=model,
                            text=True, capture_output=True, timeout=300)
    assert result.returncode != 0 and "error:" in result.stdout, "corrupted artifact was accepted"

    # Native calls are evidence about integration/model agreement, separate from the proof.
    fn = ctypes.CDLL(str(library)).sigil_muladd_word
    fn.argtypes = [ctypes.c_uint64] * 3
    fn.restype = ctypes.c_uint64
    edge = [0, 1, (1 << 31) - 1, 1 << 31, (1 << 32) - 1]
    for a in edge:
        for b in edge:
            for c in edge:
                assert fn(a, b, c) == a * b + c
    rng = random.Random(20261022)
    for _ in range(1000):
        a, b, c = [rng.getrandbits(32) for _ in range(3)]
        assert fn(a, b, c) == a * b + c
    run(["gcc", str(HERE / "caller.c"), str(library), "-o", str(work / "caller")], work)
    assert run([str(work / "caller")], work).strip() == str(0xffffffff00000000)
    print("Passed: universal model proofs; final artifact byte binding; corrupt-byte rejection;")
    print("1,125 native calls against integer arithmetic; linked C executable smoke test.")
    print("This proves one primitive under the model, not Sigil or the surrounding loader/caller.")


if __name__ == "__main__":
    main()
