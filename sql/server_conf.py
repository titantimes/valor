# Connecting to SQL DB for handling server configurations
import mysql.connector
import os
from dotenv import load_dotenv
# in case it hasn't already been done yet
load_dotenv()

class ValorSQL:
    db = mysql.connector.connect(
        host = os.environ["DBHOST"],
        user = os.environ["DBUSER"],
        password = os.environ["DBPASS"],
        database = os.environ["DBNAME"]
    )
    cursor = db.cursor()
    @classmethod
    def insert_new_server(cls, *args):
        # get columns N before string indicates unicode
        cls.cursor.execute("SHOW columns FROM server_options")
        cols = tuple(c[0] for c in cls.cursor.fetchall())
        if len(args) != len(cols):
            raise Exception("DB QUERY: Column Mismatch")
        cls.cursor.execute(
            f"INSERT INTO server_options ({', '.join(map(str, cols))}) VALUES ({', '.join(map(str, args))})")
        cls.db.commit()
    
    # should probably use a decorator for the ones with _add_new_user
    @classmethod
    def set_user_wynnbuilder(cls, userid: int, pref: str, r: bool):
        cls._add_new_user(userid)
        cls.cursor.execute(f"UPDATE user_config SET {pref} = {r} WHERE user_id = {userid}")
        cls.db.commit()

    @classmethod
    def get_user_config(cls, userid: int):
        cls._add_new_user(userid)
        cls.cursor.execute("SHOW columns FROM user_config")
        cols = tuple(c[0] for c in cls.cursor.fetchall())
        cls.cursor.execute(f"SELECT * FROM user_config WHERE user_id = {userid}")
        res = cls.cursor.fetchone()
        return {cols[i]: res[i] for i in range(len(cols))}
    @classmethod
    def _add_new_user(cls, userid: int):
        cls.cursor.execute(f"SELECT * FROM user_config WHERE user_id = {userid}")
        if len(cls.cursor.fetchall()): # if user exists
            return
        cls.cursor.execute("SHOW columns FROM user_config")
        cols = tuple(c[0] for c in cls.cursor.fetchall())
        cls.cursor.execute(f"INSERT INTO user_config (user_id) VALUES ({userid})")
        cls.db.commit()

if __name__ == "__main__":
    # ValorSQL.insert_new_server(1, 1)
    ValorSQL._add_new_user(1651)
    cursor = ValorSQL.db.cursor()
    cursor.execute("SELECT * FROM user_config")
    print(cursor.fetchall())