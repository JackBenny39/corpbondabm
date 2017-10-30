import numpy as np
import pandas as pd

from math import pow


class BondMarket(object):
    '''
    BondMarket
    
    base class for bond market
    '''
    
    def __init__(self, name):
        '''
        Initialize BondMarket with some base class attributes and a method
        
        
        '''
        self._market_id = name # trader id
        self.bonds = []
        self.trades = []
        self.last_prices = {}
        self.price_history = []
        self.trade_sequence = 0
        
    def __repr__(self):
        return 'BondMarket({0})'.format(self._market_id)
    
    def add_bond(self, name, nominal, maturity, coupon, ytm, nper):
        price = self._price_bond(100, maturity, coupon, ytm, nper)
        self.bonds.append({'Name': name, 'Nominal': nominal, 'Maturity': maturity, 'Coupon': coupon, 'Yield': ytm, 'Price': price})
        self.last_prices[name] = price
        
    def _price_bond(self, nominal, maturity, coupon, ytm, nper):
        n = nper*maturity
        payment = nominal*coupon/nper
        rate = ytm/nper
        discount = pow(1+rate,-n)
        return payment*(1-discount)/rate + discount*nominal
    
    def compute_weights_from_price(self):
        prices = np.array([x['Price']*x['Nominal']/100 for x in self.bonds])
        market_value = np.sum(prices)
        weights = prices/market_value
        return weights
    
    def compute_weights_from_nominal(self):
        nominals = np.array([x['Nominal'] for x in self.bonds])
        nominal_value = np.sum(nominals)
        weights = nominals/nominal_value
        names = [x['Name'] for x in self.bonds]
        return dict(zip(names, weights))
    
    def report_trades(self, matched_quote, step):
        # Report all information to the transaction collector
        self.trade_sequence += 1
        trade_report = {'Sequence': self.trade_sequence, 'Dealer': matched_quote['Dealer'], 'OrderId': matched_quote['order_id'], 
                        'Bond': matched_quote['name'], 'Size': matched_quote['amount'], 'Side': matched_quote['side'], 
                        'Price': matched_quote['price'], 'Day': step}
        self.trades.append(trade_report)
        self.last_prices[trade_report['Bond']] = trade_report['Price']
        
    def make_dealer_confirm(self, matched_quote):
        # Report Dealer, Size, Bond, Side
        return {'Dealer': matched_quote['Dealer'], 'Size': matched_quote['amount'], 'Bond': matched_quote['name'],
                'Side': matched_quote['side'], 'Price': matched_quote['price']}
        
    def make_buyside_confirm(self, matched_quote):
        # Report BuySide, Size, Bond, Side, Price
        buy_side = matched_quote['order_id'].split('_')[0]
        return {'BuySide': buy_side, 'Size': matched_quote['amount'], 'Bond': matched_quote['name'], 
                'Side': matched_quote['side'], 'Price': matched_quote['price']}
        
    def match_trade(self, quotes, step):
        # if side is buy, dealer is quoting ask prices
        side = quotes[0]['side']
        prices = [quotes[i]['price'] for i in range(0,len(quotes))]
        best_price = np.min(prices) if side == 'buy' else np.max(prices)
        best_quotes = [q for q in quotes if q['price'] == best_price]
        match = best_quotes[np.random.randint(0, len(best_quotes))]
        self.report_trades(match, step)
        return self.make_dealer_confirm(match), self.make_buyside_confirm(match)
    
    def print_last_prices(self, step):
        current_prices = {bond: price for bond, price in self.last_prices.items()}
        current_prices['Date'] = step
        self.price_history.append(current_prices)
    
    def last_prices_to_h5(self, filename):
        '''Append last prices to an h5 file'''
        temp_df = pd.DataFrame(self.price_history)
        temp_df.to_hdf(filename, 'last_prices', append=True, format='table', complevel=5, complib='blosc') 
        
    def trades_to_h5(self, filename):
        '''Append trades to an h5 file'''
        temp_df = pd.DataFrame(self.trades)
        temp_df.to_hdf(filename, 'trades', append=True, format='table', complevel=5, complib='blosc')
            
        
