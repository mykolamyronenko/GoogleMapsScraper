# FFmpeg Video Merger

Basic Google Maps scraper


## Requirements
- Python 3.7+
- The following Python libraries:
  - `playwright`
  - `pandas`
  - `openpyxl`
  - `tqdm`
 
## Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/mykolamyronenko/GoogleMapsScraper.git
   cd GoogleMapsScraper
   ```

2. **Create a virtual environment:**
   ```
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
      ```
      .venv\Scripts\activate
      ```

   - On macOS/Linux:
      ```
      source .venv/bin/activate
      ```
   
4. **Activate the virtual environment:**
    ```  
    pip install -r requirements.txt playwright install chromium
    ```
   
5. **Install browser:**
    ```  
    playwright install chromium
    ```
## Usage

1. Run the application:
    ```
    python main.py
    ```

2. Write your search query or put multiple search queries in input.txt

3. Write number of listings to scrape(by default each query contains 122 or less listings)



