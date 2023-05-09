# CryptoSentinel

![CryptoSentinel Logo](assets/logo.png)

CryptoSentinel is a Telegram bot that provides users with cryptocurrency-related information, market trends, news, and open trading positions through a monthly subscription. Built using Python and the `python-telegram-bot` library, the bot leverages LunarCrush and Binance APIs for data.

## Features

CryptoSentinel offers the following features:

- Coin of the Day: `/cotd`
- Top coins by market cap: `/global_top`
- Overall market sentiment: `/sentiment`
- Latest market trends: `/whatsup`
- Weekly dominance change: `/wdom`
- Latest news in the crypto world: `/news`
- Trader positions: `/positions`

## Getting Started

Follow these steps to set up CryptoSentinel on your local machine:

1. Clone the repository:

git clone https://github.com/yourusername/CryptoSentinel.git


2. Change to the project directory:

cd CryptoSentinel


3. Create a virtual environment:

python3 -m venv venv


4. Activate the virtual environment:

- On Windows:

  ```
  venv\Scripts\activate
  ```

- On macOS and Linux:

  ```
  source venv/bin/activate
  ```

5. Install the required dependencies:

pip install -r requirements.txt


6. Create a `.env` file in the project root directory with the following variables:

TELEGRAM_API_TOKEN=<your_telegram_api_token>
LUNARCRUSH_API_KEY=<your_lunarcrush_api_key>
RAPIDAPI_KEY=<your_rapidapi_key>
DATABASE_URL=<your_database_url>


7. Run the bot:

python main.py



## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

CryptoSentinel is released under the [CC BY-NC-SA 4.0 License](LICENSE.md).
