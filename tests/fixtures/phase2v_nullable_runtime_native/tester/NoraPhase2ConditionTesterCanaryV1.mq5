#property strict

#include "NoraPhase2RuntimeV1.mqh"

#define NORA_PHASE2_RUNTIME_CASE_COUNT 44

const NoraTriBoolV1 NoraRuntime_Expected[44] = {NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1};
const bool NoraRuntime_ExpectedTrigger[44] = {false, true, false, false, false, false, false, false, false, false, false, true, false, false, true, false, false, true, true, true, true, true, false, false, false, false, true, false, false, false, false, false, true, false, false, false, false, true, false, false, false, false, false, true};

string NoraRuntime_TriText(const NoraTriBoolV1 value)
{
   if(value == NORA_BOOL_NULL_V1) return "null";
   if(value == NORA_BOOL_TRUE_V1) return "true";
   return "false";
}
string NoraRuntime_BoolText(const bool value)
{
   return value ? "true" : "false";
}

NoraTriBoolV1 NoraRuntime_ActualNullable(const int index)
{
   switch(index)
   {
      case 0: return NoraBoolNotV1(NORA_BOOL_NULL_V1);
      case 1: return NoraBoolNotV1(NORA_BOOL_FALSE_V1);
      case 2: return NoraBoolNotV1(NORA_BOOL_TRUE_V1);
      case 3: return NoraBoolAndV1(NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1);
      case 4: return NoraBoolAndV1(NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1);
      case 5: return NoraBoolAndV1(NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1);
      case 6: return NoraBoolAndV1(NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1);
      case 7: return NoraBoolAndV1(NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1);
      case 8: return NoraBoolAndV1(NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1);
      case 9: return NoraBoolAndV1(NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1);
      case 10: return NoraBoolAndV1(NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1);
      case 11: return NoraBoolAndV1(NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1);
      case 12: return NoraBoolOrV1(NORA_BOOL_NULL_V1, NORA_BOOL_NULL_V1);
      case 13: return NoraBoolOrV1(NORA_BOOL_NULL_V1, NORA_BOOL_FALSE_V1);
      case 14: return NoraBoolOrV1(NORA_BOOL_NULL_V1, NORA_BOOL_TRUE_V1);
      case 15: return NoraBoolOrV1(NORA_BOOL_FALSE_V1, NORA_BOOL_NULL_V1);
      case 16: return NoraBoolOrV1(NORA_BOOL_FALSE_V1, NORA_BOOL_FALSE_V1);
      case 17: return NoraBoolOrV1(NORA_BOOL_FALSE_V1, NORA_BOOL_TRUE_V1);
      case 18: return NoraBoolOrV1(NORA_BOOL_TRUE_V1, NORA_BOOL_NULL_V1);
      case 19: return NoraBoolOrV1(NORA_BOOL_TRUE_V1, NORA_BOOL_FALSE_V1);
      case 20: return NoraBoolOrV1(NORA_BOOL_TRUE_V1, NORA_BOOL_TRUE_V1);
      case 21: return NoraCompareGtV1(NoraNumericValueV1(2.0), NoraNumericValueV1(1.0));
      case 22: return NoraCompareGtV1(NoraNumericValueV1(1.0), NoraNumericValueV1(2.0));
      case 23: return NoraCompareGtV1(NoraNumericNullV1(), NoraNumericValueV1(1.0));
      case 24: return NoraCompareGtV1(NoraNumericValueV1(1.0), NoraNumericNullV1());
      case 25: return NoraCompareGtV1(NoraNumericNullV1(), NoraNumericNullV1());
      case 26: return NoraCompareGteV1(NoraNumericValueV1(2.0), NoraNumericValueV1(1.0));
      case 27: return NoraCompareGteV1(NoraNumericValueV1(1.0), NoraNumericValueV1(2.0));
      case 28: return NoraCompareGteV1(NoraNumericNullV1(), NoraNumericValueV1(1.0));
      case 29: return NoraCompareGteV1(NoraNumericValueV1(1.0), NoraNumericNullV1());
      case 30: return NoraCompareGteV1(NoraNumericNullV1(), NoraNumericNullV1());
      case 31: return NoraCompareLtV1(NoraNumericValueV1(2.0), NoraNumericValueV1(1.0));
      case 32: return NoraCompareLtV1(NoraNumericValueV1(1.0), NoraNumericValueV1(2.0));
      case 33: return NoraCompareLtV1(NoraNumericNullV1(), NoraNumericValueV1(1.0));
      case 34: return NoraCompareLtV1(NoraNumericValueV1(1.0), NoraNumericNullV1());
      case 35: return NoraCompareLtV1(NoraNumericNullV1(), NoraNumericNullV1());
      case 36: return NoraCompareLteV1(NoraNumericValueV1(2.0), NoraNumericValueV1(1.0));
      case 37: return NoraCompareLteV1(NoraNumericValueV1(1.0), NoraNumericValueV1(2.0));
      case 38: return NoraCompareLteV1(NoraNumericNullV1(), NoraNumericValueV1(1.0));
      case 39: return NoraCompareLteV1(NoraNumericValueV1(1.0), NoraNumericNullV1());
      case 40: return NoraCompareLteV1(NoraNumericNullV1(), NoraNumericNullV1());
      case 41: return NORA_BOOL_NULL_V1;
      case 42: return NORA_BOOL_FALSE_V1;
      case 43: return NORA_BOOL_TRUE_V1;
   }
   return NORA_BOOL_NULL_V1;
}

