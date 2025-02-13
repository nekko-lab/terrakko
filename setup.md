# Set Up Terrakko

## Proxmox VE

### Add a new user and role

- Create `TerrakkoAccess` role

  ```shell
  pveum role add TerrakkoAccess -privs "VM.Config.Cloudinit, VM.Allocate, VM.Audit, VM.Monitor, VM.PowerMgmt, VM.Clone"
  ```

- Create new user `terrakko@pve`
  - `PASSWORD=<your password>`
  
  ```shell
  pveum user add terrakko@pve --password $PASSWORD
  ```

- Add the `TerrakkoAccess` role to `terrakko@pve`

  ```shell
  pveum aclmod / -user terrakko@pve -role TerrakkoAccess
  ```

### Create a token

- Create a token for `terrakko@pve`

  ```shell
  $ pvesh create /access/users/terrakko@pve/token/terrakko --privsep 0
  ┌──────────────┬──────────────────────────────────────┐
  │ key          │ value                                │
  ╞══════════════╪══════════════════════════════════════╡
  │ full-tokenid │ terrakko@pve!terrakko                │
  ├──────────────┼──────────────────────────────────────┤
  │ info         │ {"privsep":"0"}                      │
  ├──────────────┼──────────────────────────────────────┤
  │ value        │ xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx │
  └──────────────┴──────────────────────────────────────┘
  ```

### Create VM Template with Cloud-init

You can create VM templates by Ansible.  

- [nekko-cloud](https://github.com/nekko-lab/nekko-cloud/tree/5eb88569918a52e2e92dccbc407bc39ed353c473/iaas/cloudinit)

## Discord

- Make a Terrakko channel
- Copy the channel ID
- Go to [Discord.dev](https://discord.com/developers/applications/1294635078470864916/information) and get Terrakko bot URL
- Access the Guild Install URL and Install Terrakko bot

## Local machine

- Run `git clone`
- Make `.env` file
  - Proxmox VE token
  - Region data
  - Discord bot token
  - Discord channel ID

### Docker

- move `/app`

```bash
cd app
```

- Run Docker Compose command

```bash
docker compose  -f "docker-compose.yaml" up
```

### Kubernetes

- Run s

```bash
docker build -t ghcr.io/cyokozai/terrakko:latest .
```
