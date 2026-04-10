# Set Up Terrakko

## Proxmox VE

### Add a new user and role

- Create `TerrakkoAccess` role
  - [Role details](README.md#proxmox-ve-privileges-terrakkoaccess)

  ```shell
  pveum role add TerrakkoAccess -privs "VM.Config.Cloudinit, VM.Config.Options, VM.Allocate, VM.Audit, VM.Monitor, VM.PowerMgmt, VM.Clone"
  ```

- Create new user `terrakko-agent@pve`
  - `PASSWORD=<your password>`
  
  ```shell
  pveum user add terrakko-agent@pve --password $PASSWORD
  ```

- Add the `TerrakkoAccess` role to `terrakko-agent@pve`

  ```shell
  pveum aclmod / -user terrakko-agent@pve -role TerrakkoAccess
  ```

### Create a token

- Create a token for `terrakko-agent@pve`

  ```shell
  $ pvesh create /access/users/terrakko-agent@pve/token/terrakko --privsep 0
  ┌──────────────┬──────────────────────────────────────┐
  │ key          │ value                                │
  ╞══════════════╪══════════════════════════════════════╡
  │ full-tokenid │ terrakko-agent@pve!terrakko          │
  ├──────────────┼──────────────────────────────────────┤
  │ info         │ {"privsep":"0"}                      │
  ├──────────────┼──────────────────────────────────────┤
  │ value        │ xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx │
  └──────────────┴──────────────────────────────────────┘
  ```

### Create VM Template with Cloud-init

You can create VM templates by Ansible.  

- [nekko-cloud](https://github.com/nekko-lab/nekko-cloud/tree/5eb88569918a52e2e92dccbc407bc39ed353c473/iaas/cloudinit)

### Resource Pool based access restrictions

***<details><summary> Details </summary>***

- Add the `terrakko-agent@pve` user to the accessible resource pool members

  ![setup1.png](/images/setup1.png)

- Grant the `TerrakkoAccess` role if you want to grant access to the resource pool

  ![setup2.png](/images/setup2.png)

- To prevent access to a resource pool, grant the `NoAccess` role

  ![setup3.png](/images/setup3.png)

</details>

---

## Discord

- Make a Terrakko channel
- Copy the channel ID
- Go to [Discord.dev](https://discord.com/developers/applications/1294635078470864916/information) and get Terrakko bot URL
- Access the Guild Install URL and Install Terrakko bot

---

## Local machine

- Run `git clone`
- Make `.env` file
  - Proxmox VE token
  - Region data
  - CA certificate path (optional)
  - Discord bot token

---

### Docker

- move `/app`

```bash
cd app
```

- Run Docker Compose command

```bash
docker compose up -d --build
```

---

### ~~Kubernetes~~
