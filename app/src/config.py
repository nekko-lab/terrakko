##########################################################################
#                                                                        #
#       Configuration                                                    #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# dotenv
from dotenv import load_dotenv

# json
import json

# os
import os

load_dotenv()



#------ Config ----------------------------------------------------------#

# Version
version = "1.0.2"

# Logo
LOGO = """
                                              _ 
  _____  _____ ____  ____  ____  _  __ _  __ |_\\_ 
 /__ __\\/  __//  __\\/  __\\/  _ \\/ |/ // |/ //\\_  \\_ 
   / \\  |  \\  |  \\/||  \\/|| /_\||   / |   /|_  \\_  \\ 
   | |  |  /_ |    /|    /| | |||   \\ |   \\| \\_  \\__| 
   \\_/  \\____\\\\_/\\_\\\\_/\\_\\\\_/ \\/\\_|\\_\\\\_|\\_\\\\__\\___/
"""

# Domain name
DOMAIN = os.getenv("DOMAIN")

# Timeout
TIME = 180

# Database path
db_path = './db/'

# Database name
dbname = 'userdata'

# Database
usrdata = db_path + dbname + '.db'

#------ env file --------------------------------------------------------#

# Proxmox VE
PVE_HOST = os.getenv("PVE_HOST")
PVE_USER = os.getenv("PVE_USER")
PVE_PASS = os.getenv("PVE_PASS")
PVE_TOKEN = os.getenv("PVE_TOKEN")
PVE_SECRET = os.getenv("PVE_SECRET")
PVE_REGION = json.loads(os.getenv("PVE_REGION"))
PVE_TEMP_ID = json.loads(os.getenv("PVE_TEMP_ID"))

# Discord Bot
DIS_TOKEN = os.getenv("DIS_TOKEN")
DIS_CHANNEL_ID = int(os.getenv("DIS_CHANNEL_ID"))

#------------------------------------------------------------------------#