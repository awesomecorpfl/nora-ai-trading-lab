#ifndef NORA_PHASE2_ATR_RUNTIME_V1_MQH
#define NORA_PHASE2_ATR_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraAtr3V1(const double &high_values[], const double &low_values[], const double &close_values[], const int row_index)
{
   if(row_index < 0 || !MathIsValidNumber(high_values[row_index]) || !MathIsValidNumber(low_values[row_index]) || !MathIsValidNumber(close_values[row_index]))
      return NoraNumericNullV1();
   double tr_sum = 0.0;
   double atr_value = 0.0;
   for(int index = 0; index <= row_index; index++)
   {
      if(!MathIsValidNumber(high_values[index]) || !MathIsValidNumber(low_values[index]) || !MathIsValidNumber(close_values[index]))
         return NoraNumericNullV1();
      double true_range = high_values[index] - low_values[index];
      if(index > 0)
         true_range = MathMax(true_range, MathMax(MathAbs(high_values[index] - close_values[index - 1]), MathAbs(low_values[index] - close_values[index - 1])));
      if(!MathIsValidNumber(true_range))
         return NoraNumericNullV1();
      if(index < 3)
      {
         tr_sum += true_range;
         if(index == 2)
            atr_value = tr_sum / 3.0;
      }
      else
         atr_value = (atr_value * 2.0 + true_range) / 3.0;
   }
   if(row_index < 2 || !MathIsValidNumber(atr_value))
      return NoraNumericNullV1();
   return NoraNumericValueV1(atr_value);
}

#endif
