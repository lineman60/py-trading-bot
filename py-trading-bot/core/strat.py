#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np
import numbers

from core.common import VBTfunc, save_vbt_both, remove_multi
import core.indicators as ic
from core.macro import VBTMACROFILTER, VBTMACROMODE, VBTMACROTREND, VBTMACROTRENDPRD, major_int
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
import inspect
import pandas as pd

import logging
logger = logging.getLogger(__name__)
"""
Strategies on one action, no preselection

So it determines entries and exits for one action to optimize the return
"""
def defi_i_fast_sub(
        all_t: list,
        t: pd.core.frame.DataFrame, 
        calc_arrs: list, 
        jj: int
        ) -> list:
    """
    Multiply the entries or exits by the array (0 or 1)

    Arguments
    ----------
        all_t: entries or exits for all strategies before
        t: entries or exits for the strategy to be added
        calc_arrs: array of the strategy combination 
        jj: index of the strategy to be added in calc_arrs
    """ 
    try:
        for ii in range(len(calc_arrs)):
            t2=ic.VBTSUM.run(t,k=calc_arrs[ii][jj]).out
            t2=remove_multi(t2)
            all_t[ii]+=t2
    
        return all_t  
    except Exception as e:
        print(e)
   
def filter_macro(all_t: list,
                 macro_trend: pd.core.frame.DataFrame,
                 ) -> pd.core.frame.DataFrame:
    """
    For each trend set the correct entries and exits

    Arguments
    ----------
        all_t: entries or exits for all strategies before
        macro_trend: trend for each symbols and moment in time
    """   
    ent=None
    dic={0:-1, 1:1, 2:0}  #bull, bear, uncertain
    
    for ii in range(len(all_t)):
        ents_raw=VBTMACROFILTER.run(all_t[ii],macro_trend,dic[ii]).out #
        if ent is None:
            ent=ents_raw
        else:
            ent=ic.VBTOR.run(ent, ents_raw).out
    return ent
      
