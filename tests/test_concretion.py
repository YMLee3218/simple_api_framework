import unittest

from concrete import AbstractMeta, NoAbstractError, OverwriteConcreteError, concrete


class TestConcrete(unittest.TestCase):
    def test_single_concrete(self):
        class Base(metaclass=AbstractMeta):
            pass

        @concrete
        class Concrete(Base):
            pass

        self.assertTrue(isinstance(Base(), Concrete))

    def test_default_concrete(self):
        class Base(metaclass=AbstractMeta):
            pass

        self.assertTrue(isinstance(Base(), Base))

    def test_multi_concrete(self):
        class Base1(metaclass=AbstractMeta):
            pass

        class Base2:
            pass

        class Base3(metaclass=AbstractMeta):
            pass

        @concrete
        class Concrete(Base1, Base2, Base3):
            pass

        self.assertTrue(isinstance(Base1(), Concrete))
        self.assertTrue(isinstance(Base2(), Base2))
        self.assertFalse(isinstance(Base2(), Concrete))
        self.assertTrue(isinstance(Base3(), Concrete))

    def test_overwrite_concrete_error(self):
        class Base(metaclass=AbstractMeta):
            pass

        @concrete
        class Concrete1(Base):
            pass

        with self.assertRaises(OverwriteConcreteError):
            @concrete
            class Concrete2(Base):
                pass

    def test_no_concrete_target_error(self):
        with self.assertRaises(NoAbstractError):
            @concrete
            class Concrete:
                pass

        class Base:
            pass

        with self.assertRaises(NoAbstractError):
            @concrete
            class Concrete(Base):
                pass
