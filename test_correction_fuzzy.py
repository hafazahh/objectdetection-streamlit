"""Test Indonesian plate format correction and fuzzy member matching."""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ocr
import db

def test_format_correction():
    """Test 1: Format correction for various OCR-garbage inputs."""
    print("=" * 60)
    print("TEST 1: Indonesian Plate Format Correction")
    print("=" * 60)

    test_cases = [
        # (input, expected_corrected, expected_was_corrected)
        ('81234A8C', 'B1234ABC', True),
        ('D5678XYZ', 'D5678XYZ', False),  # already valid
        ('F9O12DEF', 'F9012DEF', True),
        ('L3456GH1', 'L3456GHI', True),
        ('B1234ABC', 'B1234ABC', False),  # already valid
        ('GARBAGE', 'GARBAGE', False),    # cannot repair
        ('12', '12', False),              # too short
    ]

    all_passed = True
    for input_text, expected_corrected, expected_corrected_flag in test_cases:
        corrected, was_corrected = ocr.correct_plate_format(input_text)
        passed = (corrected == expected_corrected and was_corrected == expected_corrected_flag)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {input_text!r} -> {corrected!r} (corrected={was_corrected})")
        if not passed:
            print(f"         Expected: {expected_corrected!r}, corrected={expected_corrected_flag}")
            all_passed = False

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def test_fuzzy_matching():
    """Test 2: Fuzzy matching against seeded members."""
    print("\n" + "=" * 60)
    print("TEST 2: Fuzzy Member Matching")
    print("=" * 60)

    # Ensure DB is initialized and seeded
    db.init_db()
    db.seed_members()

    test_cases = [
        # (input, expected_name, expected_match_type)
        ('B1234ABC', 'Budi Santoso', 'exact'),
        ('B1234ABD', 'Budi Santoso', 'fuzzy'),  # one char off
        ('X9999XXX', None, None),  # ambiguous/random
    ]

    all_passed = True
    for input_text, expected_name, expected_match_type in test_cases:
        member, match_type = ocr.match_member(input_text)
        actual_name = member['nama'] if member else None
        passed = (actual_name == expected_name and match_type == expected_match_type)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {input_text!r} -> name={actual_name!r}, type={match_type!r}")
        if not passed:
            print(f"         Expected: name={expected_name!r}, type={expected_match_type!r}")
            all_passed = False

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def test_correction_then_match():
    """Test 3: Full pipeline - correction followed by matching."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Pipeline (Correction + Matching)")
    print("=" * 60)

    test_cases = [
        # (ocr_raw, expected_member_name, expected_match_type)
        ('81234A8C', 'Budi Santoso', 'exact'),  # corrects to B1234ABC
        ('F9O12DEF', 'Andi Wijaya', 'exact'),   # corrects to F9012DEF
        ('L3456GH1', 'Dewi Lestari', 'exact'),  # corrects to L3456GHI
    ]

    all_passed = True
    for raw_input, expected_name, expected_match_type in test_cases:
        corrected, was_corrected = ocr.correct_plate_format(raw_input)
        member, match_type = ocr.match_member(corrected)
        actual_name = member['nama'] if member else None
        passed = (actual_name == expected_name and match_type == expected_match_type)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {raw_input!r} -> corrected={corrected!r} -> name={actual_name!r}, type={match_type!r}")
        if not passed:
            print(f"         Expected: name={expected_name!r}, type={expected_match_type!r}")
            all_passed = False

    print(f"\n  Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def main():
    print("ANPR Format Correction + Fuzzy Matching Tests")
    print("=" * 60)

    results = []
    results.append(("Format Correction", test_format_correction()))
    results.append(("Fuzzy Matching", test_fuzzy_matching()))
    results.append(("Full Pipeline", test_correction_then_match()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print(f"{'=' * 60}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
