# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#region imports
from AlgorithmImports import *
#endregion

class IndexOptionBearCallSpreadAlgorithm(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2021, 1, 1)
        self.set_cash(100000)

        self.spy = self.add_equity("SPY", Resolution.MINUTE).symbol

        index = self.add_index("VIX", Resolution.MINUTE).symbol
        option = self.add_index_option(index, "VIXW", Resolution.MINUTE)
        option.set_filter(lambda x: x.strikes(-5, 5).expiration(15, 45))
        
        self.vixw = option.symbol
        self.tickets = []

    def on_data(self, slice: Slice) -> None:
        if not self.portfolio[self.spy].invested:
            self.market_order(self.spy, 100)
        
        # Return if hedge position presents
        if any([self.portfolio[x.symbol].invested for x in self.tickets]):
            return

        # Return if hedge position presents
        chain = slice.option_chains.get(self.vixw)
        if not chain: return

        # Get the nearest expiry date of the contracts
        expiry = min([x.expiry for x in chain])
        
        # Select the call Option contracts with the nearest expiry and sort by strike price
        calls = sorted([i for i in chain if i.expiry == expiry and i.right == OptionRight.CALL], 
                        key=lambda x: x.strike)
        if len(calls) < 2: return
        
        # Buy the bear call spread
        bear_call_spread = OptionStrategies.bear_call_spread(self.vixw, calls[0].strike, calls[-1].strike, expiry)
        self.tickets = self.buy(bear_call_spread, 1)