def defi_i_fast( 
        open_: pd.core.frame.DataFrame,
        high: pd.core.frame.DataFrame, 
        low: pd.core.frame.DataFrame, 
        close: pd.core.frame.DataFrame,
        calc_arrs: list,
        macro_trend: pd.core.frame.DataFrame=None,
        ) -> (list, list):
    """
    Calculate the entries and exits for each strategy of the array separately

    Arguments
    ----------
        close: close prices
        all_t: entries and exits for one strategy or the array
        ent_or_ex: do we want to return the entries or exits?
        calc_arr: array of the strategy combination 
        macro_trend: trend for each symbols and moment in time
    """ 
    try:
        non_pattern_len=7
        
        all_t_ent=[np.full(np.shape(close),0.0) for ii in range(len(calc_arrs))]
        all_t_ex=[np.full(np.shape(close),0.0) for ii in range(len(calc_arrs))]
        
        #determine if it is needed to calculate
        u_core=[False for ii in range(non_pattern_len)]
        u_bull=[False for ii in range(len(BULL_PATTERNS))]
        u_bear=[False for ii in range(len(BEAR_PATTERNS))]
        
        for ii in range(len(calc_arrs)): #3
            for jj in range(non_pattern_len):
                if calc_arrs[ii][jj] or calc_arrs[ii][jj+non_pattern_len+len(BULL_PATTERNS)]: #needed for entry or exit
                     u_core[jj]=True
            for jj in range(len(BULL_PATTERNS)):
                if calc_arrs[ii][non_pattern_len+jj]:
                    u_bull[jj]=True
            for jj in range(len(BEAR_PATTERNS)):
                if calc_arrs[ii][2*non_pattern_len+len(BULL_PATTERNS)+jj]:
                    u_bear[jj]=True                    

        if u_core[0]:
            t=ic.VBTMA.run(close)
            all_t_ent=defi_i_fast_sub(all_t_ent,t.entries, calc_arrs, 0)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.exits, calc_arrs, 0+non_pattern_len+len(BULL_PATTERNS))
         
        if u_core[1] or u_core[2]:
            t=ic.VBTSTOCHKAMA.run(high,low,close)
            all_t_ent=defi_i_fast_sub(all_t_ent,t.entries_stoch, calc_arrs, 1)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.exits_stoch, calc_arrs, 1+non_pattern_len+len(BULL_PATTERNS))
            all_t_ent=defi_i_fast_sub(all_t_ent,t.entries_kama, calc_arrs, 2)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.exits_kama, calc_arrs, 2+non_pattern_len+len(BULL_PATTERNS))            
        
        if u_core[3]:
            t=ic.VBTSUPERTREND.run(high,low,close)
            all_t_ent=defi_i_fast_sub(all_t_ent,t.entries, calc_arrs, 3)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.exits, calc_arrs, 3+non_pattern_len+len(BULL_PATTERNS))
              
        if u_core[4]:
            t=vbt.BBANDS.run(close)
            all_t_ent=defi_i_fast_sub(all_t_ent,t.lower_above(close), calc_arrs, 4)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.upper_below(close), calc_arrs, 4+non_pattern_len+len(BULL_PATTERNS))
  
        if u_core[5] or u_core[6]: 
            t=vbt.RSI.run(close,wtype='simple')
            all_t_ent=defi_i_fast_sub(all_t_ent,t.rsi_crossed_below(20), calc_arrs, 5)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.rsi_crossed_above(80), calc_arrs, 5+non_pattern_len+len(BULL_PATTERNS))
            all_t_ent=defi_i_fast_sub(all_t_ent,t.rsi_crossed_below(30), calc_arrs, 6)
            all_t_ex=defi_i_fast_sub(all_t_ex,t.rsi_crossed_above(70), calc_arrs, 6+non_pattern_len+len(BULL_PATTERNS))            
        
        for ii, f_name in enumerate(BULL_PATTERNS):
            if u_bull[ii]:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,f_name, "ent").out
                all_t_ent=defi_i_fast_sub(all_t_ent,t, calc_arrs, non_pattern_len+ii)
            
        for ii, f_name in enumerate(BEAR_PATTERNS):
            if u_bear[ii]:
                t=ic.VBTPATTERNONE.run(open_,high,low,close,f_name, "ex").out
                all_t_ex=defi_i_fast_sub(all_t_ex,t, calc_arrs, ii+2*non_pattern_len+len(BULL_PATTERNS))        

        for ii in range(len(calc_arrs)):
            all_t_ent[ii]=(all_t_ent[ii]>=1)
            all_t_ex[ii]=(all_t_ex[ii]>=1)
        #agregate the signals for different macro trends
        if macro_trend is not None:
            all_t_ent=filter_macro(all_t_ent, macro_trend)                    
            all_t_ex=filter_macro(all_t_ex, macro_trend)     
        else:
            all_t_ent=all_t_ent[0]
            all_t_ex=all_t_ex[0]

        return all_t_ent, all_t_ex
    except Exception as e:
        import sys
        _, e_, exc_tb = sys.exc_info()
        print(e)
        print("line " + str(exc_tb.tb_lineno))
        logger.error(e, stack_info=True, exc_info=True)     

def defi_nomacro(
        close: pd.core.frame.DataFrame,
        all_t: list,
        ent_or_ex: str, 
        a_simple: list
        )-> (pd.core.frame.DataFrame, pd.core.frame.DataFrame):
    """
    transform the array of strategy into entries and exits

    Arguments
    ----------
        close: close prices
        all_t: entries and exits for one strategy or the array
        ent_or_ex: do we want to return the entries or exits?
        calc_arr: array of the strategy combination 
    """
    non_pattern_len=7
    len_ent=non_pattern_len+len(BULL_PATTERNS)
    len_ex=non_pattern_len+len(BEAR_PATTERNS)
    ent=None

    if ent_or_ex=="ent":
        arr=a_simple[0:len_ent] 
    else:
        arr=a_simple[len_ent:len_ent+len_ex]  
    
    for ii in range(len(arr)):
        if arr[ii]:
            t=all_t[ii]
                    
            if ent is None:
                ent=t
            else:
                ent=ic.VBTOR.run(ent,t).out
                
    default=ic.VBTAND.run(ent, np.full(all_t[0].shape, False)).out #trick to keep the right shape
    return ent, default

