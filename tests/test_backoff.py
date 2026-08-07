from grit import constant, expo, fibo, linear


def test_constant():
    w = constant(2)
    assert [w(1), w(2), w(3)] == [2, 2, 2]


def test_linear():
    w = linear(2)
    assert [w(1), w(2), w(3)] == [2, 4, 6]


def test_expo_caps():
    w = expo(base=1, factor=2, cap=10)
    assert [w(1), w(2), w(3), w(10)] == [1, 2, 4, 10]


def test_fibo():
    w = fibo()
    assert [w(1), w(2), w(3), w(4), w(5)] == [1, 1, 2, 3, 5]