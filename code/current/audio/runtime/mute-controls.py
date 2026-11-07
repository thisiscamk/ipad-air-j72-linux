"""Owner-present quiet one-second tone only. Output muted again in finally."""
import ctypes as C,json,time,math,struct
A=C.CDLL('libasound.so.2');P=C.c_void_p;I=C.c_int;U=C.c_uint;L=C.c_long
for n,args,ret in [
 ('snd_strerror',[I],C.c_char_p),('snd_ctl_open',[C.POINTER(P),C.c_char_p,I],I),('snd_ctl_close',[P],I),
 ('snd_ctl_elem_id_malloc',[C.POINTER(P)],I),('snd_ctl_elem_id_free',[P],None),
 ('snd_ctl_elem_id_set_interface',[P,I],None),('snd_ctl_elem_id_set_name',[P,C.c_char_p],None),
 ('snd_ctl_elem_value_malloc',[C.POINTER(P)],I),('snd_ctl_elem_value_free',[P],None),
 ('snd_ctl_elem_value_set_id',[P,P],None),('snd_ctl_elem_value_set_boolean',[P,U,L],None),
 ('snd_ctl_elem_value_get_boolean',[P,U],I),('snd_ctl_elem_value_set_integer',[P,U,L],None),
 ('snd_ctl_elem_value_get_integer',[P,U],L),('snd_ctl_elem_write',[P,P],I),('snd_ctl_elem_read',[P,P],I),
 ('snd_pcm_open',[C.POINTER(P),C.c_char_p,I,I],I),('snd_pcm_close',[P],I),
 ('snd_pcm_format_value',[C.c_char_p],I),('snd_pcm_access_name',[I],C.c_char_p),
 ('snd_pcm_set_params',[P,I,I,U,U,I,U],I),('snd_pcm_writei',[P,P,C.c_ulong],L),('snd_pcm_drain',[P],I),('snd_pcm_drop',[P],I),
]:
 f=getattr(A,n);f.argtypes=args;f.restype=ret

def ok(rc):
 if rc<0:raise RuntimeError(A.snd_strerror(rc).decode()+f' ({rc})')
 return rc

ctl=P();pcm=P();r={'audio':'quiet 440Hz stereo tone','frames':0,'rate':48000,'speaker_control_db':-30,'pcm_peak':8192,'duration_limit_seconds':1}
def control(name,kind,value):
 ident=P();v=P()
 try:
  ok(A.snd_ctl_elem_id_malloc(C.byref(ident)));ok(A.snd_ctl_elem_value_malloc(C.byref(v)))
  A.snd_ctl_elem_id_set_interface(ident,2);A.snd_ctl_elem_id_set_name(ident,name.encode());A.snd_ctl_elem_value_set_id(v,ident)
  getattr(A,'snd_ctl_elem_value_set_'+kind)(v,0,value);ok(A.snd_ctl_elem_write(ctl,v));ok(A.snd_ctl_elem_read(ctl,v))
  assert getattr(A,'snd_ctl_elem_value_get_'+kind)(v,0)==value
 finally:
  if v:A.snd_ctl_elem_value_free(v)
  if ident:A.snd_ctl_elem_id_free(ident)
try:
 ok(A.snd_ctl_open(C.byref(ctl),b'hw:Test',0))
 control('Speaker Playback Switch','boolean',0)
 control('Headphone Playback Switch','boolean',0)
 control('Speaker Playback Volume','integer',144)
 print(json.dumps({'muted':True,'volume_raw':144}))
finally:
 if ctl:A.snd_ctl_close(ctl)
