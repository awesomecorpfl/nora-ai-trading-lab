#ifndef NORA_PHASE2_DISTANCE_ATR_RUNTIME_V1_MQH
#define NORA_PHASE2_DISTANCE_ATR_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraDistanceAtrV1(const NoraNullableDoubleV1 &input_value, const NoraNullableDoubleV1 &reference_value, const NoraNullableDoubleV1 &atr_value)
{
   if(input_value.is_null || reference_value.is_null || atr_value.is_null || !MathIsValidNumber(input_value.value) || !MathIsValidNumber(reference_value.value) || !MathIsValidNumber(atr_value.value) || atr_value.value <= 0.0)
      return NoraNumericNullV1();
   double numerator = input_value.value - reference_value.value;
   double result = numerator / atr_value.value;
   if(!MathIsValidNumber(numerator) || !MathIsValidNumber(result))
      return NoraNumericNullV1();
   return NoraNumericValueV1(result);
}

#endif