bool NoraRuntime_ActualTrigger(const int index)
{
   switch(index)
   {
      case 0: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(0));
      case 1: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(1));
      case 2: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(2));
      case 3: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(3));
      case 4: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(4));
      case 5: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(5));
      case 6: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(6));
      case 7: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(7));
      case 8: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(8));
      case 9: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(9));
      case 10: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(10));
      case 11: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(11));
      case 12: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(12));
      case 13: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(13));
      case 14: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(14));
      case 15: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(15));
      case 16: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(16));
      case 17: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(17));
      case 18: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(18));
      case 19: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(19));
      case 20: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(20));
      case 21: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(21));
      case 22: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(22));
      case 23: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(23));
      case 24: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(24));
      case 25: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(25));
      case 26: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(26));
      case 27: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(27));
      case 28: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(28));
      case 29: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(29));
      case 30: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(30));
      case 31: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(31));
      case 32: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(32));
      case 33: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(33));
      case 34: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(34));
      case 35: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(35));
      case 36: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(36));
      case 37: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(37));
      case 38: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(38));
      case 39: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(39));
      case 40: return NoraConditionTriggersV1(NoraRuntime_ActualNullable(40));
      case 41: return NoraConditionTriggersV1(NORA_BOOL_NULL_V1);
      case 42: return NoraConditionTriggersV1(NORA_BOOL_FALSE_V1);
      case 43: return NoraConditionTriggersV1(NORA_BOOL_TRUE_V1);
   }
   return false;
}

bool NoraRuntimeDone = false;

void NoraRuntimePublish()
{
   const int count = 44;
   const int handle = FileOpen("nora_phase2_condition_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE) { Print("NORA_PHASE2V_RUNTIME_FILE_OPEN_FAILED"); return; }
   Print("NORA_PHASE2V_RUNTIME_BEGIN");
   FileWrite(handle, "record_type", "row_index", "operation", "actual_nullable", "expected_nullable", "actual_trigger", "expected_trigger", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed = 0;
   int failed = 0;
   for(int index = 0; index < count; index++)
   {
      NoraTriBoolV1 actual = NoraRuntime_ActualNullable(index);
      bool trigger = NoraRuntime_ActualTrigger(index);
      bool row_pass = actual == NoraRuntime_Expected[index] && trigger == NoraRuntime_ExpectedTrigger[index];
      if(row_pass) passed++; else failed++;
      FileWrite(handle, "row", index, "semantic", NoraRuntime_TriText(actual), NoraRuntime_TriText(NoraRuntime_Expected[index]), NoraRuntime_BoolText(trigger), NoraRuntime_BoolText(NoraRuntime_ExpectedTrigger[index]), NoraRuntime_BoolText(row_pass), "", "", "", "");
   }
   bool overall = failed == 0 && passed == count;
   FileWrite(handle, "summary", -1, "semantic", "", "", "", "", NoraRuntime_BoolText(overall), count, passed, failed, NoraRuntime_BoolText(overall));
   FileFlush(handle); FileClose(handle);
   Print(overall ? "NORA_PHASE2V_RUNTIME_PASS" : "NORA_PHASE2V_RUNTIME_FAIL");
}

int OnInit()
{
   Print("NORA_PHASE2V_RUNTIME_EA_INIT_ENTER");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(NoraRuntimeDone) return;
   NoraRuntimeDone = true;
   NoraRuntimePublish();
   TesterStop();
}
