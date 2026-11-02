/* SPDX-License-Identifier: GPL-2.0-or-later
 * USB recovery initialization derived from xerub's 2015 restored_external,
 * with no mount, installation, snapshot, restore or shell command path.
 * Minimal authored ABI declarations; no SDK headers are distributed.
 */
typedef unsigned long size_t;
typedef unsigned int io_service_t;
typedef const void *CFRef;
extern int printf(const char*,...);
extern unsigned sleep(unsigned);
extern unsigned getuid(void);
extern int sysctlbyname(const char*,void*,size_t*,void*,size_t);
extern int execv(const char*,char *const[]);
extern CFRef CFStringCreateWithCString(CFRef,const char*,unsigned);
extern CFRef CFNumberCreate(CFRef,long,const void*);
extern void CFRelease(CFRef);
extern CFRef CFRetain(CFRef);
extern CFRef IOServiceMatching(const char*);
extern io_service_t IOServiceGetMatchingService(unsigned,CFRef);
extern int IOObjectRelease(io_service_t);
extern int IORegistryEntrySetCFProperties(io_service_t,CFRef);
extern CFRef IOUSBDeviceDescriptionCreateWithType(CFRef,CFRef);
extern void IOUSBDeviceDescriptionSetSerialString(CFRef,CFRef);
extern int IOUSBDeviceControllerCreate(CFRef,CFRef*);
extern int IOUSBDeviceControllerSetDescription(CFRef,CFRef);
#include "j72-recovery-guard.h"
static CFRef string(const char*s){return CFStringCreateWithCString(0,s,0x08000100U);}
static io_service_t service(const char*name,unsigned retries){
 CFRef match=IOServiceMatching(name);if(!match)return 0;
 io_service_t found=0;
 for(unsigned i=0;i<=retries;i++){CFRetain(match);found=IOServiceGetMatchingService(0,match);if(found)break;if(i<retries)sleep(1);}
 CFRelease(match);return found;
}
int main(void){
 char model[32]={0},args[2048]={0};size_t n=sizeof(model),a=sizeof(args);
 if(getuid()!=0||sysctlbyname("hw.machine",model,&n,0,0)||!n||n>=sizeof(model)||model[n-1]||!same(model,"iPad4,2"))return 2;
 if(sysctlbyname("kern.bootargs",args,&a,0,0)||!a||a>=sizeof(args)||args[a-1]||!safe_args(args)){printf("J72 recovery refused: expected approved RAM-root boot arguments\n");return 3;}
 io_service_t wd=service("IOWatchDogTimer",0);
 if(wd){int zero=0;CFRef number=CFNumberCreate(0,3,&zero);if(number){IORegistryEntrySetCFProperties(wd,number);CFRelease(number);}IOObjectRelease(wd);}
 CFRef type=string("standardMuxOnly");if(!type)return 4;
 CFRef desc=IOUSBDeviceDescriptionCreateWithType(0,type);CFRelease(type);if(!desc)return 5;
 CFRef serial=string("J72_RO_RECOVERY_V1");if(!serial){CFRelease(desc);return 6;}
 IOUSBDeviceDescriptionSetSerialString(desc,serial);CFRelease(serial);
 int status;
 CFRef controller=0;
 for(unsigned i=0;i<10;i++){if(IOUSBDeviceControllerCreate(0,&controller)==0&&controller)break;sleep(1);}
 if(!controller){CFRelease(desc);return 8;}
 status=IOUSBDeviceControllerSetDescription(controller,desc);CFRelease(controller);CFRelease(desc);if(status)return 9;
 io_service_t mux=service("AppleUSBDeviceMux",10);if(!mux)return 10;IOObjectRelease(mux);
 printf("J72 RAM recovery: USB ready, public-key SSH only; no internal filesystem mounted\n");
 char *const argv[]={"/usr/local/bin/dropbear","-F","-E","-s","-r","/private/etc/dropbear/dropbear_rsa_host_key","-p","22","-P","/var/run/dropbear.pid",0};
 execv(argv[0],argv);return 11;
}
