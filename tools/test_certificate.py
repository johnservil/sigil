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
        self.check(C.decoding("\u200b " + text.upper() + "\n", 32))

    def test_exact_errors(self):
        self.check(C.decoding("", 1))
        self.check(C.decoding("\u200b_0", 1))
        self.check(C.decoding(C.S.ALPHABET[-1] * 2, 1))
        self.check(C.decoding("01", 1))

    def test_wrong_answers_rejected(self):
        # Hand-calculable: 0 * 7129 = 0, represented by the two zero digits.
        source = C.encoding(b"\0")
        self.assertIn("([48, 48] : List Nat)", source)
        self.check(source.replace("([48, 48] : List Nat)", "([48, 49] : List Nat)"), False)
        # Change the accepted data and the exact error, independently.
        source = C.decoding("00", 1)
        self.check(source.replace(".ok [0]", ".ok [1]"), False)
        source = C.decoding("01", 1)
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
