import numpy as np


ALPHA = 0.00017
BETA_D = 0.56
BETA_D1 = -0.0002
BETA_W = 0.6
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
        
    def compute_portfolio_value(self, prices):
        bond_values = [self.portfolio[x]['Nominal']*prices[x]/100 for x in self.bond_list]
        return np.sum(bond_values)
    
    
    
class MutualFund(BuySide):
    '''
    MutualFund
        
        
    '''
    def __init__(self, name, lower_bound, upper_bound, target, bond_list, portfolio, weights):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name, bond_list, portfolio)
        self.trader_type = 'MutualFund'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.target = target
        self.nav_history = {}
        self.cash = 0
        self.index_weights = weights
        self.index_weight_array = self.make_weight_array()
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def make_weight_array(self):
        return np.array([self.index_weights[x] for x in self.bond_list])
    
    def compute_weights_from_nominal(self):
        nominals = np.array([self.portfolio[x]['Nominal'] for x in self.bond_list])
        nominal_value = np.sum(nominals)
        weights = nominals/nominal_value
        return dict(zip(self.bond_list, weights))
    
    def add_nav_to_history(self, step, prices):
        nav = self.compute_portfolio_value(prices) + self.cash
        self.nav_history[step] = nav
    
    def compute_flow(self, step):
        wealth_lag1 = self.nav_history[step-1]
        retdaily_lag1 = wealth_lag1/self.nav_history[step-2] - 1
        retweekly_lag1 = wealth_lag1/self.nav_history[step-6] - 1
        flow_ratio = ALPHA + (BETA_D + BETA_D1*(retdaily_lag1<0))*retdaily_lag1 + (BETA_W + BETA_W1*(retweekly_lag1<0))*retweekly_lag1
        return flow_ratio*wealth_lag1
    
    def modify_portfolio(self, confirm):
        bond = confirm['name']
        if confirm['side'] == 'buy':
            self.portfolio[bond]['Nominal'] += confirm['size']
            self.cash -= confirm['size']*confirm['price']
        else:
            self.portfolio[bond]['Nominal'] -= confirm['size']
            self.cash += confirm['size']*confirm['price']
            
    def make_portfolio_decision(self, step, prices):
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
        last_nav = self.nav_history[step-1]
        expected_cash = self.compute_flow(step)
        expected_cash_pct = (self.cash + expected_cash)/(last_nav + expected_cash)
        if expected_cash_pct < self.lower_bound or expected_cash_pct > self.upper_bound:
            nominals = np.array([self.portfolio[x]['Nominal'] for x in self.bond_list])
            xprices = np.array([prices[x]/100 for x in self.bond_list])
            expected_nav = last_nav + expected_cash
            target_nominal_value = (1 - self.target)*expected_nav
            target_nominals = self.index_weight_array * target_nominal_value
            diffs = target_nominals - nominals
            expected_amounts = diffs*xprices
            if expected_cash_pct < self.lower_bound:
                side = 'sell'
                target_sell_amount = self.target*expected_nav - self.cash
                expected_sell_sum = np.abs(np.sum(expected_amounts[expected_amounts<0]))
                ratio = target_sell_amount/expected_sell_sum
                final_sizes = ratio*diffs
                for i,bond in enumerate(self.bond_list):
                    if final_sizes[i] <= -1.0:
                        self.make_rfq(bond, side, np.abs(np.round(final_sizes[i],0)))
            elif expected_cash_pct > self.upper_bound:
                side = 'buy'
                target_buy_amount = (self.cash + expected_cash) - self.target*expected_nav
                expected_buy_sum = np.abs(np.sum(expected_amounts[expected_amounts>0]))
                ratio = target_buy_amount/expected_buy_sum
                final_sizes = ratio*diffs
                for i,bond in enumerate(self.bond_list):
                    if final_sizes[i] >= 1.0:
                        self.make_rfq(bond, side, np.abs(np.round(final_sizes[i],0)))
 
        
    
    
class InsuranceCo(BuySide):
    '''
    InsuranceCo
        
        
    '''
    def __init__(self, name, bond_weight_target, bond_list, portfolio):
        '''
        Initialize InsuranceCo
        
        
        '''
        BuySide.__init__(self, name, bond_list, portfolio)
        self.trader_type = 'InsuranceCo'
        self.equity = 0
        self.bond_weight_target = bond_weight_target
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def modify_portfolio(self, confirm):
        bond = confirm['name']
        if confirm['side'] == 'buy':
            self.portfolio[bond]['Nominal'] += confirm['size']
            self.equity -= confirm['size']*confirm['price']
        else:
            self.portfolio[bond]['Nominal'] -= confirm['size']
            self.equity += confirm['size']*confirm['price']
    
    def make_portfolio_decision(self, prices, equity_return):
        '''
        The InsuranceCo needs to know:
        1. Bond portfolio value
        2. Equity portfolio value
        
        And then:
        1. Randomly buys/sells bonds to re-weight
        '''
        self.rfq_collector.clear()
        self.equity *= (1+equity_return)
        bond_value = self.compute_portfolio_value(prices)
        portfolio_value = self.equity+bond_value
        bond_diff = bond_value - self.bond_weight_target*portfolio_value
        if np.abs(bond_diff) >= 1.0:
            side = 'sell' if bond_diff >= 1.0 else 'buy'
            bond = self.bond_list[np.random.randint(0, len(self.bond_list))]
            bond_price = prices[bond]/100
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
    
    def __init__(self, name, bond_list, portfolio, long_limit, short_limit):
        '''
        Initialize Dealer with some base class attributes and a method
        
        
        '''
        self._trader_id = name # trader id
        self.trader_type = 'Dealer'
        self.bond_list = bond_list
        self.portfolio = portfolio
        self.update_limits(long_limit, short_limit)
        
    def __repr__(self):
        return 'Dealer({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def update_limits(self, long, short):
        for bond in self.bond_list:
            self.portfolio[bond]['LowerLimit'] = -self.portfolio[bond]['Nominal']*short
            self.portfolio[bond]['UpperLimit'] = self.portfolio[bond]['Nominal']*long
            self.portfolio[bond]['Quantity'] = 0
            
    def update_price(self, prices):
        pass
            
    def make_quote(self, rfq):
        # if incoming order to sell, dealer buys and increases inventory
        size = rfq['amount'] if rfq['side'] == 'sell' else -rfq['amount']
        expected_inventory = self.portfolio[rfq['name']]['Quantity'] + size
        if expected_inventory < 0:
            scale = (expected_inventory/self.portfolio[rfq['name']]['LowerLimit'])*(1 - self.portfolio[rfq['name']]['Specialization']/10)
        #rfq =  {'order_id': order_id, 'name': name, 'side': side, 'amount': amount}
            
    
    
    
    