#ifndef NORA_PHASE2_RUNTIME_V1_MQH
#define NORA_PHASE2_RUNTIME_V1_MQH

enum NoraTriBoolV1
{
   NORA_BOOL_NULL_V1  = -1,
   NORA_BOOL_FALSE_V1 = 0,
   NORA_BOOL_TRUE_V1  = 1
};

struct NoraNullableDoubleV1
{
   bool   is_null;
   double value;
};

NoraTriBoolV1 NoraBoolNullV1()
{
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolFalseV1()
{
   return NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraBoolTrueV1()
{
   return NORA_BOOL_TRUE_V1;
}

bool NoraBoolIsNullV1(NoraTriBoolV1 condition)
{
   return condition == NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolGetValueV1(NoraTriBoolV1 condition)
{
   return condition;
}

NoraNullableDoubleV1 NoraNumericNullV1()
{
   NoraNullableDoubleV1 result;
   result.is_null = true;
   result.value = 0.0;
   return result;
}

NoraNullableDoubleV1 NoraNumericValueV1(double value)
{
   NoraNullableDoubleV1 result;
   result.is_null = false;
   result.value = value;
   return result;
}

bool NoraNumericIsNullV1(const NoraNullableDoubleV1 &value)
{
   return value.is_null;
}

bool NoraNumericTryGetValueV1(const NoraNullableDoubleV1 &value, double &output)
{
   if(value.is_null)
      return false;
   output = value.value;
   return true;
}

NoraTriBoolV1 NoraBoolNotV1(NoraTriBoolV1 condition)
{
   if(condition == NORA_BOOL_NULL_V1)
      return NORA_BOOL_NULL_V1;
   if(condition == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_FALSE_V1;
   return NORA_BOOL_TRUE_V1;
}

NoraTriBoolV1 NoraBoolAndV1(const NoraTriBoolV1 left, const NoraTriBoolV1 right)
{
   if(left == NORA_BOOL_FALSE_V1 || right == NORA_BOOL_FALSE_V1)
      return NORA_BOOL_FALSE_V1;
   if(left == NORA_BOOL_TRUE_V1 && right == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_TRUE_V1;
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraBoolOrV1(const NoraTriBoolV1 left, const NoraTriBoolV1 right)
{
   if(left == NORA_BOOL_TRUE_V1 || right == NORA_BOOL_TRUE_V1)
      return NORA_BOOL_TRUE_V1;
   if(left == NORA_BOOL_FALSE_V1 && right == NORA_BOOL_FALSE_V1)
      return NORA_BOOL_FALSE_V1;
   return NORA_BOOL_NULL_V1;
}

NoraTriBoolV1 NoraCompareGtV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value > right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareGteV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value >= right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareLtV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value < right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

NoraTriBoolV1 NoraCompareLteV1(const NoraNullableDoubleV1 &left, const NoraNullableDoubleV1 &right)
{
   if(left.is_null || right.is_null)
      return NORA_BOOL_NULL_V1;
   return left.value <= right.value ? NORA_BOOL_TRUE_V1 : NORA_BOOL_FALSE_V1;
}

bool NoraConditionTriggersV1(const NoraTriBoolV1 condition)
{
   return condition == NORA_BOOL_TRUE_V1;
}

#endif
