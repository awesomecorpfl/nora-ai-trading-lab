#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2ConditionV1.mqh"

#define NORA_PHASE2_TESTER_ROW_COUNT 12

const NoraTriBoolV1 NoraTester_Bool_close_cross_above_sma3[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};

const NoraTriBoolV1 NoraTester_Bool_sma3_cross_below_close[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1};

const bool NoraTester_Num_sma3_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};

const double NoraTester_Num_sma3_Values[12] = {0.0, 0.0, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334};

const NoraTriBoolV1 NoraTester_ExpectedNullable[12] = {NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1};

const bool NoraTester_ExpectedTrigger[12] = {false, false, false, true, true, true, true, true, true, true, true, true};

NoraNullableDoubleV1 NoraTester_Num_sma3Value(const int row_index)
{
   if(NoraTester_Num_sma3_NullMask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(NoraTester_Num_sma3_Values[row_index]);
}

bool NoraTesterDone = false;

string NoraTesterNullableText(const NoraTriBoolV1 value)
{
   if(value == NORA_BOOL_NULL_V1)
      return "null";
   if(value == NORA_BOOL_TRUE_V1)
      return "true";
   return "false";
}

string NoraTesterBoolText(const bool value)
{
   return value ? "true" : "false";
}

void NoraTesterPublish()
{
   const int handle = FileOpen("nora_phase2_condition_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("NORA_PHASE2J_FILE_OPEN_FAILED:" + (string)GetLastError());
      return;
   }
   Print("NORA_PHASE2J_FILE_OPEN_OK");
   Print("NORA_PHASE2J_FIXTURE_BEGIN");
   FileWrite(handle, "record_type", "row_index", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2_TESTER_ROW_COUNT; row_index++)
   {
      NoraTriBoolV1 actual_nullable = NoraCondition_667db0ab50a7f3b9_V1(NoraTester_Bool_close_cross_above_sma3[row_index],
         NoraTester_Bool_sma3_cross_below_close[row_index],
         NoraTester_Num_sma3Value(row_index));
      bool actual_trigger = NoraTrigger_667db0ab50a7f3b9_V1(NoraTester_Bool_close_cross_above_sma3[row_index],
         NoraTester_Bool_sma3_cross_below_close[row_index],
         NoraTester_Num_sma3Value(row_index));
      bool row_pass = actual_nullable == NoraTester_ExpectedNullable[row_index] && actual_trigger == NoraTester_ExpectedTrigger[row_index];
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      FileWrite(handle, "row", row_index, NoraTesterNullableText(actual_nullable), NoraTesterNullableText(NoraTester_ExpectedNullable[row_index]), NoraTesterBoolText(actual_trigger), NoraTesterBoolText(NoraTester_ExpectedTrigger[row_index]), NoraTesterBoolText(row_pass), "", "", "", "");
   }
   bool overall_pass = failed_rows == 0 && passed_rows == NORA_PHASE2_TESTER_ROW_COUNT;
   FileWrite(handle, "summary", -1, "", "", "", "", NoraTesterBoolText(overall_pass), NORA_PHASE2_TESTER_ROW_COUNT, passed_rows, failed_rows, NoraTesterBoolText(overall_pass));
   FileFlush(handle);
   Print("NORA_PHASE2J_CSV_FLUSHED");
   FileClose(handle);
   Print(overall_pass ? "NORA_PHASE2J_FIXTURE_PASS" : "NORA_PHASE2J_FIXTURE_FAIL");
}

int OnInit()
{
   Print("NORA_PHASE2J_EA_INIT_ENTER");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(NoraTesterDone)
      return;
   NoraTesterDone = true;
   NoraTesterPublish();
   Print("NORA_PHASE2J_TESTER_STOP_REQUESTED");
   TesterStop();
}
