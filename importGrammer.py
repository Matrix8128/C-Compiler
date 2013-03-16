#!/usr/bin/env python
from raw_cfg import *

V=raw_V.strip().split()
T=raw_T.strip().split()
cfg=raw_cfg.strip().split('\n')
CFG={}
V.append('B')
augumentItem=('B',((),(first_V.strip(),),'$'))
for pro in cfg:
	li=pro.split('->')
	left=li[0].strip()
	right=tuple(li[1].split())
	if CFG.has_key(left) and right not in CFG[left]:
		CFG[left].append(right)
	else:
		CFG[left]=[right]

	 	