def strat_wrapper_simple(
        open_: pd.core.frame.DataFrame,
        high: pd.core.frame.DataFrame, 
        low: pd.core.frame.DataFrame, 
        close: pd.core.frame.DataFrame, 
        a_simple: list,
        dir_simple:str="long"
        ) -> (pd.core.frame.DataFrame, pd.core.frame.DataFrame, pd.core.frame.DataFrame, pd.core.frame.DataFrame):
    """
    wrapper for the different strategy functions

    No trend split

    Each strategy is defined by the arrays a_simple

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        a_simple: array of the strategy combination 
        dir_simple: direction to use during bull trend
    """
    ent,ex=defi_i_fast( open_,high, low, close,[a_simple])
    default=ic.VBTAND.run(ent, np.full(ent.shape, False)).out #trick to keep the right shape
    
    if dir_simple in ["long","both"]:
        entries=ent
        exits=ex
    else:
        entries=default
        exits=default
        
    if dir_simple in ["both","short"]:
        entries_short=ex
        exits_short=ent
    else:
        entries_short=default
        exits_short=default

    return entries, exits, entries_short, exits_short

def strat_wrapper_macro(open_: np.array,
                        high: np.array, 
                        low: np.array, 
                        close: np.array, 
                        a_bull: list, 
                        a_bear: list, 
                        a_uncertain: list,
                        dir_bull: str="long", 
                        dir_bear: str="both",
                        dir_uncertain: str="both",
                        prd:bool=False,
                        ):
    """
    wrapper for the different strategy functions

    split the trend in 3 parts: bear, uncertain, bull
    set a strategy for each of them

    Each strategy is defined by the arrays a_bull, a_bear, a_uncertain

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        a_bull: array of the strategy combination to use for bull trend
        a_bear: array of the strategy combination to use for bear trend
        a_uncertain: array of the strategy combination to use for uncertain trend
        dir_bull: direction to use during bull trend
        dir_bear: direction to use during bear trend
        dir_uncertain: direction to use during uncertain trend
    """
    try:
        
        if prd:
            t=VBTMACROTRENDPRD.run(close)
        else:
            t=VBTMACROTREND.run(close)
        
        #combine for the given array the signals and patterns
        ent,ex=defi_i_fast( open_,
                           high,
                           low, 
                           close,
                           calc_arrs=[a_bull,a_bear, a_uncertain ],
                           macro_trend=t.macro_trend)
        #put both/long/short
        t2=VBTMACROMODE.run(ent,ex, t.macro_trend,\
                           dir_bull=dir_bull,
                           dir_bear=dir_bear,
                           dir_uncertain=dir_uncertain)
    
        return t2.entries, t2.exits, t2.entries_short, t2.exits_short, t.macro_trend, t.min_ind, t.max_ind  
    except Exception as e:
        import sys
        _, e_, exc_tb = sys.exc_info()
        print(e)
        print("line " + str(exc_tb.tb_lineno))
        logger.error(e, stack_info=True, exc_info=True) 

