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

- Node.js 18+ (TypeScript)
- Docker (optional)
  - Debian GNU/Linux 12 bookworm
  - [Node:22](https://hub.docker.com/_/node/)

---

## Requirements

### Tools

- `Node.js`: 18.0.0 or higher
- `npm`: 11.6.2 or higher
- `TypeScript`: 5.5.3
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

### Node.js Dependencies ([`package.json`](app/package.json))

#### Production Dependencies

  | Package                                                       | Version |
  | ------------------------------------------------------------- | ------- |
  | [`axios`](https://axios-http.com/)                            | ^1.7.7  |
  | [`better-sqlite3`](https://github.com/WiseLibs/better-sqlite3)| ^11.6.0 |
  | [`discord.js`](https://discord.js.org/)                       | ^14.14.1|
  | [`dotenv`](https://github.com/motdotla/dotenv)                | ^16.4.5 |

#### Development Dependencies

  | Package                                                       | Version |
  | ------------------------------------------------------------- | ------- |
  | [`@types/better-sqlite3`](https://www.npmjs.com/package/@types/better-sqlite3) | ^7.6.11 |
  | [`@types/jest`](https://www.npmjs.com/package/@types/jest)    | ^30.0.0 |
  | [`@types/node`](https://www.npmjs.com/package/@types/node)    | ^20.19.27|
  | [`jest`](https://jestjs.io/)                                  | ^30.2.0 |
  | [`ts-jest`](https://kulshekhar.github.io/ts-jest/)            | ^29.4.6 |
  | [`ts-node`](https://typestrong.org/ts-node/)                  | ^10.9.2 |
  | [`typescript`](https://www.typescriptlang.org/)               | ^5.5.3  |

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

Terrakko uses a **Layered Architecture** with clear separation of concerns:

- **Presentation Layer**: Discord UI components (Embeds, Buttons, Select Menus)
- **Application Layer**: Discord event handling and routing
- **Domain Layer**: Business logic (VM, User, Session management)
- **Infrastructure Layer**: External system communication (Proxmox API, Database)
- **Utilities Layer**: Common utilities (Logger, Validator, Time)

For detailed architecture documentation, see [architecture.md](architecture.md)

---

## Contact Us

- <networkcontentslab@gmail.com>
