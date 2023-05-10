# CryptoSentinel Collaboration Guide

Welcome to the CryptoSentinel collaboration guide! This document aims to provide an overview of the project, its features, data sources, and goals for potential collaborators interested in contributing to the project with ideas for new features and user experience enhancements.

## Table of Contents

- Introduction
- Bot Commands and Features
- Data Sources
- Product Road Map
- Goals and Milestones
- Collaboration Process

## Introduction

CryptoSentinel is a Telegram bot designed for crypto investors and traders. It provides users with valuable cryptocurrency-related information, market trends, news, and open trading positions through a monthly subscription. The bot is built using Python and the python-telegram-bot library and leverages LunarCrush and Binance APIs for data.

## Bot Commands and Features

CryptoSentinel offers a variety of commands and features, grouped into basic (free) and premium (paid subscription) categories:


### Basic features (Free)

    /cotd: Coin of the Day (Fetches LunarCrush's coin of the day)
    /global_top [metric]: Top coins from Lunar Crush by metric given (social_score, social_volume, alt_rank)
    /sentiment: Overall market sentiment (fetched from socials like twitter, reddit, etc)

### Premium features (Paid subscription)

    /whatsup: Latest market trends
    /wdom: Weekly dominance change for Bitcoin compared to Altcoins
    /news: Latest news in the crypto world
    /positions: Trader positions (Displays biggest open positions from Binance Copy Traders and Compares Whale vs Retail Positions)
    /trader <UID>: Trader information for a specific UID on Binance

For a more detailed description of each command, please refer to the README.md file.

## Data Sources
CryptoSentinel uses two primary data sources:

**LunarCrush**:
    Provides data related to social media activity, market data, and URL engagement for cryptocurrencies. The LunarCrush API v3 is a RESTful JSON API with various documented endpoints available, each with required and/or optional query string input parameters to customize the output. LunarCrush API powers the lunarcrush.com website and mobile apps. The base URL for the API is https://lunarcrush.com/api3.

    Some of the available LunarCrush API endpoints include:

        /coinoftheday: Get the current LunarCrush Coin of the Day
        /coins: Get a general snapshot of LunarCrush metrics on the entire list of tracked coins
        /coins/:coin: Get a robust and detailed snapshot of a specific coin's metrics
        /coins/:coin/influencers: Get a list of crypto influencers for a specified coin or token
        /coins/:coin/insights: Get a list of LunarCrush insights for a specific coin or token
        /coins/global: Get aggregated metrics across all coins tracked on the LunarCrush platform
        /coins/influencers: Get a list of overall crypto influencers across all coins

    The API is available on a pay-as-you-go plan with 2,000 free daily credits and a cost of $0.005 for each additional credit.

**RapidAPI Binance:**
    Provides data from the Binance Futures Leaderboard, including trader positions, leaderboards, and market data. The Binance Futures Leaderboard API is hosted on RapidAPI and is written in Python with FastAPI and AIOHTTP for asynchronous requests. Uvicorn is used as an ASGI server.

    Some of the key features of the Binance Futures Leaderboard API include:

        Advanced search with filters: Allows searching for specific symbols (e.g., BTCUSDT, ETHUSDT), time periods (weekly, monthly), sorting by PNL, ROI or followers, and specific trade types (USDⓈ-M and COIN-M).
        Get open positions from different traders: Retrieve open positions from various traders and access position details such as symbol, open time, PNL, ROI, and amount.
        Search traders by name: Find specific traders by name (e.g., Elon Musk, Vitalik Buterin).
        Get trader information: Obtain details like Twitter URL, followers, and open positions for a trader.

    Use cases for the Binance Futures Leaderboard API include automating trading with leaderboard data, signal bots, and trend analysis. The RapidAPI plan costs $10 per month for 10,000 calls and has a rate limit of 5 requests per second. Each additional call costs $0.001.

## Product Road Map

The current product road map includes the following milestones:

- Add user management features on the backend
- Add Frontend monthly payment solutions for users
- Release a minimum viable product (MVP) within 2 months
- Add support for additional cryptocurrencies and exchanges in later versions
- Explore other revenue streams and partnerships

Please refer to the Product Road Map document for more details.

## Goals and Milestones

- Launch MVP
- Reach 10 paying users
- Reach 100 paying users

## Collaboration Process

If you're interested in collaborating with us on feature ideas and user experience enhancements, please contact the project owner on Discord at AccursedGalaxy#8843. We're looking forward to hearing your ideas and working together to make CryptoSentinel even better for our users!

Please note that all coding will be done by the project owner, and your role will be to provide ideas and suggestions for new features or improvements to the user experience.