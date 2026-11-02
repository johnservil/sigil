"""Exercise answer certificates through Lean, including deliberately wrong answers.

Run from the repository root after `(cd lean && lake build)`:
    python3 tools/test_certificate.py
"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("certificate", Path(__file__).with_name("certificate.py"))
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


class Certificates(unittest.TestCase):
    def check(self, source, accepts=True):
        with tempfile.TemporaryDirectory(prefix="sigil-answer-") as tmp:
            path = Path(tmp) / "Answer.lean"
            path.write_text(source, encoding="utf-8")
            result = subprocess.run(["lake", "env", "lean", "--trust=0", str(path)], cwd=ROOT / "lean",
                                    text=True, capture_output=True, timeout=120)
        if accepts:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("warning:", result.stdout + result.stderr)
            self.assertIn(result.stdout.strip(), {
                "'SigilAnswer.answer' does not depend on any axioms",
                "'SigilAnswer.answer' depends on axioms: [propext]",
            })
        else:
            self.assertNotEqual(result.returncode, 0, "Lean accepted a deliberately wrong answer")
            self.assertIn("error:", result.stdout + result.stderr)

    def test_encode(self):
        for data in [b"\0", b"\xff", bytes(range(32))]:
            with self.subTest(data=data.hex()):
                self.check(C.encoding(data))

    def test_decode(self):
        text = C.S.encode(bytes(range(32)))
        self.check(C.decoding(text, 32))
        self.check(C.decoding("\u200b " + text[:5] + "\u2060" + text[5:] + "\n", 32))

    def test_exact_errors(self):
        zero = C.S.encode(b"\0")
        self.check(C.decoding("", 1))
        self.check(C.decoding("\u200b_" + zero[1], 1))
        self.check(C.decoding(C.S.ALPHABET[-1] * 2, 1))
        self.check(C.decoding(zero[0] + "\u202e", 1))

    def test_wrong_answers_rejected(self):
        # The zero byte's sigil, with its last letter changed: Lean refuses it.
        zero = C.S.encode(b"\0")
        right = f"({C.nats(map(ord, zero))} : List Nat)"
        wrong = f"({C.nats([ord(zero[0]), ord(zero[1]) + 1])} : List Nat)"
        source = C.encoding(b"\0")
        self.assertIn(right, source)
        self.check(source.replace(right, wrong), False)
        # Change the accepted data and the exact error, independently.
        source = C.decoding(zero, 1)
        self.check(source.replace(".ok [0]", ".ok [1]"), False)
        changed = zero[0] + C.S.ALPHABET[(C.S.DIGIT[zero[1]] + 1) % C.S.N]
        source = C.decoding(changed, 1)
        self.assertIn(".error (.check)", source)
        self.check(source.replace(".error (.check)", ".error (.range)"), False)

    def test_untrusted_text_is_only_numerals(self):
        source = C.decoding("-/\naxiom malicious : False\n/-", 1)
        self.assertNotIn("malicious", source)
        self.check(source)

    def test_contract(self):
        with self.assertRaises(AssertionError):
            C.encoding(b"")
        with self.assertRaises(AssertionError):
            C.decoding("", 0)


if __name__ == "__main__":
    unittest.main()
