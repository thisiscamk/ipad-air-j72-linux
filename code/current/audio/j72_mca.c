// SPDX-License-Identifier: GPL-2.0-only
/* Experimental J72 MCA-v1 playback subset, 48kHz stereo S16 only.
 * A7 register sequence is independently checked against saved iOS replay.
 * No RX support or MCA IRQ handling yet: mask MCA IRQs, use SIO completions.
 */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/pm_runtime.h>
#include <linux/clk-provider.h>
#include <linux/dmaengine.h>
#include <linux/soc/apple/sio.h>
#include <sound/soc.h>
#include <sound/pcm_params.h>
#include <sound/dmaengine_pcm.h>
struct j72_mca {
 struct device *dev;void __iomem *base,*mclk,*sw;struct clk_hw clk;
 struct snd_dmaengine_dai_dma_data tx;struct apple_sio_dma_config cfg;
 u32 route[3];bool routed;
};
static void put(struct j72_mca *m,u32 off,u32 value){writel(value,m->base+off);}
static struct j72_mca *fromclk(struct clk_hw *h){return container_of(h,struct j72_mca,clk);}
static int clkprep(struct clk_hw *h){int r=pm_runtime_resume_and_get(fromclk(h)->dev);return r<0?r:0;}
static void clkunprep(struct clk_hw *h){pm_runtime_put_sync_suspend(fromclk(h)->dev);}
static int clken(struct clk_hw *h){writel(0x58,fromclk(h)->mclk);return 0;}
static void clkdis(struct clk_hw *h){writel(0,fromclk(h)->mclk);}
static unsigned long clkrate(struct clk_hw *h,unsigned long p){return 12000000;}
static const struct clk_ops clocks={.prepare=clkprep,.unprepare=clkunprep,.enable=clken,.disable=clkdis,.recalc_rate=clkrate};
static int fmt(struct snd_soc_dai *d,unsigned f){
 return ((f&SND_SOC_DAIFMT_CLOCK_PROVIDER_MASK)==SND_SOC_DAIFMT_BC_FC &&
         (f&SND_SOC_DAIFMT_FORMAT_MASK)==SND_SOC_DAIFMT_I2S &&
         (f&SND_SOC_DAIFMT_INV_MASK)==SND_SOC_DAIFMT_NB_NF)?0:-EINVAL;
}
static int startup(struct snd_pcm_substream *s,struct snd_soc_dai *d){
 struct j72_mca *m=snd_soc_dai_get_drvdata(d);int ret=pm_runtime_resume_and_get(m->dev);return ret<0?ret:0;
}
static void route_off(struct j72_mca *m){
 if(!m->routed)return;
 writel(m->route[0],m->sw);writel(m->route[1],m->sw+20);writel(m->route[2],m->sw+60);m->routed=false;
}
static void shutdown(struct snd_pcm_substream *s,struct snd_soc_dai *d){
 struct j72_mca *m=snd_soc_dai_get_drvdata(d);
 put(m,0x18,0);put(m,0x0c,0);put(m,0x10,0);route_off(m);pm_runtime_put_sync_suspend(m->dev);
}
static int params(struct snd_pcm_substream *s,struct snd_pcm_hw_params *p,struct snd_soc_dai *d){
 return params_rate(p)==48000&&params_channels(p)==2&&params_format(p)==SNDRV_PCM_FORMAT_S16_LE?0:-EINVAL;
}
static int prepare(struct snd_pcm_substream *s,struct snd_soc_dai *d){
 struct j72_mca *m=snd_soc_dai_get_drvdata(d);u32 value;int ret;
 put(m,0x44,3);put(m,0x48,1);
 ret=readl_poll_timeout(m->base+0x48,value,!(value&1),10,10000);if(ret)return ret;
 put(m,0x10,0);put(m,0x1c,0xf);put(m,0x30,0xf); /* all MCA causes masked */
 put(m,8,0x1010);put(m,0x20,0x2f0030);put(m,0x34,0x30004);
 put(m,0x14,0);put(m,0x24,3);put(m,0x38,3);put(m,0x18,0x10a);put(m,0x2c,0x108);
 put(m,0x10,1);put(m,0x40,0xb0003000);put(m,0xc,0x0f101048);
 if(!m->routed){m->route[0]=readl(m->sw);m->route[1]=readl(m->sw+20);m->route[2]=readl(m->sw+60);m->routed=true;}
 /* Owner ADT/active iOS route AUD0-PIN0, switch version3. */
 writel(0x18,m->sw);writel(0x80808,m->sw+20);writel(0x10,m->sw+60);
 return 0;
}
static int trigger(struct snd_pcm_substream *s,int cmd,struct snd_soc_dai *d){
 struct j72_mca *m=snd_soc_dai_get_drvdata(d);u32 value;
 switch(cmd){
 case SNDRV_PCM_TRIGGER_START:case SNDRV_PCM_TRIGGER_RESUME:case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
  put(m,0x40,0xb0003000);put(m,0x18,0x10b);put(m,0xc,0x0f10104a);return 0;
 case SNDRV_PCM_TRIGGER_STOP:case SNDRV_PCM_TRIGGER_SUSPEND:case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
  put(m,0x18,0);put(m,0x44,1);
  return readl_poll_timeout_atomic(m->base+0x44,value,!(value&1),1,1000);
 }
 return -EINVAL;
}
static int hwfree(struct snd_pcm_substream *s,struct snd_soc_dai *d){
 struct j72_mca *m=snd_soc_dai_get_drvdata(d);put(m,0xc,0);route_off(m);return 0;
}
static int dai_probe(struct snd_soc_dai *d){struct j72_mca *m=snd_soc_dai_get_drvdata(d);snd_soc_dai_init_dma_data(d,&m->tx,NULL);return 0;}
static const struct snd_soc_dai_ops dai_ops={.probe=dai_probe,.set_fmt=fmt,.startup=startup,.shutdown=shutdown,.hw_params=params,.prepare=prepare,.trigger=trigger,.hw_free=hwfree};
static struct snd_soc_dai_driver dai={.name="j72-mca-v1",.playback={.stream_name="Playback",.channels_min=2,.channels_max=2,.rates=SNDRV_PCM_RATE_48000,.formats=SNDRV_PCM_FMTBIT_S16_LE},.ops=&dai_ops};
static const struct snd_soc_component_driver component={.name="j72-mca-v1"};
static int slave(struct snd_pcm_substream *s,struct snd_pcm_hw_params *p,struct dma_slave_config *sc){
 struct snd_soc_pcm_runtime *r=snd_soc_substream_to_rtd(s);struct j72_mca *m=snd_soc_dai_get_drvdata(snd_soc_rtd_to_cpu(r,0));int ret;
 ret=snd_dmaengine_pcm_prepare_slave_config(s,p,sc);if(ret)return ret;
 m->cfg=(struct apple_sio_dma_config){.xfer=0x21,.timeout=0,.fifo=0xcc,.trigger=0xac,.limit=192};
 sc->peripheral_config=&m->cfg;sc->peripheral_size=sizeof(m->cfg);return 0;
}
static const struct snd_pcm_hardware pcm_hw={
 .info=SNDRV_PCM_INFO_INTERLEAVED|SNDRV_PCM_INFO_MMAP|SNDRV_PCM_INFO_MMAP_VALID|SNDRV_PCM_INFO_BLOCK_TRANSFER|SNDRV_PCM_INFO_BATCH,
 .formats=SNDRV_PCM_FMTBIT_S16_LE,.rates=SNDRV_PCM_RATE_48000,.rate_min=48000,.rate_max=48000,.channels_min=2,.channels_max=2,
 .buffer_bytes_max=128*1024,.period_bytes_min=512,.period_bytes_max=32*1024,.periods_min=2,.periods_max=16,
};
static const struct snd_dmaengine_pcm_config pcm={.prepare_slave_config=slave,.pcm_hardware=&pcm_hw,.prealloc_buffer_size=128*1024};
static int probe(struct platform_device *p){
 struct device *dev=&p->dev;struct j72_mca *m;struct clk_init_data init={.name="j72-mca0-mclk",.ops=&clocks};u32 version,fifo;int ret;
 if(!of_machine_is_compatible("apple,j72"))return -ENODEV;
 m=devm_kzalloc(dev,sizeof(*m),GFP_KERNEL);if(!m)return -ENOMEM;m->dev=dev;platform_set_drvdata(p,m);
 m->base=devm_platform_ioremap_resource_byname(p,"mca");if(IS_ERR(m->base))return PTR_ERR(m->base);
 m->mclk=devm_platform_ioremap_resource_byname(p,"mclk");if(IS_ERR(m->mclk))return PTR_ERR(m->mclk);
 m->sw=devm_platform_ioremap_resource_byname(p,"switch");if(IS_ERR(m->sw))return PTR_ERR(m->sw);
 ret=devm_pm_runtime_enable(dev);if(ret)return ret;
 ret=pm_runtime_resume_and_get(dev);if(ret<0)return ret;
 version=readl(m->base);fifo=readl(m->base+4);pm_runtime_put_sync_suspend(dev);
 if(version!=0x10001||fifo!=0x800080)return -ENODEV;
 m->clk.init=&init;ret=devm_clk_hw_register(dev,&m->clk);if(ret)return ret;
 ret=devm_of_clk_add_hw_provider(dev,of_clk_hw_simple_get,&m->clk);if(ret)return ret;
 ret=devm_snd_soc_register_component(dev,&component,&dai,1);if(ret)return ret;
 return devm_snd_dmaengine_pcm_register(dev,&pcm,0);
}
static const struct of_device_id ids[]={{.compatible="orchard,j72-mca-v1-test"},{}};
static struct platform_driver j72_mca_driver={.probe=probe,.driver={.name="j72-mca-v1",.of_match_table=ids}};
module_platform_driver(j72_mca_driver);MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Experimental J72 MCA-v1 48k stereo S16 playback subset; not yet qualified");
