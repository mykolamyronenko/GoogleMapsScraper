from playwright.async_api import async_playwright
import pandas as pd
import os, sys, time
from tqdm.asyncio import tqdm

# Initialize lists to store data
names, rates, addresses, phones, websites, reviews_count, glinks, links, latitudes, longitudes = [], [], [], [], [], [], [], [], [], []

async def get_search_list():
    # Ask the user whether to input search term manually or use input.txt
    choice = input("Would you like to input search term manually (1) or use input.txt (2)? ")
    if choice == '1':
        # If user chooses manual input, prompt for search term
        search_for = input("Please enter your search term: ")
        search_list = [search_for.strip()]
    elif choice == '2':
        # If user chooses input.txt, read search terms from the file
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = [line.strip() for line in file.readlines()]
        else:
            # If input.txt does not exist, print error and exit
            print(f'Error: {input_file_name} not found.')
            sys.exit()
    else:
        # If user input is invalid, print error and exit
        print('Invalid choice. Exiting.')
        sys.exit()
    return search_list

async def scrape_data(page, total):
    # Count initial number of listings found
    listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
    print(f'Found: {listings}')
    previous_listings = listings
    while listings < total:
        # Scroll down the page to load more listings
        await page.mouse.wheel(0, 10000)
        await page.wait_for_timeout(2000)
        listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
        print(f'Scrolled to: {listings}')
        if listings == previous_listings:
            # Check if end of the list is reached
            if await page.locator('//p[@class="fontBodyMedium "]//span[text()="You\'ve reached the end of the list."]').count() > 0:
                listings = total
                break
            else:
                # Click on the first listing to load more details
                inside_listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                if inside_listings:
                    await inside_listings[0].click()
                    await page.wait_for_timeout(2000)
        previous_listings = listings
    return min(listings, total)

async def extract_data(page, listings):
    # Locate elements containing the required data
    names_by_xpath = await page.locator('//div[contains(@class, "fontHeadlineSmall ")]').all()
    avg_rates_by_xpath = await page.locator('//div[contains(@class,"fontBodyMedium")]//span[contains(@aria-label, "stars")]/span[1]').all()
    glink_by_xpath = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()

    # Extract and store data in respective lists
    for name in tqdm(names_by_xpath[:listings]):
        names.append(await name.inner_text() if name else None)

    for avg_rate in tqdm(avg_rates_by_xpath[:listings]):
        rates.append(await avg_rate.inner_text() if avg_rate else None)

    for glink in tqdm(glink_by_xpath[:listings]):
        glinks.append(await glink.get_attribute('href') if glink else None)

    inside_listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()

    for listing in tqdm(inside_listings[:listings]):
        await listing.click()
        await page.wait_for_timeout(5000)
        address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
        website_xpath = '//a[@data-value="Open website"]'
        phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
        review_count_xpath = '//div[contains(@class, "fontBodyMedium")]//span/span/span[contains(@aria-label, "reviews")]'

        addresses.append(await page.locator(address_xpath).inner_text() if await page.locator(address_xpath).count() > 0 else '')
        websites.append(await page.locator(website_xpath).get_attribute('href') if await page.locator(website_xpath).count() > 0 else '')
        phones.append(await page.locator(phone_number_xpath).inner_text() if await page.locator(phone_number_xpath).count() > 0 else '')
        review_text = await page.locator(review_count_xpath).inner_text() if await page.locator(review_count_xpath).count() > 0 else ''
        reviews_count.append(review_text.replace(',', '').replace('(', '').replace(')', '').strip())
        await page.wait_for_timeout(1000)

async def extract_coordinates():
    # Extract coordinates from the Google Maps links
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--lang=en-US'])
        page = await browser.new_page()
        for glink in tqdm(glinks):
            await page.goto(glink, timeout=60000)
            await page.wait_for_timeout(5000)
            links.append(page.url)
        await browser.close()

    # Parse coordinates from the URL
    for coordinate in links:
        try:
            parts = coordinate.split('@')[1].split(',')
            latitudes.append(parts[0])
            longitudes.append(parts[1])
        except IndexError:
            latitudes.append(None)
            longitudes.append(None)

def save_data(search_for):
    # Create a DataFrame from the extracted data
    map_data = {
        'Name': names, 'Address': addresses, 'Phone': phones, 'Website': websites,
        'Google Link': links, 'Latitude': latitudes, 'Longitude': longitudes,
        'Reviews_Count': reviews_count, 'Average Rates': rates
    }
    df = pd.DataFrame(map_data)
    print(df)

    # Save the DataFrame to an Excel file
    output_folder = 'output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filename = search_for.replace(' ', '_').lower()
    df.to_excel(os.path.join(output_folder, f'{filename}.xlsx'), index=False)

async def main():
    # Get the list of search terms
    search_list = await get_search_list()
    total = int(input("Please enter the total number of results you want: "))

    async with async_playwright() as p:
        start_time = time.time()
        browser = await p.chromium.launch(headless=True, args=['--lang=en-US'])
        page = await browser.new_page()
        await page.goto("https://www.google.com/maps?hl=en", timeout=60000)
        await page.wait_for_timeout(5000)

        # Perform search for each term in the list
        for search_for_index, search_for in enumerate(search_list):
            #print(f"-----\n{search_for_index} - {search_for}")
            print(f"------ {search_for}------")
            await page.locator('//input[@id="searchboxinput"]').fill(search_for)
            await page.wait_for_timeout(3000)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(4000)
            await page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            # Scrape and extract data for the current search term
            listings = await scrape_data(page, total)
            print(f'Processing on: {listings}')
            await extract_data(page, listings)

            # Extract coordinates and save data for the current search term
            await extract_coordinates()
            save_data(search_for)

            # Clear lists for the next search term
            names.clear()
            rates.clear()
            addresses.clear()
            phones.clear()
            websites.clear()
            reviews_count.clear()
            glinks.clear()
            links.clear()
            latitudes.clear()
            longitudes.clear()

        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = elapsed_time / 60
        print(f"Scraping took {minutes:.2f} minutes.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
