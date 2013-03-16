#!/usr/bin/env python
import os,re,pickle,pprint,time
import copy

class symbolItem:
	r'''store all the imformation about symbol
	'''
	def __init__(self):
		self.Name=None
		self.scope=0
		self.ItemType=None #FUNC,VAR
		self.VarType=None #base type like(int,double...)
		self.Address=None#offset from the begin of the symbolTable(%rsp)
		self.Width=None#size of memory
 		self.TablePoint=None

class symbolTable:
	r'''symbol table.
	'''

	def __init__(self):
		self.parentTable=None
		self.indexInParent=None
		self.offset=0
		self.width=0
		self.Type=None
		self.symList=[]
		self.currentScope=0

	def length(self):
		r'''return the num of symbols in the table.
		'''
		return len(self.symList)		
	def addSymbol(self,ItemType,VarType=None,Name=None,width=0,TablePoint=None):
		r'''add symbol to current table if the symbol is not exist in the table\
			elsewise,print waring,raise exception.
		'''
		if Name  in [i.Name for i in self.symList if i.scope==self.currentScope]:
			print '%s is already defined'%Name
			raise Exception
		symItem=symbolItem()
		symItem.Name=Name
		symItem.ItemType=ItemType	
		if symItem.ItemType=='VAR':
			symItem.VarType=VarType
			self.width+=width
			symItem.Width=width
			symItem.Address=hex(-self.width)+'(%rbp)'
			symItem.scope=self.currentScope
			self.symList.append(symItem)
			return symItem.Address
		elif symItem.ItemType=='FUNC':#the FUNC type symbolItem has no address 
			symItem.scope=self.currentScope
			symItem.TablePoint=TablePoint
			symItem.Address='_'+symItem.Name #label	
			self.symList.append(symItem)
			return symItem.Address
		else:
			raise Exception
	def addSpecifialSym(self,symItem):
		r'''add the symbolItem to symTable if the name is ok.
		'''
		if symItem.Name in [i.Name for i in self.symList if i.scope==self.currentScope]:
			print '%s is already defined'%symItem.Name
			raise Exception
		self.symList.append(symItem)
	
		
	def getSymbol(self,Name):
		r'''get the symbol by the Name.get the symbol with biggest scope if the name is same
		'''
	
		maxScope=-1
		symItem=None
		for i in self.symList:
			if i.Name==Name and i.scope>maxScope:
				symItem=i
				maxScope=i.scope
		return symItem 
	def removeCurrentScope(self):
		r'''remove all the items whose scope equals currentScope.
			then currentScop-=1
		'''
		totalWidth=0
		newList=[]
		for symItem in self.symList:
			if symItem.scope==self.currentScope:
				totalWidth+=symItem.Width
			else:
				newList.append(symItem)
		self.symList=newList
		self.width-=totalWidth
		oldOffset=self.offset
		needed=self.width
		if needed%16!=0:
			needed=(needed/16+1)*16
		self.offset=needed
		self.currentScope-=1
		return oldOffset-self.offset
			
class Attribute:
	r'''every symbol(V or T) has a Attr
	'''
	
	def __init__(self):
		self.Symbol=None
		self.Name=None
		self.Code=[]
		self.BaseType=None #int void double bool 
		self.StructType=None#ARRAY,VAR,EXP,FUNC
		self.Value=None
		self.Op=None
		self.Typelist=[]
		self.Arglist=[]

