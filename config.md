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
- `PVE_TEMP_NAME`: VM template name to search across all nodes (e.g. `ubuntu24.04-General-template-v1.0.0`)
- `PVE_CA_CERT`: Path to CA certificate file for SSL verification (leave empty to use system CA bundle)

### Discord Bot

- `DIS_TOKEN`: Discord Bot Token
