# gmap_size
GNU map file parser to get each object file text/data/bss size

This tool would be work with GNU map file(Generated by GCC with -Wl,-Map option),
and parser the given section names and counting the size in:
  - total text, data, bss
  - each object file's total text, data, bss
  - each object file's symbol type and size

Command option would be:
```
gmap_size.py [-h] [-i I] [-v] [-t TEXT] [--text TEXT] [-d DATA] [--data DATA] [-b BSS] [--bss BSS] [--ignore IGNORE] [--symbol]

optional arguments:
  -h, --help       show this help message and exit
  -i I             Input map file
  -v               Verbose mode
  -t TEXT          Text sections list, seperate with comma
  --text TEXT      Same as -t
  -d DATA          Data sections list, seperate with comma
  --data DATA      Same as -d
  -b BSS           Bss sections list, seperate with comma
  --bss BSS        Same as -b
  --ignore IGNORE  Ignore sections list, sperate with comma
  --detail         Report symbol usage in detail
```

Normally the usage would be:

```
python gmap_size.py -i {.map file} -t .text,.vectors -d .rodata,.data -b .bss,.stack,.heap --detail
```

For the case STM32:
```
python gmap_size.py -i {.map file} -t .isr_vector,.text,.init -d .rodata,.data,.ARM,.ARM.exidx,.init_array,.fini_array -b .bss,._user_heap_stack --detail
```

The output could be:
```
========== Section Size ==========
Total Text = 79692   (Dec)  0x1374c  (Hex)
Total Data = 10988   (Dec)  0x2aec   (Hex)
Total Bss  = 65212   (Dec)  0xfebc   (Hex)


Text      Data      Bss       Object
======================================
432       0         128       Core/Src/tim.o
3304      0         0         Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_uart.o
580       0         0         Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash_ex.o
220       0         0         Core/Src/syscalls.o
1876      16        188       Middlewares/Third_Party/FreeRTOS/Source/timers.o
592       272       0         Core/Src/service_app/sapp_curtain.o
2364      0         0         Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rcc.o
4312      1264      528       Core/Src/atom_console.o
52        0         12        Core/Src/iwdg.o
108       0         4         Core/Src/sysmem.o
...
452       0         0         Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_cortex.o
1024      0         0         Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_gpio.o
--------------------------------------
79692     10988     65212     Total = 152.2 KB


========== Symbol Size Report ==========
Core/Src/tim.o :
  text    160       .text.MX_TIM1_Init
  text    152       .text.MX_TIM2_Init
  text    120       .text.HAL_TIM_Base_MspInit
  Bss     128       COMMON


Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_uart.o :
  text    154       .text.HAL_UART_Init
  text    170       .text.HAL_UART_Receive_IT
  text    512       .text.HAL_UART_IRQHandler
  text    20        .text.HAL_UART_TxCpltCallback
  text    20        .text.HAL_UART_ErrorCallback
  text    60        .text.UART_EndRxTransfer
  text    40        .text.UART_DMAAbortOnError
  text    172       .text.UART_Transmit_IT
  text    48        .text.UART_EndTransmit_IT
  text    258       .text.UART_Receive_IT
  text    2         *fill*
  text    1848      .text.UART_SetConfig


Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash_ex.o :
  text    224       .text.HAL_FLASHEx_Erase
  text    72        .text.FLASH_MassErase
  text    144       .text.FLASH_Erase_Sector
  text    140       .text.FLASH_FlushCaches

...
...
```
