#!/usr/bin/python

#get LR(1) parser
import pprint,time,os,pickle
from importGrammer import *
from scanner import *
from translate import *
class Parser:
	r'''Parser.
	'''
	def __init__(self,Grammer,T,V,augumentItem):
		self.CFG=Grammer
		self.T=T
		self.V=V
		self.ItemSet=[]#set of all closures
		self.augumentItem=augumentItem
		self.action=[]
		self.goto=[]
		self.trans=Translate()
	
	def firstOpSym(self,var):
		r"""get the first op set of symbol var.
		"""
		first=[]
		if var in self.T:
			return [var]
		elif var in self.V:
			for right in self.CFG[var]:
				if right==None:
					first.append(None)
				elif right[0] in self.T:
					first.append(right[0])
				elif right[0]==var:#recrusive A->Aa
					continue
				elif right[0] in self.V:
					isBreak=False
					for s in right:
						l=self.firstOpSym(s)
						first+=l
						if None in l:first.remove(None)
						else:
							isBreak=True
							break
					if isBreak==False:
						if None not in first:first.append(None)
				else:return None
			return first		
		else:return None	
	
	def firstOpList(self,slist):
		r"""get the first op list.
		"""
		first=[]
		if slist[0] in self.T+['$']:
			return [slist[0]]
		if slist[0] in self.V:
			isBreak=False
			for s in slist:
				l=self.firstOpSym(s)
				first+=l
				if None in l:first.remove(None)
				else:
					isBreak=True
					break
			if isBreak==False:
				if None not in first:first.append(None)
			return first	
		else:
			return None
		
