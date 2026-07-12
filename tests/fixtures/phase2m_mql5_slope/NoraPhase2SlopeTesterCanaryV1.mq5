#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2SlopeRuntimeV1.mqh"

#define NORA_PHASE2M_ROW_COUNT 12

const double NoraSlopeInput_Values[12] = {0.0, 0.0, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334};
const bool NoraSlopeInput_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};
const double NoraExpectedSlope_Values[12] = {0.0, 0.0, 0.0, 0.00033333333333351867, 3.3333333333107618e-05, 0.00036666666666684833, 3.3333333333107618e-05, 0.00036666666666684833, 3.3333333333107618e-05, 0.00036666666666684833, 3.3333333333107618e-05, 0.00036666666666684833};
const bool NoraExpectedSlope_NullMask[12] = {true, true, true, false, false, false, false, false, false, false, false, false};


NoraNullableDoubleV1 NoraSlopeInputValue(const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2M_ROW_COUNT || NoraSlopeInput_NullMask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraSlopeInput_Values[row_index]);
}

string NoraPhase2MNullableText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null)
      return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_slope_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "actual_slope", "expected_slope", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2M_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 current = NoraSlopeInputValue(row_index);
      NoraNullableDoubleV1 previous = row_index == 0 ? NoraNumericNullV1() : NoraSlopeInputValue(row_index - 1);
      NoraNullableDoubleV1 actual_slope = NoraSlopeLookback1V1(current, previous);
      bool current_null = actual_slope.is_null;
      bool expected_null = NoraExpectedSlope_NullMask[row_index];
      bool row_pass = false;
      if(current_null && expected_null)
         row_pass = true;
      else if(!current_null && !expected_null)
         row_pass = MathAbs(actual_slope.value - NoraExpectedSlope_Values[row_index]) < 0.000000000000001;
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      FileWrite(handle, "row", row_index, NoraPhase2MNullableText(actual_slope), expected_null ? "null" : DoubleToString(NoraExpectedSlope_Values[row_index], 16), row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2M_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", overall_pass ? "true" : "false", NORA_PHASE2M_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
