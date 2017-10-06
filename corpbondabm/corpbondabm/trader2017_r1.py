import numpy as np


ALPHA = 0.00017
BETA_D = 0.56
BETA_D1 = -.0002
BETA_W = 0.6
BETA_W1 = -0.0002


class BuySide(object):
    '''
    BuySide
    
    base class for buy side traders
    '''
    
    def __init__(self, name):
        '''
        Initialize BuySide with some base class attributes and a method
        
        rfq is a public container for carrying price quote requests to the sell side
        '''
        self._trader_id = name # trader id
        self.rfq_collector = []
        self._rfq_sequence = 0
        
    def __repr__(self):
        return 'BuySide({0})'.format(self._trader_id)
    
    
class MutualFund(BuySide):
    '''
    MutualFund
        
        
    '''
    def __init__(self, name, lower_bound, upper_bound, target, bond_list, portfolio, weights):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'MutualFund'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.target = target
        self.bond_list = bond_list
        self.portfolio = portfolio
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
    
    def compute_portfolio_value(self, prices):
        bond_values = [self.portfolio[x]['Nominal']*prices[x]/100 for x in self.bond_list]
        return np.sum(bond_values)
    
    def add_nav_to_history(self, step, prices):
        nav = self.compute_portfolio_value(prices) + self.cash
        self.nav_history[step] = nav
    
    def compute_flow(self, step):
        wealth_lag1 = self.nav_history[step-1]
        retdaily_lag1 = wealth_lag1/self.nav_history[step-2] - 1
        retweekly_lag1 = wealth_lag1/self.nav_history[step-6] - 1
        flow_ratio = ALPHA + (BETA_D + BETA_D1*(retdaily_lag1<0))*retdaily_lag1 + (BETA_W + BETA_W1*(retweekly_lag1<0))*retweekly_lag1
        return flow_ratio*wealth_lag1
    
    def make_rfq(self, name, side, amount):
        self._rfq_sequence += 1
        order_id = '%s_%d' % (self._trader_id, self._rfq_sequence)
        rfq =  {'order_id': order_id, 'name': name, 'side': side, 'amount': amount}
        self.rfq_collector.append(rfq)
        
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
        print(self.rfq_collector)
        nominals = np.array([self.portfolio[x]['Nominal'] for x in self.bond_list])
        
        prices = np.array([prices[x]/100 for x in self.bond_list])
        last_nav = self.nav_history[step-1]
        expected_cash_pct = (self.cash + self.compute_flow(step))/last_nav
        if expected_cash_pct < self.lower_bound:
            side = 'sell'
            target_sell_amount = self.target*last_nav - self.cash
            print(target_sell_amount)
            target_nominal_value = np.sum(nominals) - target_sell_amount
            target_nominals = self.index_weight_array * target_nominal_value
            diffs = target_nominals - nominals
            expected_sell_amounts = diffs*prices
            expected_sell_sum = np.abs(np.sum(expected_sell_amounts[expected_sell_amounts<0]))
            ratio = target_sell_amount/expected_sell_sum
            final_sizes = ratio*diffs
            for i,bond in enumerate(self.bond_list):
                if final_sizes[i] <= -1.0:
                    self.make_rfq(bond, side, np.abs(np.round(final_sizes[i],0)))
        
        #elif expected_cash_pct > self.upper_bound:
            #side = 'buy'
            #buy_amount = (expected_cash_pct - self.target)*last_nav
            #for bond in self.bond_list:
                #amount = self.index_weights[bond]*buy_amount
                #if amount >= 1:
                    #self.make_rfq(bond, side, int(amount))
        
    
    
class InsuranceCo(BuySide):
    '''
    InsuranceCo
        
        
    '''
    def __init__(self, name):
        '''
        Initialize InsuranceCo
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'InsuranceCo'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    
class HedgeFund(BuySide):
    '''
    HedgeFund
        
        
    '''
    def __init__(self, name):
        '''
        Initialize HedgeFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'HedgeFund'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)