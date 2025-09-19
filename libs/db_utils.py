import psycopg2

class db_utils:
    def __init__(self, host, database, user, password, port=6543, sslmode="require"):
        """
        Initialize the database connection.
        """
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            sslmode=sslmode
        )
        self.cur = self.conn.cursor()

    def execute(self, query, params=None, fetch_output=False):
        """
        Execute a query.
        :param query: SQL query string
        :param params: Optional tuple of parameters
        :param fetch_output: If True, returns query results
        :return: Query results or None
        """
        self.cur.execute(query, params or ())
        if fetch_output:
            return self.cur.fetchall()
        self.conn.commit()
        return None

    def query(self, query, params=None):
        """
        Shortcut for SELECT queries that always return results.
        """
        self.cur.execute(query, params or ())
        return self.cur.fetchall()

    def close(self):
        """
        Close cursor and connection.
        """
        self.cur.close()
        self.conn.close()
