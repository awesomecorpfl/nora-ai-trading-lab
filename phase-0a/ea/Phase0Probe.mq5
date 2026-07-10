#property strict
#property version   "1.0"
#include <Trade/Trade.mqh>

input double Volume = 0.01;
input string RunId = "unset";
input ulong Magic = 900001;

CTrade trade;
bool opened = false;
bool finished = false;
datetime opened_at = 0;

string OutputName(const string suffix)
{
   return "NoraPhase0A\\" + RunId + "_" + suffix;
}

int OnInit()
{
   trade.SetExpertMagicNumber(Magic);
   trade.SetTypeFillingBySymbol(_Symbol);
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(finished)
      return;

   if(!opened)
   {
      if(trade.Buy(Volume, _Symbol))
      {
         opened = true;
         opened_at = iTime(_Symbol, _Period, 0);
      }
      return;
   }

   if(iTime(_Symbol, _Period, 0) >= opened_at + 3 * PeriodSeconds(_Period))
   {
      if(PositionSelect(_Symbol) && trade.PositionClose(_Symbol))
         finished = true;
   }
}

double OnTester()
{
   const int trades_handle = FileOpen(OutputName("trades.csv"), FILE_WRITE|FILE_CSV|FILE_COMMON, ';');
   const int metrics_handle = FileOpen(OutputName("metrics.csv"), FILE_WRITE|FILE_CSV|FILE_COMMON, ';');
   if(trades_handle == INVALID_HANDLE || metrics_handle == INVALID_HANDLE)
      return -1.0;

   FileWrite(trades_handle, "ticket", "time", "entry", "type", "volume", "price", "profit", "commission", "swap", "symbol", "magic");
   HistorySelect(0, TimeCurrent());
   const int total = HistoryDealsTotal();
   int relevant = 0;
   int exits = 0;
   double net_profit = 0.0;
   for(int i = 0; i < total; i++)
   {
      const ulong ticket = HistoryDealGetTicket(i);
      if((ulong)HistoryDealGetInteger(ticket, DEAL_MAGIC) != Magic)
         continue;
      const long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      const long type = HistoryDealGetInteger(ticket, DEAL_TYPE);
      const double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      const double commission = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      const double swap = HistoryDealGetDouble(ticket, DEAL_SWAP);
      FileWrite(trades_handle, ticket,
                TimeToString((datetime)HistoryDealGetInteger(ticket, DEAL_TIME), TIME_DATE|TIME_SECONDS),
                entry, type, HistoryDealGetDouble(ticket, DEAL_VOLUME),
                HistoryDealGetDouble(ticket, DEAL_PRICE), profit, commission, swap,
                HistoryDealGetString(ticket, DEAL_SYMBOL), HistoryDealGetInteger(ticket, DEAL_MAGIC));
      relevant++;
      if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
      {
         exits++;
         net_profit += profit + commission + swap;
      }
   }
   FileWrite(metrics_handle, "metric", "value");
   FileWrite(metrics_handle, "relevant_deals", relevant);
   FileWrite(metrics_handle, "closed_trades", exits);
   FileWrite(metrics_handle, "net_profit", DoubleToString(net_profit, 2));
   FileWrite(metrics_handle, "finished", finished ? 1 : 0);
   FileClose(trades_handle);
   FileClose(metrics_handle);
   return net_profit;
}

