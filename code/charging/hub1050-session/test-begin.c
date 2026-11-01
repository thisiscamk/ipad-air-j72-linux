
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
struct kernel_param {};
static int policy_lock,request_work,queued,locks;
static bool ready,armed,power_down;
static struct {bool used,active,restore_failed;} policy;
static bool sysfs_streq(const char *a,const char *b){return !strcmp(a,b);}
static void mutex_lock(int *p){(void)p;locks++;}
static void mutex_unlock(int *p){(void)p;locks--;}
static void schedule_work(int *p){(void)p;queued=1;}
static int begin_set(const char *value, const struct kernel_param *unused)
{
	int ret = 0;
	if (!sysfs_streq(value, "continue-qualified-hub-60min")) return -EINVAL;
	mutex_lock(&policy_lock);
	if (!ready || !armed || policy.used || policy.active || power_down ||
	    policy.restore_failed) ret = -EPERM;
	else schedule_work(&request_work);
	mutex_unlock(&policy_lock);
	return ret;
}

static void reset(void){ready=armed=true;power_down=false;memset(&policy,0,sizeof(policy));queued=locks=0;}
int main(void){
 const char *token="continue-qualified-hub-60min";
 reset();assert(begin_set(token,0)==0&&queued&&locks==0);
 reset();assert(begin_set("bad",0)==-EINVAL&&!queued&&!locks);
 for(int i=0;i<6;i++){
  reset();
  switch(i){case 0:ready=false;break;case 1:armed=false;break;case 2:policy.used=true;break;case 3:policy.active=true;break;case 4:power_down=true;break;case 5:policy.restore_failed=true;break;}
  assert(begin_set(token,0)==-EPERM&&!queued&&!locks);
 }
 puts("PASS: actual begin callback queues armed request; refuses wrong token and six unsafe states");
}
