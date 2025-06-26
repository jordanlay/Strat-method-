//+------------------------------------------------------------------+
//|                                                      StratEA.mq5 |
//|   Example STRAT-based Expert Advisor with optimization inputs    |
//+------------------------------------------------------------------+
#property strict

input double   MaximumRisk    = 0.02; // % of balance per trade
input double   DecreaseFactor = 3.0;  // Martingale decrease factor
input int      MAPeriod       = 12;   // MA period
input int      MAShift        = 6;    // MA shift

int    Magic = 123456;
double Lots = 0;

//--- helper to get moving average value
double MA(int shift)
{
   return iMA(NULL,0,MAPeriod,MAShift,MODE_EMA,PRICE_CLOSE,shift);
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Close all EA positions                                           |
//+------------------------------------------------------------------+
void ClosePositions()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;

      if(!PositionSelectByTicket(ticket))
         continue;

      if(PositionGetInteger(POSITION_MAGIC)!=Magic)
         continue;

      double volume=PositionGetDouble(POSITION_VOLUME);
      ENUM_ORDER_TYPE type=(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)
                            ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      double price=(type==ORDER_TYPE_BUY)
                     ? SymbolInfoDouble(_Symbol,SYMBOL_ASK)
                     : SymbolInfoDouble(_Symbol,SYMBOL_BID);

      MqlTradeRequest req={0};
      MqlTradeResult  res={0};
      req.action   = TRADE_ACTION_DEAL;
      req.position = ticket;
      req.symbol   = _Symbol;
      req.magic    = Magic;
      req.type     = type;
      req.volume   = volume;
      req.price    = price;
      OrderSend(req,res);
   }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ClosePositions();
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk                                 |
//+------------------------------------------------------------------+
void CalculateLots()
{
   double bal=AccountInfoDouble(ACCOUNT_BALANCE);
   double risk=bal*MaximumRisk;
   double stop=SymbolInfoDouble(_Symbol,SYMBOL_POINT)*SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(stop<=0) stop=SymbolInfoDouble(_Symbol,SYMBOL_POINT)*10;
   Lots=risk/(stop*DecreaseFactor);
   double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double lotStep=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   Lots=MathMax(minLot,MathFloor(Lots/lotStep)*lotStep);
}

//+------------------------------------------------------------------+
//| Open market position                                             |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE type)
{
   CalculateLots();
   MqlTradeRequest req={0};
   MqlTradeResult  res={0};
   req.action=TRADE_ACTION_DEAL;
   req.symbol=_Symbol;
   req.magic=Magic;
   req.volume=Lots;
   req.type=type;
   req.price=(type==ORDER_TYPE_BUY)?SymbolInfoDouble(_Symbol,SYMBOL_ASK):SymbolInfoDouble(_Symbol,SYMBOL_BID);
   req.deviation=10;
   OrderSend(req,res);
}

//+------------------------------------------------------------------+
//| Determine candle direction                                       |
//+------------------------------------------------------------------+
string CandleDir(ENUM_TIMEFRAMES tf)
{
   int shift=1; // last closed candle
   double open=iOpen(NULL,tf,shift);
   double close=iClose(NULL,tf,shift);
   if(close>open) return "up";
   if(close<open) return "down";
   return "flat";
}

//+------------------------------------------------------------------+
//| Check trend across STRAT timeframes                              |
//+------------------------------------------------------------------+
string StratTrend()
{
   string h1=CandleDir(PERIOD_H1);
   string h4=CandleDir(PERIOD_H4);
   string d1=CandleDir(PERIOD_D1);
   string w1=CandleDir(PERIOD_W1);
   if(h1==h4 && h1==d1 && h1==w1)
      return h1;
   return "none";
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   string trend=StratTrend();
   if(trend=="up")
   {
      if(PositionSelect(_Symbol))
      {
         if(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_SELL)
            ClosePositions();
      }
      else
         OpenPosition(ORDER_TYPE_BUY);
   }
   else if(trend=="down")
   {
      if(PositionSelect(_Symbol))
      {
         if(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)
            ClosePositions();
      }
      else
         OpenPosition(ORDER_TYPE_SELL);
   }
}

//+------------------------------------------------------------------+
//| OnTester returns win percentage                                  |
//+------------------------------------------------------------------+
double OnTester()
{
   int wins=0, deals=HistoryDealsTotal();
   for(int i=0;i<deals;i++)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(HistoryDealGetDouble(ticket,DEAL_PROFIT)>0)
         wins++;
   }
   if(deals==0) return 0.0;
   return 100.0*wins/deals;
}

//+------------------------------------------------------------------+
