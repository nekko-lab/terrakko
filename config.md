# [config\.py](app/src/config.py)

## Version

- Terrakko version

## LOGO

```text
                                              _  
  _____  _____ ____  ____  ____  _  __ _  __ |_\_  
 /__ __\/  __//  __\/  __\/  _ \/ |/ // |/ //\_  \_  
   / \  |  \  |  \/||  \/|| /_\||   / |   /|_  \_  \  
   | |  |  /_ |    /|    /| | |||   \ |   \| \_  \__|  
   \_/  \____\\_/\_\\_/\_\\_/ \/\_|\_\\_|\_\\__\___/  
  
```

## Config

- `DOMAIN`: Host name of VM
- `TIME`: Timeout (in seconds)

## Database

- `db_path`: The path of database directory
- `dbname`: The database name
- `usrdata`: The path of database

## Environment Variables ([.env](app/.env-temp))

### Docker

- `WORKDIR`: Directry name

### Proxmox VE

- `PVE_HOST`: Proxmox VE Node Host IP Address
- `PVE_USER`: Proxmox VE User (Don't use root)
- `PVE_PASS`: Proxmox VE Password (No problem even if it's empty)
- `PVE_TOKEN`: Proxmox VE Token Name
- `PVE_SECRET`: Proxmox VE Token Secret
- `PVE_REGION`: Proxmox VE Node Name
- `PVE_TEMP_ID`: Proxmox VE VM Template ID

### Discord Bot

- `DIS_TOKEN`: Discord Bot Token
- `DIS_CHANNEL_ID`: Discord Channel ID (integer)
