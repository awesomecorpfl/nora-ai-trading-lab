#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2ConditionV1.mqh"

#define NORA_PHASE2_FIXTURE_ROW_COUNT 12

const NoraTriBoolV1 NoraFixture_Bool_close_cross_above_sma3[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};

const NoraTriBoolV1 NoraFixture_Bool_sma3_cross_below_close[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};

const bool NoraFixture_Num_sma3_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};

const double NoraFixture_Num_sma3_Values[12] = {0.0, 0.0, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334};

const NoraTriBoolV1 NoraFixture_ExpectedNullable[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1};

const bool NoraFixture_ExpectedTrigger[12] = {false, false, false, true, true, true, true, true, true, true, true, true};

NoraNullableDoubleV1 NoraFixture_Num_sma3Value(const int row_index)
{
   if(NoraFixture_Num_sma3_NullMask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraFixture_Num_sma3_Values[row_index]);
}

string NoraFixtureNullableText(const NoraTriBoolV1 value)
{
   if(value == NORA_BOOL_NULL_V1)
      return "null";
   if(value == NORA_BOOL_TRUE_V1)
      return "true";
   return "false";
}

string NoraFixtureTriggerText(const bool value)
{
   return value ? "true" : "false";
}

void OnStart()
{
   const string filename = "nora_phase2_condition_fixture_v1.csv";
   const int handle = FileOpen(filename, FILE_WRITE | FILE_CSV, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("nora_phase2_fixture_error,file_open_failed");
      return;
   }
   FileWrite(handle, "record_type", "row_index", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   const int row_count = NORA_PHASE2_FIXTURE_ROW_COUNT;
   int passed_rows = 0;
   int failed_rows = 0;
   if(row_count != 12)
   {
      FileWrite(handle, "summary", -1, "", "", "", "", "false", row_count, 0, row_count, "false");
      FileClose(handle);
      return;
   }
   for(int row_index = 0; row_index < row_count; row_index++)
   {
      NoraTriBoolV1 actual_nullable = NoraCondition_667db0ab50a7f3b9_V1(NoraFixture_Bool_close_cross_above_sma3[row_index],
         NoraFixture_Bool_sma3_cross_below_close[row_index],
         NoraFixture_Num_sma3Value(row_index));
      bool actual_trigger = NoraTrigger_667db0ab50a7f3b9_V1(NoraFixture_Bool_close_cross_above_sma3[row_index],
         NoraFixture_Bool_sma3_cross_below_close[row_index],
         NoraFixture_Num_sma3Value(row_index));
      bool row_pass = actual_nullable == NoraFixture_ExpectedNullable[row_index] && actual_trigger == NoraFixture_ExpectedTrigger[row_index];
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      FileWrite(handle, "row", row_index, NoraFixtureNullableText(actual_nullable), NoraFixtureNullableText(NoraFixture_ExpectedNullable[row_index]), NoraFixtureTriggerText(actual_trigger), NoraFixtureTriggerText(NoraFixture_ExpectedTrigger[row_index]), row_pass ? "true" : "false", "", "", "", "");
   }
   FileWrite(handle, "summary", -1, "", "", "", "", failed_rows == 0 ? "true" : "false", row_count, passed_rows, failed_rows, failed_rows == 0 ? "true" : "false");
   FileClose(handle);
}
