from collections import OrderedDict
import unittest
from unittest.mock import patch, MagicMock
from hdbcli.dbapi import ProgrammingError
from base_handler_test import BaseDatabaseHandlerTest
from mindsdb.integrations.handlers.hana_handler.hana_handler import HanaHandler


class TestHanaHandler(BaseDatabaseHandlerTest, unittest.TestCase):

    @property
    def dummy_connection_data(self):
        return OrderedDict(
            address='123e4567-e89b-12d3-a456-426614174000.hana.trial-us10.hanacloud.ondemand.com',
            port=443,
            user='example_user',
            password='example_pass'
        )

    @property
    def err_to_raise_on_connect_failure(self):
        return ProgrammingError("Connection Failed")

    @property
    def get_tables_query(self):
        return """
            SELECT SCHEMA_NAME,
                   TABLE_NAME,
                   'BASE TABLE' AS TABLE_TYPE
            FROM
                SYS.TABLES
            WHERE IS_SYSTEM_TABLE = 'FALSE'
              AND IS_USER_DEFINED_TYPE = 'FALSE'
              AND IS_TEMPORARY = 'FALSE'

            UNION

            SELECT SCHEMA_NAME,
                   VIEW_NAME AS TABLE_NAME,
                   'VIEW' AS TABLE_TYPE
            FROM
                SYS.VIEWS
            WHERE SCHEMA_NAME <> 'SYS'
              AND SCHEMA_NAME NOT LIKE '_SYS%'
        """

    @property
    def get_columns_query(self):
        return f"""
            SELECT COLUMN_NAME AS Field,
                DATA_TYPE_NAME AS Type
            FROM SYS.TABLE_COLUMNS
            WHERE TABLE_NAME = '{self.mock_table}'

            UNION ALL

            SELECT COLUMN_NAME AS Field,
                DATA_TYPE_NAME AS Type
            FROM SYS.VIEW_COLUMNS
            WHERE VIEW_NAME = '{self.mock_table}'
        """

    def create_handler(self):
        return HanaHandler('hana', connection_data=self.dummy_connection_data)

    def create_patcher(self):
        return patch('hdbcli.dbapi.connect')

    @patch('hdbcli.dbapi.connect')
    def test_successful_connection(self, mock_connect):
        # Simulate a successful connection
        mock_connect.return_value = MagicMock()
        handler = self.create_handler()
        self.assertIsNotNone(handler)

    @patch('hdbcli.dbapi.connect')
    def test_connection_failure(self, mock_connect):
        # Simulate a connection failure
        mock_connect.side_effect = self.err_to_raise_on_connect_failure
        with self.assertRaises(ProgrammingError):
            handler = self.create_handler()

    @patch('hdbcli.dbapi.connect')
    def test_get_tables_empty_result(self, mock_connect):
        # Simulate empty tables result
        mock_connect.return_value.cursor.return_value.fetchall.return_value = []
        handler = self.create_handler()
        tables = handler.get_tables()
        self.assertEqual(tables, [])

    @patch('hdbcli.dbapi.connect')
    def test_get_columns_empty_result(self, mock_connect):
        # Simulate empty columns result
        mock_connect.return_value.cursor.return_value.fetchall.return_value = []
        handler = self.create_handler()
        columns = handler.get_columns(self.mock_table)
        self.assertEqual(columns, [])


if __name__ == '__main__':
    unittest.main()