### For backtesting ###
class Strat(VBTfunc):
    def __init__(self,symbol_index,period,**kwargs):
        super().__init__(symbol_index,period)
        
        if kwargs.get("index",False):
            #self.only_index=True
            self.close=self.close_ind
            self.open=self.open_ind
            self.low=self.low_ind
            self.high=self.high_ind
        else:
            #self.only_index=False
            self.symbols_simple=self.close.columns.values
            
        if kwargs.get("suffix"):
            self.suffix="_" + kwargs.get("suffix")
        else:
            self.suffix=""
        
    def get_output(self,s):
        self.entries=s.entries
        self.exits=s.exits
        self.entries_short=s.entries_short
        self.exits_short=s.exits_short
        self.trend=s.trend
        self.kama=s.kama
        self.bb_bw=s.bb_bw
        self.macro_trend=s.macro_trend
        self.max_ind=s.max_ind
        self.min_ind=s.min_ind
  
    def symbols_simple_to_complex(self,symbol_simple,ent_or_ex):
        if ent_or_ex=="ent":
            self.symbols_complex=self.entries.columns.values
        else:
            self.symbols_complex=self.exits.columns.values
        
        for ii, e in enumerate(self.symbols_complex):
            if type(e)==tuple:
                if e[-1]==symbol_simple: #9
                    return e
            elif type(e)==str:
                if e==symbol_simple: #9
                    return e                
        raise ValueError("symbols_simple_to_complex not found for symbol: "+str(symbol_simple) +\
                         " columns available: "+str(self.symbols_complex))
    
    def save(self):
        save_vbt_both(self.close, 
                 self.entries, 
                 self.exits, 
                 self.entries_short,
                 self.exits_short,                  
                 suffix=self.suffix
                 )

    def get_return(self,**kwargs):
        pf=vbt.Portfolio.from_signals(self.close, 
                                      entries =self.entries,
                                      exits =  self.exits,
                                      short_entries=self.entries_short,
                                      short_exits  =self.exits_short,
                                      upon_opposite_entry="Reverse"
                                      )
        #benchmark_return makes sense only for bull
        delta=pf.total_return().values[0]
        return delta
    
    def call_strat(self,name,**kwargs):
        getattr(self,name)(**kwargs)
########## Strats ##############
# Example of simple strategy for pedagogic purposes
    def stratHold(self):
        t=ic.VBTVERYBULL.run(self.close)
        self.entries=t.entries
        self.exits=t.exits
        self.entries_short=t.exits
        self.exits_short=t.exits

    def stratRSI(self,**kwargs):
        t=vbt.RSI.run(self.close,wtype='simple')
        self.entries=t.rsi_crossed_below(20)
        self.exits=t.rsi_crossed_above(80)
        t2=ic.VBTFALSE.run(self.close)
        self.entries_short=t2.entries
        self.exits_short=t2.entries
        
    def stratRSIeq(self,**kwargs):
        a=[0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 
           0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 
       0., 0., 0., 0., 0.]

        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)     
        
