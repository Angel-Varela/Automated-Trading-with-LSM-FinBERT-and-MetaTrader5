# Achilles, Neural Network to Predict the Gold Vs US Dollar
Integration with Trading Bot for Automatic Trading 💹🐮

We're implementing real time predictions from a LLSM Neural Netwok trained on historical data in a trading bot. Automatintg trading, fast, simple and affordable.


First Component: LSTM Neural Network trained on seasonal Times Frames 15 Minutes, 5 Minutes and 1 Minute data of the S&P500 Market, with this model we'll try to predict the future market during 30 days or 33000 minutes
We're getting the estimate prices of the market and we'll save this into a CSV file for our trading bot

Second Component: FINbert Sentiment Analysis to scratch and estimate the news in 4 different WebSites:

-https://www.bloomberg.com (XAU-USD)

-https://www.benzinga.com (XAU-USD)

-https://www.investing.com (XAU-USD)

-https://www.ft.com (General Market News)

Third Component: Trading bot Used in mt5 in a Paper account. Based on the CSV File and the sentiments of the news we'll trade
