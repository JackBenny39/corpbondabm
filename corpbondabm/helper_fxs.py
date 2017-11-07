import numpy as np

    
def add_durations(self):
    self.durations = [self.get_duration(x['Nominal'], x['Maturity'], x['Coupon'], x['Yield'], 2) for x in self.bonds]
    
    
def get_duration(self, nominal, maturity, coupon, ytm, nper):
    cash_flows = [nominal*coupon/nper]*(nper*maturity)
    cash_flows[-1] += nominal
    times = [0.5*j for j in range(1, len(cash_flows)+1)]
    discounted_cf = np.array([pow(1+ytm/nper, -i*nper) for i in times])*cash_flows
    price = np.sum(discounted_cf)
    mac_duration = np.sum(times*discounted_cf/price)
    mod_duration = mac_duration/(1+ytm/nper)
    return mod_duration