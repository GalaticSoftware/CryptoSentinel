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

    /cotd: Coin of the Day
    /global_top [metric]: Top coins by market cap or other metrics
    /sentiment: Overall market sentiment

### Premium features (Paid subscription)

    /whatsup: Latest market trends
    /wdom: Weekly dominance change
    /news: Latest news in the crypto world
    /positions: Trader positions
    /trader <UID>: Trader information for a specific UID on Binance

For a more detailed description of each command, please refer to the README.md file.
Data Sources

## CryptoSentinel uses two primary data sources:

    LunarCrush: Provides data related to social media activity, market data, and URL engagement for cryptocurrencies. The API is available on a pay-as-you-go plan with 2,000 free daily credits and a cost of $0.005 for each additional credit.

    Binance: Offers data from the Binance exchange, including trader positions, leaderboards, and market data. The RapidAPI plan costs $10 per month for 10,000 calls and has a rate limit of 5 requests per second. Each additional call costs $0.001.

## Product Road Map

The current product road map includes the following milestones:

- Add user management features on the backend
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