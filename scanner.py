#!/usr/bin/env python

import os,sys,input

class Scanner:
	r'''Scanner.
	'''
	def __init__(self,sPath):
		r""" initialization.
		"""
		self.initKeyword()
		self.initTokenDict()
		self.inp=input.Input()
		self.inp.open(sPath)
		self.matchResult=None
				
				
	def initKeyword(self):
		r"""initialize keyword_list.
		"""
		self.keywords=['include','int','double','float','break','else','char','const','if','else','for','while','swith','break','continue','return','default','do','void']

	def addKeyword(self,keyword):
		r"""add keyword to keyword_list.
		"""
		self.keywords.append(keyword)

	def isKeyword(self,keyword):
		r"""if the keyword in the keyword_list.
		"""
		if keyword in self.keywords:
			return True
		else:
			return False
		
	def initTokenDict(self):
		r"""initialize token dict.
		"""
	#	print 'initTokenDict'
	

	IDTransTable=list(range(0,3))
	IDTransTable[0]={'nondigit':1}
	IDTransTable[1]={'nondigit':1,'digit':1,'other':2}
	IDTransTable[2]={'final':'ID'}
	def matchID(self):
		r"""try to match an ID.
		"""
		digit=[str(d) for d in range(0,10)]	
		lower='abcdefghijklmnopqrstuvwxyz'
		nondigit=list(lower)+list(lower.upper())+['_']
		
		def map(c):
			if c in digit:return 'digit'
			elif c in nondigit:return 'nondigit'
			else:return 'other'
		state=0
		end=0
		while True:
			
			if 'final' in self.IDTransTable[state]:
				self.matchResult=(self.inp.cutString(end-2),self.IDTransTable[state]['final'])
				if self.isKeyword(self.matchResult[0]):
					self.matchResult=(self.matchResult[0],'KEYWORD')
				return True
			s=map(self.inp.getChar(end))
			if s in self.IDTransTable[state]:
				state=self.IDTransTable[state][s]
				end+=1
				continue
			else:
				return False
	
		
	NumTransTable=list(range(0,10))		
	NumTransTable[0]={'digit':1}
	NumTransTable[1]={'digit':1,'.':2,'other':3,'E':5,'sign':3}
	NumTransTable[2]={'digit':4}
	NumTransTable[3]={'final':'INT'}
	NumTransTable[4]={'digit':4,'E':5,'other':6}
	NumTransTable[5]={'sign':7,'digit':8}
	NumTransTable[6]={'final':'DOUBLE'}
	NumTransTable[7]={'digit':8}
	NumTransTable[8]={'digit':8,'other':9}
	NumTransTable[9]={'final':'DOUBLE'}
	def matchNum(self):
		r"""try to match an Num, incude int and float. 
		"""
#		print 'matchNum'
		
		digit=[str(d) for d in range(0,10)]
		sign=['+','-']
		def map(c):
			if c in digit:return 'digit'
			elif c in sign:return 'sign'
			elif c =='E' :return 'E'
			elif c =='.':return '.'
			else:return 'other'
		state=0
		end=0
		while True:
			
#			print 'state:',state,self.inp.getChar(end),self.inp.copyString(end)
			if 'final' in self.NumTransTable[state]:
				self.matchResult=(self.inp.cutString(end-2),self.NumTransTable[state]['final'])
				return True
			s=map(self.inp.getChar(end))
#			print self.inp.getChar(end),state
#			print 'next:',s
			if s in self.NumTransTable[state]:
				state=self.NumTransTable[state][s]
				end+=1
				continue
			else:
				return False
		
	def matchChar(self):
		r"""try to match a constant char.
		"""
		if self.inp.getChar(0)=="'":
			if self.inp.getChar(2)=="'":
				self.matchResult=(self.inp.cutString(2),'CHAR')
				return True
			elif self.inp.getChar(1)=='\\' and self.inp.getChar(3)=="'":
				self.matchResult=(self.inp.cutString(3),'CHAR')
				return True
			else:
				return False
		return False
		
	def matchString(self):
		r"""try to match a constan string.
		"""
		end=0
		if self.inp.getChar(end)=='"':
			end+=1
			while self.inp.getChar(end):
				if self.inp.getChar(end)=='"':
					if self.inp.getChar(end-1)!='\\':
						break
				end+=1
			if self.inp.getChar(end):
				self.matchResult=(self.inp.cutString(end),'STRING')
				return True
		return False
		
	singleOp=['+','-','*','/','%','=','>','<','!','&','|','^','.']
	multiOp=['++','+=','--','-=','*=','/=','%=','==','>=','<=','!=','&&','||']
	def matchOperator(self):
		r"""try to match a operator.
		"""
		if self.inp.getChar(0) in self.singleOp:
			if self.inp.copyString(1) in self.multiOp:
				self.matchResult=(self.inp.cutString(1),'OP')
			else:
				self.matchResult=(self.inp.cutString(0),'OP')
			return True
		return False

	punc=['[',']','{','}','(',')',',',';',':','#']
	def matchPunctuator(self):
		r"""try to match a punctuator.
		"""
		if self.inp.getChar(0) in self.punc:
			self.matchResult=(self.inp.cutString(0),'PUNC')
			return True
		return False	
	
	def getToken(self):
		r"""return an token (name,lex_code,string) if get one,lex_code=-1 if error happened
		there are 7 kinds of token:0.KEYWORD 1.ID 2.Num(INT,DOUBLE) 3.CHAR 4.STRING 5.PUNC 6.OP
		"""
		isBlank=lambda c: True if c in [' ','\t','\n','\r'] else False
		#skip the blanks
		while True:
			c=self.inp.getChar(0)
			if c and isBlank(c):#not None and is Blank
				self.inp.cutString(0)
				continue
			break
		
		if self.matchID():
			return self.matchResult
		elif self.matchNum():
			return self.matchResult
		elif self.matchChar():
			return self.matchResult
		elif self.matchString():
			return self.matchResult
		elif self.matchPunctuator():
			return self.matchResult
		elif self.matchOperator():
			return self.matchResult

	
if __name__=='__main__':
	sc=Scanner('test.c')
	while sc.getToken():
		print sc.matchResult +(sc.inp.line_num,sc.inp.index_num)







