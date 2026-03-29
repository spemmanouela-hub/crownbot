#!/bin/bash
cd /home/ubuntu/discord-bot
source venv/bin/activate
python bot.py
```

**`.gitignore`**
```
.env
servers.db
__pycache__/
*.pyc
