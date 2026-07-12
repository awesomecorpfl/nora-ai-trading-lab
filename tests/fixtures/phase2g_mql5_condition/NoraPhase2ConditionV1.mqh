#ifndef NORA_PHASE2_CONDITION_667DB0AB50A7F3B9_V1_MQH
#define NORA_PHASE2_CONDITION_667DB0AB50A7F3B9_V1_MQH

#include "NoraPhase2RuntimeV1.mqh"

NoraTriBoolV1 NoraCondition_667db0ab50a7f3b9_V1(
   NoraTriBoolV1 nora_bool_close_cross_above_sma3_47260c9c5e68,
   NoraTriBoolV1 nora_bool_sma3_cross_below_close_f82f2c17f999,
   const NoraNullableDoubleV1 & nora_num_sma3_662a95a8677d
)
{
   return NoraBoolAndV1(NoraCompareGtV1(nora_num_sma3_662a95a8677d, NoraNumericValueV1(1.1008)), NoraBoolOrV1(nora_bool_close_cross_above_sma3_47260c9c5e68, NoraBoolNotV1(nora_bool_sma3_cross_below_close_f82f2c17f999)));
}

bool NoraTrigger_667db0ab50a7f3b9_V1(
   NoraTriBoolV1 nora_bool_close_cross_above_sma3_47260c9c5e68,
   NoraTriBoolV1 nora_bool_sma3_cross_below_close_f82f2c17f999,
   const NoraNullableDoubleV1 & nora_num_sma3_662a95a8677d
)
{
   return NoraConditionTriggersV1(
      NoraCondition_667db0ab50a7f3b9_V1(
         nora_bool_close_cross_above_sma3_47260c9c5e68,
         nora_bool_sma3_cross_below_close_f82f2c17f999,
         nora_num_sma3_662a95a8677d
      )
   );
}

#endif
