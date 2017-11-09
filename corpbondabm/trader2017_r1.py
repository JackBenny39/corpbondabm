import numpy as np
import pandas as pd


ALPHA = 0.00017
BETA_D = 0.56
BETA_D1 = -0.0002
BETA_W = 0.60
BETA_W1 = -0.0002


class BuySide(object):
    '''
    BuySide
    
    base class for buy side traders
    '''
    
    def __init__(self, name, bond_list, portfolio):
        '''
        Initialize BuySide with some base class attributes and a method
        
        rfq is a public container for carrying price quote requests to the sell side
        '''
        self._trader_id = name # trader id
        self.bond_list = bond_list
        self.portfolio = portfolio
        self.rfq_collector = []
        self._rfq_sequence = 0
        
    def __repr__(self):
        return 'BuySide({0})'.format(self._trader_id)
    
    def make_rfq(self, name, side, amount):
        self._rfq_sequence += 1
        order_id = '%s_%d' % (self._trader_id, self._rfq_sequence)
        rfq =  {'order_id': order_id, 'name': name, 'side': side, 'amount': amount}
        self.rfq_collector.append(rfq)
        
    def update_prices(self, prices):
        for bond in self.bond_list:
            self.portfolio[bond]['Price'] = prices[bond]
        
    def compute_portfolio_value(self):
        return np.sum([self.portfolio[x]['Nominal']*self.portfolio[x]['Price']/100 for x in self.bond_list])
    
        
class MutualFund(BuySide):
    '''
    MutualFund
        
        
    '''
    def __init__(self, name, lower_bound, upper_bound, target, bond_list, portfolio, weights, shares):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name, bond_list, portfolio)
        self.trader_type = 'MutualFund'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.target = target
        self.nav_history = {}
        self.shares = shares
        self.index_weight_array = self.make_weight_array(weights)
        self.setup_portfolio()
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def setup_portfolio(self):
        bond_value = self.compute_portfolio_value()
        self.cash = self.target*bond_value/(1-self.target)
        self.add_nav_to_history(0)
    
    def make_weight_array(self, weights):
        return np.array([weights[x] for x in self.bond_list])
    
    #def compute_weights_from_nominal(self):
        #nominals = np.array([self.portfolio[x]['Nominal'] for x in self.bond_list])
        #nominal_value = np.sum(nominals)
        #weights = nominals/nominal_value
        #return dict(zip(self.bond_list, weights))
    
    def add_nav_to_history(self, step):
        # First compute the bond value, previous cash + cash from transactions and nav per share with existing shares
        bond_value = self.compute_portfolio_value()
        cash = self.cash
        nav = bond_value + cash
        nav_per_share = nav/self.shares
        self.nav_history[step] = {'Step': step, 'BondValue': bond_value, 'Cash': cash, 'NAV': nav, 'NAVPerShare': nav_per_share}
        # Then compute the cash inflow during the day, add to cash and buy/sell shares at the previously computed nav per share
        expected_cash_flow = self.compute_flow(step) if step >= 8 else 0
        self.cash += expected_cash_flow
        self.shares += expected_cash_flow/nav_per_share
        
    def compute_flow(self, step):
        nav_lag1 = self.nav_history[step-1]['NAVPerShare']
        retdaily_lag1 = nav_lag1/self.nav_history[step-2]['NAVPerShare'] - 1
        retweekly_lag1 = nav_lag1/self.nav_history[step-6]['NAVPerShare'] - 1
        flow_ratio = ALPHA + BETA_D*retdaily_lag1 + BETA_D1*(retdaily_lag1<0) + BETA_W*retweekly_lag1 + BETA_W1*(retweekly_lag1<0)
        return flow_ratio*self.nav_history[step-1]['NAV']
    
    def modify_portfolio(self, confirm):
        bond = confirm['Bond']
        if confirm['Side'] == 'buy':
            self.portfolio[bond]['Nominal'] += confirm['Size']
            self.cash -= confirm['Size']*confirm['Price']/100
        else:
            self.portfolio[bond]['Nominal'] -= confirm['Size']
            self.cash += confirm['Size']*confirm['Price']/100
        self.portfolio[bond]['Price'] = confirm['Price']
            
    def make_portfolio_decision(self, step):
        '''
        The MutualFund needs to know:
        1. Cash Position relative to limits
        2. Nominal Index Weights (fixed)
        
        And then:
        1. Submits orders if cash is not within the limits
        2. Bond choice weighting to match Index
        
        But:
        1. Buying can wait, while
        2. Selling cannot
        '''
        self.rfq_collector.clear()
        expected_cash_flow = self.compute_flow(step)
        expected_cash_position = self.cash + expected_cash_flow
        expected_nav = self.nav_history[step-1]['BondValue'] + expected_cash_position
        if expected_cash_position < self.lower_bound*expected_nav or expected_cash_position > self.upper_bound*expected_nav:
            target_cash = self.target * expected_nav
            cash_to_raise = target_cash - expected_cash_position
            xprices = np.array([self.portfolio[x]['Price']/100 for x in self.bond_list])
            sizes = np.abs(np.round(self.index_weight_array*cash_to_raise/xprices,0))
            if expected_cash_position < self.lower_bound*expected_nav:
                side = 'sell'
            elif expected_cash_position > self.upper_bound*expected_nav:
                side = 'buy'
            for i,bond in enumerate(self.bond_list):
                if sizes[i] >= 1.0:
                    self.make_rfq(bond, side, sizes[i])
    
    def nav_to_h5(self, filename):
        df = pd.DataFrame([v for v in self.nav_history.values()])
        df.to_hdf(filename, 'nav', append=True, format='table', complevel=5, complib='blosc')
 
        
