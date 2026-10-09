# 💌 Date Invite

A romantic, interactive invitation website built to make asking someone out feel personal and memorable.

The experience is presented in Persian (Farsi) and guides visitors through a series of playful choices in an elegant dark interface with gold accents.

## ✨ Features

- 💌 A custom opening message and interactive invitation
- 💖 Step-by-step questions and responses
- 🍽️ Food preference selection
- 🕗 Date-time selection
- 📱 Responsive layout for mobile and desktop
- ✨ Animated transitions and decorative effects
- 🔐 Admin page for reviewing submitted answers
- 🐍 Python and Django backend

## 🧰 Built With

- Python
- Django
- SQLite
- HTML
- CSS
- JavaScript

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/MohammadMHB/Date-invite.git
cd Date-invite
```

### 2. Install dependencies

Make sure Python is installed, then run:

```bash
pip install -r requirements.txt
```

### 3. Run the application

If the Django entry-point file is in the current directory, start the app with:

```bash
gunicorn app:application
```

For local development, use the project's configured Django entry point. If the application is located in a subdirectory, enter that directory first.

## ⚙️ Configuration

The application supports these environment variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `ADMIN_PASSWORD` | Password for the admin panel |
| `DEBUG` | Set to `1` to enable debug mode |

Use a strong secret key and admin password in production. Do not commit credentials or secret environment files to the repository.

## 🔎 Admin Panel

The admin panel is available at:

```text
/panel/
```

Open this route on your deployed website and use the configured admin password to review submitted answers.

## 💾 Data Persistence

The app currently uses SQLite for storing responses. On serverless platforms, a database stored in a temporary directory may be cleared between executions or deployments. For reliable long-term storage, configure a persistent database.

## 🌐 Deployment

The app can be deployed to a Python-compatible hosting platform with the appropriate project and runtime configuration.

## 👤 Author

**Mohammad Mohebianfar**

- GitHub: [@MohammadMHB](https://github.com/MohammadMHB)

---

Made with ❤️ for a little extra romance.
