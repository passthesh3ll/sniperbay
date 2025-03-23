import json, re, math, httpx, asyncio, telegram, asyncio
from typing import Dict, List, Literal
from urllib.parse import urlencode
from parsel import Selector

# GLOBAL INSTANCE OF BOT
TOKEN = ''
CHAT_ID = ''
bot = telegram.Bot(token=TOKEN)

session = httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    http2=True,
    #follow_redirects=True
)

eu_members = [
    "Austria", "Belgio", "Bulgaria","Cipro", "Croazia", "Danimarca", "Estonia", "Finlandia", "Francia",
    "Germania", "Grecia", "Irlanda", "Italia", "Lettonia", "Lituania", "Lussemburgo", "Malta", "Paesi Bassi", 
    "Polonia", "Portogallo", "Repubblica Ceca", "Romania", "Slovacchia", "Slovenia", "Spagna", "Svezia", "Ungheria"
]

def has_characters(string):
    for char in string:
        if char.isalpha():
            return True
    return False

def clean_price(price):
    price = price.replace(" di spese di spedizione stimate","")
    price = price.replace(" di spese di spedizione","")
    price = price.replace("+EUR ","")
    price = price.replace("EUR ","")
    price = price.replace(",",".")
    price = price.strip()
    return price
    
def parse_search(response: httpx.Response) -> List[Dict]:
    """parse ebay's search page for listing preview details"""
    previews = []
    # each listing has it's own HTML box where all of the data is contained
    sel = Selector(response.text)
    listing_boxes = sel.css(".srp-results li.s-item")
    for box in listing_boxes:
        # quick helpers to extract first element and all elements
        css = lambda css: box.css(css).get("").strip()
        css_all = lambda css: box.css(css).getall()


        url = css("a.s-item__link::attr(href)").split("?")[0]
        title = css(".s-item__title>span::text")
        if css(".s-item__price .ITALIC::text"):
            price = css(".s-item__price .ITALIC::text").replace(" da","")
        else:
            price = css(".s-item__price::text").replace(" da","")
        price = clean_price(price)

        if css(".s-item__shipping .ITALIC::text"):
            shipping = css(".s-item__shipping .ITALIC::text")
        else: 
            shipping = css(".s-item__shipping::text")
        shipping = clean_price(shipping)

        if has_characters(shipping): # se è un numero
            total_price = price
        else:
            total_price = float(price)+float(shipping)
            total_price = f"{total_price:.2f}"

        if css(".s-item__itemLocation .ITALIC::text"):
            location = css(".s-item__itemLocation .ITALIC::text")
        else: 
            location = css(".s-item__itemLocation::text")
        location = location.replace("da ","")

        #list_date = css(".s-item__listingDate span::text"),
        time_left = css(".s-item__time-left::text")
        subtitles = css_all(".s-item__subtitle::text")
        if(" | " in subtitles): subtitles.remove(" | ")
        condition = css(".s-item__subtitle .SECONDARY_INFO::text")
        photo = css(".s-item__image img::attr(src)")
        #rating = css(".s-item__reviews .clipped::text"),
        #rating_count = css(".s-item__reviews-count span::text"),

        previews.append(
            {
                "url": url,
                "title": title,
                "price": price,
                "shipping":shipping,
                "total_price":total_price,
                "location":location,
                "time_left": time_left,
                "subtitles": subtitles,
                "condition": condition,
                "photo": photo,
            }
        )
    return previews

async def scrape_search(
    query,
    max_pages=1,
    category=58058, #categoria informatica
    items_per_page=240,
    #sort: Literal["best_match", "ending_soonest", "newly_listed"] = "newly_listed",
) -> List[Dict]:
    """Scrape Ebay's search results page for product preview data for given"""

    def make_request(page):
        return "https://www.ebay.it/sch/i.html?" + urlencode(
            {
                "_nkw": query,
                "_sacat": category,
                "_ipg": items_per_page,
                "_sop": '15',
                "_pgn": page,
                # SNIPER PARAMETERS
                "LH_TitleDesc": '1',
                "LH_Auction":'1',
                "LH_Time":'1',
                "_ftrt":'901',
                "_ftrv":'1',
                "_dmd":'2',
                "imm":'1',
                "LH_PrefLoc":'2',
                # LH_PrefLoc=0 (Default)
                # LH_PrefLoc=1 (My country)
                # LH_PrefLoc=2 (Worldwide)
                # LH_PrefLoc=3 (United States)
                # LH_PrefLoc=99&rt=nc&_stpos=POSTCODE&_sadis=MILES&_fspt=1 (Within MILES of POSTCODE)
            }
        )

    first_page = await session.get(make_request(page=1))
    results = parse_search(first_page)
    if max_pages == 1:
        return results
    # find total amount of results for concurrent pagination
    total_results = first_page.selector.css(".srp-controls__count-heading>span::text").get()
    total_results = int(total_results.replace(",", ""))
    total_pages = math.ceil(total_results / items_per_page)
    if total_pages > max_pages:
        total_pages = max_pages
    other_pages = [session.get(make_request(page=i)) for i in range(2, total_pages + 1)]
    for response in asyncio.as_completed(other_pages):
        response = await response
        try:
            results.extend(parse_search(response))
        except Exception as e:
            print(f"failed to scrape search page {response.url}")
    return results

async def send_message(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.HTML)
    except Exception as e:
        print(f"Error sending the message: {e}")

async def main():
    # run search
    data = await scrape_search("(0,1,2,3,4,5,6,7,8,9,a,b,c,p,an,the,of,for,i,my,new,used)")
    #print(json.dumps(data, indent=4))

                # "url": url,
                # "title": title,
                # "price": price,
                # "shipping":shipping,
                # "total_price":total_price,
                # "location":location,
                # "time_left": time_left,
                # "subtitles": subtitles,
                # "condition": condition,
                # "photo": photo,


    await send_message("📢 <b>Nuove aste in scadenza</b>")
    await asyncio.sleep(3)
    for item in data:
        if (item['location'] in eu_members) and (float(item['total_price'])<45):
            message = ""
            message += f"📦️ <b>{item['title']}</b>\n"
            message += f"💰️ {item['total_price']}€ ({item['price']}€ 💶 + {item['shipping']}€ ✈️)\n"
            message += f"⏳️ {item['time_left']}\n"
            message += f"🌍️ {item['location']}\n"
            message += f"{item['url']}\n"
            
            await asyncio.sleep(3)
            await send_message(message)

if __name__ == "__main__":
    asyncio.run(main())
