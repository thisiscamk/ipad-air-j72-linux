/* SPDX-License-Identifier: GPL-2.0-or-later */
static int same(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static int token(const char*s,size_t n,const char*word){size_t k=0;while(word[k])k++;if(k!=n)return 0;for(k=0;k<n;k++)if(s[k]!=word[k])return 0;return 1;}
/* Strict allowlist: refusal occurs before any IOKit call or child process. */
static int safe_args(const char*s){int md0=0;while(*s){while(*s==' ')s++;if(!*s)break;const char*p=s;while(*s&&*s!=' ')s++;size_t n=(size_t)(s-p);if(token(p,n,"rd=md0"))md0=1;else if(!token(p,n,"debug=0x2014e")&&!token(p,n,"-v")&&!token(p,n,"wdt=-1"))return 0;}return md0;}
