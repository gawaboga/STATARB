# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from asyncio import gather, run
import ccxt.async_support as ccxt  # noqa: E402
from configurations import BASKET, LOGGER, SNAPSHOT_RATE, MAX_BOOK_ROWS, exchange_params 
from typing import Optional
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(f"{root}/python")
print('CCXT Version:', ccxt.__version__)
async def order_book(exchange: ccxt.Exchange, symbol: str, limit: Optional[int] = None, params=None) -> None:
    """
    Asynchronous function that fetches order book data from a cryptocurrency exchange for a given symbol.

    Args:
        exchange (object): An instance of a cryptocurrency exchange from the ccxt library.
        symbol (str): The trading symbol for which the order book data needs to be fetched.

    Returns:
        None

    Raises:
        Exception: If the symbol is not supported by the exchange.
    """
    if params is None:
        params = {}
    #limit = MAX_BOOK_ROWS
    try:
        orderbook = await exchange.fetch_order_book(symbol, limit, params)
        now = exchange.milliseconds()
        if orderbook['asks'] and orderbook['bids']:
            print(exchange.iso8601(now), exchange.id, symbol, orderbook['asks'][0], orderbook['bids'][0])
            #wait 0.1 seconds
            await asyncio.sleep(1)

        # --------------------> DO YOUR LOGIC HERE <------------------

    except Exception as e:
        LOGGER.info(e)
    except KeyboardInterrupt:
        LOGGER.info("Keyboard interrupt received. Stopping the symbol loop orderbook fetch.")
        
        #break  # you can break just this one loop if it fails

async def symbol_loop(exchange: ccxt.Exchange, symbol: str) -> None:
    """
    Asynchronous function that fetches order book data from a cryptocurrency exchange for a given symbol.

    Args:
        exchange (object): An instance of a cryptocurrency exchange from the ccxt library.
        symbol (str): The trading symbol for which the order book data needs to be fetched.

    Returns:
        None

    Raises:
        Exception: If the symbol is not supported by the exchange.
    """
    LOGGER.info(f"Starting the {exchange} symbol loop with {symbol}")
    
    if exchange.id is None or exchange.id not in exchange_params:
        # Log an error message or raise an exception
        raise ValueError(f"Invalid exchange ID in exchange params configuration: {exchange.id}")
    else:
        limit = exchange_params[exchange.id].get('limit')
        params = exchange_params[exchange.id].get('params', {})

    while True:
        try:
            await order_book(exchange, symbol, limit, params)
        except KeyboardInterrupt:
            LOGGER.info("Keyboard interrupt received. Stopping the symbol loop orderbook fetch.")
            break
        except Exception as e:
            LOGGER.info(e)
            break  # you can break just this one loop if it fails


async def exchange_loop(exchange_id: str, symbols: list, ccxt_errors=False) -> None:
    """
    Asynchronously loops through a list of symbols for a given cryptocurrency exchange.
    
    Args:
        exchange_id (str): The ID of the cryptocurrency exchange.
        symbols (list): A list of trading symbols for which the order book data needs to be fetched.
    
    Returns:
        None
    
    Summary:
        The `exchange_loop` function is an asynchronous function that loops through a list of symbols for a given cryptocurrency exchange. 
        It loads the markets for the exchange and filters the symbols that are tradable. 
        Then, it creates a list of asynchronous tasks to fetch order book data for each symbol using the `symbol_loop` function. 
        Finally, it waits for all the tasks to complete and closes the exchange connection.
    """
    LOGGER.info(f"Starting the {exchange_id} exchange loop with {symbols}")

    # Create an instance of the cryptocurrency exchange using the exchange_id
    exchange = getattr(ccxt, exchange_id)()
    
    try:
        # Load markets
        await exchange.load_markets()
        # exchange.verbose = True  # uncomment for debugging purposes  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        await exchange.close()
    except ccxt.BaseError as e:
        if ccxt_errors:
            await exchange.close()
            raise e
        
    # Filter unsupported symbols
    for symbol in symbols:
        if symbol not in exchange.symbols:
            LOGGER.warning(f'{exchange} does not support symbol {symbol}, skipping it')
            symbols.remove(symbol)
            continue
            #raise Exception(f'{exchange} does not support symbol {symbol}, deleting it')
            
    # Create a list of asynchronous tasks to fetch order book data for each symbol
    tasks = [symbol_loop(exchange, symbol) for symbol in symbols]

    # Start processing tasks
    await asyncio.gather(*tasks, return_exceptions=True)

    # Close the exchange connection
    await exchange.close()


async def main():
    basket_of_symbols = ['BTC/USDT', 'ETH/USDT', 'fff']  # Define your basket of symbols here

    LOGGER.info(f'Starting recorder with basket = {basket_of_symbols}')
    
    exchanges = {
        'coinbasepro': basket_of_symbols,
        'binance': basket_of_symbols,
        'bitfinex': basket_of_symbols,
    }
    
    # Create a list of asynchronous tasks to fetch order book data for each symbol
    
    tasks = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    
    # Wait for all the tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    

#run(main())

if __name__ == "__main__":
    """
    Entry point of application
    """
run(main())

