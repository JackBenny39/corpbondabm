


class BuySide(object):
    '''
    BuySide
    
    base class for buy side traders
    '''
    
    def __init__(self, name):
        '''
        Initialize BuySide with some base class attributes and a method
        
        rfp is a public container for carrying price requests to the sell side
        '''
        self._trader_id = name # trader id
        self.rfp = []
        self._rfp_sequence = 0
        
    def __repr__(self):
        return 'BuySide({0})'.format(self._trader_id)
    
    
class MutualFund(BuySide):
    '''
    MutualFund
        
        
    '''
    def __init__(self, name):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'MutualFund'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    
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