#item ('S',((),('L','=','R'),'$')) means S->.L=R,$  
	
	def Closure(self,itemList):
		r"""return the closure based on given itemlist.
		"""
		C=itemList[:]
		sizeofC=len(C)
		while True:
			for item in C:#e.g:S->.L=R,$
				unmatch=item[1][1]#'L=R'
				ex_sym=item[1][2]#'$'
				if len(unmatch)>0 and unmatch[0] in self.V:
					first=self.firstOpList(unmatch[1:]+(ex_sym,))	
					for s in first:
						if s==None:s='$'
						for right in self.CFG[unmatch[0]]:
							newItem=(unmatch[0],((),right,s))
							if newItem not in C:
								C.append(newItem)
			if(len(C)<=sizeofC):break
			sizeofC=len(C)
		return C	
					
				
	
	def Goto(self,closureIndex,closure,symbol):
		r"""return the closure of successive item only if the closure
			doesn't exist in ItemSet, otherwise return none
		"""
		J=[]
		for item in closure:
			
			matched=item[1][0]
			unmatch=item[1][1]
			forwardChar=item[1][2]
			if len(unmatch)==0:#reduce and acc
				if item[0]==self.augumentItem[0] and forwardChar=='$':#acc
					self.action[closureIndex]['$']='acc'
				else:
					Reduce='reduce '+item[0]+'->'+' '.join(matched)
					self.action[closureIndex][forwardChar]=Reduce
			if len(unmatch)>0 and unmatch[0]==symbol:
				goItem=(item[0],((matched[:]+(symbol,)),(unmatch[1:]),item[1][2]))
				if goItem not in J:
					J.append(goItem)
		if len(J)==0:
			return None #no sucessive items
		
		goIndex=self.tryExist(J)
		result=None
		if goIndex is not None:#exist?
			result=self.Closure(J)
			goIndex=self.ClosureExist(result)#if goIndex==None,then really exists
		if goIndex is not None:#really exist
			result=None
		else:#does't exist	
			goIndex=len(self.ItemSet)
			if result is None:
				result=self.Closure(J)
		#goto and shift
		if symbol in self.T:
			self.action[closureIndex][symbol]='shift '+str(goIndex)
		elif symbol  in self.V:
			self.goto[closureIndex][symbol]=goIndex
		return result
	
	def tryExist(self,itemList):
		if len(itemList)==0:
			return None
		for index,closure in enumerate(self.ItemSet):
			if isinstance(closure,list):
				exist=True
			for item in itemList:
				if item not in closure:
					exist=False
					break
			if exist:
		#		CL=self.Closure(itemList)
		#		if self.ClosureExist(CL) is None:#not really exists
		#			print	'itemList:',itemList
		#			print self.ItemSet[index]
		#			print 	'newClosure:',CL 
		
				return index
		return None
	
	def ClosureExist(self,closure):
		r'''
		return index of the existed closure if exists,
		return None elsewise
		'''		
		for index,col in enumerate(self.ItemSet):
			if len(col)!=len(closure):
				continue
			else:
				flag=True
				for item in closure:
					if item not in col:
						flag=False#not the same
						break
				if flag==True:
					return index
		return None
	
	def getItemSet(self,actionFile,gotoFile):
		r'''get the set of all closures.
		'''
		if os.path.exists(actionFile) and os.path.exists(gotoFile):
			with open(actionFile,'rb') as in_f:
				self.action=pickle.load(in_f)
			with open(gotoFile,'rb') as in_f:
				self.goto=pickle.load(in_f)
		else:	
	
			firstItem=self.augumentItem
			firstClosure=self.Closure([firstItem])
			self.ItemSet=[firstClosure]
		
			self.action.append({})
			self.goto.append({})
			sizeOfSet=len(self.ItemSet)
			for index,closure in enumerate(self.ItemSet):
				for t in self.V+self.T:
					newClosure=self.Goto(index,closure,t)
					if newClosure is not None:
						self.ItemSet.append(newClosure)
						self.action.append({})
						self.goto.append({})
			with open(actionFile,'wb') as out_f:
				pickle.dump(self.action,out_f)
			with open(gotoFile,'wb') as out_f:
				pickle.dump(self.goto,out_f)

	def showItemSet(self):
		for i,clo in enumerate(self.ItemSet):
			print 'I'+str(i)+':'
			for item in clo:
				print item[0]+'->'+''.join(item[1][0])+'.'+''.join(item[1][1])+','+item[1][2]
	
	def showLR1table(self):
		print 'action table:'
		for i,d in enumerate(self.action):
			print str(i)+':'
			pprint.pprint(d)
		
		print 'goto table:'
		for i,d in enumerate(self.goto):
			print str(i)+':'
			pprint.pprint(d)

	def TokenToTerm(self,Token):
		r'''translate token to termianl.
		'''
		if Token[1] in ['PUNC','OP','KEYWORD']:
			if Token[0] in self.T:
				return Token[0]
		elif Token[1]=='ID':
			return 'id'
		elif Token[1] in ['INT','DOUBLE','CHAR','STRING']:
			return Token[1]
				
	def analyse(self,filePath):
		r'''analyse file.
		'''
		sc=Scanner(filePath)
		inputList=[]
		tokenList=[]
		while sc.getToken():
		#	print sc.matchResult
			tokenList.append(sc.matchResult[0])
			inputList.append(self.TokenToTerm(sc.matchResult))
		
		inputList.append('$')
		stack=[0]
		index=0
		while True:
			currentState=stack[-1]
			inputSym=inputList[index]
	#		print currentState,inputSym,tokenList[index]
			result=self.action[currentState][inputSym].strip()
			ty=result.split()[0]
			if ty=='shift':
				nextState=int(result.split()[1])
				stack.append(nextState)
				if inputSym=='{':
					self.trans.newScope()
			#	print 'shift',nextState
				TermAttr=Attribute()#################
				TermAttr.Symbol=inputSym##############
				TermAttr.Name=tokenList[index]############
				self.trans.addAttr(TermAttr)#############
				index+=1
			elif ty=='reduce':
				pro=result.replace('reduce','').strip()
				print pro
				left=pro.split('->')[0].strip()
				right=pro.split('->')[1].strip().split()
				for i in range(len(right)):
					stack.pop()
				currentState=stack[-1]
				nextState=self.goto[currentState][left]
				stack.append(nextState)
				self.trans.translate(left,right)#############
			elif ty=='acc':
				print 'done'
				break
			else:
				print 'something is wrong'

		

			
Pa=Parser(CFG,T,V,augumentItem)
t1=time.clock()
Pa.getItemSet('actionTable','gotoTable')
print time.clock()-t1

if __name__=='__main__':
#	Pa.showItemSet()
	src=sys.argv[1]
	src=src.split('.')[0]
	Pa.analyse('%s.c'%src)
	print '\n'.join(Pa.trans.codeList)
	with open('%s.s'%src,'wb') as out_f:
		out_f.write('\n'.join(Pa.trans.codeList))
	print 'compiling....'
	log=os.popen('as -o %s.o %s.s'%(src,src)).readlines()
	print '\n'.join(log)
	print 'linking....'
	log=os.popen('ld -dynamic-linker /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 -lc -o %s %s.o'%(src,src)).readlines()
	print '\n'.join(log)
	
	pass
#	Pa.showItemSet()
#	Pa.showLR1table()	


