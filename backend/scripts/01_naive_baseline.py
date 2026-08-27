
DOCUMENT = """
1.1 "Software" means the object-code version of Northwind's proprietary routing-optimization platform, including any Updates provided under this Agreement, but excluding any Third-Party Components identified in Exhibit B.

1.2 "Update" means any patch, bug fix, or minor version release that Northwind makes generally available to licensees at no additional charge during the Term.

2.1 Subject to the terms of this Agreement, Northwind grants Licensee a non-exclusive, non-transferable, worldwide license to install and use the Software solely for Licensee's internal business operations.

2.2 Licensee shall not sublicense, reverse engineer, or distribute the Software to any third party except as expressly permitted under Section 4.3 (Authorized Resellers).

4.1 Licensee shall pay the annual license fee set forth in Exhibit A within thirty (30) days of the invoice date.

4.2(a) Any amount not paid when due shall accrue interest at the lesser of 1.5% per month or the maximum rate permitted by law.

4.2(b) If any invoiced amount remains unpaid for more than sixty (60) days, Northwind may suspend Licensee's access to the Software until payment is received in full.

7.1 Either party may terminate this Agreement upon thirty (30) days' written notice if the other party materially breaches this Agreement and fails to cure within that period.
""".strip()

def naive_chunk(text: str, chunk_size: int = 200) -> list[str]:
    """Split into fixed-size windows, ignoring sentence/clause boundaries — on purpose."""
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


if __name__ == "__main__":
    for i, chunk in enumerate(naive_chunk(DOCUMENT)):
        print(f"--- chunk {i} ({len(chunk)} chars) ---")
        print(chunk)
        print()