class InsuranceCo(BuySide):
    '''
    InsuranceCo
        
        
    '''
    def __init__(self, name, equity_weight_target, bond_list, portfolio, year):
        '''
        Initialize InsuranceCo
        
        
        '''
        BuySide.__init__(self, name, bond_list, portfolio)
        self.trader_type = 'InsuranceCo'
        self.bond_weight_target = 1 - equity_weight_target
        self.equity_returns = self.make_equity_returns(year)
        self.equity = self.setup_portfolio(equity_weight_target)
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def setup_portfolio(self, equity_weight):
        return equity_weight*self.compute_portfolio_value()/(1-equity_weight)
    
    def modify_portfolio(self, confirm):
        bond = confirm['Bond']
        if confirm['Side'] == 'buy':
            self.portfolio[bond]['Nominal'] += confirm['Size']
            self.equity -= confirm['Size']*confirm['Price']/100
        else:
            self.portfolio[bond]['Nominal'] -= confirm['Size']
            self.equity += confirm['Size']*confirm['Price']/100
        self.portfolio[bond]['Price'] = confirm['Price']
            
    def make_equity_returns(self, inyear):
        indf = pd.read_csv('../csv/gspc.csv', parse_dates=['Date'])
        indf = indf.assign(Year = [x.year for x in indf.Date],
                           Return = indf['Adj Close'].pct_change()/100)
        return np.array(indf[indf.Year==inyear]['Return'])
    
    def make_portfolio_decision(self, step):
        '''
        The InsuranceCo needs to know:
        1. Bond portfolio value
        2. Equity portfolio value
        
        And then:
        1. Randomly buys/sells bonds to re-weight
        '''
        self.rfq_collector.clear()
        self.equity *= (1+self.equity_returns[step-1])
        bond_value = self.compute_portfolio_value()
        portfolio_value = self.equity+bond_value
        equity_percent = self.equity/portfolio_value
        if equity_percent < 0.395 or equity_percent > 0.405:
            bond_diff = bond_value - self.bond_weight_target*portfolio_value
            if np.abs(bond_diff) >= 1.0:
                side = 'sell' if bond_diff >= 1.0 else 'buy'
                bond = self.bond_list[np.random.randint(0, len(self.bond_list))]
                bond_price = self.portfolio[bond]['Price']/100
                self.make_rfq(bond, side, np.abs(np.round(bond_diff/bond_price,0)))
    
    
class HedgeFund(BuySide):
    '''
    HedgeFund
        
        
    '''
    def __init__(self, name, bond_list, portfolio):
        '''
        Initialize HedgeFund
        
        
        '''
        BuySide.__init__(self, name, bond_list, portfolio)
        self.trader_type = 'HedgeFund'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    
