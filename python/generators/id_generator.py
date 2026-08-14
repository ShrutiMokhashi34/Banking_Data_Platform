"""
===============================================================================
Banking Data Platform
id_generator.py

Reusable Persistent ID Generator

Author : Shruti Mokhashi
===============================================================================
"""

from __future__ import annotations

import atexit
import json
from pathlib import Path
from typing import Dict

# =============================================================================
# ID PREFIXES
# =============================================================================

ID_PREFIXES = {
    "customer": "CUST",
    "address": "ADDR",
    "loan": "LN",
    "application": "APP",
    "repayment": "RP",
    "collateral": "COL",
    "account": "ACC",
    "branch": "BR",
    "employee": "EMP",
    "card": "CD",
    "transaction": "TR",
    "merchant": "MER",
    "alert": "ALR",
    "holiday": "HOL",
}

# =============================================================================
# Sequence File
# =============================================================================

SEQUENCE_FILE = Path(__file__).parent / "id_sequence.json"

# =============================================================================
# Default Starting Values
#
# These reflect the actual counts already generated on Day 1, so the
# very first ID handed out on Day 2 continues immediately after the
# last Day 1 ID for each entity, with no overlap and no gaps.
#
#   CUST00005000   ADDR00006260   BR00000050   EMP00000350
#   MER00001000    ACC00007000    CD00007321   TR00250000
#   HOL00000024    ALR00003000    LN00002500   APP00004000
#   RP00035000     COL00001617
# =============================================================================

DEFAULT_SEQUENCES = {

    # Customer Domain
    "CUST": 5000,
    "ADDR": 6260,

    # Loan Domain
    "LN": 2500,
    "APP": 4000,
    "RP": 35000,
    "COL": 1617,

    # Banking Domain
    "ACC": 7000,
    "CD": 7321,
    "TR": 250000,

    # Organization Domain
    "BR": 50,
    "EMP": 350,

    # Merchant Domain
    "MER": 1000,

    # Merchant & Risk / Reference Domain
    "ALR": 3000,
    "HOL": 24,
}

# =============================================================================
# Sequence Persistence
# =============================================================================

def _load_sequences() -> Dict[str, int]:
    """
    Load the last generated ID for every entity.

    If the sequence file does not exist, it is created using
    DEFAULT_SEQUENCES (the Day 1 ending counts) as the starting point.
    """

    if not SEQUENCE_FILE.exists():

        with open(SEQUENCE_FILE, "w") as fp:

            json.dump(
                DEFAULT_SEQUENCES,
                fp,
                indent=4,
            )

        return DEFAULT_SEQUENCES.copy()

    with open(SEQUENCE_FILE, "r") as fp:

        return json.load(fp)


def save_sequences() -> None:
    """
    Persist the current in-memory sequence values to disk.

    IMPORTANT: this is intentionally NOT called inside generate_id().
    Writing the sequence file to disk on every single ID (hundreds of
    thousands of times for a full day's run) is what makes ID
    generation slow. Instead, the current counters are kept in memory
    for the whole run and flushed to disk:

        • automatically once, when the Python process exits
          (registered below via atexit), and
        • any time you call this function explicitly - e.g. at the
          end of each domain generator's run() method, if you want a
          guaranteed checkpoint before moving to the next script.
    """

    with open(SEQUENCE_FILE, "w") as fp:

        json.dump(
            _SEQUENCES,
            fp,
            indent=4,
        )


# =============================================================================
# Load Sequences
# =============================================================================

_SEQUENCES = _load_sequences()

# Guarantee the latest counters are written to disk even if the caller
# never explicitly calls save_sequences() - this runs once, at normal
# process exit, not on every generate_id() call.
atexit.register(save_sequences)

# =============================================================================
# Generic ID Generator
# =============================================================================

def generate_id(
    prefix: str,
    width: int = 8,
) -> str:
    """
    Generate the next sequential ID.

    Examples
    --------
    CUST00005001
    ACC00007001
    TR00250001

    The sequence is incremented in memory only. It is persisted to
    disk once (see save_sequences()), not on every call, so IDs still
    never overlap across multiple runs/days without paying a disk
    write per ID.
    """

    if prefix not in _SEQUENCES:

        raise ValueError(
            f"Invalid prefix: {prefix}"
        )

    _SEQUENCES[prefix] += 1

    return f"{prefix}{_SEQUENCES[prefix]:0{width}d}"


# =============================================================================
# Convenience Functions
# =============================================================================

def customer_id():
    return generate_id(ID_PREFIXES["customer"])


def address_id():
    return generate_id(ID_PREFIXES["address"])


def loan_id():
    return generate_id(ID_PREFIXES["loan"])


def application_id():
    return generate_id(ID_PREFIXES["application"])


def repayment_id():
    return generate_id(ID_PREFIXES["repayment"])


def collateral_id():
    return generate_id(ID_PREFIXES["collateral"])


def account_id():
    return generate_id(ID_PREFIXES["account"])


def branch_id():
    return generate_id(ID_PREFIXES["branch"])


def employee_id():
    return generate_id(ID_PREFIXES["employee"])


def card_id():
    return generate_id(ID_PREFIXES["card"])


def transaction_id():
    return generate_id(ID_PREFIXES["transaction"])


def merchant_id():
    return generate_id(ID_PREFIXES["merchant"])


def alert_id():
    return generate_id(ID_PREFIXES["alert"])


def holiday_id():
    return generate_id(ID_PREFIXES["holiday"])


# =============================================================================
# Utility Functions
# =============================================================================

def current_sequences() -> Dict[str, int]:
    """
    Return the current sequence values.

    Useful for debugging or reporting.
    """

    return _SEQUENCES.copy()


def reset_counters() -> None:
    """
    Reset all sequences back to the Day 1 baseline
    (DEFAULT_SEQUENCES) and persist immediately.
    """

    global _SEQUENCES

    _SEQUENCES = DEFAULT_SEQUENCES.copy()

    save_sequences()