# The best strategy without macro is hold, here strat D bear is acceptable and provides some signals
# to define pattern light
    def stratDbear(self,**kwargs):
        a=[0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0., 0., 0., 1., 1., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 0., 1., 0.]


        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)
        
    def stratReal(self,**kwargs):
        a_bull=[1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0.,
               1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
               1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_bear=[1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        a_uncertain= [1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
               0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.,
               1., 0., 0., 0., 0., 1., 0., 1., 1., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)  

    def stratDiv(self,**kwargs):
        
        #optimal with fee 0,0005
        a=[0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 1., 1.,
       1., 0., 1., 0., 0., 0., 0., 1., 0., 0.]
        
        #optimal with fee 0,0001
       # a=[0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       # 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
        #1., 1., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0.]

        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)

        
    def stratTestSimple(self,**kwargs):
        a=[0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]


        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)
    #In long/both/both, on period 2007-2022, CAC40 return 5.26 (bench 2.26), DAX xy (2.66), NASDAQ xy (17.2)  
    def stratD(self,**kwargs):
        a_bull= [1., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 1., 1., 0.,
                1., 0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
                0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
        a_bear= [1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1,
         0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0]
        a_uncertain= [0., 0., 1., 0., 0., 1., 0., 0., 1., 0., 0., 1., 0., 1., 0., 1.,
                1., 1., 1., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,
                0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)      
        
    #In long/both/both, on period 2007-2022, CAC40 return 4.35 (bench 2.26), DAX xy (2.66), NASDAQ xy (17.2)    
    def stratE(self,**kwargs):
        a_bull=[0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,
        1., 1., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0.]
        a_bear= [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0,
         1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0]
        a_uncertain=  [1., 0., 0., 0., 0., 1., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0.,
         0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 1., 1., 0., 0., 1., 1., 0., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)         
 
#In long/both/both, 
    def stratF(self,**kwargs):
        a_bull=[0., 0., 0., 0., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 0., 1.,
            1., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
            0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_bear= [0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1,
           1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0,
           0, 0]
        a_uncertain=  [0., 1., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0.,
            0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
            0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)         
        
#In long/both/both, 

    #Optimized on 2007-2023, CAC40 7.58 (3.13 bench), DAX 2.31 (1.68), NASDAQ 19.88 (12.1), IT 15.69 (8.44)
    def stratG(self,**kwargs):
        a_bull=[0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0., 1., 0., 1., 0., 1.,
                1., 1., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
                0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.]
        a_bear= [0., 1., 0., 0., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 0., 1.,
         1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
         1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_uncertain=  [0., 1., 1., 0., 0., 1., 1., 0., 0., 1., 1., 1., 1., 1., 0., 0.,
         1., 0., 1., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 1., 0., 1., 1., 0., 0., 0., 0., 1., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs) 
        
    def stratIndex(self,**kwargs):
        a_bull=[1., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 1., 1., 0., 0., 1.,
       0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]
        a_bear=[1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0]
        a_uncertain=[1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 1.,
       0., 0., 1., 0., 0., 0., 1., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs) 
    
    #reoptimization with 2007-2023 FCHI 9.43 (0.15 for the benchmark), GDAXI 3.09 (0.7), IXIC 4.58 (3.31), DJI 1.5 (1.65)
    def stratIndexB(self,**kwargs):
        a_bull=[1., 0., 0., 1., 1., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0.,
                1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0.,
                0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 1., 0.]
        a_bear=[0., 0., 0., 1., 1., 1., 1., 0., 0., 0., 0., 0., 1., 1., 0., 0.,
         1., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
         0., 1., 0., 1., 0., 0., 1., 0., 0., 1., 1., 0.]
        a_uncertain=[1., 1., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0.,
         1., 0., 1., 0., 0., 0., 1., 0., 0., 1., 0., 1., 0., 0., 0., 0.,
         0., 1., 0., 1., 1., 0., 1., 1., 1., 1., 0., 0.] 
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)   
       
    def stratIndexSL(self,**kwargs):
        a_bull=[1., 1., 0., 0., 1., 0., 1., 0., 0., 0., 1., 1., 1., 1., 0., 0.,
        1., 1., 1., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 0.]
        a_bear=[0., 0., 1., 1., 0., 1., 1., 0., 0., 0., 0., 0., 1., 1., 0., 0.,
         1., 0., 0., 0., 1., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
         0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 1., 0.]
        a_uncertain=[1., 1., 1., 1., 1., 0., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0.,
         1., 1., 0., 0., 1., 1., 1., 0., 1., 1., 1., 1., 0., 0., 0., 0.,
         0., 0., 1., 1., 1., 0., 1., 1., 1., 1., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)         

    def stratIndexTSL(self,**kwargs):
        a_bull=[1., 0., 0., 1., 1., 0., 1., 0., 0., 0., 1., 1., 0., 1., 0., 0.,
                0., 0., 0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
                0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0.]
        a_bear=[0., 0., 1., 0., 1., 1., 1., 0., 0., 0., 0., 0., 1., 1., 1., 0.,
         1., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.,
         0., 1., 0., 1., 0., 0., 1., 1., 0., 1., 1., 0.]
        a_uncertain=[1., 1., 0., 1., 0., 1., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0.,
         1., 0., 1., 1., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0.,
         0., 1., 0., 1., 1., 0., 1., 0., 1., 1., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)
        
    #Optimized on 2007-2023, for sl=0.5 %
    def stratSL(self,**kwargs):
        a_bull=[1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 0., 0., 1., 0., 1.,
        1., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 1.,
        0., 0., 1., 0., 0., 1., 0., 1., 0., 1., 0., 0.]
        a_bear=[1., 1., 0., 0., 0., 1., 1., 0., 0., 1., 0., 0., 1., 1., 1., 1.,
        1., 0., 1., 0., 1., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
        1., 0., 0., 1., 1., 0., 0., 0., 0., 1., 0., 0.]
        a_uncertain=[1., 1., 1., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 0., 1.,
        1., 1., 1., 1., 1., 1., 0., 1., 0., 0., 1., 1., 0., 0., 0., 0.,
        0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0.] 
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)   
        
    #Optimized on 2007-2023, for tsl=0.5 %
    def stratTSL(self,**kwargs):
        a_bull=[0., 1., 1., 0., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 0., 1.,
        1., 1., 1., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.]
        a_bear=[1., 1., 1., 1., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 0., 1.,
        1., 0., 1., 1., 1., 1., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
        1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0.]
        a_uncertain= [1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 1., 0.,
        1., 1., 1., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 1., 0., 1., 1., 0., 0., 0., 0., 1., 0., 0.]  
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)           
        
    # As strat_kama_stoch for bear and uncertain trend
    # Use MA for bull, so if the 5 days smoothed price crosses the 15 days smoothed price, a signal is created
    def strat_kama_stoch_matrend_bbands(self,**kwargs): #ex strat11
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             dir_uncertain=kwargs.get("dir_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",
                             trend_key="bbands")
        self.get_output(s)  
        
    def strat_kama_stoch_matrend_macdbb_macro(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=True,
                             dir_bull=kwargs.get("dir_bull","long"), 
                             dir_bear=kwargs.get("dir_bear","short"),
                             dir_uncertain=kwargs.get("dir_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="macdbb",
                             macro_trend_index=kwargs.get("macro_trend_index",False))
        self.get_output(s)        

def function_to_res(
        f_name: str, 
        open_: np.array, 
        high: np.array, 
        low: np.array, 
        close: np.array,
        light: bool=None
        ) -> (np.array, np.array):
    '''
    Wrapper to call function from indicators based on their name

    Arguments
    ----------
        f_name: name of the function in indicators
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        light: for pattern, choose pattern normal or light
    '''
    f_callable=getattr(ic,f_name)
    dic={}

    for k in ["open_","close","high","low","light"]:
        if k in inspect.getfullargspec(f_callable.run).args:
            dic[k]=locals()[k]

    res = f_callable.run(**dic)
    return res.entries, res.exits

def strat_wrapper(
        open_: np.array,
        high: np.array, 
        low: np.array, 
        close: np.array, 
        close_ind: np.array,
        f_bull:str="VBTSTOCHKAMA", 
        f_bear:str="VBTSTOCHKAMA", 
        f_uncertain:str="VBTSTOCHKAMA",
        f_very_bull:str="VBTSTOCHKAMA", 
        f_very_bear:str="VBTSTOCHKAMA",
        trend_lim: numbers.Number=1.5, 
        trend_lim2: numbers.Number=10, 
        macro_trend_bool:bool=False,
        dir_bull:str="long", 
        dir_bear:str="short",
        dir_uncertain:str="both",
        trend_key:str="bbands",
        macro_trend_index:bool=False,
        light:bool=True):
    '''
    wrapper for the different strategy functions

    split the trend in 5 parts: very bear, bear, uncertain, bull and very bull
    set a strategy for each of them

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        close_ind: close prices of the corresponding main index
        f_bull: strategy function to use during bull trend
        f_bear: strategy function to use during bear trend
        f_uncertain: strategy function to use during uncertain trend
        f_very_bull: strategy function to use during very bull trend
        f_very_bear: strategy function to use during very bear trend
        trend_lim: score of the trend between uncertain and bear/bull
        trend_lim2: score of the trend between bear/bull and very bear/very bull
        macro_trend_bool: differentiate the direction depending on the macro trend
        dir_bull: direction to use during bull trend
        dir_bear: direction to use during bear trend
        dir_uncertain: direction to use during uncertain trend
        trend_key: which trend function is to be used
        macro_trend_index: base the macro trend calculation on the main index only, or not
        light: for pattern, choose pattern normal or light
    '''
    
    macro_trend=np.full(close.shape, 0)  
    min_ind=np.full(close.shape, 0)   
    max_ind=np.full(close.shape, 0)   
    
    if macro_trend_bool:
        if macro_trend_index:
            macro_trend,min_ind, max_ind=major_int(close_ind)
        else:   
            macro_trend,min_ind, max_ind=major_int(close,threshold=0.03)
        
    if trend_key=="bbands":
        t=ic.VBTBBANDSTREND.run(close)
    else:
        t=ic.VBTMACDBBTREND.run(close)
  
    ent_very_bull, ex_very_bull=function_to_res(f_very_bull,open_, high, low, close,light=light)
    ent_very_bear, ex_very_bear=function_to_res(f_very_bear, open_, high, low, close,light=light)
    ent_bull, ex_bull=function_to_res(f_bull,open_, high, low, close,light=light)
    ent_bear, ex_bear=function_to_res(f_bear, open_, high, low, close,light=light)
    ent_uncertain, ex_uncertain=function_to_res(f_uncertain, open_, high, low, close,light=light)

    temp_ent= np.full(close.shape, False)   
    temp_ex= np.full(close.shape, False)       
    entries= np.full(close.shape, False)   
    exits= np.full(close.shape, False)   
    entries_short= np.full(close.shape, False)   
    exits_short= np.full(close.shape, False)
    
    temp=2
    
    for ii in range(len(close)):
          if trend_lim!=100:
              if t.trend[ii]<=-trend_lim2:
                  temp_ent[ii] = ent_very_bull[ii]
                  temp_ex[ii] = ex_very_bull[ii] 
              elif t.trend[ii]>=trend_lim2:
                  temp_ent[ii] = ent_very_bear[ii]
                  temp_ex[ii] = ex_very_bear[ii]                   
              elif t.trend[ii]<-trend_lim:
                  temp_ent[ii] = ent_bull[ii]
                  temp_ex[ii] = ex_bull[ii] 
              elif t.trend[ii]>trend_lim:
                  temp_ent[ii] = ent_bear[ii]
                  temp_ex[ii] = ex_bear[ii]
              else:
                  temp_ent[ii] = ent_uncertain[ii]    
                  temp_ex[ii] = ex_uncertain[ii]  
          else:
              temp_ent[ii] = ent_uncertain[ii]    
              temp_ex[ii] = ex_uncertain[ii]  

          if macro_trend_bool:
              if macro_trend[ii]==-1:
                  if (temp!=0 and dir_bull not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=0 and dir_bull not in ["both", "long"]):
                      exits[ii] = True

                  if dir_bull in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_bull in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=0
                  
              elif macro_trend[ii]==1:
                  if (temp!=1 and dir_bear not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=1 and dir_bear not in ["both", "long"]):
                      exits[ii] = True

                  if dir_bear in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_bear in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=1
              else:
                  if (temp!=2 and dir_uncertain not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=2 and dir_uncertain not in ["both", "long"]):
                      exits[ii] = True
                  
                  if dir_uncertain in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_uncertain in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]                  

                  temp=2
          else: #no macro trend
              if dir_uncertain in ["both", "short"]:
                  entries_short[ii] = temp_ex[ii]
                  exits_short[ii] = temp_ent[ii] 
                
              if dir_uncertain in ["both", "long"]:
                  entries[ii] = temp_ent[ii]
                  exits[ii] = temp_ex[ii]    
     
    return entries, exits, entries_short, exits_short, t.trend, macro_trend, t.kama, t.bb_bw, min_ind, max_ind  
  
STRATWRAPPER = vbt.IF(
     class_name='StratWrapper',
     short_name='st_wrapper',
     input_names=['high', 'low', 'close','open_','close_ind'],
     param_names=['f_bull', 'f_bear', 'f_uncertain','f_very_bull', 'f_very_bear','trend_lim', 
                  'trend_lim2', 
                  'macro_trend_bool','dir_bull',
                  'dir_bear','dir_uncertain','trend_key','macro_trend_index'],
     output_names=['entries', 'exits', 'entries_short', 'exits_short','trend','macro_trend',
                   'kama','bb_bw','min_ind', 'max_ind'] 
).with_apply_func(
     strat_wrapper, 
     takes_1d=True, 
     trend_lim=1.5,
     trend_lim2=10,
     macro_trend_bool=False,
     dir_bull="long", 
     dir_bear="short",
     dir_uncertain="both",
     f_bull="VBTSTOCHKAMA", 
     f_bear="VBTSTOCHKAMA", 
     f_uncertain="VBTSTOCHKAMA",
     f_very_bull="VBTSTOCHKAMA", 
     f_very_bear="VBTSTOCHKAMA", 
     trend_key="bbands",
     macro_trend_index=False,
     light=True
)              