# SniperBay Telegram Bot
![sniperbay](https://github.com/user-attachments/assets/17e6d2b5-b6a2-401e-9d45-b7403cc1ab86)


## Description

A telegram bot to scrape the close to expiry (~1h) auction from the computer section of ebay.it, and post them in a telegram channel, ready to be sniped/scalped.

## Dependencies

* `parsel`
* `python-telegram-bot`
* `httpx[http2]`
* `asyncio`

## Configuration

1. Obtain a Telegram Bot Token using BotFather and put TOKEN and CHAT_ID in the variables at the beginning of the code
```python
TOKEN = ''
CHAT_ID = ''
```
2. Add your bot to the Telegram chat where you want to receive notifications
3. If you want you can change min price (45€ by default) and location filter (EU by default)
```py
if (item['location'] in eu_members) and (float(item['total_price'])<45):
```
4. You can schedule the bot with cron (I suggest 30min for the best trade-off)

## Screen
![image](https://i.imgur.com/AEjcErg.png)