class Dealer(object):
    '''
    Dealer
    
    Dealer receives rfqs and quotes prices similar to Treynor (FAJ, 1987):
    1. The active side of the quote is a function of expected inventory and 
       the outside spread
    2. The passive side of the quote is a fixed spread related to average trade size
       outside spread and inventory range
    '''
    
    def __init__(self, name, bond_list, portfolio, long_limit, short_limit, bounds, spread_factor):
        '''
        Initialize Dealer with some base class attributes and a method
        
        
        '''
        self._trader_id = name # trader id
        self.trader_type = 'Dealer'
        self.bond_list = bond_list
        self.portfolio = portfolio
        self.lower_bound = bounds[0]
        self.upper_bound = bounds[1]
        self.spread_factor = spread_factor
        self.update_limits(long_limit, short_limit)
        
    def __repr__(self):
        return 'Dealer({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def update_limits(self, long1, short1):
        for bond in self.bond_list:
            self.portfolio[bond]['LowerLimit'] = -self.portfolio[bond]['Nominal']*short1
            self.portfolio[bond]['UpperLimit'] = self.portfolio[bond]['Nominal']*long1
            self.portfolio[bond]['Quantity'] = 0
            
    def update_prices(self, prices):
        for bond in self.bond_list:
            self.portfolio[bond]['Price'] = prices[bond]
    
    def modify_portfolio(self, confirm):
        bond = confirm['Bond']
        # if confirm order to sell, dealer buys and increases inventory
        if confirm['Side'] == 'buy':
            self.portfolio[bond]['Quantity'] -= confirm['Size']
        else:
            self.portfolio[bond]['Quantity'] += confirm['Size']
        self.portfolio[bond]['Price'] = confirm['Price']
            
    def make_quote(self, rfq):
        order_id = rfq['order_id']
        bond = rfq['name']
        side = rfq['side']
        amount = rfq['amount']
        lower_limit = self.portfolio[bond]['LowerLimit']
        upper_limit = self.portfolio[bond]['UpperLimit']
        bond_price = self.portfolio[bond]['Price']
        outside_spread = (self.upper_bound + self.lower_bound)*bond_price
        inventory_range = upper_limit - lower_limit
        # Treynor Standard Accommodation = 10000 (i.e., $10 Million - Nominal)
        inside_spread = self.spread_factor*outside_spread/inventory_range
        # if incoming order to sell, dealer buys and increases inventory
        size = amount if side == 'sell' else -amount
        expected_inventory = self.portfolio[bond]['Quantity'] + size
        if lower_limit <= expected_inventory <= upper_limit:
            specialization = 1 - self.portfolio[bond]['Specialization']/10
            if expected_inventory < 0:
                scale = (expected_inventory/lower_limit)*specialization
                ask_price = (1 + scale*self.upper_bound)*bond_price
                bid_price = ask_price - inside_spread
                price = bid_price if side == 'sell' else ask_price
                quote = {'Dealer': self._trader_id, 'order_id': order_id, 'name': bond, 'amount': amount, 'side': side, 'price': price}
            elif expected_inventory > 0:
                scale = (expected_inventory/upper_limit)*specialization
                bid_price = (1 - scale*self.lower_bound)*bond_price
                ask_price = bid_price + inside_spread
                price = bid_price if side == 'sell' else ask_price
                quote = {'Dealer': self._trader_id, 'order_id': order_id, 'name': bond, 'amount': amount, 'side': side, 'price': price}
            elif expected_inventory == 0:
                half_spread = inside_spread/2
                bid_price = bond_price - half_spread
                ask_price = bond_price + half_spread
                price = bid_price if side == 'sell' else ask_price
                quote = {'Dealer': self._trader_id, 'order_id': order_id, 'name': bond, 'amount': amount, 'side': side, 'price': price}
        else:
            quote = None #{'Dealer': self._trader_id, 'order_id': order_id, 'name': bond, 'amount': None, 'side': side, 'price': None}
        return quote
            
    
    
    
    
