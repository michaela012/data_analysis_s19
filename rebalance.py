import csv
import matplotlib.pyplot as plt
from datetime import datetime

def print_duration(fn):
    def fn_with_duration(*args, **kwargs):
        start = datetime.now()
        ret = fn(*args, **kwargs)
        print("FN {} took: {}".format(fn.__name__, datetime.now()-start))
        return ret
    return fn_with_duration


class ReturnData(object):
    def __init__(self, filename):
        self.filename = filename
        self.ordered_dates = None
        self.rolling_periods = None

    #TODO: make this only run once, and reference the dictionary, not the function
    # @print_duration
    def get_return_data(self):
        '''
        reads data from csv file containing historical data for total returns, value, and asset
        allocations for unbalanced, monthly rebalanced, and annually rebalanced portfolio.
        '''
        #initialize dict for date and list of monthly returns, ordered list of dates
        # dict form {date: [large cap, small cap, international equity, bonds, cash]}
        return_dict = {}
        #read csv
        with open(self.filename) as rebal:
            for row in csv.reader(rebal):
                if row[1].isalpha() or row[1] == '':
                    continue
                else:
                    date = row[1]
                    lc_ret = row[2]
                    sc_ret = row[3]
                    int_ret = row[4]
                    bond_ret = row[5]
                    cash_ret = row[6]

                #add data to dict, list
                return_dict[date] = [lc_ret, sc_ret, int_ret, bond_ret, cash_ret]

        return return_dict

    def get_ordered_dates(self):
        if self.ordered_dates is not None:
            return self.ordered_dates
        else:
            ordered_dates = []
            #read csv
            with open("/home/michaela/summerwork/rebalancing_project/rebalance.csv") as rebal:
                for row in csv.reader(rebal):
                    if not(row[1].isalpha()) and not(row[1] == ''):
                        date = row[1]
                        ordered_dates.append(date)
            self.ordered_dates = ordered_dates
            return self.ordered_dates

    def beginning_of_month(self, your_date):
        if your_date[1] == "/":
            return your_date[:1] + "/1/" + your_date[-4:]
        if your_date[2] == "/":
            return your_date[:2] + "/1/" + your_date[-4:]

    def end_of_month(self, your_date, ordered_dates):
        '''
        input m/yyyy (str), last business day of months (lst)
        return last business day of given month
        '''
        for date in ordered_dates:
            if date[-4:] == your_date[-4:] and date[:2] == your_date[:2]:
                return date

    def get_rolling_periods(self, length = 25):
        '''
        input: length of each rolling period (int)
        returns rolling periods in list of tuples
        '''
        if self.rolling_periods is not None:
            return self.rolling_periods
        else:
            ordered_dates = self.get_ordered_dates()
            rolling_periods = []
            total_month_count = len(ordered_dates)
            for i in range (0, total_month_count-(((length-1)*12)+11)):
                start = self.beginning_of_month(ordered_dates[i])
                end = ordered_dates[i+((length-1)*12)+11]
                rolling_periods.append((start,end))
            self.rolling_periods = rolling_periods
            return self.rolling_periods


