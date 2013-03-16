#!/usr/bin/env python
raw_V='''
AddExp ArgExpList AssignExp AssignOp BlockItem BlockItemList CompoundStmt  Declaration Declarations Declarator Exp ExpStmt ExternalDeclaration FunDeclarator FunDefinition InitDeclarationList 	InitDeclarator Initializer InitializerList IterationStmt JmpStmt  MultipExp ParamDeclaration ParamList PostfixExp PrimaryExp Program 	RalExp RalOp SelectStmt Stmt TypeSpecifier 
'''

raw_T='''
 != % &  ( ) * *= + ++ += , - -- -= / /=  ; < <= = == > >=   break  continue return  if  else  for while id  bool void  int INT double DOUBLE  STRING CHAR  [ ] {  }
'''
first_V='''Program'''

raw_cfg='''
Program -> Declarations
Declarations -> ExternalDeclaration 
Declarations -> Declarations ExternalDeclaration
ExternalDeclaration -> FunDefinition 
ExternalDeclaration -> Declaration
FunDefinition -> TypeSpecifier FunDeclarator CompoundStmt
TypeSpecifier -> void 
TypeSpecifier -> int
TypeSpecifier -> double
TypeSpecifier -> bool
FunDeclarator -> id ( ParamList ) 
FunDeclarator -> id ( )
ParamList -> ParamDeclaration 
ParamList -> ParamList , ParamDeclaration
ParamDeclaration -> TypeSpecifier id
CompoundStmt -> { BlockItemList }
BlockItemList -> BlockItem 
BlockItemList -> BlockItem BlockItemList
BlockItem -> Declaration 
BlockItem -> Stmt
Declaration -> TypeSpecifier InitDeclarationList ;
InitDeclarationList -> InitDeclarator 
InitDeclarationList -> InitDeclarationList , InitDeclarator
InitDeclarator -> Declarator 
InitDeclarator -> Declarator = Initializer
Declarator -> id
Declarator -> id [ AddExp ]
Initializer -> AssignExp 
Initializer -> { InitializerList }
InitializerList -> Initializer 
InitializerList -> Initializer , InitializerList
Stmt -> CompoundStmt 
Stmt -> ExpStmt 
Stmt -> SelectStmt 
Stmt -> IterationStmt 
Stmt -> JmpStmt
ExpStmt -> ; 
ExpStmt -> Exp ;
SelectStmt -> if ( Exp ) Stmt 
SelectStmt -> if ( Exp ) Stmt else Stmt
IterationStmt -> while ( Exp ) Stmt 
IterationStmt -> for ( Exp ; Exp ; Exp ) Stmt 
IterationStmt -> for ( Exp ; Exp ; ) Stmt
JmpStmt -> continue ;
JmpStmt -> break ; 
JmpStmt -> return ; 
JmpStmt -> return  Exp ;
Exp -> AssignExp 
Exp -> Exp , AssignExp	
AssignExp -> RalExp
AssignExp -> PostfixExp AssignOp AssignExp
RalExp -> AddExp 
RalExp -> AddExp RalOp RalExp
AddExp -> MultipExp 
AddExp -> AddExp + MultipExp 
AddExp -> AddExp - MultipExp
MultipExp -> PostfixExp 
MultipExp -> MultipExp * PostfixExp 
MultipExp -> MultipExp / PostfixExp
MultipExp -> MultipExp % PostfixExp
PostfixExp -> PrimaryExp 
PostfixExp -> PostfixExp [ AddExp ] 
PostfixExp -> PostfixExp ( ) 
PostfixExp -> PostfixExp ( ArgExpList ) 
PostfixExp -> PostfixExp ++ 
PostfixExp -> PostfixExp --
PostfixExp -> & PostfixExp 
ArgExpList -> AssignExp 
ArgExpList -> ArgExpList , AssignExp
PrimaryExp -> id 
PrimaryExp -> INT 
PrimaryExp -> DOUBLE
PrimaryExp -> STRING
PrimaryExp -> CHAR
PrimaryExp -> ( Exp )
RalOp -> < 
RalOp -> > 
RalOp -> <= 
RalOp -> >= 
RalOp -> == 
RalOp -> !=
AssignOp -> = 
AssignOp -> *= 
AssignOp -> /= 
AssignOp -> += 
AssignOp -> -=
'''

