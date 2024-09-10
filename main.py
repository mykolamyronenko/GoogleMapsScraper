from playwright.async_api import async_playwright
import pandas as pd
import os, sys, time
from tqdm.asyncio import tqdm

# Initialize lists to store data
data = {
    'names': [], 'rates': [], 'addresses': [], 'phones': [], 'websites': [],
    'reviews_count': [], 'glinks': [], 'links': [], 'latitudes': [], 'longitudes': []
}

async def get_search_list():
    choice = input("Would you like to input search term manually (1) or use input.txt (2)? ")
    if choice == '1':
        search_for = input("Please enter your search term: ")
        return [search_for.strip()]
    elif choice == '2':
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                return [line.strip() for line in file.readlines()]
        else:
            print(f'Error: {input_file_name} not found.')
            sys.exit()
    else:
        print('Invalid choice. Exiting.')
        sys.exit()

async def scrape_data(page, total):
    listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
    print(f'Found: {listings}')
    previous_listings = listings
    while listings < total:
        await page.mouse.wheel(0, 10000)
        await page.wait_for_timeout(2000)
        listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
        print(f'Scrolled to: {listings}')
        if listings == previous_listings:
            if await page.locator('//p[@class="fontBodyMedium "]//span[text()="You\'ve reached the end of the list."]').count() > 0:
                print("You\'ve reached the end of the search query.")
                break
            else:
                inside_listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                if inside_listings:
                    click_index = max(0, listings - 3)
                    await inside_listings[click_index].click()
                    print(click_index)
                    await page.wait_for_timeout(2000)
        previous_listings = listings
    return min(listings, total)

async def extract_listing(page, listings):
    glink_by_xpath = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
    for glink in tqdm(glink_by_xpath[:listings]):
        data['glinks'].append(await glink.get_attribute('href') if glink else None)

async def extract_listing_elements():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--lang=en-US'])
        page = await browser.new_page()
        for glink in tqdm(data['glinks']):
            await page.goto(glink, timeout=60000)
            await page.wait_for_timeout(5000)
            data['links'].append(page.url)
            data['names'].append(await get_element_text(page, '//div[@style="padding-bottom: 4px;"]//h1'))
            data['rates'].append(await get_element_text(page, '//div[@style="padding-bottom: 4px;"]//div[contains(@jslog,"mutable:true;")]/span[1]/span[1]'))
            data['addresses'].append(await get_element_text(page, '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'))
            data['websites'].append(await get_element_attribute(page, '//a[@data-value="Open website"]', 'href'))
            data['phones'].append(await get_element_text(page, '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'))
            review = await get_element_text(page, '//div[@style="padding-bottom: 4px;"]//div[contains(@jslog,"mutable:true;")]/span[2]')
            data['reviews_count'].append(review.replace(',', '').replace('(', '').replace(')', '').strip())
            await page.wait_for_timeout(2000)
        await browser.close()

async def get_element_text(page, selector, timeout=30000):
    try:
        element = page.locator(selector)
        if await element.count() > 0:
            return await element.inner_text(timeout=timeout)
        return ''
    except Exception as e:
        print(f"Error getting text for selector {selector}: {e}")
        return ''

async def get_element_attribute(page, selector, attribute, timeout=30000):
    try:
        element = page.locator(selector)
        if await element.count() > 0:
            return await element.get_attribute(attribute, timeout=timeout)
        return ''
    except Exception as e:
        print(f"Error getting attribute {attribute} for selector {selector}: {e}")
        return ''

def parse_coordinates():
    for coordinate in data['links']:
        try:
            parts = coordinate.split('@')[1].split(',')
            data['latitudes'].append(parts[0])
            data['longitudes'].append(parts[1])
        except IndexError:
            data['latitudes'].append(None)
            data['longitudes'].append(None)

def save_data(search_for):
    map_data = {
        'Name': data['names'], 'Address': data['addresses'], 'Phone': data['phones'], 
        'Website': data['websites'], 'Google Link': data['links'], 
        'Latitude': data['latitudes'], 'Longitude': data['longitudes'], 
        'Reviews_Count': data['reviews_count'], 'Average Rates': data['rates']
    }
    df = pd.DataFrame(map_data)
    print(df)
    output_folder = 'output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filename = search_for.replace(' ', '_').lower()
    df.to_excel(os.path.join(output_folder, f'{filename}.xlsx'), index=False)

async def main():
    search_list = await get_search_list()
    total = int(input("Please enter the total number of results you want: "))

    async with async_playwright() as p:
        start_time = time.time()
        browser = await p.chromium.launch(headless=True, args=['--lang=en-US'])
        page = await browser.new_page()
        await page.goto("https://www.google.com/maps?hl=en", timeout=60000)
        await page.wait_for_timeout(5000)

        for search_for in search_list:
            print(f"------ {search_for} ------")
            await page.locator('//input[@id="searchboxinput"]').fill(search_for)
            await page.wait_for_timeout(3000)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(4000)
            await page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            listings = await scrape_data(page, total)
            print(f'Processing on: {listings}')
            await extract_listing(page, listings)
            await extract_listing_elements()
            parse_coordinates()
            save_data(search_for)

            for key in data.keys():
                data[key].clear()

        end_time = time.time()
        print(f"Scraping took {(end_time - start_time) / 60:.2f} minutes.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
