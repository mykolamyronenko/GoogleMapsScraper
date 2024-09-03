from playwright.sync_api import sync_playwright
import pandas as pd
import os, sys, time
from tqdm import tqdm

map_names = []
rates = []
addresses = []
phones = []
websites = []
reviews_count = []

def main():
    search_for = input("Please enter your search term: ")
    total = int(input("Please enter the total number of results you want: "))

    # Prepare the list of search terms
    search_list = [search_for.strip()] if search_for else []
    if not search_list:
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = [line.strip() for line in file.readlines()]
        if not search_list:
            print('Error occurred: You must either pass the -s search argument, or add searches to input.txt')
            sys.exit()

    with sync_playwright() as p:
        start_time = time.time()
        browser = p.chromium.launch(headless=True, args=['--lang=en-US'])
        page = browser.new_page()
        page.goto("https://www.google.com/maps?hl=en", timeout=60000)
        page.wait_for_timeout(5000)
        

        for search_for_index, search_for in enumerate(search_list):
            print(f"-----\n{search_for_index} - {search_for}")
            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.wait_for_timeout(3000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
        print(f'Found: {listings}')
        previous_listings = listings
        while listings < total:
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(2000)
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
            print(f'Scrolled to: {listings}')
            if listings == previous_listings:
                if page.locator('//p[@class="fontBodyMedium "]//span[text()="You\'ve reached the end of the list."]').count() > 0:
                    listings = total
                    break
                else:
                    inside_listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:listings]
                    if inside_listings:
                        inside_listings[0].click()
                        page.wait_for_timeout(2000)
                        # page.locator('//button[@aria-label="Close"]/div').click()
                        # page.wait_for_timeout(2000)
            previous_listings = listings
        if listings > total:
            listings = total

        print(f'Processing on: {listings}')

        names_by_xpath = page.locator('//div[contains(@class, "fontHeadlineSmall ")]').all()[:listings]
        avg_rates_by_xpath = page.locator('//div[contains(@class,"fontBodyMedium")]//span[contains(@aria-label, "stars")]/span[1]').all()[:listings]

        for name in tqdm(names_by_xpath):
            if page.locator('//div[contains(@class, "fontHeadlineSmall ")]').count() > 0:
                map_names.append(name.inner_text())
                page.wait_for_timeout(2000)
            else:
                map_names.append(None)

        for avg_rate in tqdm(avg_rates_by_xpath):
            if page.locator('//div[contains(@class,"fontBodyMedium")]//span[contains(@aria-label, "stars")]/span[1]').count() > 0:
                rates.append(avg_rate.inner_text())
                page.wait_for_timeout(2000)
            else:
                rates.append(None)

        inside_listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:listings]

        for listing in tqdm(inside_listings):
            listing.click()
            page.wait_for_timeout(3000)
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            review_count_xpath = '//div[contains(@class, "fontBodyMedium")]//span/span/span[contains(@aria-label, "reviews")]'

            if page.locator(address_xpath).count() > 0:
                address = page.locator(address_xpath).all()[0].inner_text()
                page.wait_for_timeout(2000)
            else:
                address = ''
            addresses.append(address)

            if page.locator(website_xpath).count() > 0:
                website = page.locator(website_xpath).all()[0].inner_text()
                page.wait_for_timeout(2000)
            else:
                website = ''
            websites.append(website)

            if page.locator(phone_number_xpath).count() > 0:
                phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                page.wait_for_timeout(2000)
            else:
                phone_number = ''
            phones.append(phone_number)

            if page.locator(review_count_xpath).count() > 0:
                review_count = page.locator(review_count_xpath).inner_text().replace(',', '').replace('(', '').replace(')', '').strip()
                page.wait_for_timeout(2000)
            else:
                review_count = ''
            reviews_count.append(review_count)
            page.wait_for_timeout(1000)

        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = elapsed_time / 60
        print(f"Scraping took {minutes:.2f} minutes.")

        map_data = {'Name': map_names, 'Address': addresses, 'Phone': phones, 'Website': websites, 'Reviews_Count': reviews_count, 'Average Rates': rates}
        df = pd.DataFrame(map_data)
        print(df)

        output_folder = 'output'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        filename = search_for.replace(' ', '_').lower()
        df.to_excel(os.path.join(output_folder, f'{filename}.xlsx'), index=False)
        browser.close()

if __name__ == "__main__":
    main()
