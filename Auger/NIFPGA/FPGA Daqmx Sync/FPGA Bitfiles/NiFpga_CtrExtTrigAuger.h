/*
 * Generated with the FPGA Interface C API Generator 14.0.0
 * for NI-RIO 14.0.0 or later.
 */

#ifndef __NiFpga_CtrExtTrigAuger_h__
#define __NiFpga_CtrExtTrigAuger_h__

#ifndef NiFpga_Version
   #define NiFpga_Version 1400
#endif

#include "NiFpga.h"

/**
 * The filename of the FPGA bitfile.
 *
 * This is a #define to allow for string literal concatenation. For example:
 *
 *    static const char* const Bitfile = "C:\\" NiFpga_CtrExtTrigAuger_Bitfile;
 */
#define NiFpga_CtrExtTrigAuger_Bitfile "NiFpga_CtrExtTrigAuger.lvbitx"

/**
 * The signature of the FPGA bitfile.
 */
static const char* const NiFpga_CtrExtTrigAuger_Signature = "C785982188720152F75C0DE37DB6F8C8";

typedef enum
{
   NiFpga_CtrExtTrigAuger_IndicatorBool_Overflow = 0x811A,
} NiFpga_CtrExtTrigAuger_IndicatorBool;

typedef enum
{
   NiFpga_CtrExtTrigAuger_ControlU8_TriggerMode = 0x810E,
} NiFpga_CtrExtTrigAuger_ControlU8;

typedef enum
{
   NiFpga_CtrExtTrigAuger_ControlU32_SampleCount = 0x8110,
   NiFpga_CtrExtTrigAuger_ControlU32_SamplePeriod = 0x8114,
} NiFpga_CtrExtTrigAuger_ControlU32;

typedef enum
{
   NiFpga_CtrExtTrigAuger_TargetToHostFifoU64_CounterFIFO = 0,
} NiFpga_CtrExtTrigAuger_TargetToHostFifoU64;

#endif
