#Imports
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
from timedelta import Timedelta
from Finbert_Utils import estimate_sentiment
import pandas as pd
from Historic_Crypto import LiveCryptoData
from bs4 import BeautifulSoup
import requests
import threading

if mt5.initialize():
    pass
    if not mt5.initialize(login=your_credentials, server="your_server",password="your_password"):
            print("initialize() failed, error code =",mt5.last_error())
symbol = "XAUUSD"
symbol_info = mt5.symbol_info(symbol)
symbol_info_tick = mt5.symbol_info_tick(symbol)
price = symbol_info_tick.ask

class TradingBot():
    def get_df(self):
        #Import the dataframe
        columns_names = ("Date", "Price")
        dataframe = pd.read_csv(r"XAUUSD-Df.csv", names=columns_names, skiprows=1)

        #Right here we can  use the date colum on the dataframe in order to check the row and find the nearest 10 rows
        now_time = datetime.now().replace(microsecond=0, second=4) #We'll change seconds depending on the dataframe
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
        min_short = max(closest_index - 8, 0)  # Ensure the index range doesn't go below 0
        max_short = min(closest_index + 7, len(data.index))  # Ensure the index range doesn't go beyond the DataFrame
        min_long = max(closest_index - 20, 0)  # Ensure the index range doesn't go below 0
        max_long = min(closest_index + 20, len(data.index))  # Ensure the index range doesn't go beyond the DataFrame
        # Fetch rows
        nearest_rows = data.iloc[min_short:max_short]
        long_rows = data.iloc[min_long:max_long]
        return nearest_rows, closest_index, now, data, long_rows
    #OUR RUN FUNCTION
    def run_function(self):
        #POSITIONAL SIZING
        risk = float(0.3) #Money to risk
        # acc_info = mt5.account_info() #UNCOMENT WHEN IT'S READY TO BE RELAESED
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
        while True:
            start_time = time.time()
            url_1 = "https://www.bloomberg.com/search?query=XAUUSD"
            response = requests.get(url_1, headers={'user-agent': 'news_scraper'})
            soup = BeautifulSoup(response.content, "html.parser")
            news_section = soup.find('section', class_="mainContent__35589475db")
            if news_section:
                news = news_section.find(class_='storyItem__aaf871c1c5')
                for news in news_section:
                    titles = news.find(class_='headline__3a97424275')
                    title_1 = news.get_text()
            probability_1, sentiment_1 = estimate_sentiment(news=title_1)
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
            #FOURTH RESOURCE ---GENERAL ECONOMIC NEWS---
            url_4 = "https://www.ft.com/markets"
            request = requests.get(url_4, headers={'user-agent': 'news_scraper'})
            soup = BeautifulSoup(request.content, "html.parser")
            news_section_4 = soup.find('ul', class_="o-teaser-collection__list")
            if news_section_4:
                news_items = news_section.find_all(class_='o-teaser-collection__item')
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
            #CREATE AN AVERAGE OF THE PROBABILITY AND SENTIMENTS    
            sentiments = [sentiment_1, sentiment_2, sentiment_3, sentiment_4]
            sentiment_values = {"positive": 1, "neutral": 0, "negative": -1}
            numerical_sentiments = [sentiment_values[sentiment] for sentiment in sentiments]
            average_sentiment = sum(numerical_sentiments) / len(numerical_sentiments)
            if average_sentiment > 0:
                overall_sentiment = "positive"
            elif average_sentiment < 0:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            average = [probability_1, probability_2, probability_3, probability_4]
            average_probability = sum(average) / len(average)
            print("PROBABILITY", average_probability, "SENTIMENT", overall_sentiment)
            while time.time() - start_time < 1200:
                #average_probability,  overall_sentiment, = self.probabilities_sentiment(self)
                nearest_rows, _, _, _, long_rows = self.get_df()
                now_time = datetime.now().replace(microsecond=0, second=4) #We'll change seconds depending on the dataframe
                timeframe = mt5.TIMEFRAME_M1
                now_str = now_time.strftime('%Y-%m-%d %H:%M:%S')
                now = pd.Timestamp(now_str)
                now = now + timedelta(minutes=1)
                minutes = now - timedelta(minutes=17)
                rates = mt5.copy_rates_range(symbol, timeframe, minutes, now)
                prices = rates['close'][-1]
                acc_info = mt5.account_info() #GET ACCOUNT INFO 
                lowest = nearest_rows['Price'].min()
                highest = nearest_rows["Price"].max()
                highest_long = long_rows["Price"].max() 
                lowest_long = long_rows["Price"].max() 
                min_price_df = nearest_rows.loc[[nearest_rows['Price'].idxmin()], ['Date', 'Price']]
                max_price_df = nearest_rows.loc[[nearest_rows['Price'].idxmin()], ['Date', 'Price']]  
                # # Get the current price
                nearest_time = nearest_rows.iloc[(nearest_rows['Date'] - now).abs().argsort()[:1]]['Date'].values[0]
                current_price = nearest_rows.loc[nearest_rows["Date"] == nearest_time, "Price"].values[0]
                open_positions = mt5.positions_get(symbol=symbol) #Look for open positions in Mt5
                buy_orders = [order for order in open_positions if order.type == mt5.ORDER_TYPE_BUY]
                sell_orders = [order for order in open_positions if order.type == mt5.ORDER_TYPE_SELL]
                if open_positions:
                    highest_profit_pos = max(open_positions, key=lambda pos: pos.profit)
                sorted_positions = sorted(open_positions, key=lambda pos: pos.profit, reverse=True)
                top_positions = sorted_positions[:2]
                threshold_tp = 300.0
                threshold_sl = -250.0
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
                    print("Running...", now_str, "Current Price:", current_price, "AP:", round(average_probability, 6))                   
                #MARKET IS BULLISH
                elif overall_sentiment == 'positive':
                        if prices == max(rates['close']):
                            print(f"Price: {float(prices)}. Cannot Buy Right Now. Highest price at the moment")
                        else:
                            if current_price == lowest:#If the now's minute is the lowest between the sooner and latest 10
                                if average_probability > 0.90:#We'll buy if the market goes up and the news are positive
                                    print("**BUY ORDER PLACED**")
                                    print(min_price_df) 
                                    self.buy_order = buy_stock()
                                else:
                                    pass
                            elif open_positions:
                                if prices == min(rates['close']):
                                    print(f"Price: {float(prices)}. Cannot Close the order when the price is the lowest")
                                else:
                                    if current_price == highest:
                                        self.close_order =  close_order(highest_profit_pos)#Close the last position and take the profit\
                                        print("**ORDER CLOSED**")
                                        print(close_order)
                                    elif acc_info.profit >= threshold_tp and current_price == highest_long:# and current_price == highest_long
                                        for i, position in enumerate(top_positions, start=1):
                                            self.close_order = close_order(position)
                                            print(f"{i}: {position.profit, position.ticket}")
                                    else:
                                        pass
                #MARKET IS BEARISH
                elif overall_sentiment == 'negative':
                    if prices == min(rates['close']):
                        print(f"Prices: {prices}. Cannot Sell Right Now. Lowest price at the moment")
                    else:
                        if current_price == highest:#If the now's minute is the lowest between the sooner and latest 10
                            if average_probability < 0.50: #We'll sell if the market goes down and the news are negative
                                print("**SELL ORDER PLACED**")
                                print(max_price_df)
                                self.sell_order = sell_stock()
                            else:
                                pass
                            if open_positions:
                                if prices == max(rates['close']):
                                    print(f"Price: {float(prices)}. Cannot Close the order when the price is the highest")
                                else:
                                    if current_price == lowest:
                                        self.close_order =  close_order(highest_profit_pos)#Close the last position and take the profit
                                        print("**ORDER CLOSED**")
                                        print(close_order)
                                    elif acc_info.profit <= threshold_tp and current_price == lowest_long:# and current_price == highest_long
                                        for i, position in enumerate(top_positions, start=1):
                                            self.close_order = close_order(position)
                                            print(f"{i}: {position.profit, position.ticket}")
                        else:
                            pass
                time.sleep(60) #Run the script each minute
            
            time.sleep(1200) #Run each 20 minues to check the newest news
#RUN IN CONSOLE
if __name__ in "__main__":
    on = TradingBot()
    try: 
        on.run_function()
    except KeyboardInterrupt: #Automatic interruption with control + C
        print("Interrupted by user")
