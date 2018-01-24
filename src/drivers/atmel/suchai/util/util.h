#ifndef __UTIL_H
#define __UTIL_H

#include <stdint.h>

void serial_init(void);
void spi_init(void);
void ssc_init(void *buffer, void *buffer2, __int_handler handler);
void ssc_start(void);

uint32_t memcheck(void);
void hexdump(char *desc, void *addr, int len);

#endif