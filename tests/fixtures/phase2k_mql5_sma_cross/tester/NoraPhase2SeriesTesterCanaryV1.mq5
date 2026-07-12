#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2SeriesRuntimeV1.mqh"
#include "NoraPhase2ConditionV1.mqh"

#define NORA_PHASE2K_ROW_COUNT 12
const double NoraSeriesClose[12] = {1.1003000000000001, 1.1009, 1.1006, 1.1012999999999999, 1.101, 1.1016999999999999, 1.1013999999999999, 1.1021000000000001, 1.1017999999999999, 1.1025, 1.1022000000000001, 1.1029};
const bool NoraSeriesCloseNull[12] = {false, false, false, false, false, false, false, false, false, false, false, false};
const double NoraExpectedSma[12] = {0.0, 0.0, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334};
const bool NoraExpectedSmaNull[12] = {true, true, false, false, false, false, false, false, false, false, false, false};
const NoraTriBoolV1 NoraExpectedAbove[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};
const NoraTriBoolV1 NoraExpectedBelow[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};
const NoraTriBoolV1 NoraExpectedNullable[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1};
const bool NoraExpectedTrigger[12] = {false, false, false, true, true, true, true, true, true, true, true, true};


NoraNullableDoubleV1 NoraSeriesCloseValue(const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2K_ROW_COUNT || NoraSeriesCloseNull[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraSeriesClose[row_index]);
}

NoraNullableDoubleV1 NoraSeriesSma(const int row_index)
{
   return NoraSma3V1(NoraSeriesClose, NoraSeriesCloseNull, row_index);
}

string NoraPhase2KNullableText(const NoraTriBoolV1 value)
{
   if(value == NORA_BOOL_NULL_V1) return "null";
   return value == NORA_BOOL_TRUE_V1 ? "true" : "false";
}

string NoraPhase2KNumericText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null) return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_series_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE) return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "actual_sma", "expected_sma", "actual_cross_above", "expected_cross_above", "actual_cross_below", "expected_cross_below", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   NoraTriBoolV1 NoraSeriesCrossAbove[12];
   NoraTriBoolV1 NoraSeriesCrossBelow[12];
   for(int row_index = 0; row_index < NORA_PHASE2K_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 current_sma = NoraSeriesSma(row_index);
      NoraNullableDoubleV1 previous_sma = row_index == 0 ? NoraNumericNullV1() : NoraSeriesSma(row_index - 1);
      NoraNullableDoubleV1 current_close = NoraSeriesCloseValue(row_index);
      NoraNullableDoubleV1 previous_close = row_index == 0 ? NoraNumericNullV1() : NoraSeriesCloseValue(row_index - 1);
      NoraSeriesCrossAbove[row_index] = NoraCrossAboveV1(previous_close, previous_sma, current_close, current_sma);
      NoraSeriesCrossBelow[row_index] = NoraCrossBelowV1(previous_sma, previous_close, current_sma, current_close);
      NoraTriBoolV1 actual_nullable = NoraCondition_667db0ab50a7f3b9_V1(NoraSeriesCrossAbove[row_index], NoraSeriesCrossBelow[row_index], NoraSeriesSma(row_index));
      bool actual_trigger = NoraTrigger_667db0ab50a7f3b9_V1(NoraSeriesCrossAbove[row_index], NoraSeriesCrossBelow[row_index], NoraSeriesSma(row_index));
      bool row_pass = current_sma.is_null == NoraExpectedSmaNull[row_index] && (current_sma.is_null || MathAbs(current_sma.value - NoraExpectedSma[row_index]) < 0.000000000000001) && NoraSeriesCrossAbove[row_index] == NoraExpectedAbove[row_index] && NoraSeriesCrossBelow[row_index] == NoraExpectedBelow[row_index] && actual_nullable == NoraExpectedNullable[row_index] && actual_trigger == NoraExpectedTrigger[row_index];
      if(row_pass) passed_rows++; else failed_rows++;
      FileWrite(handle, "row", row_index, NoraPhase2KNumericText(current_sma), NoraExpectedSmaNull[row_index] ? "null" : DoubleToString(NoraExpectedSma[row_index], 16), NoraPhase2KNullableText(NoraSeriesCrossAbove[row_index]), NoraPhase2KNullableText(NoraExpectedAbove[row_index]), NoraPhase2KNullableText(NoraSeriesCrossBelow[row_index]), NoraPhase2KNullableText(NoraExpectedBelow[row_index]), NoraPhase2KNullableText(actual_nullable), NoraPhase2KNullableText(NoraExpectedNullable[row_index]), actual_trigger ? "true" : "false", NoraExpectedTrigger[row_index] ? "true" : "false", row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2K_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", "", "", "", "", "", "", "", "", overall_pass ? "true" : "false", NORA_PHASE2K_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
