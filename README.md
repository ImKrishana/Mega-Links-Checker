# Mega Links Checker Bot

A Telegram bot to check MEGA.nz links displays file/folder names, sizes, lists files and folders.

## Deployment Guide

<details>
  <summary><strong>Heroku (One-Click Deploy)</strong></summary>

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/ImKrishana/Mega-Links-Checker/tree/main)

</details>

<details>
  <summary><strong>Render (One-Click Deploy)</strong></summary>

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ImKrishana/Mega-Links-Checker&branch=main)

</details>

<details>
  <summary><strong>Koyeb (One-Click Deploy)</strong></summary>

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?name=mega-links-checker&type=git&repository=ImKrishana%2FMega-Links-Checker&branch=main&instance_type=free&regions=fra&instances_min=1&env%5BAPI_ID%5D=&env%5BAPI_HASH%5D=&env%5BBOT_TOKEN%5D=&env%5BOWNER_ID%5D=&env%5BDATABASE_URL%5D=&env%5BLOG_CHANNEL%5D=&env%5BPORT%5D=8080)

</details>
<details>
  <summary><strong>Railway (One-Click Deploy)</strong></summary>

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template?template=https://github.com/ImKrishana/Mega-Links-Checker)

</details>
<details>
  <summary><strong>VPS / Locally</strong></summary>

  1. **Clone the repository:**
      ```sh
      git clone https://github.com/ImKrishana/Mega-Links-Checker.git
      cd Mega-Links-Checker
      ```

  2. **Install dependencies:**
      ```sh
      pip install -r requirements.txt
      ```

  3. **Configure bot:**
      - Edit `config.py` with your Telegram API ID, HASH, BOT TOKEN & DATABASE URL.

  4. **Run the bot:**
      ```sh
      python3 main.py
      ```

</details>

<details>
  <summary><strong>Docker</strong></summary>

  1. **Clone the repository:**
      ```sh
      git clone https://github.com/ImKrishana/Mega-Links-Checker.git
      cd Mega-Links-Checker
      ```

  2. **Configure environment variables:**
      - Create a `.env` file:
      ```env
      BOT_TOKEN=your_bot_token
      API_ID=your_api_id
      API_HASH=your_api_hash
      OWNER_ID=your_owner_id
      DATABASE_URL=your_mongodb_url
      LOG_CHANNEL=[]
      PORT=8080
      ```

  3. **Build and start the container:**
      ```sh
      docker compose up -d --build
      ```

  4. **View logs:**
      ```sh
      docker compose logs -f thezake
      ```

  5. **Stop the bot:**
      ```sh
      docker compose down
      ```

</details>

<details>
  <summary><strong>Heroku CLI</strong></summary>

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/ImKrishana/Mega-Links-Checker MLC && cd MLC
   ```

3. **Create `config.py` File**
   ```bash
   nano config.py
   ```

   Add the required variables:
   ```python
   BOT_TOKEN = "your_bot_token"
   API_ID = 12345678
   API_HASH = "your_telegram_api_hash"
   DATABASE_URL = "your_mongodb_url"
   OWNER_ID = 123456789
   LOG_CHANNEL [-100xxxxxxxx]
   ```

4. **Commit Changes**
   ```bash
   git add . -f
   git commit -m "thezake"
   ```

5. **Create Heroku App**
   ```bash
   heroku create APP_NAME
   ```

6. **Add Remote**
   ```bash
   heroku git:remote -a APP_NAME
   ```

7. **Set Container Stack**
   ```bash
   heroku stack:set container
   ```

8. **Deploy**
   ```bash
   git push heroku main -f
   ```

9. **Check Logs**
   ```bash
   heroku logs --tail
   ```

</details>

## Variables 

<details>
  <summary><strong>View Required Variables</strong></summary>

  <br>

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | **Yes** | Your Telegram Bot Token from [@BotFather](https://t.me/BotFather) |
| `API_ID` | **Yes** | Your Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | **Yes** | Your Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `DATABASE_URL` | **Yes** | MongoDB connection URL used for storing bot data |
| `LOG_CHANNEL` | No | Optional: Channel ID for logging mega links (format: `-100xxxxxxxxxx`) |
| `PORT` | No | Port used by the web server (default: `8080`) |

</details>

## Screenshots/Demo

<details>
  <summary><strong>View Bot Interface</strong></summary>

  <br>
  <p align="center">
    <kbd>
      <img width="600" src="demo.jpg" alt="Demo">
    </kbd>
  </p>

</details>

## Admin Side

<details>
<summary><strong>Authorization Management</strong></summary>

### Authorize Users/Chats

Grant access to users or groups to use the bot.

Authorizes the current chat.
```
/authorize
```

**Authorize Specific User/Chat:**
```
/authorize CHAT_ID or USER_ID
```

**Authorize Topic in Group:**
```
/authorize CHAT_ID|TOPIC_ID
```

---

### Unauthorize Users/Chats

Remove access from authorized users or groups.

Unauthorizes the current chat.
```
/unauthorize
```

**Unauthorize Specific User/Chat:**
```
/unauthorize CHAT_ID
```

**Unauthorize Topic:**
```
/unauthorize CHAT_ID|TOPIC_ID
```

---

> **Note:** If you want to restrict specific commands to only authorized users/chats, add `CustomFilters.authorized` to the command filter in `core/handlers.py`.

**Example:**
```python
MessageHandler(
    your_command,
    filters.command("your_command") & CustomFilters.authorized
)
```

This allows the command only for authorized users/chats.

</details>

<details>
<summary><strong>Broadcast System</strong></summary>

**Forward with Tag:**
Broadcast with original sender tag.
```
/broadcast -f
```

**Silent Broadcast:**
Broadcast without notification sound.
```
/broadcast -q
```

**Combined Options:**
```
/broadcast -f -q
```

---

### Edit Broadcasts

Edit previously sent broadcast messages.
```
/broadcast BROADCAST_ID -e
```

---

### Delete Broadcasts

Delete broadcast messages from all users.

```
/broadcast BROADCAST_ID -d
```

---

### Broadcast Options

| Flag | Description |
|------|-------------|
| `-f` or `-forward` | Forward message with tag |
| `-q` or `-quiet` | Send without notification |
| `-e` or `-edit` | Edit existing broadcast |
| `-d` or `-delete` | Delete broadcast |

**Important Notes:**
- Broadcast IDs are valid only until bot restart
- After restart, you cannot edit/delete old broadcasts
- Forwarded messages can only be deleted, not edited
- Stats show: Total, Success, Blocked, Deleted, Failed

</details>

## Extras

Live bot can be found here

**Demo Bot:** [@MegaLinksCheckBot](https://t.me/MegaLinksCheckBot)

U can test all features and commands to see how it works!

<details>
  <summary><strong>Disclaimer</strong></summary>

This bot is developed strictly for **educational and research purposes only**.

</details>

---

[![License](https://img.shields.io/github/license/ImKrishana/Mega-Links-Checker)](https://github.com/ImKrishana/Mega-Links-Checker/blob/main/LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-26A5E4?logo=telegram&logoColor=white)](https://t.me/LeechBots)

If you like this project, don't forget to give it a Star !

**Developer:** [The Zake](https://t.me/TheZake)
