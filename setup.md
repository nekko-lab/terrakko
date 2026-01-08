# Set Up Terrakko

## Proxmox VE

### Add a new user and role

- Create `TerrakkoAccess` role
  - [Role details](README.md#proxmox-ve-privileges-terrakkoaccess)

  ```shell
  pveum role add TerrakkoAccess -privs "VM.Config.Cloudinit, VM.Allocate, VM.Audit, VM.Monitor, VM.PowerMgmt, VM.Clone"
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

### 1. Clone the repository

```bash
git clone https://github.com/nekko-lab/terrakko.git
cd terrakko
```

### 2. Install dependencies

```bash
cd app
npm install
```

### 3. Create `.env` file

Create a `.env` file in the `app/` directory with the following variables:

```bash
# Domain name
DOMAIN=".proxmoxve.internal.nekko-lab.dev"

# Proxmox VE
PVE_HOST="10.0.128.103"
PVE_USER="terrakko-agent@pve"
PVE_PASS="your-password"
PVE_REGION=["dev-proxmox-mk", "dev-proxmox-ur"]
PVE_TEMP_ID=["90100", "90101"]
PVE_TOKEN="terrakko"
PVE_SECRET="your-token-secret"

# Discord Bot
DIS_TOKEN="your-discord-bot-token"
DIS_CHANNEL_ID=1297112224665698336
```

### 4. Build the application

```bash
npm run build
```

### 5. Run the bot

#### Development mode (with auto-reload)

```bash
npm run dev
```

#### Production mode

```bash
npm start
```

---

## Testing

Run tests to ensure everything is working correctly:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

---

## Docker (Optional)

If you prefer to run Terrakko in a Docker container:

### 1. Move to app directory

```bash
cd app
```

### 2. Run Docker Compose

```bash
docker compose up -d --build
```

### 3. View logs

```bash
docker compose logs -f
```

### 4. Stop the container

```bash
docker compose down
```

---

## ~~Kubernetes~~
