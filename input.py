#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re,os,sys,random

class Input(object):
	r"""provide raw data from file.
        buffer and file manager.
	"""
	def __init__(self):
		r"""Initialize.
        """
		self.buffer_len=250
		self.double_buffer=[]
		self.input_f=None
		self.line_num=0
		self.index_num=0

	def open(self,sPath):
		r"""Open a file to input.
		"""
		if self.input_f:
			self.input_f.close()
		self.input_f=open(sPath)
		self.begin=0
		self.end=0
		self.file_left=self.buffer_len*10+10
		self.iter=self.iterData(self.input_f,size=(self.buffer_len))
		try:
			self.double_buffer=list(self.iter.next())
			self.double_buffer+=list(self.iter.next())
		except StopIteration:
			pass
	#		print 'the end'
		if len(self.double_buffer)<self.buffer_len*2:
			self.file_left=len(self.double_buffer)
		self.buffer_left=len(self.double_buffer)
		self.double_buffer+=['\0']*(self.buffer_len*2-self.buffer_left)
		
	def iterData(self,f,size=250):
		r"""return data wit specify size.
		"""
		while True:	
			string=f.read(size)
			if not string:
				break
			yield string

	def getEnd(self,forward):
		r"""compute the end.
		"""
		#calculate the length from self.begin to self.end (all included)
		len=forward+1
		if len>self.file_left:
		#	print 'end of file'
			return -1
		
		if len >self.buffer_left:
		#	print 'too long'
			return -2
		self.end=(self.begin+forward)%(self.buffer_len*2)
		return self.end
#API
	def getChar(self,forward):
		r"""get char.
		"""
		
		if self.getEnd(forward)<0:
			return None
		return self.double_buffer[self.end]

	def copyString(self,forward):
		r"""get String from begin to end (include double_buffer[self.end])
		"""
		result=self.getEnd(forward)
		#print 'begin and end',self.begin,self.end
		#print 'forward'+str(forward),result
		if result==-2:
			result=self.getEnd(random.randint(0,249))		
		######return None
		elif result==-1:
			if self.file_left!=0:
				self.getEnd(self.file_left-1)
				#print self.end
			else:
				return None
		#print 'begin and end end',self.begin,self.end
		if self.end>=self.begin:
			return ''.join(self.double_buffer[self.begin:self.end+1])
		else:
			return ''.join(self.double_buffer[self.begin:]+self.double_buffer[:self.end+1])
	
	def flushBuffer(self,first_buffer=True):
		r"""flush buffer.
		"""
		ss=''
		if self.file_left<self.buffer_len*2:
			return -1
		else:
			ss=self.iter.next()
			self.buffer_left+=len(ss)
			if len(ss)<self.buffer_len:
				self.file_left=self.buffer_left
			if first_buffer:
		#		print 'flush left'
				self.double_buffer[:self.buffer_len]=list(ss)+['\0']*(self.buffer_len-len(ss))
			else:
		#		print 'flush right'
				self.double_buffer[self.buffer_len:]=list(ss)+['\0']*(self.buffer_len-len(ss))

	def cutString(self,forward):
		r"""get String and  remove it from the buffer then update buffer.
		"""
		string=self.copyString(forward)
		if string is not None:
			#print list(string),len(string)
			self.buffer_left-=len(string)
			before=self.begin
			self.begin=(self.end+1)%(self.buffer_len*2)
			if self.file_left<self.buffer_len*2:
				self.file_left-=len(string)
		#	print self.begin,len(string),self.file_left
			#print before,self.begin,len(string)
		#	print 'buffer_left',self.buffer_left	
			if self.buffer_left==0:
				if 0<=before<self.buffer_len:
					self.flushBuffer(first_buffer=True)
					self.flushBuffer(first_buffer=False)
				else:
					self.flushBuffer(first_buffer=False)
					self.flushBuffer(first_buffer=True)
				return string
			elif self.begin>=self.buffer_len and self.begin-len(string)<self.buffer_len:
				self.flushBuffer(first_buffer=True)
			elif 0<=self.begin<self.buffer_len and self.begin-len(string)<0:
				self.flushBuffer(first_buffer=False)
		if '\n' in string:
			self.line_num+=1
			self.index_num=len(string)-string.index('\n')
		else:
			self.index_num+=len(string)
		return string
				
			
inp=Input()
import pprint,os
if __name__=='__main__':					
	
	ll=-1
	while ll<=509:	
		ll+=1
		inp.open('test.py')
		s=''
	#	print 'count:'+str(ll)
		count=0
		while True:
			count+=1
	#		print 'left',inp.buffer_left,inp.file_left
	#		if count>(920/(ll+1)+10) or inp.buffer_left<0:
	#			print 'icount:'+str(ll)
	#			exit(0)	
	#		print 'cc:'+str(count)
			ss=inp.cutString(0)
			if ss is None:
				break
			s+=ss
		out=open("xx/%d"%ll,'w')
		out.write(s)	
				

		
				
	
	
	
