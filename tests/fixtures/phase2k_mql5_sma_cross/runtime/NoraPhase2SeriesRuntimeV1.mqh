#ifndef NORA_PHASE2_SERIES_RUNTIME_V1_MQH
#define NORA_PHASE2_SERIES_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraSma3V1(const double &values[], const bool &null_mask[], const int row_index)
{
   if(row_index < 2 || null_mask[row_index - 2] || null_mask[row_index - 1] || null_mask[row_index])
      return NoraNumericNullV1();
   double sum = values[row_index - 2] + values[row_index - 1] + values[row_index];
   double result = sum / 3.0;
   if(!MathIsValidNumber(result))
      return NoraNumericNullV1();
   return NoraNumericValueV1(result);
}

NoraTriBoolV1 NoraCrossAboveV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)
{
   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null)
      return NORA_BOOL_NULL_V1;
   return left_previous.value <= right_previous.value && left_current.value > right_current.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCrossBelowV1(const NoraNullableDoubleV1 &left_previous, const NoraNullableDoubleV1 &right_previous, const NoraNullableDoubleV1 &left_current, const NoraNullableDoubleV1 &right_current)
{
   if(left_previous.is_null || right_previous.is_null || left_current.is_null || right_current.is_null)
      return NORA_BOOL_NULL_V1;
   return left_previous.value >= right_previous.value && left_current.value < right_current.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

#endif
