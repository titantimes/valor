# Connecting to SQL DB for handling server configurations
# import mysql.connector
# from mysql.connector import pooling
import asyncio
import aiomysql
import mysql.connector
import os
from dotenv import load_dotenv
import logging
import time

# in case it hasn't already been done yet
load_dotenv()

def init_pool(info):
    async def capture():
        ValorSQL.pool = await aiomysql.create_pool(**info)
    

class ValorSQL:
    _info = {"host": os.environ["DBHOST"],
        "user": os.environ["DBUSER"],
        "password": os.environ["DBPASS"],
        "db":os.environ["DBNAME"]}
    last_connected = time.time()
    connection_live = 120 # 2 minute(s) per connection
    # conn = mysql.connector.connect(**_info)
    conn = None
    pool = None

    @classmethod
    async def insert_new_server(cls, *args):
        # get columns N before string indicates unicode
        await cls._execute("SHOW columns FROM server_options")
        cols = tuple(c[0] for c in cls._fetchall())
        if len(args) != len(cols):
            raise Exception("DB QUERY: Column Mismatch")
        await cls._execute(
            f"INSERT INTO server_options ({', '.join(map(str, cols))}) VALUES ({', '.join(map(str, args))})")
    
    # should probably use a decorator for the ones with _add_new_user
    @classmethod
    async def set_user_wynnbuilder(cls, userid: int, pref: str, r: bool):
        cls._add_new_user(userid)
        await cls._execute(f"UPDATE user_config SET {pref} = {r} WHERE user_id = {userid}")

    @classmethod
    async def get_user_config(cls, userid: int):
        cls._add_new_user(userid)
        res = await cls._execute("SHOW columns FROM user_config")
        cols = tuple(c[0] for c in res)
        res = await cls._execute(f"SELECT * FROM user_config WHERE user_id = {userid}")
        res = res[0]
        return {cols[i]: res[i] for i in range(len(cols))}

    @classmethod
    async def _add_new_user(cls, userid: int):
        res = await cls._execute(f"SELECT * FROM user_config WHERE user_id = {userid}")
        if len(res): # if user exists
            return
        res = await cls._execute("SHOW columns FROM user_config")
        cols = tuple(c[0] for c in res)
        await cls._execute(f"INSERT INTO user_config (user_id) VALUES ({userid})")
    
    @staticmethod
    def execute_sync(query: str):
        conn = mysql.connector.connect(**ValorSQL._info)
        cursor = conn.cursor()
        cursor.execute(query)
        res = list(cursor.fetchall())
        conn.commit()
        cursor.close()

        return res

    @classmethod
    async def _execute(cls, query: str):
        # if time.time() - cls.last_connected > cls.connection_live:
        #     cls.conn.close()
        #     cls.conn = mysql.connector.connect(**cls._info)
        #     cls.last_connected = time.time()
        # while not cls.conn.is_connected():
        #     logging.info("DB disconnected. Now reconnecting")
        #     cls.conn = mysql.connector.connect(**cls._info)
        #     cls.last_connected = time.time()
        # cursor = cls.conn.cursor()
        # cursor.execute(query)
        # res = list(cursor.fetchall())
        # cls.conn.commit()
        # cursor.close()

        async with ValorSQL.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query)
                res = await cur.fetchall()
                await conn.commit()
        
        return res

    @classmethod
    async def exec_param(cls, query: str, params):
        async with ValorSQL.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                res = await cur.fetchall()
                await conn.commit()
        
        return res

    # all of the message reaction / vote polls

    @classmethod
    async def create_react_msg(cls, msg_id, expire):
        msg = await cls._execute(f"INSERT INTO react_msg VALUES ({msg_id}, {expire})")
        return msg
    
    @classmethod
    async def remove_react_msg(cls, msg_id):
        res = await cls._execute(f"DELETE FROM react_msg WHERE msg_id = {msg_id}")
        return res

    @classmethod
    async def create_react_reaction(cls, msg_id, reaction_id, action=''):
        res = await cls._execute(f"INSERT INTO react_msg_react VALUES ({msg_id}, {reaction_id}, 0, {repr(action)})")
        return res
    
    @classmethod
    async def remove_react_reaction(cls, msg_id, reaction_id):
        res = await cls._execute(f"DELETE FROM react_msg_react WHERE msg_id = {msg_id} AND reaction_id = {reaction_id}")
        return res

    @classmethod
    async def get_react_msg_reactions_all(cls, msg_id):
        # gets all reactions of a reaction msg
        res = await cls._execute(f"SELECT * FROM react_msg_react WHERE msg_id = {msg_id}")
        return res

    @classmethod
    async def get_react_msg_reaction(cls, msg_id, reaction_id):
        # gets reaction row of a specific reaction to a reaction msg 
        res = await cls._execute(f"SELECT * FROM react_msg_react WHERE msg_id = {msg_id} AND reaction_id = {reaction_id}")
        return res
    
    @classmethod
    async def add_react_reaction(cls, msg_id, reaction_id):
        res = await cls._execute(f"UPDATE react_msg_react SET count=count+1 WHERE msg_id = {msg_id} AND reaction_id = {reaction_id}")
        return res

    @classmethod
    async def get_all_react_msg(cls) -> bool:
        res = await cls._execute(f"SELECT * FROM react_msg")
        return res
    
    @classmethod
    async def get_server_config(cls, server_id: int):
        res = await cls._execute(f"SELECT * FROM server_config WHERE server_id = {server_id} LIMIT 1")
        return res
    
    @classmethod
    async def get_all_configs(cls):
        res = await cls._execute(f"SELECT terr_track_id FROM server_config")
        return res

    @classmethod 
    async def server_config_update_app_id(cls, server_id: int, app_group_id: int):
        check = await cls.get_server_config(server_id)
        if not len(check):
            await cls._execute(f"INSERT INTO server_config VALUES ({server_id}, {app_group_id}, 0, '', 0)")
        else:
            await cls._execute(f"UPDATE server_config SET app_group_id = {app_group_id} WHERE server_id = {server_id}")

    @classmethod
    async def server_config_set_app_cnt(cls, server_id: int, cnt: int):
        check = await cls.get_server_config(server_id)
        if not len(check):
            raise Exception(f"Server {server_id} has no config set")
        else:
            await cls._execute(f"UPDATE server_config SET app_count = {cnt} WHERE server_id = {server_id}")

    # @classmethod
    # def _reconnect(cls):
    #     print("ValorSQL: Reconnecting to db")
    #     cls.cursor.close()
    #     cls.db.close()
    #     cls.db = mysql.connector.connect(
    #         **cls._info
    #     )

if __name__ == "__main__":
    # ValorSQL.insert_new_server(1, 1)
    ValorSQL._add_new_user(1651)
    cursor = ValorSQL.db.cursor()
    cursor.execute("SELECT * FROM user_config")
    print(cursor.fetchall())