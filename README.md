Your README.md has some formatting and clarity issues, especially in the "How to Run Locally" and "Project Structure" sections. Here’s a corrected and improved version for clarity, formatting, and professionalism:

---

# ✨ Aura Buddy

**Aura Buddy** is a Discord economy game bot where users can earn, spend, and flex their "Aura Points" across shops, power-ups, and social leaderboards.  
It's designed to bring fun, competition, and a little chaos to your server 👾

---

## 🚀 Features

- 🪙 **Aura Points** system (earn & spend)
- 🛍️ **Shops** with items to buy using points
- 🧠 **Helpers** to manage logic (modular & scalable)
- 🧩 Easy to extend with more commands
- ⚡ Built to be fast & fun for communities

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **discord.py** (API wrapper)
- **JSON** for shop data
- Designed to be plug-n-play for your server

---

## 🧪 How to Run Locally

> Make sure you have Python 3.10+ installed.

1. **Clone the repo:**
   ```bash
   git clone https://github.com/SpideyHere01/Aura-Buddy.git
   cd Aura-Buddy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** with your bot token:
   ```
   DISCORD_BOT_TOKEN=your-token-here
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

---

## 📁 Project Structure

```
Aura-Buddy/
├── shop/
│   ├── show_shop.py        # Display shop items
│   ├── shop_helpers.py     # Helper functions
│   ├── shops.json          # Item data
├── main.py                 # Bot entry point
├── .env                    # Token (not pushed)
├── requirements.txt
```

---

## 👤 Author

Built with 💙 by SpideyHere01  
If you use it, star the repo ⭐ or share it with your friends!

---

## 📸 Screenshots (Optional)

You can add screenshots or GIFs of the bot in action here later.

---

## 🧠 Want to Contribute?

Feel free to fork the repo and suggest improvements via PRs or issues!  
DM me on Discord if you're a dev and wanna collab.

---

## 📜 License

MIT — do whatever you want, just don’t sell it without changing stuff 😄

---
