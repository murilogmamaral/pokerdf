import os
import pandas as pd
import pytest

from pokerdf.core.read_and_convert import convert_txt_to_tabular_data
from pokerdf.utils.columns import Column


def test_utf8_multi_byte_character(tmp_path):
    # Valid UTF-8 with multi-byte character (ã)
    content = """PokerStars Hand #123456789: Tournament #987654321, $10+$1 USD Hold'em No Limit - Level I (10/20) - 2026/01/01 12:00:00 ET
Table '987654321 1' 9-max Seat #1 is the button
Seat 1: Joãoã (1000 in chips)
Seat 2: Player2 (1000 in chips)
Player2: posts small blind 10
Joãoã: posts big blind 20
*** HOLE CARDS ***
Dealt to Joãoã [Ah Kh]
Player2: folds
Uncalled bet (10) returned to Joãoã
Joãoã collected 40 from pot
*** SUMMARY ***
Total pot 40 | Rake 0
Seat 1: Joãoã (button) (big blind) collected (40)
Seat 2: Player2 (small blind) folded before Flop
"""
    file_path = tmp_path / "HH20260101-T987654321.txt"
    file_path.write_text(content, encoding="utf-8")

    df = convert_txt_to_tabular_data(str(file_path))
    assert "Joãoã" in df[Column.PLAYER].values
    assert "\ufffd" not in df[Column.PLAYER].values.tolist()


def test_cp1252_encoding_fallback(tmp_path):
    # Byte 0x9A is 'š' in Windows-1252 / cp1252, invalid standalone in UTF-8
    header = "PokerStars Hand #123456789: Tournament #987654321, $10+$1 USD Hold'em No Limit - Level I (10/20) - 2026/01/01 12:00:00 ET\n"
    table = "Table '987654321 1' 9-max Seat #1 is the button\n"
    s1 = b"Seat 1: Player" + bytes([0x9A]) + b" (1000 in chips)\n"
    s2 = b"Seat 2: Player2 (1000 in chips)\n"
    sb = b"Player2: posts small blind 10\n"
    bb = b"Player" + bytes([0x9A]) + b": posts big blind 20\n"
    hc = b"*** HOLE CARDS ***\nDealt to Player" + bytes([0x9A]) + b" [Ah Kh]\nPlayer2: folds\n"
    ret = b"Uncalled bet (10) returned to Player" + bytes([0x9A]) + b"\n"
    coll = b"Player" + bytes([0x9A]) + b" collected 40 from pot\n"
    summary = b"*** SUMMARY ***\nTotal pot 40 | Rake 0\nSeat 1: Player" + bytes([0x9A]) + b" (button) (big blind) collected (40)\nSeat 2: Player2 (small blind) folded before Flop\n"

    content_bytes = header.encode("ascii") + table.encode("ascii") + s1 + s2 + sb + bb + hc + ret + coll + summary

    file_path = tmp_path / "HH20260101-T987654321.txt"
    file_path.write_bytes(content_bytes)

    df = convert_txt_to_tabular_data(str(file_path))
    assert "\ufffd" not in "".join(df[Column.PLAYER].astype(str).values)
    assert any("š" in name for name in df[Column.PLAYER].values)
