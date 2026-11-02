# SPDX-License-Identifier: MIT
"""Bounded Pongo console transport using the host's native libusb.

Commands run with non-blocking device stdout. Read output only after the device
reports command completion. Callers must keep each response below the 4095-byte
Pongo ring capacity; overflow is refused rather than treated as valid framing.
"""
import ctypes as C
import time

class PongoControl:
    def __init__(self, log):
        self.log=log;self.ctx=C.c_void_p();self.handle=None;self.claimed=False
        self.usb=C.CDLL('libusb-1.0.so.0')
        signatures={
            'libusb_init':([C.POINTER(C.c_void_p)],C.c_int),
            'libusb_open_device_with_vid_pid':([C.c_void_p,C.c_uint16,C.c_uint16],C.c_void_p),
            'libusb_claim_interface':([C.c_void_p,C.c_int],C.c_int),
            'libusb_release_interface':([C.c_void_p,C.c_int],C.c_int),
            'libusb_close':([C.c_void_p],None),'libusb_exit':([C.c_void_p],None),
            'libusb_control_transfer':([C.c_void_p,C.c_uint8,C.c_uint8,C.c_uint16,C.c_uint16,C.c_void_p,C.c_uint16,C.c_uint],C.c_int),
            'libusb_bulk_transfer':([C.c_void_p,C.c_ubyte,C.c_void_p,C.c_int,C.POINTER(C.c_int),C.c_uint],C.c_int)}
        for name,(args,result) in signatures.items():
            fn=getattr(self.usb,name);fn.argtypes=args;fn.restype=result
    def __enter__(self):
        if self.usb.libusb_init(C.byref(self.ctx))!=0:raise RuntimeError('libusb init failed')
        try:
            self.handle=self.usb.libusb_open_device_with_vid_pid(self.ctx,0x05ac,0x4141)
            if not self.handle:raise RuntimeError('Cannot open guarded Pongo device')
            if self.usb.libusb_claim_interface(self.handle,0)!=0:raise RuntimeError('Cannot claim Pongo interface')
            self.claimed=True;return self
        except BaseException:
            self.close();raise
    def close(self):
        if self.handle:
            if self.claimed:self.usb.libusb_release_interface(self.handle,0)
            self.usb.libusb_close(self.handle);self.handle=None;self.claimed=False
        if self.ctx.value:self.usb.libusb_exit(self.ctx);self.ctx=C.c_void_p()
    def __exit__(self,*args):self.close()
    def control(self,kind,request,value=0,data=b'',size=0):
        if kind&0x80:
            if (kind,request,size) not in ((0xa1,2,1),(0xa1,1,4096)):
                raise ValueError('Unsupported bounded control read')
            buf=C.create_string_buffer(size);length=size
        else:
            if len(data)>512:raise ValueError('Control write exceeds packet bound')
            buf=C.create_string_buffer(data,max(1,len(data)));length=len(data)
        n=self.usb.libusb_control_transfer(self.handle,kind,request,value,0,buf,length,1000)
        if n<0:raise RuntimeError('Pongo control transfer failed: '+str(n))
        if kind&0x80:return buf.raw[:n]
        if n!=length:raise RuntimeError('Short Pongo control write')
        return b''
    def _idle(self,deadline):
        while True:
            if time.monotonic()>deadline:raise TimeoutError('Pongo command did not finish')
            status=self.control(0xa1,2,size=1)
            if len(status)!=1 or status[0] not in (0,1):raise RuntimeError('Invalid Pongo command status')
            if status==b'\0':return
            time.sleep(.01)
    def _drain(self,deadline):
        self._idle(deadline);data=bytearray()
        while True:
            if time.monotonic()>deadline:raise TimeoutError('Pongo console drain deadline')
            # Pongo empties its entire ring per request and truncates from the
            # front if wLength is smaller. Read the full supported ring length.
            block=self.control(0xa1,1,size=4096)
            if not block:break
            data.extend(block);self.log.write(block);self.log.flush()
            if len(data)>=4095:raise RuntimeError('Pongo response reached ring capacity')
        return bytes(data)
    def synchronize(self):
        raw=self._drain(time.monotonic()+10)
        self.control(0x21,4,0xffff)
        return raw
    def command(self,line,marker,timeout=12):
        if line not in (b'help',b'modload',b'j72rescuecompact'):
            raise ValueError('Command is outside this read-only capture procedure')
        # Pongo's synchronous-stdin mode waits for command_handler_iter while
        # keeping stdout non-blocking. Status polling remains an extra guard.
        self.control(0x21,4,0)
        self.control(0x21,3,data=line+b'\n')
        deadline=time.monotonic()+timeout;data=bytearray()
        while True:
            # Queueing stdin and beginning command execution are separate steps.
            time.sleep(.02);data.extend(self._drain(deadline))
            clean=bytes(data).replace(b'\r',b'')
            if len(data)>=4095:raise RuntimeError('Command output exceeds compact bound')
            if b'J72_COMPACT_REFUSED' in clean or b'[modload_macho:!]' in clean:
                raise RuntimeError('Pongo refused compact module or inventory')
            if marker in clean and b'pongoOS> ' in clean.split(marker,1)[1]:return bytes(data)
            if time.monotonic()>deadline:raise TimeoutError('Missing Pongo command response')
    def upload_module(self,data):
        if not 0x4000<=len(data)<=0x40000:raise ValueError('Module upload outside allowed size')
        self.control(0x21,1,data=len(data).to_bytes(4,'little'))
        buf=C.create_string_buffer(data,len(data));done=C.c_int()
        result=self.usb.libusb_bulk_transfer(self.handle,2,buf,len(data),C.byref(done),5000)
        if result or done.value!=len(data):raise RuntimeError('Module bulk upload incomplete')
        time.sleep(.1)
