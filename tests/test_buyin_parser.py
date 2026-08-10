from pokerdf.utils.buyin_parser import parse_buyin

def test_parse_buyin_standard():
    res = parse_buyin("$4.60+$0.40")
    assert res.prize == 4.60
    assert res.bounty is None
    assert res.rake == 0.40
    assert res.currency == "$"

def test_parse_buyin_knockout():
    res = parse_buyin("€10+€10+€2")
    assert res.prize == 10.0
    assert res.bounty == 10.0
    assert res.rake == 2.0
    assert res.currency == "€"

def test_parse_buyin_freeroll():
    res = parse_buyin("Freeroll")
    assert res.prize == 0.0
    assert res.bounty is None
    assert res.rake == 0.0
    assert res.currency is None
