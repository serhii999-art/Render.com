import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError
import asyncio

# --- НАЛАШТУВАННЯ ---
TELEGRAM_TOKEN = "7889549476:AAH0lD6ceeMUw6ciKXL1yNBWtrLCvArNgOw"
CHAT_ID = "-1002985889083"

# Крок 1: Створюємо список сайтів для моніторингу
SITES = [
    {
        "name": "Telemart Outlet",
        "url": "https://telemart.ua/ua/outlet/",
        "css_selector": ".product-item .product-title a",
        "base_url": "https://telemart.ua"  # Для доповнення відносних посилань
    },
    {
        "name": "Setka.ua",
        "url": "https://setka.ua/",
        "css_selector": "a.product-card__title",  # Правильний селектор для Setka.ua
        "base_url": "https://setka.ua"  # Потрібно для доповнення відносних посилань
    },
    {
        "name": "Brain Уцінка",
        "url": "https://brain.com.ua/ukr/exclusive/#categoryIDs=K0041,K0001,K0051;",
        "css_selector": ".col-xs-12 .name a",  # Селектор для Brain
        "base_url": "https://brain.com.ua"  # Для доповнення відносних посилань
    }
]

# Глобальний сет для всіх відвіданих посилань з усіх сайтів
visited_links = set()


# Крок 2: Оновлюємо функцію, щоб вона приймала параметри сайту
def check_new_products(site_name, site_url, css_selector, base_url):
    """Перевіряє сторінку на наявність нових товарів за заданими параметрами."""
    global visited_links
    print(f"Перевіряю {site_name}...")
    try:
        response = requests.get(site_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Помилка при запиті до {site_name}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.select(css_selector)

    new_items = []
    for product in products:
        link = product['href']
        # Створюємо повне посилання, якщо воно відносне
        if not link.startswith('http'):
            link = base_url + link

        title = product.text.strip()
        if link not in visited_links:
            # Додаємо назву сайту до повідомлення
            message = f"[{site_name}] {title}\n{link}"
            visited_links.add(link)
            new_items.append(message)

    return new_items


async def send_telegram_message(bot, message):
    """Надсилає повідомлення в Telegram асинхронно."""
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except TelegramError as e:
        print(f"Не вдалося надіслати повідомлення: {e}")


async def main():
    if TELEGRAM_TOKEN == "ВАШ_ТЕЛЕГРАМ_ТОКЕН" or CHAT_ID == "ВАШ_CHAT_ID":
        print("ПОМИЛКА: Будь ласка, вставте ваші реальні TELEGRAM_TOKEN та CHAT_ID у код.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    await send_telegram_message(bot, "✅ Бот для моніторингу декількох сайтів запущено!")

    # Спочатку заповнюємо базу всіма існуючими товарами з усіх сайтів
    print("Перший запуск: збираю існуючі товари...")
    for site in SITES:
        initial_products = check_new_products(site["name"], site["url"], site["css_selector"], site["base_url"])
        print(f"На {site['name']} знайдено {len(initial_products)} товарів.")

    while True:
        # Крок 3: В головному циклі проходимось по кожному сайту
        all_new_products = []
        for site in SITES:
            new_products_from_site = check_new_products(site["name"], site["url"], site["css_selector"],
                                                        site["base_url"])
            if new_products_from_site:
                all_new_products.extend(new_products_from_site)

        if all_new_products:
            print(f"🔥 Знайдено нові товари: {len(all_new_products)}")
            for product_message in all_new_products:
                await send_telegram_message(bot, product_message)
        else:
            print("Нових товарів на жодному з сайтів немає.")

        print("Наступна перевірка через 30 хвилин.")
        await asyncio.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main())