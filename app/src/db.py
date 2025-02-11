##########################################################################
#                                                                        #
#       Database                                                         #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# SQLite3
import aiosqlite

# Hashing
import bcrypt

# asyncio
import asyncio

# os
import os

#------ Import files ----------------------------------------------------#

# config.py
import config 



#------ Create table ----------------------------------------------------#

async def create_table():
    print('Initializing Database...')
    
    async with aiosqlite.connect(config.usrdata) as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(f"CREATE TABLE {config.dbname}(id INTEGER PRIMARY KEY AUTOINCREMENT, uuid STRING, username STRING, password STRING, sshkey STRING)")
                await conn.commit()
                print(f"Table {config.dbname} created")
            except:
                print(f"Table {config.dbname} already exists")
    
    print('Database Initialized')

#------ Initialize database ---------------------------------------------#

try:
    asyncio.run(create_table())
except Exception as e:
    print(f"Database initialization failed: {e}")
    
    exit(1)

#------ Delete database -------------------------------------------------#

async def delete_database():
    if os.path.exists(config.usrdata):
        os.remove(config.usrdata)

#------ Insert data -----------------------------------------------------#

async def insert_data(userid, username, password, sshkey):
    async with aiosqlite.connect(config.usrdata) as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"INSERT INTO {config.dbname}(uuid, username, password, sshkey) VALUES(?, ?, ?, ?)", (userid, username, password, sshkey))
            await conn.commit()

#------ Update data -----------------------------------------------------#

async def update_data(userid, username, password, sshkey):
    async with aiosqlite.connect(config.usrdata) as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"UPDATE {config.dbname} SET username = ?, password = ?, sshkey = ? WHERE uuid = ?", (username, password, sshkey, userid))
            await conn.commit()

#------ Get data --------------------------------------------------------#

async def get_data(userid):
    async with aiosqlite.connect(config.usrdata) as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT * FROM {config.dbname} WHERE uuid = ?", (userid,))
            
            return await cur.fetchone()

#------ Get column ------------------------------------------------------#

async def get_column(column):
    async with aiosqlite.connect(config.usrdata) as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT {column} FROM {config.dbname}")
            
            return await cur.fetchall()

#------------------------------------------------------------------------#