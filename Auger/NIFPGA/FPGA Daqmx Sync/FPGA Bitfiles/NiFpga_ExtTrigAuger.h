/*
 * Generated with the FPGA Interface C API Generator 14.0.0
 * for NI-RIO 14.0.0 or later.
 */

#ifndef __NiFpga_ExtTrigAuger_h__
#define __NiFpga_ExtTrigAuger_h__

#ifndef NiFpga_Version
   #define NiFpga_Version 1400
#endif

#include "NiFpga.h"

/**
 * The filename of the FPGA bitfile.
 *
 * This is a #define to allow for string literal concatenation. For example:
 *
 *    static const char* const Bitfile = "C:\\" NiFpga_ExtTrigAuger_Bitfile;
 */
#define NiFpga_ExtTrigAuger_Bitfile "NiFpga_ExtTrigAuger.lvbitx"

/**
 * The signature of the FPGA bitfile.
 */
static const char* const NiFpga_ExtTrigAuger_Signature = "518155E01E5A1DFFECA5C4ACE62664CA";

typedef enum
{
   NiFpga_ExtTrigAuger_IndicatorBool_Overflow = 0x8112,
} NiFpga_ExtTrigAuger_IndicatorBool;

typedef enum
{
   NiFpga_ExtTrigAuger_ControlU8_TriggerMode = 0x810E,
} NiFpga_ExtTrigAuger_ControlU8;

typedef enum
{
   NiFpga_ExtTrigAuger_TargetToHostFifoU64_CounterFIFO = 0,
} NiFpga_ExtTrigAuger_TargetToHostFifoU64;

#endif
