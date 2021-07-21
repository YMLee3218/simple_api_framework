import unittest

from switch_dispatch import OverwriteCaseError, switch_dispatch


class TestSwitchDispatch(unittest.TestCase):
    def test_switch_case(self):
        @switch_dispatch
        def default(value: int) -> int:
            return value * 1

        @default.register(2)
        def _(value: int) -> int:
            return value * 10

        @default.register(3)
        def _(value: int) -> int:
            return value * 100

        self.assertEqual(default(1), 1)
        self.assertEqual(default(2), 20)
        self.assertEqual(default(3), 300)

    def test_kwargs(self):
        @switch_dispatch
        def default(value: int) -> int:
            return value * 1

        @default.register(2)
        def _(value: int) -> int:
            return value * 10

        self.assertEqual(default(value=1), 1)
        self.assertEqual(default(value=2), 20)

    def test_default(self):
        @switch_dispatch
        def default(value: int = 2) -> int:
            return value * 1

        @default.register(2)
        def _(value: int) -> int:
            return value * 10

        self.assertEqual(default(), 2)

    def test_overwrite_case(self):
        @switch_dispatch
        def default(value: int) -> int:
            return value * 1

        @default.register(2)
        def _(value: int) -> int:
            return value * 10

        with self.assertRaises(OverwriteCaseError):
            @default.register(2)
            def _(value: int) -> int:
                return value * 100

        @switch_dispatch(True)
        def default2(value: int) -> int:
            return value * 1

        @default2.register(2)
        def _(value: int) -> int:
            return value * 10

        @default2.register(2)
        def _(value: int) -> int:
            return value * 100

        self.assertEqual(default2(2), 200)

    def test_multi_condition(self):
        @switch_dispatch
        def default(value: int) -> int:
            return value * 1

        @default.register(2, 3)
        def _(value: int) -> int:
            return value * 10

        self.assertEqual(default(1), 1)
        self.assertEqual(default(2), 20)
        self.assertEqual(default(3), 30)

    def test_custom_comparator_case(self):
        @switch_dispatch(False, lambda x, y: x == y - 1)
        def default(value: int) -> int:
            return value * 1

        @default.register(2)
        def _(value: int) -> int:
            return value * 10

        @default.register(3)
        def _(value: int) -> int:
            return value * 100

        self.assertEqual(default(1), 10)
        self.assertEqual(default(2), 200)
        self.assertEqual(default(3), 3)

    def test_separate_comparator_case(self):
        @switch_dispatch
        def default(value: int) -> int:
            return value * 1

        @default.register(lambda value: value % 2 == 0)
        def _(value: int) -> int:
            return value * 10

        @default.register(2)
        def _(value: int) -> int:
            return value * 100

        @default.register(3)
        def _(value: int) -> int:
            return value * 1000

        self.assertEqual(default(1), 1)
        self.assertEqual(default(2), 20)
        self.assertEqual(default(3), 3000)