class Translate:
	r'''class of translation.
	'''
	
	def __init__(self):
		self.AttrStack=[]
		self.con_string=[]
		self.symTable=symbolTable()
		printfSym=symbolItem()
		printfSym.Name='printf'
		printfSym.Address='printf'
		printfSym.ItemType='FUNC'
		printfSym.scope=self.symTable.currentScope
		scanfSym=symbolItem()
		scanfSym.Name='scanf'
		scanfSym.Address='scanf'
		scanfSym.scope=self.symTable.currentScope	
		scanfSym.ItemType='FUNC'
		self.symTable.addSpecifialSym(printfSym)
		self.symTable.addSpecifialSym(scanfSym)
		self.codeList=None
		self.lableNum=0
		self.avilableRegs={'%eax':True,'%ebx':True,'%ecx':True,'%edx':True,'%edi':True,'%esi':True}
	def addAttr(self,attr):
		self.AttrStack.append(attr)
	
	def newLable(self):
		r'''return new lable.
		'''
		lable='_lable%d'%self.lableNum
		self.lableNum+=1
		return lable

	def getAttrs(self,right):
		r'''get the attris of the symbols in right.
		'''
		rightAttrs=[]
		right.reverse()
		for sym in right:
			attr=self.AttrStack.pop()
			if attr.Symbol!=sym:
				pass
			#	print 'wrong'
			#	raise Exception
			else:
				rightAttrs.append(attr)
		rightAttrs.reverse()	
		right.reverse()
		return rightAttrs
	
	def newScope(self):
		r'''called by the appearance of {
		'''
		self.symTable.currentScope+=1
		
	def translate_AddExp(self,right,rightAttrs,produce):
		r'''tranlate the produce about AddExp.
		return leftAttr if success
		return None otherwise
		'''
		leftAttr=Attribute()
		if produce in ['AddExp->MultipExp','MultipExp->PostfixExp','PostfixExp->PrimaryExp']:
	#		print rightAttrs.keys()
			leftAttr=rightAttrs[0]
		elif produce in ['PrimaryExp->id']:
			name=rightAttrs[0].Name
			symItem=self.symTable.getSymbol(name)
			if symItem==None:
				symItem=self.findFunc(name)
			leftAttr.Name=name
			leftAttr.Value=symItem.Address
			if symItem.ItemType =='VAR':
				leftAttr.BaseType=symItem.VarType
				leftAttr.StructType='VAR'
			elif symItem.ItemType=='FUNC':
				leftAttr.StructType='FUNC'	
					
		elif produce in ['PrimaryExp->INT']:
			name=rightAttrs[0].Name
			leftAttr.Value=int(name)
			leftAttr.StructType='CONSTANT'
			leftAttr.Code=[]
		elif produce in ['PrimaryExp->STRING']:
			name=rightAttrs[0].Name
			no=len(self.con_string)
			leftAttr.Value='$str'+str(no)
			leftAttr.StructType='STRING'
			self.con_string.append(name)
		elif produce in ['PostfixExp->PostfixExp#[#AddExp#]']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			if attr2.StructType!='EXP':
				tempR=self.temp()
				leftAttr.Code.append('mov %s,%s'%(attr2.Value,tempR))
				attr2.Value=tempR
			if attr1.StructType!='VAR':raise Exception
			address=attr1.Value.replace(')',',%s,4)'%attr2.Value.replace('e','r'))	
			leftAttr.Value=self.temp()
			leftAttr.Code.append('mov %s,%s'%(address,leftAttr.Value))		
			self.free(attr2.Value)
			leftAttr.Name='%s[%s]'%(attr1.Name,attr2.Name)
			leftAttr.StructType='VAR'
		elif produce in ['PostfixExp->PostfixExp#++','PostfixExp->PostfixExp#--']:
			attr=rightAttrs[0]
		#	print attr.Symbol,attr.Value,attr.BaseType,attr.StructType
			if attr.StructType!='VAR':
				print '++ or -- should be var'
				raise Exception
			leftAttr=attr
			
			if right[1]=='++':
				leftAttr.Code.append('addl  $0x1,%s'%leftAttr.Value)
			else:
				leftAttr.Code.append('subl  $0x1,%s'%leftAttr.Value)
		elif produce in ['PostfixExp->&#PostfixExp']:
			leftAttr=rightAttrs[1]
			tempR=self.temp()
			leftAttr.Code.append('lea %s,%s'%(leftAttr.Value,tempR.replace('e','r')))
			leftAttr.Value=tempR
			leftAttr.StructType='EXP'
			print '='*30
		elif produce in ['MultipExp->MultipExp#*#PostfixExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr=copy.deepcopy(attr1)#waring!!!!!!!!!!!!!!!!!!!!!!!!
			leftAttr.StructType='EXP'
			leftAttr.Code=attr1.Code+attr2.Code
	
			aList=[attr1,attr2]
			for i in range(len(aList)):
				if aList[i].StructType=='CONSTANT':
					aList[i].Value='$%d'%aList[i].Value
			eaxAttr=None
			notEaxAttr=None
			tempStack=[]
			if attr1.Value!='%eax' and attr2.Value!='%eax':
				if self.getReg('%eax')==False:
					leftAttr.Code.append('push %eax')
					tempStack.append('%eax')
				leftAttr.Code.append('mov %s,%%eax'%attr1.Value)
				self.free(attr1.Value)
				attr1.Value='%eax'

			
			if attr1.Value=='%eax':
				eaxAttr=attr1
				notEaxAttr=attr2
			elif attr2.Value=='%eax':
				eaxAttr=attr2
				notEaxAttr=attr1
					
			if self.getReg('%edx')==False and notEaxAttr.Value!='%edx':
				leftAttr.Code.append('push %edx')
				tempStack.append('%edx')

			leftAttr.Code.append('imul %s,%%eax'%notEaxAttr.Value)
			if '%eax' in tempStack:
				tempR=self.temp()
				leftAttr.Code.append('mov %%eax,%s'%tempR)
				leftAttr.Value=tempR
			else:
				leftAttr.Value='%eax'
			self.free(notEaxAttr.Value)
			if '%edx' not in tempStack:
				self.free('%edx')
			
			tempStack.reverse()	
			for i in tempStack:
				leftAttr.Code.append('pop %s'%i)

		elif produce in ['AddExp->AddExp#+#MultipExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr=copy.deepcopy(attr1) #waring!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			leftAttr.Code=attr1.Code+attr2.Code
			leftAttr.StructType='EXP'
			
			aList=[attr1,attr2]
			for i in range(len(aList)):
				if aList[i].StructType=='CONSTANT':
					aList[i].Value='$%d'%aList[i].Value
			if	attr1.StructType=='EXP':
				leftAttr.Code.append('addl %s,%s'%(attr2.Value,attr1.Value))
				leftAttr.Value=attr1.Value
				self.free(attr2.Value)
			elif attr2.StructType=='EXP':
				leftAttr.Code.append('addl %s,%s'%(attr1.Value,attr2.Value))
				leftAttr.Value=attr2.Value
				self.free(attr1.Value)
			else:
				leftAttr.Value=self.temp()
				leftAttr.Code.append('mov %s,%s'%(attr1.Value,leftAttr.Value))
				leftAttr.Code.append('addl %s,%s'%(attr2.Value,leftAttr.Value))

		elif produce in ['AddExp->AddExp#-#MultipExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr=copy.deepcopy(attr1)
			leftAttr.Code=attr1.Code+attr2.Code
			leftAttr.StructType='EXP'
			
			if attr1.StructType!='EXP':
				temp=self.temp()
				if attr1.StructType=='CONSTANT':
					leftAttr.Code.append('mov $%s,%s'%(attr1.Value,temp))
				else:
					leftAttr.Code.append('mov %s,%s'%(attr1.Value,temp))
				self.free(attr1.Value)
				attr1.Value=temp
			if attr2.StructType=='CONSTANT':
				attr2.Value='$%d'%attr2.Value
			leftAttr.Code.append('subl %s,%s'%(attr2.Value,attr1.Value))
			leftAttr.Value=attr1.Value
			self.free(attr2.Value)	
				
		elif produce in ['MultipExp->MultipExp#/#PostfixExp','MultipExp->MultipExp#%#PostfixExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr=copy.deepcopy(attr1)
			leftAttr.Code=attr1.Code+attr2.Code
			leftAttr.StructType='EXP'

			
			aList=[attr1,attr2]
			for i in range(len(aList)):
				if aList[i].StructType=='CONSTANT':
					aList[i].Value='$%d'%aList[i].Value
	
			tempStack=[]
			if attr1.Value!='%eax':
				if self.getReg('%eax')==False:
					if attr2.Value=='%eax':
						tempR=self.temp()
						leftAttr.Code.append('mov %%eax,%s'%tempR)
						attr2.Value=tempR
					else:
						leftAttr.Code.append('push %eax')
						tempStack.append('%eax')
				leftAttr.Code.append('mov %s,%%eax'%attr1.Value)
				self.free(attr1.Value)
				attr1.Value='%eax'
			if self.getReg('%edx')==False:
				if '%edx'==attr2.Value:
					tempR=self.temp()
					leftAttr.Code.append('mov %%edx,%s'%tempR)
					attr2.Value=tempR
				else:
					leftAttr.Code.append('push %%edx')
					tempStack.append('%edx')
			leftAttr.Code.append('sar $0x1f,%edx')
			if attr2.StructType=='CONSTANT':
				tempR=self.temp()
				leftAttr.Code.append('mov %s,%s'%(attr2.Value,tempR))
				attr2.Value=tempR
			leftAttr.Code.append('divl %s'%attr2.Value)
			not_resultR='%eax'# op is %
			resultR='%edx'
			if right[1]=='/':# op is /
				resultR='%eax'
				not_resultR='%edx'
			
			if resultR in tempStack:
				newR=self.temp()
				leftAttr.Code.append('mov %s,%s'%(resultR,newR))
				leftAttr.Value=newR
			else:
				leftAttr.Value=resultR
			self.free(attr2.Value)
			if not_resultR not in tempStack:
				self.free(not_resultR)
			tempStack.reverse()
			for i in tempStack:
				leftAttr.Code.append('pop %s'%i)

					
		elif produce in ['PrimaryExp->(#Exp#)']:		
			leftAttr=rightAttrs[1]
		else:
			return None
	#	print leftAttr.Code,'='*30
		return leftAttr
				
	def isAvilable(self,reg):
		r'''find if the reg is availble.return True or False
		'''
		return self.avilableRegs[reg]

	def getReg(self,reg):
		r'''get the specified register by marking occupied.
		'''
		if self.avilableRegs[reg]==True:
			self.avilableRegs[reg]=False
			return True
		else:
			return False
				
				
	def temp(self):
		r'''find a avilable register.
		'''
		for i in self.avilableRegs.keys():
			if self.avilableRegs[i]:
				self.avilableRegs[i]=False
				return i		
		else:
			print 'no avilable register'
			raise Exception

	def lock(self,reg):
		r'''mark the reg as occupied.
		'''
		self.avilableRegs[reg]=False

	def free(self,Value):
		r'''if Value is register,then it becomes avilable.
		'''
		if Value in self.avilableRegs.keys():
			self.avilableRegs[Value]=True
	
	def translate_AssignExp(self,right,rightAttrs,produce):
		r'''tranlate the produce about AssignExp.
		return leftAttr if sucess
		return None otherwise
		'''
		leftAttr=Attribute()
		if produce in ['RalExp->AddExp','AssignExp->RalExp','Exp->AssignExp','ExpStmt->;']:
    #       print rightAttrs.keys()
			leftAttr=rightAttrs[0]
		elif produce in ['ExpStmt->Exp#;']:
			leftAttr=rightAttrs[0]
			self.free(leftAttr.Value)
		elif produce in ['AssignExp->PostfixExp#AssignOp#AssignExp']:
			newPro=None
			destAttr=copy.deepcopy(rightAttrs[0])
			opAttr=rightAttrs[1]
			if opAttr.Name=='+=':
				right[1]='+'
				newPro='AddExp->AddExp#+#MultipExp'
				leftAttr=self.translate_AddExp(right,rightAttrs,newPro)
			elif opAttr.Name=='-=':
				right[1]='-'
				newPro='AddExp->AddExp#-#MultipExp'
				leftAttr=self.translate_AddExp(right,rightAttrs,newPro)
			elif opAttr.Name=='*=':
				right[1]='*'
				newPro='MultipExp->MultipExp#*#PostfixExp'
				leftAttr=self.translate_AddExp(right,rightAttrs,newPro)
			elif opAttr.Name=='/=':
				right[1]='/'
				newPro='MultipExp->MultipExp#/#PostfixExp'
				leftAttr=self.translate_AddExp(right,rightAttrs,newPro)
			else:
				leftAttr=rightAttrs[2]
			if leftAttr.StructType=='CONSTANT':
				leftAttr.Code.append('movl $0x%x,%s'%(leftAttr.Value,destAttr.Value))
			else:
				leftAttr.Code.append('mov %s,%s'%(leftAttr.Value,destAttr.Value))
			self.free(leftAttr.Value)
			leftAttr.Value=destAttr.Value
			leftAttr.StructType='VAR'
		elif produce in ['AssignOp->+=','AssignOp->-=','AssignOp->*=','AssignOp->/=']:
			leftAttr=rightAttrs[0]	
		else:
			return None	
		return leftAttr

	def translate_InitExp(self,right,rightAttrs,produce):
		r'''translate the produce about InitDeclaration.
		return leftAttr if sucess
		return None
		'''
		leftAttr=Attribute()
		if produce in ['Declaration->TypeSpecifier#InitDeclarationList#;']:
			leftAttr.BaseType=rightAttrs[0].BaseType
			leftAttr.Code=rightAttrs[1].Code
		elif produce in['TypeSpecifier->void','TypeSpecifier->int','TypeSpecifier->double','TypeSpecifier->bool']:
			leftAttr.BaseType=right[0]
		elif produce in ['InitDeclarationList->InitDeclarator','InitDeclarator->Declarator','InitializerList->Initializer']:
			leftAttr=rightAttrs[0]
		elif produce in ['InitDeclarationList->InitDeclarationList#,#InitDeclarator']:
			leftAttr=rightAttrs[0]
			leftAttr.Code+=rightAttrs[2].Code
		elif produce in ['Initializer->{#InitializerList#}']:
			leftAttr=rightAttrs[1]
		elif produce in ['Declarator->id']:
			attr1=rightAttrs[0]
			leftAttr.Name=attr1.Name
			leftAttr.StructType='VAR'
			if (self.symTable.offset-self.symTable.width)<4:
				leftAttr.Code=['sub $0x10,%rsp']
				self.symTable.offset+=16
			leftAttr.Value=self.symTable.addSymbol('VAR','int',attr1.Name,width=4)
			if leftAttr.Value==None:raise Exception
		elif produce in ['Declarator->id#[#AddExp#]']:
			attr=rightAttrs[2]
			leftAttr.Name=rightAttrs[0].Name
			leftAttr.StructType='ARRAY'
			if 	attr.StructType!='CONSTANT':
				raise Exception
			width=4*int(attr.Value)
			if (self.symTable.offset-self.symTable.width<width):
				needed=width-(self.symTable.offset-self.symTable.width)
				if needed%16!=0:
					needed=(needed/16+1)*16
				self.symTable.offset+=needed
				leftAttr.Code.append('sub $0x%x,%%rsp'%needed)
			leftAttr.Value=self.symTable.addSymbol('VAR','int',leftAttr.Name,width)
		elif produce in ['Initializer->AssignExp']:
			leftAttr=rightAttrs[0]
			leftAttr.Arglist=[leftAttr.Value]
		elif produce in ['InitializerList->Initializer#,#InitializerList']:
			leftAttr=rightAttrs[0]
			leftAttr.Arglist+=rightAttrs[2].Arglist
		elif produce in ['InitDeclarator->Declarator#=#Initializer']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr=copy.deepcopy(attr1)
			leftAttr.Code=attr1.Code+attr2.Code
			if attr1.StructType=='VAR':
				if attr2.StructType=='CONSTANT':
					leftAttr.Code.append('movl $0x%x,%s'%(attr2.Value,attr1.Value))
				elif attr2.StructType=='EXP':
					leftAttr.Code.append('mov %s,%s'%(attr2.Value,attr1.Value))
					self.free(attr2.Value)
				else:
					raise Exception
			elif attr1.StructType=='ARRAY':
				symItem=self.symTable.getSymbol(attr1.Name)	
				if symItem==None:raise Exception
				size=(symItem.Width)/4
				srcList=attr2.Arglist
				print [attr2.Symbol,srcList]
				if srcList and size!=len(srcList):
					print 'wrong len of array'
					raise Exception
				begin=int(eval(re.search('(0x[0-9]*)\(',attr1.Value).group(1)))
				for i in range(size):
					point=hex(begin-i*4)
					destAdd=re.sub('0x[0-9]*',point,attr1.Value)
					leftAttr.Code.append('movl $%s,%s'%(hex(srcList[i]),destAdd))
		else:
			return None
		return leftAttr	
	
	def translate_FunDefi(self,right,rightAttrs,produce):
		r'''translte the produce about Funcion Definition.
		return leftAttr if sucess.
		return None otherwise.
		'''
		leftAttr=Attribute()
		if produce in ['ParamDeclaration->TypeSpecifier#id']:
			leftAttr.Typelist=[rightAttrs[0].BaseType]
			leftAttr.Arglist=[rightAttrs[1].Name]

		elif produce in ['ParamList->ParamDeclaration','ExternalDeclaration->FunDefinition']:
			leftAttr=rightAttrs[0]
		elif produce in ['ParamList->ParamList#,#ParamDeclaration']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr.Typelist=attr1.Typelist+attr2.Typelist
			leftAttr.Arglist=attr1.Arglist+attr2.Arglist
		elif produce in ['FunDeclarator->id#(#ParamList#)','FunDeclarator->id#(#)']:
			attr=rightAttrs[0]
			leftAttr.Name=attr.Name
		
			newSymTable=symbolTable()
			self.symTable.addSymbol('FUNC',None,attr.Name,TablePoint=newSymTable)
			newSymTable.Name=attr.Name
			newSymTable.indexInParent=self.symTable.length()-1
			newSymTable.parentTable=self.symTable
			self.symTable=newSymTable		
			
			if len(right)==4:#FunDeclarator->id ( ParamList )
				leftAttr.Typelist=rightAttrs[2].Typelist
				leftAttr.Arglist=rightAttrs[2].Arglist
				arglist=rightAttrs[2].Arglist
				regList=['%edi','%esi','%edx','%ecx']
				for (index,name) in enumerate(arglist):
					symItem=symbolItem()
					symItem.Name=name
					symItem.ItemType='VAR'
					symItem.Address=regList[index]
					symItem.Width=4			
					symItem.scope=self.symTable.currentScope
					self.symTable.addSpecifialSym(symItem)
					
			elif len(right)==3:#FunDeclarator->id ( )
				leftAttr.Typelist=[]
				leftAttr.Arglist=[]
			else:
				raise Exception
			leftAttr.Code.append('_%s:'%attr.Name)
			leftAttr.Code.append('push %rbp')
			leftAttr.Code.append('mov %rsp,%rbp')
			self.symTable.currentScope-=1
			
		elif produce in ['FunDefinition->TypeSpecifier#FunDeclarator#CompoundStmt']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[1]
			attr3=rightAttrs[2]
			leftAttr.Name=attr2.Name
			leftAttr.BaseType=attr1.BaseType
			leftAttr.StructType='FUNC'
			leftAttr.Typelist=attr2.Typelist
			leftAttr.Arglist=attr2.Arglist
		
			index=self.symTable.indexInParent
			leftAttr.Code=attr2.Code+attr3.Code
			self.symTable=self.symTable.parentTable
			self.symTable.symList[index].VarType=attr1.BaseType
			leftAttr.Code.append('_ret_%s:'%leftAttr.Name)
			leftAttr.Code.append('leave')
			leftAttr.Code.append('ret')	
		else:
			return None
		return leftAttr

	def findFunc(self,funName):
		r'''return funsymitem if exists in all symtable.
		return None if not.
		'''
		table=self.symTable
		while table!=None:
			for i in table.symList:
				if i.Name==funName and i.ItemType=='FUNC':
					return i
			table=table.parentTable

	def translate_FunCall(self,right,rightAttrs,produce):
		r'''
		'''
		leftAttr=Attribute()
		if produce in ['ArgExpList->AssignExp']:
			attr=rightAttrs[0]
			leftAttr.Typelist=[attr.BaseType]			
			leftAttr.Arglist=[attr.Value]
		elif produce in ['ArgExpList->ArgExpList#,#AssignExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			leftAttr.Typelist=attr1.Typelist+[attr2.StructType]
			leftAttr.Arglist=attr1.Arglist+[attr2.Value]
			leftAttr.Code=attr1.Code+attr2.Code
		elif produce in ['PostfixExp->PostfixExp#(#)','PostfixExp->PostfixExp#(#ArgExpList#)']:
			attr1=rightAttrs[0]
			funName=attr1.Name
			funSymItem=self.findFunc(funName)
			if funSymItem==None:
				raise Exception
			funAddress=funSymItem.Address
			regList=['%rdi','%rsi','%rdx','%rcx']
			lowRegList=['%edi','%esi','%edx','%ecx']
			status=dict([(i,self.avilableRegs[i]) for i in lowRegList])
			attr2=Attribute()
			if right[2]=='ArgExpList':
				attr2=rightAttrs[2]
			leftAttr.Code=attr2.Code
			flag=False
			if self.isAvilable('%eax')==False and '%eax' not in attr2.Arglist:
				leftAttr.Code.append('push %rax')
				self.free('%eax')
				flag=True

			if right[2]=='ArgExpList':#PostfixExp->PostfixExp ( ArgExplist )
				for reg in regList:
					leftAttr.Code.append('push %s'%reg)
				for (index,addr) in enumerate(attr2.Arglist):	
					if attr2.Typelist[index]=='EXP':
						addr=addr.replace('e','r')	
					if attr2.Typelist[index]=='CONSTANT':
						leftAttr.Code.append('movl %s,%s'%(addr,regList[index]))
					else:	
						leftAttr.Code.append('mov %s,%s'%(addr,regList[index]))
					self.lock(lowRegList[index])
					if index>3:
						raise Exception
				leftAttr.Code.append('call %s'%funAddress)
				self.lock('%eax')
				for r in lowRegList:
					if status[r]==True:
						self.free(r)
				for add in attr2.Arglist:
					self.free(add)
				regList.reverse()
				for reg in regList:
					leftAttr.Code.append('pop %s'%reg)
				
			else:
				leftAttr.Code.append('call %s'%funAddress)
				self.lock('%eax')
			if flag==True  :
				leftAttr.Value=self.temp()
				leftAttr.Code.append('mov %%eax,%s'%leftAttr.Value)
				leftAttr.Code.append('pop %rax')
			else:
				leftAttr.Value='%eax'

			leftAttr.Name=funName
			leftAttr.BaseType=funSymItem.VarType
			leftAttr.StructType='EXP'
			
			
		else:
			return None
		return leftAttr
		
	def translate_CompoundStmt(self,right,rightAttrs,produce):
		r'''translate produce about Compound stamte  
		'''
		leftAttr=Attribute()
		if produce in ['BlockItemList->BlockItem','BlockItem->Declaration','BlockItem->Stmt']:
			leftAttr=rightAttrs[0]
		elif produce in ['CompoundStmt->{#BlockItemList#}']:
			leftAttr=rightAttrs[1]
		elif produce in ['BlockItemList->BlockItem#BlockItemList']:
			leftAttr.Code=rightAttrs[0].Code+rightAttrs[1].Code
		elif produce in ['Stmt->CompoundStmt']:
			leftAttr=rightAttrs[0]
			remove=self.symTable.removeCurrentScope()
			leftAttr.Code.append('sub $%s,%%rsp'%hex(remove))
		else:
			return None
		return leftAttr

	def translate_RalExp(self,right,rightAttrs,produce):
		r'''translate produce about ralExp.
		'''
		leftAttr=Attribute()
		if produce in ['RalOp-><','RalOp->>','RalOp-><=','RalOp->>=','RalOp->==','RalOp->!=']:
			leftAttr.Name=rightAttrs[0].Name
		elif produce in ['RalExp->AddExp#RalOp#RalExp']:
			attr1=rightAttrs[0]
			attr2=rightAttrs[2]
			op=rightAttrs[1].Name
			
			tempR=None
			leftAttr.Code=attr1.Code+attr2.Code
			
			if not (attr1.StructType=='CONSTANT' and attr2.StructType=='CONSTANT'):
				aList=[attr1,attr2]
				for i in range(len(aList)):
					if aList[i].StructType=='CONSTANT':
						aList[i].Value='$%d'%aList[i].Value
				if attr1.StructType!='EXP' and attr2.StructType!='EXP':
					tempR=self.temp()
					leftAttr.Code.append('mov %s,%s'%(attr1.Value,tempR))
					leftAttr.Code.append('cmp %s,%s'%(attr2.Value,tempR)) #attr1-attr2
					self.free(tempR)
				else:
					leftAttr.Code.append('cmp %s,%s'%(attr2.Value,attr1.Value))
				self.free(attr2.Value)
				self.free(attr1.Value)
			
			if op=='<':
				leftAttr.Code.append('jae bFalse')
			elif op=='>':
				leftAttr.Code.append('jbe bFalse')
			elif op=='<=':
				leftAttr.Code.append('ja bFalse')
			elif op=='>=':
				leftAttr.Code.append('jb bFalse')
			elif op=='==':
				leftAttr.Code.append('jnz bFalse')
			elif op=='!=':
				leftAttr.Code.append('jz bFalse')
			else:
				raise Exception
		else:
			return None
		return leftAttr
		
	def translate_SelectStmt(self,right,rightAttrs,produce):
		
		leftAttr=Attribute()
		if produce in ['Stmt->SelectStmt']:
			leftAttr=rightAttrs[0]
		elif produce in ['SelectStmt->if#(#Exp#)#Stmt']:
			attr1=rightAttrs[2]
			attr2=rightAttrs[4]
			lable=self.newLable()
			attr2.Code.append(lable+':')
			for (index,code) in enumerate(attr1.Code):
				attr1.Code[index]=code.replace('bFalse',lable)
			leftAttr.Code=attr1.Code+attr2.Code
			
		elif produce in ['SelectStmt->if#(#Exp#)#Stmt#else#Stmt']:
			attr1=rightAttrs[2]
			attr2=rightAttrs[4]
			attr3=rightAttrs[6]
		
			print attr1.Code
			print attr2.Code
			print attr3.Code
		#	exit(0)	
			false=self.newLable()
			attr3.Code=[false+':']+attr3.Code
			for (index,code) in enumerate(attr1.Code):
				attr1.Code[index]=code.replace('bFalse',false)
			sNext=self.newLable()
			attr3.Code.append(sNext+':')
			attr2.Code.append('jmp %s'%sNext)
			leftAttr.Code=attr1.Code+attr2.Code+attr3.Code
		else:
			return None
		return leftAttr
	
	def translate_JmpStmt(self,right,rightAttrs,produce):
		leftAttr=Attribute()
		if produce in ['Stmt->JmpStmt']:
			leftAttr=rightAttrs[0]
		elif produce in ['JmpStmt->continue#;']:
			leftAttr.Code.append('jmp loop_begin')
		elif produce in ['JmpStmt->break#;']:
			leftAttr.Code.append('jmp loop_end')
		elif produce in ['JmpStmt->return#;','JmpStmt->return#Exp#;']:
			func_name=self.symTable.parentTable.symList[self.symTable.indexInParent].Name
			ret_add='_ret_%s'%func_name
			if right[1]=='Exp':
				attr=rightAttrs[1]
				if attr.Value!='%eax':
					if attr.StructType=='CONSTANT':	
						leftAttr.Code.append('mov $%s,%%eax'%attr.Value)
					else:
						leftAttr.Code.append('mov %s,%%eax'%attr.Value)
			leftAttr.Code.append('jmp %s'%ret_add)
		else:
			return None
		return leftAttr
	
	def translate_IterationStmt(self,right,rightAttrs,produce):
		leftAttr=Attribute()
		if produce in ['Stmt->IterationStmt']:
			leftAttr=rightAttrs[0]
		elif produce in ['IterationStmt->for#(#Exp#;#Exp#;#Exp#)#Stmt','IterationStmt->for#(#Exp#;#Exp#;#)Stmt']:
			exp1=rightAttrs[2]
			exp2=rightAttrs[4]
			exp3=Attribute()
			exp3.Code=[]
			stmt=None
			if right[6]=='Exp':
				exp3=rightAttrs[6]
				stmt=rightAttrs[8]
			else:
				stmt=rightAttrs[7]
			beginLable=self.newLable()+'for_begin'
			endLable=self.newLable()+'for_end'
			
			for (index,code) in enumerate(exp2.Code):
				exp2.Code[index]=code.replace('bFalse',endLable)
			for (index,code) in enumerate(stmt.Code):
				stmt.Code[index]=code.replace('loop_end',endLable)
				stmt.Code[index]=code.replace('loop_begin',beginLable)
			leftAttr.Code=exp1.Code+['%s:'%beginLable]+exp2.Code+stmt.Code+exp3.Code+['jmp %s'%beginLable,'%s:'%endLable]
		else:
			return None
		return leftAttr	
	def translate_Top(self,right,rightAttrs,produce):
		leftAttr=Attribute()
		if produce in ['Declarations->ExternalDeclaration','ExternalDeclaration','ExternalDeclaration->Declaration','Stmt->ExpStmt']:
			leftAttr=rightAttrs[0]
		elif produce in ['Program->Declarations']:
			self.codeList=['.data']
			for (no,string) in enumerate(self.con_string):
				self.codeList.append('str%d:\t.string\t%s'%(no,string))
			self.codeList+=['.text','.globl\t_start','_start:','\tcall _main','\tmov $1,%eax','\tmov $0,%ebx','\tint $0x80']
			for code in rightAttrs[0].Code:
				if code[0]!='_':
					code='\t'+code
				self.codeList.append(code)
			self.codeList.append('\n')
	#		print '\n'.join(self.codeList)
		elif produce in ['Declarations->Declarations#ExternalDeclaration']:
			leftAttr=rightAttrs[0]
			leftAttr.Code+=rightAttrs[1].Code
		else: 
			return None
		return leftAttr
	def translate(self,left,right):
		r'''translte the produce left->right.
			right is list of symbol
		'''
		leftAttr=Attribute()
		leftAttr.Symbol=left

		produce=left+'->'+'#'.join(right)
	#	print leftAttr.Symbol
	#	print [i.Symbol for i in self.AttrStack	]
		rightAttrs=self.getAttrs(right)
		if produce=='RalExp->AddExp':
		#	print rightAttrs[0].Code
			pass
		while True:
			result=self.translate_AddExp(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_AssignExp(right,rightAttrs,produce)	
			if result:
				break
			result=self.translate_InitExp(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_FunDefi(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_CompoundStmt(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_FunCall(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_Top(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_RalExp(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_SelectStmt(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_JmpStmt(right,rightAttrs,produce)
			if result:
				break
			result=self.translate_IterationStmt(right,rightAttrs,produce)
			break
		if result:leftAttr=result
		leftAttr.Symbol=left	
	#	print leftAttr.Code	
#		print self.avilableRegs	
	#	print [(i.Name,i.scope) for i in self.symTable.symList ]
		self.addAttr(leftAttr)
		