class Portfolio(ReturnData):
    '''
    attributes: starting_value, proportion of equities, bonds, cash
    '''

    def __init__(self, start_value, prop_equities, prop_bonds, prop_cash, filename):
        self.starting_value = start_value
        self.equities = prop_equities
        self.large_cap = self.equities * .55
        self.small_cap = self.equities * .15
        self.int = self.equities * .3
        self.bonds = prop_bonds
        self.cash = prop_cash
        ReturnData.__init__(self, filename)

    def starting_portfolio(self):
        '''
        return initial portfolio allocation
        '''
        return [self.starting_value, self.starting_value * self.large_cap, self.starting_value * self.small_cap, 
            self.starting_value * self.int, self.starting_value * self.bonds, self.starting_value * self.cash]
    
    def date_range(self, start_of_period, end_of_period):
        '''
        inputs: start_of_period (str, m/d/yyyy), end_of_period
        returns ordered list of all dates in date range
        '''
        ordered_dates = self.get_ordered_dates()

        end_date_range = ordered_dates[ordered_dates.index(start_of_period): ordered_dates.index(end_of_period)]
        end_date_range.append(end_of_period)
        date_range = [self.beginning_of_month(start_of_period)]
        date_range.extend(end_date_range)

        return date_range

    def get_months_returns(self, date, date_range, portfolio):
        '''
        gets the new portfolio value for a single month, month date_range[date]
        '''
        return_dict = self.get_return_data()
        lc = ((float(return_dict[date_range[date]][0])/100)+1) * portfolio[date_range[date-1]][1]
        sc = ((float(return_dict[date_range[date]][1])/100) +1) * portfolio[date_range[date-1]][2]
        inter = ((float(return_dict[date_range[date]][2])/100)+1) * portfolio[date_range[date-1]][3]
        bond_val = ((float(return_dict[date_range[date]][3])/100)+1) * portfolio[date_range[date-1]][4]
        cash_val = ((float(return_dict[date_range[date]][4])/100)+1) * portfolio[date_range[date-1]][5]
        total_val = lc + sc + inter + bond_val + cash_val

        return [total_val, lc, sc, inter, bond_val, cash_val]


    def untouched_returns(self, starting_portfolio, date_range):
        '''
        inputs: starting_portfolio (lst, form [starting val, lc val, sc val, int val, bond val, cash val]),
            return_dict (dict, form {date:[<same form as starting_portfolio>]}
            date_range (ordered lst of dates in focus range)
        returns dict of monthly return data for unbalanced portfolio
        '''
        #initialize dict of monthly values of untouched portfolio, filled with starting port value
        # form {date: [total value, lc, sc, int., bond, cash, EP, BP, CP]}
        untouched_port = {date_range[0]: starting_portfolio}

        #populate untouched_port dict, starting range at 1 bc we have the starting port for values resulting from date_range[0]
        for date in range(1, len(date_range)):
            new_entry = self.get_months_returns(date, date_range, untouched_port)
            untouched_port[date_range[date]] = new_entry

        #return final dict with all port values for all months in pd
        return untouched_port

    def rebalance(self, current_port_values):
        '''
        input current portfolio values, form [total_val, lc, sc, int, bond, cash]
        output same total value rebalanced according to initial allocations
        '''
        total_val = current_port_values[0]
        lc = total_val * self.large_cap
        sc = total_val * self.small_cap
        inter = total_val * self.int
        bonds = total_val * self.bonds
        cash = total_val * self.cash

        return [total_val, lc, sc, inter, bonds, cash]

    def monthly_rebalanced(self, starting_portfolio, date_range):
        '''
        same as untouched but with monthly rebalancing
        '''
        #initialize dict of monthly values of monthly rebalanced portfolio, filled with starting port value
        # form {date: [total value, lc, sc, int., bond, cash, EP, BP, CP]}
        monthly_rebal_port = {date_range[0]: starting_portfolio}

        #populate monthly_rebal_port dict, starting range at 1 bc we have the starting port for values resulting from date_range[0]
        for date in range(1, len(date_range)):
            new_entry = self.get_months_returns(date, date_range, monthly_rebal_port)
            monthly_rebal_port[date_range[date]] = self.rebalance(new_entry)

        #return final dict with all port values for all months in pd
        return monthly_rebal_port

    def annually_rebalanced(self, starting_portfolio, date_range):
        '''
        same as untouched but with annual rebalancing
        '''
        #initialize dict of monthly values of annually rebalanced portfolio, filled with starting port value
        # form {date: [total value, lc, sc, int., bond, cash, EP, BP, CP]}
        annual_rebal_port = {date_range[0]: starting_portfolio}

        #populate monthly_rebal_port dict, starting range at 1 bc we have the starting port for values resulting from date_range[0]
        for date in range(1, len(date_range)):
            new_entry = self.get_months_returns(date, date_range, annual_rebal_port)
            if (date - 1) % 12 == 11:
                annual_rebal_port[date_range[date]] = self.rebalance(new_entry)
            else: 
                annual_rebal_port[date_range[date]] = new_entry
        

        #return final dict with all port values for all months in pd
        return annual_rebal_port


    def get_rebal_comparison(self, start_date, end_date):
        #get starting information
        return_dict = self.get_return_data()
        
        date_range = self.date_range(start_date, end_date)
        starting_portfolio = self.starting_portfolio()

        #get historical values of all three portfolios 
        untouched_port = self.untouched_returns(starting_portfolio, date_range)
        monthly_rebal_port = self.monthly_rebalanced(starting_portfolio, date_range)
        annual_rebal_port = self.annually_rebalanced(starting_portfolio, date_range)


        return untouched_port[end_date][0], monthly_rebal_port[end_date][0], annual_rebal_port[end_date][0]

#########


def period_value_comparison(start_val, period, data):
    '''
    start_val = starting portfolio value (int)
    period = tuple of form (start date (str, m/d/yyyy), end date(str))
    data = ReturnData object
    '''
    start_date = period[0]
    end_date = period[1]
    display_period = start_date + " - " + end_date

    first_month = data.end_of_month(period[0], data.get_ordered_dates())

    #low risk port
    low_risk_portfolio = Portfolio(start_val, 0.3, 0.65, 0.05, data.filename)
    low_untouched, low_monthly, low_annual = low_risk_portfolio.get_rebal_comparison(first_month, end_date)

    #med risk port
    med_risk_portfolio = Portfolio(start_val, 0.5, 0.45, 0.05, data.filename)
    med_untouched, med_monthly, med_annual = med_risk_portfolio.get_rebal_comparison(first_month, end_date)

    #high risk port
    high_risk_portfolio = Portfolio(start_val, 0.7, 0.25, 0.05, data.filename)
    high_untouched, high_monthly, high_annual = high_risk_portfolio.get_rebal_comparison(first_month, end_date)

    return display_period, [low_untouched, med_untouched, high_untouched, low_monthly, med_monthly, high_monthly,
        low_annual, med_annual, high_annual,
        ]

def rolling_pd_comparison(start_value, filename):
    data = ReturnData(filename)
    rolling_periods = data.get_rolling_periods()

    #build dataframe, form {"time pd": [final values of portfolios], ... }
    d = {}
    for period in rolling_periods:
        period, comparison = period_value_comparison(10, period, data)
        d[period] = comparison
    return d


if __name__ == "__main__":
    print("------------------")
    data = ReturnData("/home/michaela/summerwork/rebalancing_project/rebalance.csv")
    print(period_value_comparison(10, ("1/1/1979", "12/31/2004"), data))
    
