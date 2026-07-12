#property strict

#include "NoraPhase2RuntimeV1.mqh"
#include "NoraPhase2AtrRuntimeV1.mqh"
#include "NoraPhase2DistanceAtrRuntimeV1.mqh"

#define NORA_PHASE2P_ROW_COUNT 12

const string NoraTimestamp_Values[12] = {"2025.06.03 00:00", "2025.06.03 00:01", "2025.06.03 00:02", "2025.06.03 00:03", "2025.06.03 00:04", "2025.06.03 00:05", "2025.06.03 00:06", "2025.06.03 00:07", "2025.06.03 00:08", "2025.06.03 00:09", "2025.06.03 00:10", "2025.06.03 00:11"};
const double NoraOpen_Values[12] = {1.1000000000000001, 1.1003000000000001, 1.1009, 1.1006, 1.1012999999999999, 1.101, 1.1016999999999999, 1.1013999999999999, 1.1021000000000001, 1.1017999999999999, 1.1025, 1.1022000000000001};
const bool NoraOpen_NullMask[12] = {false, false, false, false, false, false, false, false, false, false, false, false};
const double NoraHigh_Values[12] = {1.1008, 1.1011, 1.1013999999999999, 1.1015999999999999, 1.1017999999999999, 1.1020000000000001, 1.1022000000000001, 1.1024, 1.1026, 1.1028, 1.103, 1.1032};
const bool NoraHigh_NullMask[12] = {false, false, false, false, false, false, false, false, false, false, false, false};
const double NoraLow_Values[12] = {1.0994999999999999, 1.1000000000000001, 1.1004, 1.1002000000000001, 1.1007, 1.1008, 1.1011, 1.101, 1.1014999999999999, 1.1013999999999999, 1.1019000000000001, 1.1017999999999999};
const bool NoraLow_NullMask[12] = {false, false, false, false, false, false, false, false, false, false, false, false};
const double NoraClose_Values[12] = {1.1003000000000001, 1.1009, 1.1006, 1.1012999999999999, 1.101, 1.1016999999999999, 1.1013999999999999, 1.1021000000000001, 1.1017999999999999, 1.1025, 1.1022000000000001, 1.1029};
const bool NoraClose_NullMask[12] = {false, false, false, false, false, false, false, false, false, false, false, false};
const double NoraSma3_Values[12] = {0.0, 0.0, 1.1006, 1.1009333333333335, 1.1009666666666666, 1.1013333333333335, 1.1013666666666666, 1.1017333333333335, 1.1017666666666666, 1.1021333333333334, 1.1021666666666665, 1.1025333333333334};
const bool NoraSma3_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};
const double NoraExpectedAtr_Values[12] = {0.0, 0.0, 0.0011333333333332825, 0.001222222222222137, 0.0011814814814813843, 0.0011876543209876195, 0.0011584362139917799, 0.0012389574759945426, 0.0011926383173297287, 0.0012617588782198417, 0.0012078392521465207, 0.0012718928347643698};
const bool NoraExpectedAtr_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};
const double NoraExpectedDistanceAtr_Values[12] = {0.0, 0.0, 0, 0.2999999999998062, 0.028213166144199841, 0.30873180873159684, 0.028774422735342933, 0.29594774136399932, 0.027949238967905805, 0.29059963277923562, 0.027597491366763517, 0.28828424584572393};
const bool NoraExpectedDistanceAtr_NullMask[12] = {true, true, false, false, false, false, false, false, false, false, false, false};

NoraNullableDoubleV1 NoraPhase2PValue(const double &values[], const bool &null_mask[], const int row_index)
{
   if(row_index < 0 || row_index >= NORA_PHASE2P_ROW_COUNT || null_mask[row_index])
      return NoraNumericNullV1();
   return NoraNumericValueV1(values[row_index]);
}

string NoraPhase2PNullableText(const NoraNullableDoubleV1 &value)
{
   if(value.is_null)
      return "null";
   return DoubleToString(value.value, 16);
}

int OnInit()
{
   const int handle = FileOpen("nora_phase2_atr_distance_tester_v1.csv", FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(handle, "record_type", "row_index", "timestamp", "open", "high", "low", "close", "previous_close", "actual_atr", "expected_atr", "distance_numerator", "actual_distance_atr", "expected_distance_atr", "atr_nullable", "distance_atr_nullable", "row_pass", "row_count", "passed_rows", "failed_rows", "overall_pass");
   int passed_rows = 0;
   int failed_rows = 0;
   for(int row_index = 0; row_index < NORA_PHASE2P_ROW_COUNT; row_index++)
   {
      NoraNullableDoubleV1 actual_atr = NoraAtr3V1(NoraHigh_Values, NoraLow_Values, NoraClose_Values, row_index);
      NoraNullableDoubleV1 close_value = NoraPhase2PValue(NoraClose_Values, NoraClose_NullMask, row_index);
      NoraNullableDoubleV1 sma_value = NoraPhase2PValue(NoraSma3_Values, NoraSma3_NullMask, row_index);
      NoraNullableDoubleV1 actual_distance = NoraDistanceAtrV1(close_value, sma_value, actual_atr);
      NoraNullableDoubleV1 expected_atr = NoraPhase2PValue(NoraExpectedAtr_Values, NoraExpectedAtr_NullMask, row_index);
      NoraNullableDoubleV1 expected_distance = NoraPhase2PValue(NoraExpectedDistanceAtr_Values, NoraExpectedDistanceAtr_NullMask, row_index);
      NoraNullableDoubleV1 numerator = (close_value.is_null || sma_value.is_null) ? NoraNumericNullV1() : NoraNumericValueV1(close_value.value - sma_value.value);
      bool atr_pass = actual_atr.is_null == expected_atr.is_null && (actual_atr.is_null || MathAbs(actual_atr.value - expected_atr.value) < 0.000000000000001);
      bool distance_pass = actual_distance.is_null == expected_distance.is_null && (actual_distance.is_null || MathAbs(actual_distance.value - expected_distance.value) < 0.000000000000001);
      bool row_pass = atr_pass && distance_pass;
      if(row_pass)
         passed_rows++;
      else
         failed_rows++;
      string previous_close = row_index == 0 ? "null" : DoubleToString(NoraClose_Values[row_index - 1], 16);
      FileWrite(handle, "row", row_index, NoraTimestamp_Values[row_index], DoubleToString(NoraOpen_Values[row_index], 16), DoubleToString(NoraHigh_Values[row_index], 16), DoubleToString(NoraLow_Values[row_index], 16), DoubleToString(NoraClose_Values[row_index], 16), previous_close, NoraPhase2PNullableText(actual_atr), NoraPhase2PNullableText(expected_atr), NoraPhase2PNullableText(numerator), NoraPhase2PNullableText(actual_distance), NoraPhase2PNullableText(expected_distance), actual_atr.is_null ? "true" : "false", actual_distance.is_null ? "true" : "false", row_pass ? "true" : "false", "", "", "", "");
   }
   bool overall_pass = passed_rows == NORA_PHASE2P_ROW_COUNT && failed_rows == 0;
   FileWrite(handle, "summary", -1, "", "", "", "", "", "", "", "", "", "", "", "", "", overall_pass ? "true" : "false", NORA_PHASE2P_ROW_COUNT, passed_rows, failed_rows, overall_pass ? "true" : "false");
   FileFlush(handle);
   FileClose(handle);
   TesterStop();
   return overall_pass ? INIT_SUCCEEDED : INIT_FAILED;
}
