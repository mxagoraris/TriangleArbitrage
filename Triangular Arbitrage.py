# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 15:57:01 2021

@author: Emmanouil Xagoraris
"""

import numpy as np
import pandas as pd

def TriangularArbitrage (Terms,Base,Crosscurrency,ask,bid,difference):
    
    initial = 10**6 #assuming that we have a million of the currency that 
                    #we are selling
    if difference > 0: #Terms are undervalued
        arbitrage_results = bid.loc[Base,Terms]*initial * bid.loc[Crosscurrency,Base] * bid.loc[Terms,Crosscurrency]
        currency1 = Base
        currency2 = Terms
    else:
        arbitrage_results = bid.loc[Terms,Base]*initial *bid.loc[Crosscurrency,Terms] * bid.loc[Base,Crosscurrency]
        currency1 = Terms
        currency2 = Base
    
    if arbitrage_results == np.nan:
        results = 0 
    else:
        results = arbitrage_results - initial
    if  results > 0:
        success = True
        
    else:
        success = False
    
    return (success, results, currency1,currency2)
        
        

FXMatrix = pd.read_excel("Quotation Matrix.xlsx",header=0,index_col=0)
k = len(FXMatrix)

currencies = np.array(FXMatrix.columns,dtype=str)

pd.options.display.float_format = "{:,.7f}".format

ask = np.zeros([k,k],dtype=float)
bid = np.zeros([k,k],dtype=float)
mid = np.zeros([k,k],dtype=float)
implied = np.ones([k,k],dtype=float)
quoted = np.ones([k,k],dtype=float)
arbitrage = np.ones([k,k],dtype=float)
differences = np.ones([k,k],dtype=float)
triangular_earnings = pd.DataFrame(np.zeros([k,k],dtype=float), columns = currencies,
                                   index=np.flip(currencies,0))
strategy = pd.DataFrame(np.zeros([k*3,5],dtype = float), columns = ["Buy","Crosscurrency","Sell","Result","Terms"],
                        index = np.arange(1,k*3 + 1,1))
implied_frame = pd.DataFrame(np.zeros([k,k],dtype=float), columns = currencies,
                                   index=np.flip(currencies,0))
Crosscurrency = " "
flipped_cur = np.flip(currencies)

for i in range(k):
    for j in range(k):
        if FXMatrix.iloc[i,j] == np.nan:
            ask[i,j] = np.nan
            bid[i,j] = np.nan
        else:
            fx1 = FXMatrix.iloc[j,i]
            fx2 = 1/FXMatrix.iloc[k-1-i,k-1-j]
            if fx1 > fx2:
                ask[i,j] = fx1
                bid[i,j] = fx2
            else:
                ask[i,j] = fx2
                bid[i,j] = fx1
            
        mid[i,j] = (ask[i,j]+bid[i,j])/2
        """
        We know that the given table from the excel has Ask and Bid prices 
        mixed. Therefore, we compare the reverse upper triangular and the lower 
        triangular matrix values. However, we divide some of them in order to have 
        terms and base. After that we compare them and we assign as ask the 
        variable with the greater value. On the same time we create an array 
        called mid which has the middle prices. We do that in order to see 
        which currencies should we evaluate for triangular arbitrage opportunities.
        Mid rates functions as an indication.
        """
        
                
ask_frame = pd.DataFrame(np.transpose(ask), columns = currencies
                         ,index=np.flip(currencies,0))
bid_frame  = pd.DataFrame(np.transpose(bid), columns = currencies
                         ,index=np.flip(currencies,0))
mid_frame  = pd.DataFrame(np.transpose(mid),columns = currencies
                         ,index=np.flip(currencies,0))

"""
We want to find the differnces between the quoted rates and the implied rates
which are let's say the right ones. We are doing that in order to see what 
currency should we buy or sell. We will find the implied rates from the mid rates.
In reality we assume that some of the currencies are fairly quoted and we use
them so as to find the fair price of the other currencies

Example given:
    GBP/CAD implied = GBP/USD * USD/CAD
    here we assume that USD is fairly quoted
    Therefore, if implied rate is equal to the quoted then there is no
    arbitrage opportunity. Else, there is and we need to find which is over and
    under valued. We are doing that by calculating the array differnces.
"""

constant2 = mid_frame.loc["EUR","USD"] #we define this variable in order to calculate
#USD implied rate using EUR
for i in range(k):
    constant1 = mid_frame.loc[flipped_cur[i],"USD"] #for every other case we use USD
    quoted[i,:]= mid_frame.iloc[i,:] #we create an array called quoted which 
    # the "quoted mid prices"
    implied_frame.loc[flipped_cur[i],"USD"] = constant2*mid_frame.loc[flipped_cur[i],"EUR"] #for the USD we use euro base 
    #and variable terms
    for j in range(1,k,1):
        implied_frame.loc[flipped_cur[i],currencies[j]] = constant1*mid_frame.loc["USD",currencies[j]]
        
    implied_frame.loc["EUR","USD"] = mid_frame.loc["EUR","JPY"]*mid_frame.loc["JPY","USD"]
    for j in range(k):
        if implied_frame.iloc[i,j] == quoted[i,j]:
            arbitrage[i,j] = 0
       
        implied_frame.iloc[-1,j]=1/implied_frame.iloc[k-j-1,0]    


'''
In this case we just need to check the "couples" currencies once, therefore
we calculating the differences in the lower reverse triangular matrix
   
'''  

for i in range(k-1,-1,-1):
    for j in range(0,k-i,1):
      differences[i,j] = implied_frame.iloc[i,j] - quoted[i,j]
        
      
differences_frame = pd.DataFrame(differences, columns = currencies
                         ,index=np.flip(currencies,0))



"""
We are calculating the real results from the arbitrage taking into consideration
transaction costs. We are expecting that due to transaction costs some cases that
were indicated as arbitrage opportunity from the mid table might not be profitable.
"""

sum0 = 0
for i in range(k):
    terms = flipped_cur[i]
    for j in range(k-1-i):
      base = currencies[j]
      if arbitrage[i,j] ==1:
         if base == "USD":
            if terms == "EUR":
               Crosscurrency = "JPY"
            else:
                Crosscurrency = "EUR"     
         elif terms == "USD" and base == "EUR":
            Crosscurrency = "JPY"
         else:
            Crosscurrency = "USD"
            
      (success,results,currency1,currency2) = TriangularArbitrage(terms, base, Crosscurrency, ask_frame, bid_frame, differences[i,j])
      triangular_earnings.loc[currency1,currency2]= results
      strategy.iloc[sum0,0] = currency2
      strategy.iloc[sum0,1] = Crosscurrency
      strategy.iloc[sum0,2] = currency1 
      strategy.iloc[sum0,3] = results
      strategy.iloc[sum0,4] = currency2
      sum0 = sum0 +1
      
print(strategy)
strategy.to_excel("Triangular Arbitrage.xlsx",sheet_name ="Sheet1")
            
       