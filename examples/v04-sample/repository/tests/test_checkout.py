from src.checkout import checkout


def test_declined() -> None:
    assert checkout(True) == "declined"
