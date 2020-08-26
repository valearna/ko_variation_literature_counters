import psycopg2 as psycopg2


class DBManager(object):

    def __init__(self, dbname, user, password, host):
        connection_str = "dbname='" + dbname
        if user:
            connection_str += "' user='" + user
        if password:
            connection_str += "' password='" + password
        connection_str += "' host='" + host + "'"
        self.conn = psycopg2.connect(connection_str)
        self.cur = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def get_variation_names_from_ids(self, ids: list):
        self.cur.execute("SELECT obo_name_variation FROM obo_name_variation WHERE joinkey IN ('{}')"
            .format("','".join(ids)))
        rows = self.cur.fetchall()
        var_names = [row[0] for row in rows]
        return set(var_names)

