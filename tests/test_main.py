import pytest

from src.main import add, hello


def test_hello():
    assert hello() == "Inequality study: GRACE skeleton ready."


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_add_commutative():
    assert add(4, 7) == add(7, 4)


def test_add_raises_on_non_number():
    with pytest.raises(TypeError):
        add("a", 1)
