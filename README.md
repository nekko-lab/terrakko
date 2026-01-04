# Terrakko

<img align="right" src="./logos/terrakko_icon.png" alt="Terrakko logo" width=250cm>

Terrakko is a provisioning tool that can operate Proxmox VE VM instances on Discord.

```text
                                              _  
  _____  _____ ____  ____  ____  _  __ _  __ |_\_  
 /__ __\/  __//  __\/  __\/  _ \/ |/ // |/ //\_  \_  
   / \  |  \  |  \/||  \/|| /_\||   / |   /|_  \_  \  
   | |  |  /_ |    /|    /| | |||   \ |   \| \_  \__|  
   \_/  \____\\_/\_\\_/\_\\_/ \/\_|\_\\_|\_\\__\___/  
```

---

## Environments

- Docker
  - Debian GNU/Linux 12 bookworm
  - [Python:3.11](https://hub.docker.com/_/python/)

---

## Requirements

### Tools

- `GCC`: 12.2.0 (Debian 12.2.0-14)
- `pip`: 24.2 (Python3.11)
- `libsqlite3-dev`: 3.46.1-1
- `Cloud-init`: 24.1.3-0 ubuntu1~22.04.5
- [ubuntu 22.04 server-cloudimg](https://cloud-images.ubuntu.com/releases/22.04/release/)

### Proxmox VE Privileges (TerrakkoAccess)

  | Privileges                | Details                                                 |
  | ------------------------- | ------------------------------------------------------- |
  | `VM.Clone`                | Clone a VM from a VM template.                          |
  | `VM.Monitor`              | Obtaining information about the VM, such as IP address. |
  | `VM.PowerMgmt`            | Start and stop VMs.                                     |
  | `VM.Audit`                | Audit the entire VM.                                    |
  | `VM.Allocate`             | Allocate resources to new VMs.                          |
  | `VM.Config.Cloudinit`     | API for Cloud-init related settings.                    |
  | `SDN.Use`                 | Use SDN.                                                |
  | `Datastore.AllocateSpace` | Required to allocate storage space to the data store.   |

### Python Libraries ([`requirements.txt`](app/requirements.txt))

  | Package                                                       | Version |
  | ------------------------------------------------------------- | ------- |
  | [`aiosqlite`](https://aiosqlite.omnilib.dev/en/stable/)       | 0.20.0  |
  | [`asyncio`](https://docs.python.org/ja/3/library/asyncio.html)| 3.4.3   |
  | [`bcrypt`](https://github.com/pyca/bcrypt/)                   | 4.2.0   |
  | [`discord.py`](https://discordpy.readthedocs.io/ja/latest/)   | 2.4.0   |
  | [`proxmoxer`](https://proxmoxer.github.io/docs/latest/)       | 2.1.0   |
  | [`pysqlite3`](https://github.com/coleifer/pysqlite3)          | 0.5.4   |
  | [`python-dotenv`](https://github.com/theskumar/python-dotenv) | 1.0.1   |
  | [`requests`](https://requests.readthedocs.io/en/latest/)      | 2.32.3  |
  | [`urllib3`](https://urllib3.readthedocs.io/en/stable/)        | 2.2.3   |

---

## How to setup this?

- [Link](setup.md)

---

## How to use this?

- [Link](usage.md)

---

## Config

- [Link](config.md)

## Architecture

![flowchart](images/flowchart.png)

---

## Contact Us

- <networkcontentslab@gmail.com>
