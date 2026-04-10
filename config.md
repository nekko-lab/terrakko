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
- `TIME`: Monitoring timeout in seconds (default: 900 = 15 minutes)

## Environment Variables ([.env](app/.env-temp))

### Docker

- `WORKDIR`: Directory name

### Proxmox VE

- `PVE_HOST`: Proxmox VE Node Host IP Address
- `PVE_USER`: Proxmox VE User (Don't use root)
- `PVE_TOKEN`: Proxmox VE Token Name
- `PVE_SECRET`: Proxmox VE Token Secret
- `PVE_REGION`: Proxmox VE Node Name (JSON array)
- `PVE_TEMP_ID`: Proxmox VE VM Template ID (JSON array, 1:1 correspondence with PVE_REGION)
- `PVE_CA_CERT`: Path to CA certificate file for SSL verification (leave empty to use system CA bundle)

### Discord Bot

- `DIS_TOKEN`: Discord Bot Token
