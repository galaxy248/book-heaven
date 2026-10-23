# 📚 Book Heaven
## 🌟 Overview

Book Heaven is a desktop application for bookstore management and warehouse logistics, designed for both customers and warehouse administrators. It is built using PostgreSQL 16, a Flask REST API, and a PyQt6 desktop client.

---

## 📸 Screenshots

### 1. Authentication
| Sign In | Sign Up |
| :---: | :---: |
| ![Sign In](screenshots/sign-in.png) | ![Sign Up](screenshots/sign-up.png) |

### 2. Main Dashboards (Customer vs. Admin)
| Customer Dashboard | Admin Dashboard |
| :---: | :---: |
| ![Customer Dashboard](screenshots/customer-dashboard.png) | ![Admin Dashboard](screenshots/admin-dashboard.png) |

### 3. Catalog & Inventory
| Customer Book Catalog | Admin Book Management |
| :---: | :---: |
| ![Customer Book List](screenshots/customer-book-list.png) | ![Admin Book List](screenshots/admin-book-list.png) |

### 4. Orders & Warehouse Stock
| Customer Orders History | Admin Warehouse Inventory |
| :---: | :---: |
| ![Customer Orders](screenshots/customer-orders.png) | ![Admin Warehouse](screenshots/admin-warehouse.png) |

### 5. User Profiles
| Customer Profile | Admin Profile |
| :---: | :---: |
| ![Customer Profile](screenshots/customer-profile.png) | ![Admin Profile](screenshots/admin-profile.png) |

### 6. Preferences & Themes
| Application Settings (Dark / Light Theme) |
| :---: |
| ![Settings](screenshots/settings.png) |

---

## ⚡ Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone https://github.com/galaxy248/book-heaven.git
cd book-heaven

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env
```

### 2. Start PostgreSQL (Docker)
```bash
docker compose up -d
```


### 3. Launch Backend & Desktop App
```bash
# Terminal 1 - Backend API (http://127.0.0.1:8080)
python flask/app.py

# Terminal 2 - Desktop Client
python gui/app.py
```

---

## 🔑 Demo Accounts

| Role | Username | Password |
| :--- | :--- | :---: |
| **Customer** | `ali_rezaei` | `1234` |
| **Customer** | `sara_mohammadi` | `1234` |
| **Admin** | `reza_karimi` | `1234` |

---

## 📂 Project Structure

```text
db/
├── docker/            # PostgreSQL initialization script (init.sql)
├── docker-compose.yml # PostgreSQL 16 container definition
├── flask/             # Flask REST API backend & token authentication
├── gui/               # PyQt6 desktop application (UI files, themes, controllers)
│   ├── UI/            # Qt Designer .ui forms & theme-adaptive icons
│   ├── settings/      # Local user session & token cache (git-ignored)
│   └── tmp/           # Shopping cart cache (git-ignored)
├── screenshots/       # Application screenshots
├── requirements.txt   # Python package dependencies
└── README.md
```

---

## 👥 Authors

* **Sina Jani**
* **Arman Heidari**
* **Amir Mohammad Anvari**

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
