from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, List, NamedTuple, Text
import unittest

from db import DAOGetter, DataAccessObject, DBConnector, ExecuteResult, access_to_db
from json_data import JsonObject


@dataclass
class TestDO:
    id: int
    value: Text


class TestDBConnector(DBConnector):
    DUMMY_RESULT: JsonObject = {"id": 0, "value": "test"}

    def __init__(self, observer: Callable[[Text], Any]):
        super().__init__(False)
        self.observer: Callable = observer

    def _initialize(self, readonly: bool):
        pass

    def execute(self, sql: Text, *args, should_return_single: bool = False) -> ExecuteResult:
        arguments: Text = f" / args = {args}" if 0 < len(args) else ""
        self.observer(f"{sql}{arguments}")

        return ExecuteResult(0,
                             TestDBConnector.DUMMY_RESULT if should_return_single else [TestDBConnector.DUMMY_RESULT])

    def commit(self):
        self.observer("commit")

    def rollback(self):
        self.observer("rollback")

    def close(self):
        self.observer("close")


class TestDAO(DataAccessObject):
    def __init__(self, connector: DBConnector):
        super().__init__(TestDO, "test", "id", connector)


class SQLChecker:
    def __init__(self, testcase: unittest.TestCase, expect_sql: List[Text]):
        self.testcase: unittest.TestCase = testcase
        self.expect_sql: List[Text] = expect_sql
        self.sql_index: int = 0

    def __call__(self, sql: Text):
        self.testcase.assertEqual(sql, self.expect_sql[self.sql_index])
        self.sql_index += 1


class TestDataAccessObject(unittest.TestCase):
    def test_insert(self):
        expect_sql: List[Text] = [r"select test_seq.nextval as id from dual",
                                  r"insert into test(id, value) values (?,?) / args = (0, 'test')",
                                  r"commit",
                                  r"close"]
        checker: SQLChecker = SQLChecker(self, expect_sql)
        connector: TestDBConnector = TestDBConnector(checker)
        with access_to_db(connector) as dao_getter:
            dao_getter: DAOGetter
            result: TestDO = dao_getter[TestDAO].insert(TestDO(0, "test"))
            self.assertEqual(result.id, 0)
            self.assertEqual(result.value, "test")

    def test_select(self):
        expect_sql: List[Text] = [r"select * from test where id = ? / args = (0,)",
                                  r"commit",
                                  r"close"]
        checker: SQLChecker = SQLChecker(self, expect_sql)
        connector: TestDBConnector = TestDBConnector(checker)
        with access_to_db(connector) as dao_getter:
            dao_getter: DAOGetter
            result: TestDO = dao_getter[TestDAO].select(0)
            self.assertEqual(result.id, 0)
            self.assertEqual(result.value, "test")

        class FindTest(NamedTuple):
            value: Text

        expect_sql2: List[Text] = [r"select * from test where value = ? / args = ('test',)",
                                   r"commit",
                                   r"close"]
        checker2: SQLChecker = SQLChecker(self, expect_sql2)
        connector2: TestDBConnector = TestDBConnector(checker2)
        with access_to_db(connector2) as dao_getter:
            dao_getter: DAOGetter
            result: TestDO = dao_getter[TestDAO].select_where(FindTest("test"), should_return_single=False)[0]
            self.assertEqual(result.id, 0)
            self.assertEqual(result.value, "test")

        expect_sql3: List[Text] = [r"select * from test where value = ? / args = ('test',)",
                                   r"commit",
                                   r"close"]
        checker3: SQLChecker = SQLChecker(self, expect_sql3)
        connector3: TestDBConnector = TestDBConnector(checker3)
        with access_to_db(connector3) as dao_getter:
            dao_getter: DAOGetter
            dao_getter[TestDAO].select_where("value = ?", "test", should_return_single=True)

    def test_update(self):
        expect_sql: List[Text] = [r"update test set value = ? where id = ? / args = ('test2', 0)",
                                  r"commit",
                                  r"close"]
        checker: SQLChecker = SQLChecker(self, expect_sql)
        connector: TestDBConnector = TestDBConnector(checker)
        with access_to_db(connector) as dao_getter:
            dao_getter: DAOGetter
            dao_getter[TestDAO].update(TestDO(0, 'test2'))

        class FindTest(NamedTuple):
            id: int

        expect_sql2: List[Text] = [r"update test set value = ? where id = ? / args = ('test2', 0)",
                                   r"commit",
                                   r"close"]
        checker2: SQLChecker = SQLChecker(self, expect_sql2)
        connector2: TestDBConnector = TestDBConnector(checker2)
        with access_to_db(connector2) as dao_getter:
            dao_getter: DAOGetter
            dao_getter[TestDAO].update_where(TestDO(0, 'test2'), FindTest(0))

        expect_sql3: List[Text] = [r"update test set value = ? where id = ? / args = ('test2', 0)",
                                   r"commit",
                                   r"close"]
        checker3: SQLChecker = SQLChecker(self, expect_sql3)
        connector3: TestDBConnector = TestDBConnector(checker3)
        with access_to_db(connector3) as dao_getter:
            dao_getter: DAOGetter
            dao_getter[TestDAO].update_where(TestDO(0, 'test2'), "id = ?", 0)

    def test_rollback(self):
        expect_sql: List[Text] = [r"rollback",
                                  r"close"]
        checker: SQLChecker = SQLChecker(self, expect_sql)
        connector: TestDBConnector = TestDBConnector(checker)
        try:
            with access_to_db(connector):
                raise Exception()
        except Exception:
            pass

    def test_db(self):
        @dataclass
        class User:
            id: int
            email: Text
            password: int
            create_datetime: datetime = field(init=False, default_factory=datetime.now)
            update_datetime: datetime = field(init=False, default_factory=datetime.now)

        class FindUser(NamedTuple):
            email: Text

        class UserDAO(DataAccessObject):
            def __init__(self, connector: DBConnector):
                super().__init__(User, "MEMBER", "id", connector)

        with access_to_db(False) as dao_getter:
            dao_getter: DAOGetter

            new_user: User = dao_getter[UserDAO].insert(User(0, "Min", 1234))
            self.assertEqual(new_user.email, "Min")
            self.assertEqual(new_user.password, 1234)

            new_user.create_datetime = new_user.create_datetime.replace(microsecond=0)
            new_user.update_datetime = new_user.update_datetime.replace(microsecond=0)
            find_user: FindUser = FindUser("Min")
            self.assertEqual(dao_getter[UserDAO].select(new_user.id), new_user)
            self.assertEqual(dao_getter[UserDAO].select_where(find_user, should_return_single=True), new_user)
            self.assertEqual(dao_getter[UserDAO].select_where(find_user, should_return_single=False), [new_user])

            new_user.password = 12345
            self.assertEqual(dao_getter[UserDAO].update(new_user), 1)
            self.assertEqual(dao_getter[UserDAO].select(new_user.id).password, 12345)

            new_user.password = 123456
            self.assertEqual(dao_getter[UserDAO].update_where(new_user, find_user), 1)
            self.assertEqual(dao_getter[UserDAO].select(new_user.id).password, 123456)

            self.assertEqual(dao_getter[UserDAO].delete(new_user.id), 1)
            self.assertEqual(dao_getter[UserDAO].select(new_user.id), None)

            dao_getter[UserDAO].insert(new_user)
            self.assertEqual(dao_getter[UserDAO].delete_where(find_user), 1)
            self.assertEqual(dao_getter[UserDAO].select(new_user.id), None)
