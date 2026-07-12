#ifndef NORA_PHASE2_SLOPE_RUNTIME_V1_MQH
#define NORA_PHASE2_SLOPE_RUNTIME_V1_MQH
#include "NoraPhase2RuntimeV1.mqh"

NoraNullableDoubleV1 NoraSlopeLookback1V1(
   const NoraNullableDoubleV1 &current_value,
   const NoraNullableDoubleV1 &previous_value
)
{
   if(current_value.is_null || previous_value.is_null)
      return NoraNumericNullV1();
   double v = (current_value.value - previous_value.value) / 1.0;
   if(!MathIsValidNumber(v))
      return NoraNumericNullV1();
   return NoraNumericValueV1(v);
}

#endif
