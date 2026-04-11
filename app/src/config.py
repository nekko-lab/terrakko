##########################################################################
#                                                                        #
#       Configuration                                                    #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# dotenv
from dotenv import load_dotenv

# os
import os

load_dotenv()



#------ Config ----------------------------------------------------------#

# Version
version = "0.2.0"

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
TIME = 900

#------ env file --------------------------------------------------------#

# Proxmox VE
PVE_HOST      = os.getenv("PVE_HOST")
PVE_USER      = os.getenv("PVE_USER")
PVE_TOKEN     = os.getenv("PVE_TOKEN")
PVE_SECRET    = os.getenv("PVE_SECRET")
PVE_TEMP_NAME = os.getenv("PVE_TEMP_NAME", "ubuntu24.04-General-template-v1.0.0")

# SSL verification: set PVE_CA_CERT to the CA certificate path, or leave empty to use system CA bundle
PVE_CA_CERT   = os.getenv("PVE_CA_CERT", "")

# Discord Bot
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# bw-agent (Bitwarden Send for password delivery)
BW_AGENT_URL  = os.getenv("BW_AGENT_URL", "")

#------------------------------------------------------------------------#