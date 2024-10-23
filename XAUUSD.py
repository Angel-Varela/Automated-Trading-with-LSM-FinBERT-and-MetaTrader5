#Imports
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from Finbert_Utils import estimate_sentiment
import pandas as pd
from bs4 import BeautifulSoup
import requests

"""
Initialize our model
"""
if mt5.initialize():
    pass
    if not mt5.initialize(login=51863590, server="ICMarketsSC-Demo",password="1lfz&CJ7jyX2N8"):
            print("initialize() failed, error code =",mt5.last_error())
symbol = "XAUUSD"
symbol_info = mt5.symbol_info(symbol)
symbol_info_tick = mt5.symbol_info_tick(symbol)
price = symbol_info_tick.ask

class TradingBot():
    def get_df(self):
        """
        Use the Predicted Df and made slices of data based on the now's time
        """
        #Import the dataframe
        columns_names = ("Date", "Price")
        dataframe = pd.read_csv(r"C:\Users\Angel\OneDrive\Escritorio\Vs Code\.vscode\XAUUSD.csv", names=columns_names, skiprows=1)
        #Right here we can  use the date colum on the dataframe in order to check the row and find the nearest 10 rows
        now_time = datetime.now().replace(microsecond=0, second=37) #We'll change seconds depending on the dataframe
        now_str = now_time.strftime('%Y-%m-%d %H:%M:%S')
        now = pd.Timestamp(now_str)

        data = pd.DataFrame(dataframe)
        data["Date"] = pd.to_datetime(data["Date"], format='%Y-%m-%d %H:%M:%S')
        # Ensure the data is sorted by Date
        data = data.sort_values(by="Date").reset_index(drop=True)
        data["Price"] = np.floor(data["Price"] * 10**6) / 10**6
       
        # Find the nearest 10 rows
        nearest_time = pd.to_datetime(now_str, format='%Y-%m-%d %H:%M:%S')
        data['diff'] = (data['Date'] - nearest_time).abs()                                           
        closest_index = data['diff'].idxmin()
        data = data.drop('diff', axis=1) #Drop the diff column
        min_short = max(closest_index - 13, 0)  # Ensure the index range doesn't go below 0
        max_short = min(closest_index + 12, len(data.index))  # Ensure the index range doesn't go beyond the DataFrame
        min_long = max(closest_index - 20, 0)  # Ensure the index range doesn't go below 0
        max_long = min(closest_index + 20, len(data.index))  # Ensure the index range doesn't go beyond the DataFrame
        # Fetch rows
        nearest_rows = data.iloc[min_short:max_short] #SLICE OF DATA
        long_rows = data.iloc[min_long:max_long]
        return nearest_rows, closest_index, now, data, long_rows
    #OUR RUN FUNCTION
    def positional_sizing(self):
        """
        Define our Volume = 30%
        """
        #POSITIONAL SIZING
        risk = float(0.3) #Money to risk
        # acc_info = mt5.account_info() #UNCOMENT WHEN IT'S READY TO BE RELAESED on real account
        # total_balance = acc_info.balance
        def get_balance(total_balance):
            if isinstance(total_balance, tuple):
                # Assuming balance is the first element in the tuple
                return float(total_balance[0])
            elif isinstance(total_balance, float):
                return total_balance
        balance = 1000  #***get_balance(total_balance)***    
        qty_1 = balance*risk #Replace with Balance.
        qty = round(qty_1 / price, 2)
        return qty
    #Here comes the sentiment analysis
    def inner_loop(self): # We are not using the first source anymore
        """""
        - Scrapt Data from Benzinga.com, Investing.com and Ft.com
        - Estimate Sentiment, Positive or Negative
        - Estimate Probatility, up to 1.0
        - Return Sentiment and Probability
        """""
        #SECOND SOURCE BENZINGA
        url_2 = "https://www.benzinga.com/search?q=XAU-USD"
        response_2 = requests.get(url_2, headers={'user-agent': 'news_scraper'})
        soup_2 = BeautifulSoup(response_2.content, "html.parser")
        news_section_2 = soup_2.find('div', class_="content-feed-list")
        if news_section_2:
            news = news_section_2.find(class_='list-item-info')
            for news in news_section_2:
                title = news.find(class_='list-item-title')
                title_2 = title.get_text()
        probability_2, sentiment_2 = estimate_sentiment(news=title_2)
        #THIRD SOURCE INVESTING.COM
        url_3 = "https://www.investing.com/currencies/xau-usd-news"
        response_3 = requests.get(url_3, headers={'user-agent': 'news_scraper'})
        soup_3 = BeautifulSoup(response_3.content, "html.parser")
        news_section_3 = soup_3.find('div', class_="mb-4")
        if news_section_3:
            news = news_section_3.find(class_='article-item')
            for news in news_section_3:
                title_3 = news.find('div', class_='block w-full sm:flex-1 ')
                title_3 = news.get_text()
        probability_3, sentiment_3 = estimate_sentiment(news=title_3)
        # #FOURTH RESOURCE ---GENERAL ECONOMIC NEWS---
        url_4 = "https://www.ft.com/us-dollar"
        request = requests.get(url_4, headers={'user-agent': 'news_scraper'})
        soup = BeautifulSoup(request.content, "html.parser")
        news_section_4 = soup.find('ul', class_="o-teaser-collection__list js-stream-list")
        if news_section_4:
            news_items = news_section_4.find_all(class_='o-teaser-collection__item o-grid-row')
            articles = []
            for news in news_items:
                title = news.find(class_='js-teaser-heading-link')
                content = news.find(class_='js-teaser-standfirst-link')
                if title and content:
                    articles.append({
                        "Titles": title.get_text(),
                        "Contents": content.get_text()
                    })
            # Create a DataFrame
            full_news = pd.DataFrame(articles)
            # Convert DataFrame to string
            articles_str = full_news.to_string(index=False)
            # Pass the string to estimate_sentiment
            probability_4, sentiment_4 = estimate_sentiment(news=articles_str)
            r = 1 - probability_4
            def usd_dollar(sentiment_4):
                if sentiment_4 == 'positive':
                        sentiment_4 == 'negative'
                elif sentiment_4 == 'negative':
                    sentiment_4 == 'positive'
                else:
                    sentiment_4 == 'neutral'
                return sentiment_4
            usd_sentiment = usd_dollar(sentiment_4)
        sentiments = [sentiment_2, sentiment_3, sentiment_4]
        sentiment_values = {"positive": 1, "neutral": 0, "negative": -1}
        numerical_sentiments = [sentiment_values[sentiment] for sentiment in sentiments]
        average_sentiment = sum(numerical_sentiments) / len(numerical_sentiments)
        if average_sentiment > 0:
            overall_sentiment = "positive"
        elif average_sentiment < 0:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        average = [ probability_2, probability_3, probability_4]
        weights = [1, 1, 1]
        weighted_sum = sum(p * w for p, w in zip(average, weights))
        average_probability = weighted_sum / len(average)
        print("PROBABILITY", average_probability, "SENTIMENT", overall_sentiment)
        #print("Probability 1:", probability_1)
        print("Probability 2:", probability_2)
        print("Probability 3:", probability_3)
        print("Probabitlity 4:", probability_4)
        print("Sentiment 2:", sentiment_2)
        print("Sentiment 3:", sentiment_3)
        print("Sentiment 4:", sentiment_4)
        return average_probability, overall_sentiment
    
    def outer_loop(self):
        """
        Outer Loop
        Each Minute use now's real price as base for trading
        Extract the min and max on the slice of previus data
        Define buy, sell and close orders
        Infinite loop to trade
        """
        start_time = time.time()
        average_probability, overall_sentiment = self.inner_loop()
        while True:
            if time.time() - start_time >= 1200: #GET THE NEWS EACH 20 MINUTES
                average_probability, overall_sentiment = self.inner_loop()
                start_time = time.time()
            nearest_rows, _, _, _, long_rows = self.get_df() 
            qty = self.positional_sizing()
            now_time = datetime.now().replace(microsecond=0, second=37) #We'll change seconds depending on the dataframe
            timeframe = mt5.TIMEFRAME_M1
            now_str = now_time.strftime('%Y-%m-%d %H:%M:%S')
            now = pd.Timestamp(now_str) + timedelta(minutes=1)
            now_1 = datetime.now()
            minutes = now_1- timedelta(minutes=17)
            rates = mt5.copy_rates_range(symbol, timeframe, minutes, now_1)
            rates = pd.DataFrame(rates)
            if rates.size > 0: #Check if thd DF is empty, if so that means the market is closed right now
                prices = float(rates['close'].iloc[16])
                top_prices = rates["close"].nlargest(3)
                # date = pd.to_datetime(rates['time'], unit='s')
                # date = str(date.iloc[16])
            else: #If the prices are not found on the extracted df from MetaTrader5 use the data scrapped on YahooFinance
                print("Prices needs to be scrapped")
                url_prices = "https://finance.yahoo.com/quote/GC=F/"
                z = requests.get(url_prices, headers={'user-agent': 'news_scraper'})
                soup = BeautifulSoup(z.content, "html.parser")
                section = soup.find('fin-streamer', class_="livePrice yf-1tejb6")
                prices = section.get_text()
                prices = prices.replace(',', '')
                prices = float(prices) 
            acc_info = mt5.account_info() #GET ACCOUNT INFO 
            lowest = nearest_rows["Price"].min()
            highest = nearest_rows["Price"].max()
            min_price_df = nearest_rows.loc[[nearest_rows['Price'].idxmin()], ['Date', 'Price']]
            max_price_df = nearest_rows.loc[[nearest_rows['Price'].idxmin()], ['Date', 'Price']]  
            # Get the current price
            nearest_time = nearest_rows.iloc[(nearest_rows['Date'] - now).abs().argsort()[:1]]['Date'].values[0]
            current_price = nearest_rows.loc[nearest_rows["Date"] == nearest_time, "Price"].values[0]
            open_positions = mt5.positions_get(symbol=symbol) #Look for open positions in Mt5
            if open_positions:
                highest_profit_pos = max(open_positions, key=lambda pos: pos.profit) #USE alternativily to close the highest prot order instead of two
                sorted_positions = sorted(open_positions, key=lambda pos: pos.profit, reverse=True)
                top_positions = sorted_positions[:2]
            # threshold_tp = 300.0
            threshold_sl = -25.0
            sl = prices*0.99
            tp = prices*1.1
            ls = prices*1.1
            pt = prices*0.99
            buy = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": qty, #MINIMUM 0.01 for S&P
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(symbol).ask,
                "sl": sl,
                "tp": tp,
                "comment": "Buy Order Executed",
                "deviation": 20,
                "magic": 254000,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                }           
            sell = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": qty, #MINIMUM 0.01 for S&P
                "type": mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(symbol).bid,
                "sl": ls,
                "tp": pt,
                "comment": "Sell Order Executed",
                "deviation": 20,
                "magic": 254001,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                }            
            def buy_stock():
                order = mt5.order_send(buy)
                return order           
            def sell_stock():
                order = mt5.order_send(sell)
                return order        
            def close_order(position):
                if position and hasattr(position, 'type'):
                    tick = mt5.symbol_info_tick(position.symbol)
                    close_order = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "position": position.ticket,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
                        "price": tick.ask if position.type == 1 else tick.bid,  
                        "deviation": 19,
                        "magic": 69,
                        "comment": "ORDER CLOSED",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    order_close = mt5.order_send(close_order)
                return order_close
            if (nearest_rows["Date"] == now).any():
                print(symbol, now_str, "Predicted Price:", current_price, "Real Price:", prices)                   
                #MARKET IS BULLISH
                if overall_sentiment == 'positive':
                        if current_price == lowest:#If the now's minute is the lowest between the sooner and latest 10
                            if average_probability >= 0.87:#We'll buy if the market goes up and the news are positive
                                if any(prices == top_prices):
                                    print(f"Price: {float(prices)}. Cannot Buy Right Now. Highest price at the moment")
                                else:
                                    print("**BUY ORDER PLACED**")
                                    print(min_price_df) 
                                    buy_order = buy_stock()
                        elif open_positions:
                            if acc_info.profit <= threshold_sl:
                                print("Cannot take profit. Profit is equal or lower than $25")
                            elif current_price == highest:#If the now's minute is the lowest between the sooner and latest 10
                                if prices == min(rates['close']):
                                    print(f"Price: {float(prices)}. Cannot Take Profit Right Now. Lowest price at the moment")
                                else:
                                    for position in top_positions:
                                        print("**Take Profit of Last Buy Order**")
                                        print(min_price_df) 
                                        self.close_order = close_order(position=position) 
                        else:
                            pass
                #MARKET IS BEARISH
                elif overall_sentiment == 'negative':
                        if current_price == highest:#If the now's minute is the lowest between the sooner and latest 10
                            if average_probability <= 0.60:#We'll buy if the market goes up and the news are positive
                                if prices == min(rates['close']):
                                    print(f"Price: {float(prices)}. Cannot Sell Right Now. Lowest price at the moment")
                                else:
                                    print("**SELL ORDER PLACED**")
                                    print(max_price_df) 
                                    sell_order = sell_stock()

                        elif open_positions:
                            if acc_info.profit <= threshold_sl:
                                print("Cannot take profit. Profit is equal or lower than $25")
                            elif current_price == lowest:#If the now's minute is the highest between the sooner and latest 10
                                if prices == min(rates['close']):
                                    print(f"Price: {float(prices)}. Cannot Take Profit Right Now. Highest price at the moment")
                                else:
                                    for position in top_positions:
                                        print("**Take Profit of Last Sell Order**")
                                        print(min_price_df) 
                                        self.close_order = close_order(position=position) 
                        else:
                            pass
            time.sleep(60) #Run the script each minute
#RUN IN CONSOLE
if __name__ in "__main__":
    on = TradingBot()
    
    try: 
        on.outer_loop()

    except KeyboardInterrupt: #Automatic interruption with control + C
        print("Interrupted by user")