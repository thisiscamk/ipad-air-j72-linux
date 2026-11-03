/* SPDX-License-Identifier: GPL-2.0-only */
/* stdin contains private wire replies; print aggregate recognition only. */
#include <assert.h>
#include <stdio.h>
#include "j72-data-phase.h"
int main(void) {
 unsigned char size[2],rx[J72_DATA_CAPACITY];
 unsigned records=0,recognized=0,wire,length;
 while(fread(size,1,2,stdin)==2) {
  wire=size[0]|((unsigned)size[1]<<8);assert(wire>=7&&wire<=2459);
  assert(fread(rx,1,wire,stdin)==wire);
  length=j72_data_header_length(rx,wire);
  records++;if(length)recognized++;
 }
 assert(!ferror(stdin));
 printf("records=%u\nrecognized_positive_headers=%u\n",records,recognized);
 return 0;
}
