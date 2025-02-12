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
# This function creates a table in the database                          #
#------------------------------------------------------------------------#

async def create_table():
    
    print('Initializing Database...')
    
    async with aiosqlite.connect(config.usrdata) as conn: # Connect to the database
        
        async with conn.cursor() as cur: # Create a cursor
            
            try: # Try to create the table
                
                # Create the table
                await cur.execute(f"CREATE TABLE {config.dbname}(id INTEGER PRIMARY KEY AUTOINCREMENT, uuid STRING, username STRING, password STRING, sshkey STRING)")
                
                # Commit the changes
                await conn.commit()
                
                print(f"Table {config.dbname} created")
                
            except: # If the table already exists
                
                print(f"Table {config.dbname} already exists")
    
    print('Database Initialized')

#------ Delete database -------------------------------------------------#
# This function deletes the database                                     #
#------------------------------------------------------------------------#

async def delete_database():
    
    if os.path.exists(config.usrdata): # Check if the file exists
        
        os.remove(config.usrdata) # Delete the file

#------ Insert data -----------------------------------------------------#

async def insert_data(userid, username, password, sshkey):
    
    async with aiosqlite.connect(config.usrdata) as conn: # Connect to the database
        
        async with conn.cursor() as cur: # Create a cursor
            
            # Insert the data
            await cur.execute(f"INSERT INTO {config.dbname}(uuid, username, password, sshkey) VALUES(?, ?, ?, ?)", (userid, username, password, sshkey))
            
            # Commit the changes
            await conn.commit()

#------ Update data -----------------------------------------------------#

async def update_data(userid, username, password, sshkey):
    
    async with aiosqlite.connect(config.usrdata) as conn: # Connect to the database
        
        async with conn.cursor() as cur: # Create a cursor
            
            # Update the data
            await cur.execute(f"UPDATE {config.dbname} SET username = ?, password = ?, sshkey = ? WHERE uuid = ?", (username, password, sshkey, userid))
            
            # Commit the changes
            await conn.commit()

#------ Get data --------------------------------------------------------#
# This function gets the user data from the database                     #
#------------------------------------------------------------------------#

async def get_userdata(userid):
    
    async with aiosqlite.connect(config.usrdata) as conn: # Connect to the database
        
        async with conn.cursor() as cur: # Create a cursor
            
            # Get the data
            await cur.execute(f"SELECT * FROM {config.dbname} WHERE uuid = ?", (userid,))
            
            # Return the data
            return await cur.fetchone()

#------ Get column ------------------------------------------------------#
# This function gets a column from the database                          #
#------------------------------------------------------------------------#

async def get_column(column):
    
    async with aiosqlite.connect(config.usrdata) as conn: # Connect to the database
        
        async with conn.cursor() as cur: # Create a cursor
            
            # Get the column
            await cur.execute(f"SELECT {column} FROM {config.dbname}")
            
            # Return the column
            return await cur.fetchall()

#------ Initialize database ---------------------------------------------#
# This block of code initializes the database                            #
#------------------------------------------------------------------------#

try: # Try to create the table
    
    # Run the create_table function
    asyncio.run(create_table())
    
except Exception as e: # If an error occurs
    
    print(f"Database initialization failed: {e}")
    
    exit(1) # Exit the program

#------------------------------------------------------------------------#