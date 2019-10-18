import csv
import matplotlib.pyplot as plt

class ReturnData(object):
    def __init__(self, filename):
        self.filename = filename
        self.ordered_dates = None
        self.rolling_periods = None
        self.rolling_period_length = None

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
                    lcg = row[2]
                    lcv = row[3]
                    mcg = row[4]
                    mcv = row[5]
                    scg = row[6]
                    scv = row[7]

                #add data to dict, list
                return_dict[date] = [lcg, lcv, mcg, mcv, scg, scv]

        return return_dict

    def get_ordered_dates(self):
        if self.ordered_dates is not None:
            return self.ordered_dates
        else:
            ordered_dates = []
            #read csv
            with open(self.filename) as f:
                for row in csv.reader(f):
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

    def get_rolling_periods(self, length):
        '''
        input: length of each rolling period in months (int)
        returns rolling periods in list of tuples
        '''
        if self.rolling_periods is not None and self.rolling_period_length == length:
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

    def __init__(self, start_value, filename):
        self.starting_value = start_value
        ReturnData.__init__(self, filename)
        self.starting_port = [self.starting_value,self.starting_value,self.starting_value,self.starting_value,self.starting_value,self.starting_value]

    
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
        lcg = ((float(return_dict[date_range[date]][0])/100)+1) * portfolio[date_range[date-1]][0]
        lcv = ((float(return_dict[date_range[date]][1])/100)+1) * portfolio[date_range[date-1]][1]
        mcg = ((float(return_dict[date_range[date]][2])/100)+1) * portfolio[date_range[date-1]][2]
        mcv = ((float(return_dict[date_range[date]][3])/100)+1) * portfolio[date_range[date-1]][3]
        scg = ((float(return_dict[date_range[date]][4])/100)+1) * portfolio[date_range[date-1]][4]
        scv = ((float(return_dict[date_range[date]][5])/100)+1) * portfolio[date_range[date-1]][5]

        return [lcg, lcv, mcg, mcv, scg, scv]


    def untouched_returns(self, starting_portfolio, date_range):
        '''
        inputs: starting_portfolio (lst, form [starting val, lc val, sc val, int val, bond val, cash val]),
            return_dict (dict, form {date:[<same form as starting_portfolio>]}
            date_range (ordered lst of dates in focus range)
        returns dict of monthly return data for unbalanced portfolio
        '''
        #initialize dict of monthly values of untouched portfolio, filled with starting port value
        # form {date: [value]}
        port = {date_range[0]: self.starting_port}

        #populate port value dict, starting range at 1 bc we have the starting port for values resulting from date_range[0]
        for date in range(1, len(date_range)):
            new_entry = self.get_months_returns(date, date_range, port)
            port[date_range[date]] = new_entry

        #return final dict with all port values for all months in pd
        return port


    def get_comparison(self, start_date, end_date):
        #get starting information
        return_dict = self.get_return_data()
        
        date_range = self.date_range(start_date, end_date)
        starting_portfolio = self.starting_port

        #get historical values of all portfolios 
        all_values = self.untouched_returns(starting_portfolio, date_range)


        return all_values

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

    #get all data
    portfolio = Portfolio(start_val, data.filename)
    all_values = portfolio.get_comparison(first_month, end_date)

    #name data
    lcg = all_values[end_date][0]
    lcv = all_values[end_date][1]
    mcg = all_values[end_date][2]
    mcv = all_values[end_date][3]
    scg = all_values[end_date][4]
    scv = all_values[end_date][5]

    return [display_period, lcg, lcv, mcg, mcv, scg, scv]

def rolling_pd_comparison(start_value, filename):
    data = ReturnData(filename)

    #build dataframe, form {"time pd": [final values], ... }
    five_yr = [["date", "lcg", "lcv", "mcg", "mcv", "scg", "scv"]]
    rolling_periods = data.get_rolling_periods(5)
    for period in rolling_periods:
        period_comparison = period_value_comparison(10, period, data)
        five_yr.append(period_comparison)

    ten_yr = [["date", "lcg", "lcv", "mcg", "mcv", "scg", "scv"]]
    rolling_periods = data.get_rolling_periods(10)
    for period in rolling_periods:
        period_comparison = period_value_comparison(10, period, data)
        ten_yr.append(period_comparison)

    twenty_yr = [["date", "lcg", "lcv", "mcg", "mcv", "scg", "scv"]]
    rolling_periods = data.get_rolling_periods(20)
    for period in rolling_periods:
        period_comparison = period_value_comparison(10, period, data)
        twenty_yr.append(period_comparison)

    return five_yr, ten_yr, twenty_yr


if __name__ == "__main__":
    #data = ReturnData("/home/michaela/summerwork/growth_value_project/growth_value.csv")
    #print(period_value_comparison(10, ("1/1/2000", "12/31/2004"), data))
    five_yr, ten_yr, twenty_yr = rolling_pd_comparison(10,"/home/michaela/summerwork/growth_value_project/growth_value_return_data.csv")
    

    with open("five_yr_data.csv", "w", newline = "") as fyd:
        writer = csv.writer(fyd)
        writer.writerows(five_yr)

    with open("ten_yr_data.csv", "w", newline = "") as tyd:
        writer = csv.writer(tyd)
        writer.writerows(ten_yr)

    with open("twenty_yr_data.csv", "w", newline="") as twyd:
        writer = csv.writer(twyd)
        writer.writerows(twenty_yr)

    