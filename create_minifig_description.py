# html parsing and browser surfing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

# accepting args
import sys

# sleeping and date retrieval
import time
from datetime import datetime

# function to get them and subtheme of minifig (e.g., NINJAGO: Rise of the Snakes)
def get_themes(soup):

    # the only mention of the themes is in the string of links at the top of the page
    # have to do some digging to get to the actual text of the themes
    title_parent = soup.find('div', class_='innercontent')
    title_table = title_parent.find_all('table')[0]
    title_text = title_table.text.strip()

    theme = None
    subtheme = None

    # set subtheme if present; otherwise set it as N/A
    if len(title_text.split(':')) == 5:
        theme = title_text.split(':')[2].strip()
        subtheme = title_text.split(':')[3].strip()
    elif len(title_text.split(':')) == 4:
        theme = title_text.split(':')[2].strip()
        subtheme = 'N/A'

    return theme, subtheme

# function to get release year(s) of the minifig
def get_release_years(soup):

    # when the years are a range (e.g., 2012 - 2013), the start year is contained in the yearReleasedSec ID and the end year is just the next element in the HTML
    start_year_element = soup.find(id='yearReleasedSec')

    # get next sibling element; it will either be a year (e.g., '- 2013') or a <br>
    end_year_element = start_year_element.next_sibling
    start_year = start_year_element.text.strip()

    release_year = ''

    # year_range is a bool for if the year is singular or a range
    year_range = False

    # if the end year element is <br> its text will be an empty string
    if end_year_element.text.strip() != '':
        release_year += f"{start_year} {end_year_element.text.strip()}"
        year_range = True
    else:
        release_year += start_year
    
    return release_year, year_range

# function to get appearance bools since minifigs can appear in books, sets, whatever else
def get_appearance_bools(soup):

    # instantiate bools
    set_appearance = None
    book_appearance = None

    # make a list of all element trees labaled as a table
    tables = soup.find_all('table')

    # find the table containing appearances matching a string always present (I think)
    appearance_table = None
    for table in tables:
        if "Item Appears In" in table.text:
            appearance_table = table

    # find all elements labeled 'td' (table data) in the selected table
    table_data = appearance_table.find_all('td')
    appearance_data = None

    # parse through table data and find element containing desired info, again with matching a string that is probably always present
    for data in table_data:
        if "Item Appears In" in data.text.strip():
            appearance_data = data
    
    # set bools based on if media appearances are listed; BrickLink either shows '1 Book/1 Set' or they don't show anything
    if "Set" in appearance_data.text.strip():
        set_appearance = True
    if "Book" in appearance_data.text.strip():
        book_appearance = True

    return set_appearance, book_appearance

# function to get a list of all the sets the minifig appears in
def get_set_appearances(driver, identifier):

    # load the webpage with the list of sets per minifig
    driver.get(f"https://www.bricklink.com/catalogItemIn.asp?M={identifier}&in=S")

    # get HTML/JS script
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # make a list of all element trees labaled as a table
    tables = soup.find_all('table')

    table_index = None

    # since the table containing the sets doesn't have a class or id, I found it by matching text that every webpage shares in the target table
    for i, table in enumerate(tables):

        # store table index if target text is present in table
        if 'Appears As Regular:' in table.text.strip():
            table_index = i
            
    # if table_index remains as None, the target table was not found
    if table_index is None:
        raise ValueError("Set Appearance Table Not Found")
    
    # store extraced sets in 'Set Name - Set Number' format
    sets = []
    
    # find all the table rows in the table containing the sets
    set_table = tables[table_index].find_all('tr')

    # dynamically find row start index; while HTML/JS is mostly the same there are slight differences that make it impossible to rely on a static start index
    start_index = None
    for i, item in enumerate(set_table):

        # store row start index if target text is present in a row
        if 'Appears As Regular:' in item.text.strip():
            start_index = i + 1
            break
    # if start_index remains as None, the target row was not found
    if start_index is None:
        raise ValueError("Start Index Not Found")

    # skip initial bloat
    set_items = set_table[start_index:]

    # populate sets list
    for set in set_items:

        # get table data for each listed set
        set_soup = set.find_all('td')

        # extract set name and number using some funky shit
        set_number = set_soup[2].text.strip().split('(')[0].strip()
        set_name_unmatched = set_soup[3].text.strip()
        set_name = re.match(r'^([^\d]+)', set_name_unmatched).group(1).strip()
        sets.append(f"{set_name} - {set_number}")

    return sets

