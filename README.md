# Introduction to FlickFusion 

## Table of Contents (Open Source Project)

- [Project Overview](#project-overview)
- [Features](#features)
- [Technical Requirements](#technical-requirements)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Commands](#commands)
- [Deployment Options](#deployment-options)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Overview

The **Telegram Movie Request Bot** is a user-friendly bot designed to help users request movies easily within Telegram groups. It automatically forwards movies from a private channel to authorized groups based on user requests. The bot includes a database for managing movie entries and provides a streamlined experience for both users and admins.

## Features

- 🎥 **Automatic Movie Forwarding**: Instantly forward requested movies from a private channel.
- 📝 **Admin Management**: Multiple admin support for managing the movie database.
- 🔍 **Movie Search**: Search for movies by title and year.
- 📩 **Message ID-Based Storage**: Store movies using their Telegram message IDs.
- 📊 **SQLite / PostgreSQL Database Integration**: Use SQLite by default, with an option to connect to PostgreSQL for larger datasets.

## Technical Requirements

To run this bot, ensure you have the following set up:

1. **Python**: Version 3.10 or higher
2. **Telegram API Access**: Obtain a bot token from [BotFather](https://core.telegram.org/bots#botfather)
3. **Admin Privileges**: Admin access in both the group and the private channel
4. **Required Packages**:
   - `python-telegram-bot`
   - `peewee`
   - `python-dotenv`
   - `psycopg2-binary` (optional, for PostgreSQL support)

## Setup Instructions [Tap To View]

<details>
<summary><b>Simple Setup [For pro Guy's only 😁]</b></summary>
  
  A minimal set-up instructions for pro Guy's. 
  
1. **Connect Your VPS**:
2. **Clone Repository**
3. **Install Requirements**
4. **Fill .env with your actual credentials**
5. **Screen -S Flick** (For Running all time)
6. **python main.py**
  
</details>

<details>
<summary><b>Local Set-up</b></summary>

Follow these steps to set up the bot on your local machine:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ReOneSec/FlickFusion.git
   cd FlickFusion 
   ```

2. **Create a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   Create a `requirements.txt` file with the following contents:
   ```
   python-telegram-bot==20.3
   peewee==3.16.0
   python-dotenv==1.0.0
   psycopg2-binary==2.9.6  # Optional, for PostgreSQL support
   ```
   Then install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root with the following content:
   ```ini
   BOT_TOKEN=your_bot_token
   ADMIN_ID=your_user_id,another_admin_id  # Comma-separated for multiple admins
   CHANNEL_ID=your_channel_id
   AUTH_GRP=authorised_group_id,another_group_id  # Comma-separated for multiple groups
   DATABASE_URL=sql-databases.url  # Optional, defaults to local SQLite
   ```

5. **Initialize the Database**:
   Run the following command to create the database and tables:
   ```bash
   python main.py
   ```
</details>

<details>
<summary><b>Deploy on VPS [Ubuntu/Debian]</b></summary>

Follow these steps to set up the bot on an Ubuntu VPS:

1. **Connect to Your VPS**:
   ```bash
   ssh username@your_vps_ip
   ```

2. **Update System and Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv git
   ```

3. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telegram-movie-bot.git
   cd telegram-movie-bot
   ```

4. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Configure Environment Variables**:
   ```bash
   nano .env
   ```
   Add the following content:
   ```ini
   BOT_TOKEN=your_bot_token
   ADMIN_ID=your_user_id,another_admin_id
   CHANNEL_ID=your_channel_id
   AUTH_GRP=authorised_group_id,another_group_id
   DATABASE_URL=sql-databases.url  # Optional
   ```

7. **Run the Bot**:
   ```bash
   python3 main.py
   ```

8. **Setup as a System Service** (Recommended):
   ```bash
   sudo nano /etc/systemd/system/moviebot.service
   ```
   Add the following content:
   ```ini
   [Unit]
   Description=Telegram Movie Request Bot
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/telegram-movie-bot
   ExecStart=/path/to/telegram-movie-bot/venv/bin/python3 main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
   Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable moviebot
   sudo systemctl start moviebot
   ```

9. **Check Service Status**:
   ```bash
   sudo systemctl status moviebot
   ```
</details>

<details>
<summary><b>Deploy in Termux</b></summary>

Follow these steps to run the bot on your Android device using Termux:

1. **Install Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or Google Play Store.

2. **Update Termux and Install Dependencies**:
   ```bash
   pkg update
   pkg upgrade -y
   pkg install -y python git
   ```

3. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telegram-movie-bot.git
   cd telegram-movie-bot
   ```

4. **Set Up Python Environment**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**:
   ```bash
   nano .env
   ```
   Add the following content:
   ```ini
   BOT_TOKEN=your_bot_token
   ADMIN_ID=your_user_id,another_admin_id
   CHANNEL_ID=your_channel_id
   AUTH_GRP=authorised_group_id,another_group_id
   DATABASE_URL=movies.db  # Use SQLite for Termux
   ```

6. **Run the Bot**:
   ```bash
   python main.py
   ```

7. **Keep the Bot Running in Background**:
   ```bash
   # Run the bot with nohup
   nohup python main.py > bot.log 2>&1 &
   ```
   
8. **Managing the Bot**:
   To check if the bot is running:
   ```bash
   ps aux | grep python
   ```
   
   To view log output:
   ```bash
   cat bot.log
   ```
   
   To stop the bot:
   ```bash
   pkill -f "python main.py"
   ```
</details>

## Usage

To start the bot, run the following command:
```bash
python main.py
```

After starting, you can interact with the bot in your Telegram group.

## Commands

### User Commands
- `/start`: Get a welcome message and usage instructions.
- `/help`: Display a list of available commands.
- `/search <Movie Name>`: Check Availability of a movie by title (e.g., `/search Inception`).
- `/get <Movie Name>`: Get This Movie.
- `/get`: To Get Any Random Movie.

### Admin Commands
- `/addmovie <title>`: Add a new movie to the database.
- `/listmovies`: List all available movies in the database.
- `/deletemovie <id>`: Delete a movie by its ID.
- `/cancel`: To cancel any Ongoing Process.

## Deployment Options

<details>
<summary><b>Running as a Background Service</b></summary>

Running as a Background Service

#### Using Screen (Simple Approach)
Screen is a simple tool that allows you to run processes in the background and reattach to them later.

```bash
# Install screen
sudo apt install screen  # Ubuntu/Debian
pkg install screen       # Termux

# Start a new screen session
screen -S moviebot

# Run your bot
python main.py

# Detach from screen (press Ctrl+A, then D)
```

To reattach to the screen session:
```bash
screen -r moviebot
```
</details>

<details>
<summary><b>Using Docker</b></summary>

Using Docker

If you prefer using Docker for deployment:

1. **Create a Dockerfile**:
   ```bash
   nano Dockerfile
   ```
   Add the following content:
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["python", "main.py"]
   ```

2. **Build and Run the Docker Container**:
   ```bash
   docker build -t movie-request-bot .
   docker run -d --name moviebot --restart always --env-file .env movie-request-bot
   ```

3. **Check Container Logs**:
   ```bash
   docker logs -f moviebot
   ```
</details>

## Contributing

Contributions are welcome! If you have suggestions or improvements, please fork the repository and submit a pull request. 

1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, feel free to reach out:

- **Name**: ViperROX 
- **Email**: contactsahabaj@gmail.com
- **Telegram**: [@ViperROX](https://t.me/ViperROX)

---

Thank you for using the Telegram Movie Request Bot! Enjoy exploring the world of cinema with FlickFusion! 🎬🍿
