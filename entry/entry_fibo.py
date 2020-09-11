import math_op as mo
import initialize as init
import operator as op
import math



class EntFibo(init.Initialize):

    @classmethod
    def __init__(cls,series,last_retracement = True, first_retracement = True, extension = True):

        """ Class that uses Fibonnacci strategy to enter and exit from the market

        Trying to enter the market with Fibonacci retracement and extension. 3 types:
            1- Retracement from the last wave
            2- Retracement from beginning of the trend
            3- Extension from a previous wave (largest one in the last trend)

        Then try to exit the market using Fibonnacci extension or retracement


        Parameters
        ----------
            last_retracement : bool
                Tell the system if it trys to enter and exit the market using the last low
            - first_retracement is to say if we try to retrace from the beginning of the trend
            - extenstion is to say if we try to buy by extending largest setback from the trend
            - lenght_trend is to say how long we check for either global extremum or search for the largest
              setback/retracement (for extension). By default, it's 1.5 times the lenght of the nb_data we use as a
              parameter to test the indicator (so 50% more)

        Notes (Improvements to do)
        --------------------------

            - No slippage included in entry or exit. If the price reached the desired level, we just exit at either the
            current price or the next desired price
            - The system doesn't check on a shorter time frame if it reaches an entry point and a stop at the same time
            or even an exit point and stop at the same time (in case of high volatility).
                - The system is "conservative", if a stop is trigerred it will priorise it over an entry or exit.
                    It also prioritizes an entry over a new low/high or when the system reaches an extension's condition
                    (conditions that make the system stop trying to enter in the market when trigerred)
                - Taking into account the system, those are really rare cases. However it could be tested by using a
                shorter time every time an entry or exit signal
                - Desired modifications should be in functions "try_entry" and "try_exit"

        """

        super().__init__(cls,class_method=True)
        cls.last_retracement = last_retracement
        cls.first_retracement = first_retracement
        cls.extension=extension
        cls.series=series
        cls.extreme = {}
        cls.high="high"
        cls.low="low"
        cls.high_idx="high_idx"
        cls.low_idx = "low_idx"
        cls.fst_ext_cdt = False

    @classmethod
    def __call__(cls,curr_row,buy_signal=False,sell_signal=False):
        """
        Default function to determine the entry point
        """

        cls.buy_signal = buy_signal
        cls.sell_signal = sell_signal
        cls.curr_row = curr_row
        cls.is_entry = False

        cls.first_data = curr_row - cls.nb_data - cls.buffer_extremum + 1
        if cls.first_data < 0:
            cls.first_data = 0

        if buy_signal and sell_signal :
            raise Exception('Cannot have a buy and sell signal at the same time')

        cls.set_extremum()

        if cls.buy_signal:
            start_point=cls.extreme[cls.low_idx]
            cls.fst_op=op.gt
            cls.sec_op=op.lt
            cls.trd_op=op.sub
            cls.fth_op=op.add
            cls.fif_op=op.ge
            cls.six_op=op.le
            cls.fst_data = cls.high
            cls.sec_data = cls.low
            cls.fst_idx = cls.high_idx
            cls.sec_idx = cls.low_idx
            cls.entry = cls.stop = cls.low_name
            cls.exit = cls.high_name
            cls.inv = -1

        if cls.sell_signal:
            start_point = cls.extreme[cls.high_idx]
            cls.fst_op=op.lt
            cls.sec_op=op.gt
            cls.trd_op=op.add
            cls.fth_op=op.sub
            cls.fif_op=op.le
            cls.six_op=op.ge
            cls.fst_data = cls.low
            cls.sec_data = cls.high
            cls.fst_idx = cls.low_idx
            cls.sec_idx = cls.high_idx
            cls.entry = cls.stop = cls.high_name
            cls.exit = cls.low_name
            cls.inv = 1

        cls.mo_ = mo.MathOp(series=cls.series, default_col=cls.default_data)
        cls.local_extremum_=cls.mo_.local_extremum(start_point=start_point, end_point=cls.curr_row, window=cls.window)

        if cls.extension:
            cls.largest_extension()

        cls.try_entry()

        if cls.is_entry:
            cls.try_exit()

    @classmethod
    def largest_extension(cls):
        """
        Find largest extension from current trend
        """

        if cls.buy_signal:
            my_data={}
            fst_data='curr_high'
            sec_data='curr_low'
            my_data[fst_data]=None
            my_data[sec_data] = None
            fst_name=cls.rel_high
            sec_name=cls.rel_low

        if cls.sell_signal:
            my_data={}
            fst_data='curr_low'
            sec_data='curr_high'
            my_data[fst_data]=None
            my_data[sec_data] = None
            fst_name=cls.rel_low
            sec_name=cls.rel_high

        curr_row_ = 0

        while curr_row_ < len(cls.local_extremum_):

            if  my_data[fst_data] == None:
                my_data[fst_data] = cls.local_extremum_.iloc[curr_row_,cls.local_extremum_.columns.get_loc(fst_name)]
                curr_row_+=1

                t_curr_row = curr_row_

                try:
                    test = cls.local_extremum_.iloc[t_curr_row, cls.local_extremum_.columns.get_loc(fst_name)]

                except:
                    continue

                while not math.isnan(cls.local_extremum_.iloc[t_curr_row, \
                                                              cls.local_extremum_.columns.get_loc(fst_name)]) & (
                                  t_curr_row < len(cls.local_extremum_)):

                    if cls.fst_op(cls.local_extremum_.iloc[t_curr_row, cls.local_extremum_.columns.get_loc(fst_name)], \
                                  my_data[fst_data]):
                        my_data[fst_data] = cls.local_extremum_.iloc[t_curr_row, \
                                                                     cls.local_extremum_.columns.get_loc(fst_name)]

                    t_curr_row += 1

                    try:
                        test = cls.local_extremum_.iloc[t_curr_row, cls.local_extremum_.columns.get_loc(fst_name)]

                    except:
                        continue

                t_curr_row = 0
                continue

            if (math.isnan(my_data[fst_data]) \
                 | cls.fst_op(cls.local_extremum_.iloc[curr_row_,cls.local_extremum_.columns.get_loc(fst_name)], \
                          my_data[fst_data])) & (my_data[sec_data] == None):
                my_data[fst_data] = cls.local_extremum_.iloc[curr_row_,cls.local_extremum_.columns.get_loc(fst_name)]


            if my_data[sec_data] == None:

                my_data[sec_data] = cls.local_extremum_.iloc[curr_row_, cls.local_extremum_.columns.get_loc(sec_name)]
                curr_row_+=1

                if curr_row_ ==  len(cls.local_extremum_):
                    pass

                else:
                    t_curr_row = curr_row_

                    try:
                        test = cls.local_extremum_.iloc[t_curr_row, cls.local_extremum_.columns.get_loc(sec_name)]

                    except:
                        continue

                    while not math.isnan(cls.local_extremum_.iloc[t_curr_row, \
                     cls.local_extremum_.columns.get_loc(sec_name)]) & (t_curr_row < len(cls.local_extremum_)):

                        if cls.sec_op(cls.local_extremum_.iloc[t_curr_row, \
                                        cls.local_extremum_.columns.get_loc(sec_name)], my_data[sec_data]):

                            my_data[sec_data] = cls.local_extremum_.iloc[t_curr_row, \
                                                                        cls.local_extremum_.columns.get_loc(sec_name)]

                        t_curr_row += 1

                        try:
                            test = cls.local_extremum_.iloc[t_curr_row, cls.local_extremum_.columns.get_loc(fst_name)]

                        except:
                            continue

                    t_curr_row = 0
                    continue


            if (math.isnan(my_data[sec_data])) \
                    | cls.sec_op(cls.local_extremum_.iloc[curr_row_,cls.local_extremum_.columns.get_loc(sec_name)], \
                         my_data[sec_data]):
                my_data[sec_data] = cls.local_extremum_.iloc[curr_row_, cls.local_extremum_.columns.get_loc(sec_name)]

                curr_row_+=1

                if curr_row_ == len(cls.local_extremum_):
                    pass
                
                else:
                    continue

            if not hasattr(cls,'largest_extension_'):
                cls.largest_extension_ = cls.inv*(my_data[sec_data] - my_data[fst_data])
                my_data[fst_data] = None
                my_data[sec_data] = None
                continue

            if op.ge(cls.inv*(my_data[sec_data] - my_data[fst_data]), cls.largest_extension_):
                cls.largest_extension_ = cls.inv*(my_data[sec_data] - my_data[fst_data])
                my_data[fst_data] = None
                my_data[sec_data] = None
                continue

            my_data[fst_data] = None
            my_data[sec_data] = None

    @classmethod
    def set_extremum(cls):
        """
        PURPOSE
        -------
        Set the global max and min for the given range (from first_data to curr_row)

        """

        data_range = cls.series.loc[cls.first_data:cls.curr_row,cls.default_data]
        cls.extreme = {cls.high : data_range.max(),
                       cls.low : data_range.min(),
                       cls.high_idx : data_range.idxmax(),
                       cls.low_idx : data_range.idxmin()
                       }

    @classmethod
    def try_entry(cls):
        """ Method to try entering in the market

        Function that will try to enter in the market :
                Until we hit the desired extension and/or retracement
                Stop trying to enter in the market when a condition is met
                    (Fibonnacci extension 0.618% of largest past extension)

        NOTES
        -----
        Note that the system will priorise an entry over a new high or new low (to be more conservative). To solve
        this issue (rare cases, only with high volatility) :
            Check simulateneously if a new high or low is reached &  (if a buy/sell level is trigerred |
                market hits minimum required extension (if this condition is tested))
            Then, on a shorter timeframe, check if an entry | minimum required extension is reached before the
                market makes new low or high, vice versa

        """

        data_test = len(cls.series)-cls.curr_row-1

        if cls.is_entry:
            raise Exception('Already have an open position in the market...')

        for curr_row_ in range(data_test):

            if cls.buy_signal:
                pass

            if cls.sell_signal:
                pass

            cls.curr_row += 1

            relative_extreme = cls.series.loc[cls.curr_row, cls.default_data]

            #Buy or sell signal (entry)
            #   - Buy if current market price goes below our signal or equal
            #   - Sell if current market price goee above our signal or equal
            if cls.fif_op(cls.trd_op(cls.extreme[cls.fst_data],cls.largest_extension_),\
                          cls.series.loc[cls.curr_row,cls.entry]):

                cls.is_entry = True
                break

            #Market hits the minimum required extension - first condition met (point to enter in the market)
            if cls.bol_st_ext & cls.fif_op(cls.trd_op(cls.extreme[cls.fst_data], \
                        cls.largest_extension_ * cls.fst_cdt_ext), cls.series.loc[cls.curr_row,cls.entry]):

                relative_extreme = cls.series.loc[cls.curr_row, cls.entry]

                cls.fst_ext_cdt = True
                continue

            # The system will stop trying to enter in the market :
            #   - first condition (extension) is met (hit a required
            #       % of the largest extension, previously (61.8% by default)
            #   - It went back then reached the minimum retracement (88.2% by default)

            if cls.bol_st_ext & cls.fst_ext_cdt & \
                    cls.six_op(cls.fth_op(relative_extreme,cls.inv*(op.sub(relative_extreme, \
                        cls.extreme[cls.fst_data])*cls.sec_cdt_ext)),cls.series.loc[cls.curr_row,cls.exit]) :
                print(f"The market hits previously the required {cls.fst_cdt_ext} % of the largest extension \
                       and then retrace in the opposite direction of {cls.sec_cdt_ext}")

                break

            #Changing global low or high if current one is lower or higher
            if cls.fst_op(cls.series.loc[cls.curr_row, cls.default_data], cls.extreme[cls.fst_data]):

                cls.extreme[cls.fst_data] = cls.series.loc[cls.curr_row, cls.default_data]
                cls.extreme[cls.fst_idx] = cls.curr_row

    @classmethod
    def try_exit(cls):

        """Method which try to exit the market.

        The goal of this method is to exit the market when a close signal is triggered or a stop loss is
        trigerred

        Notes
        -----
        The stops is tighten if :
            `self.bol_st_ext` is `True` in `initialize.py` (we tell the system to test this feature) &
            `self.sec_cdt_ext` in `initialize.py` is met, ie the market rebounces (or setback) to the desired
                retracement compared to the last peak or low (default value is 0.882 and `self.default_data` used for
                calculation is `self.adj_close_name`

        """

        """ 
        if cls.sell_signal:
            start_point = cls.extreme[cls.high_idx]
            cls.fst_op=op.lt
            cls.sec_op=op.gt
            cls.trd_op=op.add
            cls.fth_op=op.sub
            cls.fif_op=op.le
            cls.six_op=op.ge
            cls.fst_data = cls.low
            cls.sec_data = cls.high
            cls.fst_idx = cls.low_idx
            cls.sec_idx = cls.high_idx
            cls.entry = cls.stop = cls.high_name
            cls.exit = cls.low_name
            cls.inv = 1
        """
    
        # Buy or sell signal (exit)
        #   - Buy if current market price goes below our signal or equal
        #   - Sell if current market price goee above our signal or equal

        if cls.fif_op(cls.trd_op(cls.extreme[cls.fst_data], cls.largest_extension_), \
                      cls.series.loc[cls.curr_row, cls.entry]):
            pass
        #break

        cls.is_entry = False