def get_book_appearances(driver, identifier):
    driver.get(f"https://www.bricklink.com/catalogItemIn.asp?M={identifier}&in=B")

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # make a list of all element trees labaled as a table
    tables = soup.find_all('table')

    table_index = None

    # since the table containing the book doesn't have a class or id, I found it by matching text that every webpage shares in the target table
    for i, table in enumerate(tables):

        # store table index if target text is present in table
        if 'Appears As Regular:' in table.text.strip():
            table_index = i
            
    # if table_index remains as None, the target table was not found
    if table_index is None:
        raise ValueError("Book Appearance Table Not Found")
    
    # store extraced books in 'Book Name - Book Number' format
    books = []
    
    # find all the table rows in the table containing the books
    book_table = tables[table_index].find_all('tr')

    # dynamically find row start index; while HTML/JS is mostly the same there are slight differences that make it impossible to rely on a static start index
    start_index = None
    for i, item in enumerate(book_table):

        # store row start index if target text is present in a row
        if 'Appears As Regular:' in item.text.strip():
            start_index = i + 1
            break

    # if start_index remains as None, the target row was not found
    if start_index is None:
        raise ValueError("Start Index Not Found")

    # skip initial bloat
    book_items = book_table[start_index:]

    # populate book list
    for book in book_items:

        # get table data for each listed book
        book_soup = book.find_all('td')

        # extract book name and number using some funky shit
        book_number = book_soup[2].text.strip().split('(')[0].strip()
        book_name_unmatched = book_soup[3].text.strip()
        book_name = re.match(r'^([^\d]+)', book_name_unmatched).group(1).strip()
        book_name = book_name.split("Catalog:")[0]
        books.append(f"{book_name} - {book_number}")

    return books
    
    
# function to get min, avg, and max price during the CURRENT time period
def get_prices(soup):

    # all 4 prices tables share the same class so store all of them in a list and pick the index of the desired one (Current, Used)
    price_tables = soup.find_all('table', class_='pcipgSummaryTable')
    current_used_table = price_tables[3]

    # get all the rows contained within the table body
    current_used_rows = current_used_table.find('tbody').find_all('tr')

    # get the price types which are structured as '[Type:, US $1.00]'
    min_price = current_used_rows[2].find_all('td')[1].text.strip()
    avg_price = current_used_rows[3].find_all('td')[1].text.strip()
    max_price = current_used_rows[5].find_all('td')[1].text.strip()

    return min_price, avg_price, max_price

# function to get the date when the script is run for pricing purposes
def get_date():
    now = datetime.now()
    formatted_date = now.strftime("%m/%d/%Y")
    return formatted_date

# thing that does the stuff
if __name__ == '__main__':

    # take the item number (e.g., njo0047) as the first argument
    identifier = sys.argv[1]

    # trying to suppress DevTools log but no luck
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    driver = webdriver.Chrome(options=options)

    # load minifig page with price guide section selected to get most info in one page
    driver.get(f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={identifier}#T=P")

    # wait for cookie popup and destroy that shit (using JS because it didn't work the other way)
    cookie_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[text()='Just necessary']"))
    )
    driver.execute_script("arguments[0].click();", cookie_btn)

    # get HTML/JS for the whole page
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # sleep for 1/5 seconds to let the page load in fully
    time.sleep(.20)

    # get the name using its conveniently named ID
    name = soup.find(id='item-name-title').text.strip()

    # get theme and subtheme
    theme, subtheme = get_themes(soup=soup)

    # get release year and year range bool
    release_year, year_range = get_release_years(soup=soup)

    # get the weight using its conveniently named ID
    weight = soup.find(id='item-weight-info').text.strip()

    # get bools for the types of media the minifig appears in (sets, books, etc later)
    in_sets, in_books = get_appearance_bools(soup=soup)

    # get the date for price transparency
    date = get_date()

    # get min, avg, and max price
    min_price, avg_price, max_price = get_prices(soup=soup)

    # print all of the scraped information since I only need to copy the text from the terminal; plurals are accounted for
    print(f"Minifig Name: {name}")
    print(f"Item Number: {identifier}")
    print(f"Theme: {theme}")
    print(f"Subtheme: {subtheme}")
    if year_range is True:
        print(f"Years Released: {release_year}")
    elif year_range is False:
        print(f"Year Released: {release_year}")
    print(f"Weight: {weight}")

    print(f"Current Prices as of {date}")
    print(f"Min Price: {min_price}")
    print(f"Avg Price: {avg_price}")
    print(f"Max Price: {max_price}")

    # get the list of sets the minifig appears in
    if in_sets == True:
        sets = get_set_appearances(driver=driver, identifier=identifier)
        if len(sets) == 1:
            print("Appears in 1 Set:")
        else:
            print(f"Appears in {len(sets)} Sets:")
        for set in sets:
            print(set)

    # get the list of books the minifig appears in
    if in_books == True:
        books = get_book_appearances(driver=driver, identifier=identifier)
        if len(books) == 1:
            print("Appears in 1 Book:")
        else:
            print(f"Appears in {len(books)} Books:")
        for book in books:
            print(book)

    # close the web driver
    driver.quit()
