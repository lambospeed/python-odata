#!/usr/bin/python 
#----------------------------------------------------------------------------------------------------------------------------------------------                                  
import pdb
import urlparse
import MySQLdb
import os
import json
import re
import math
import time
#----------------------------------------------------------------------------------------------------------------------------------------------
#Global variables
DATABASE_NAME = 'test'
DATABASE_USER = 'pavan'
SERVICE_PATH_LENGTH = 3
NONE_OBJECT = 'N'
NULL = ''
#----------------------------------------------------------------------------------------------------------------------------------------------
#Canonical Functions exclusively supported by OData. Rest of the functions are supported by MySQL
def substitute(ele):
	ele = ele.strip()
	index = ele.find('(')
	
	if(index == -1):
		return None
	
	name = ele[:index].lower()
	args = ele[index+1:-1]

	if(name == 'contains'):
		arg1,arg2 = args.split(',')
		return arg1 + ' like ' + '\'' + '%' + arg2[1:-1] + '%' + '\''
	
	elif(name == 'startswith'):
		arg1,arg2 = args.split(',')
		return arg1 + ' like ' + '\'' + arg2[1:-1] + '%' + '\''

	elif(name == 'endswith'):
		arg1,arg2 = args.split(',')
		return arg1 + ' like ' + '\'' + '%' + arg2[1:-1] + '\''

	elif(name == 'indexof'):
		return 'INSTR' + ele[index:]

	elif(name == 'islower'):
		return args + ' = ' + 'LOWER' + ele[index:] 

	elif(name == 'isupper'):
		return args + ' = ' + 'UPPER' + ele[index:]

	elif(name == 'currentdate'):
		return 'DATE' + '(' + 'NOW()' + ')'

	elif(name == 'currenttime'):
		return 'TIME' + '(' + 'NOW()' + ')'

def functionEvaluator(exp):
	exp = exp.strip()
	parts = exp.split(' ')
	result = []

	for p in parts:
		s = substitute(p)
		if(s == None):
			result.append(p)
		else:
			result.append(s)

	return ' '.join(result)

def evaluate_expression(exp):

	exp = re.sub('%20',' ',exp)
	exp = re.sub('%27','\'',exp)
	exp = re.sub('%28','(',exp)
	exp = re.sub('%29',')',exp)
	exp = re.sub(' eq ',' = ',exp)
	exp = re.sub(' ne ',' != ',exp)
	exp = re.sub(' gt ',' > ',exp)
	exp = re.sub(' ge ',' >= ',exp)
	exp = re.sub(' lt ',' < ',exp)
	exp = re.sub(' le ',' <= ',exp)

	exp = re.sub(' add ',' + ',exp)
	exp = re.sub(' sub ',' - ',exp)
	exp = re.sub(' mul ',' * ',exp)
	exp = re.sub(' div ',' / ',exp)
	exp = re.sub(' mod ',' % ',exp)

	
	return exp

def evaluate(exp):
	exp = evaluate_expression(exp)
	return functionEvaluator(exp)
#---------------------------------------------------------------------------------------------------------------------------------------------
#Different formats of printing
def removeEmptyStrings(lis):
	if(lis == []):
		return lis

	if(lis[0] == ""):
		lis = lis[1:]
		return lis

	if(lis[-1] == ""):
		lis = lis[:-1]
	
	return lis

def getString(str1):
	if(str1[0] == "'"):
		return str1[1:-1]
	else:
		return str1

def inHTMLFormat(column_names,result):
	col_list = column_names.split(';')
	col_list = removeEmptyStrings(col_list)
	rows_list = result.split(';')
	rows_list = removeEmptyStrings(rows_list)

	print "Content-Type: text/html"
	print

	row_no = 0

	for res in rows_list:
		row = res[1:-1].split(',')
		col_no = 0
		print 'Row ' + str(row_no+1) + '<br>'
		
		for col in col_list:
			print col + ': ' + row[col_no]
			print '<br>'
			col_no = col_no + 1;
		
		print '<br>'
		row_no = row_no + 1
	if(len(rows_list) == 0):
		print 'HTTP_STATUS 404'
	else:
		print 'HTTP_STATUS 200'

def inJSONFormat(column_names,result):
	col_list = column_names.split(';')
	col_list = removeEmptyStrings(col_list)
	rows_list = result.split(';')
	rows_list = removeEmptyStrings(rows_list)
	
	lis = []

	for res in rows_list:
		row = res[1:-1].split(',')
		col_no = 0
		dic = {}

		for col in col_list:
			dic[col] = row[col_no]
			col_no = col_no + 1;

		lis.append(dic)
	if(len(lis) == 0):
		lis.append({'HTTP_STATUS':404})
	else:
		lis.append({'HTTP_STATUS':200})

	obj = json.dumps(lis)

	print "Content-Type: application/json"
	print
	print obj

def inXMLFormat(column_names,result):
	col_list = column_names.split(';')
	col_list = removeEmptyStrings(col_list)
	rows_list = result.split(';')
	rows_list = removeEmptyStrings(rows_list)
	
	row_no = 0
	
	print "Content-Type: text/xml"
	print
	print '<?xml version="1.0" encoding="UTF-8"?>'
	print '<Database>'
	
	for res in rows_list:
		row = res[1:-1].split(',')
		row = removeEmptyStrings(row)
		col_no = 0

		print '<row ID="'+str(row_no+1)+'">' 		

		for col in col_list:
			col = getString(col)
			print '<'+col +'>' + row[col_no] + '</'+ col +'>'		
			col_no = col_no + 1
		
		row_no = row_no + 1
		print '</row>'

	if(len(rows_list) == 0):
		print '<HTTP_STATUS>' + '404' + '</HTTP_STATUS>'
	else:
		print '<HTTP_STATUS>' + '200' + '</HTTP_STATUS>' 
	
	print '</Database>'
#---------------------------------------------------------------------------------------------------------------------------------------------
#URL related functions 
def splitURL(url):
	return urlparse.urlparse(url)	

def getService(path,size):
	path = path[1:]
	strlist = path.split('/')

	return '/'.join(strlist[:size])

def getResource(path,size):
	path = path[1:]
	strlist = path.split('/')

	return '/'.join(strlist[size:])

def getURL():
	host = os.environ['HTTP_HOST']
	request = os.environ['REQUEST_URI']
	
	return 'http://' + host + request

def getResourceAndKey(reslist):
	result = []

	for res in reslist:
		start_pos = res.find('(')
		end_pos = len(res) - res[::-1].find(')') - 1

		if(start_pos == -1 or end_pos == -1): 
			result.append((res,'noarg'))

		else:
			result.append((res[:start_pos],res[start_pos+1:end_pos]))

	return result

def createQueryDict(query):
	dic = {}

	if(query == NULL):
		return dic

	lis = query.split('&')

	for ele in lis:
		system_query,expression = ele.split('=')
		dic[system_query] = expression
	
	return dic

def startURL():
	url = getURL()
	urlparts = splitURL(url)

	service = getService(urlparts.path[1:],SERVICE_PATH_LENGTH)
	resource =  getResource(urlparts.path[1:],SERVICE_PATH_LENGTH)

	reslist = resource.split('/')
	res_key_list = getResourceAndKey(reslist)

	return res_key_list,urlparts
#----------------------------------------------------------------------------------------------------------------------------------------------
#SQL related functions
def errorHandlerForSQL(cursor,sqlquery,primaryKey=0):
	error = NULL
	if(primaryKey == 1):
		cursor.execute(sqlquery)
		pk = cursor.fetchone()
		if(pk == None):	
			error = error + '(' + 'PRIMARY KEY does not exist for the resource' + ',' + 'Check the resource' + ')' + ';'
			return cursor,error,NONE_OBJECT
		else:
			return cursor,error,pk
	try:	
		cursor.execute(sqlquery)	
	except MySQLdb.DataError, e:
		error = error + '(' + 'DATA ERROR-numeric value out of range or division by zero' + ')' + ';'
	except MySQLdb.IntegrityError, e:
		error = error + '(' + 'INTEGRITY ERROR-relational integrity is not adhered to' + ')' + ';'
	except MySQLdb.OperationalError, e:
		error = error + '(' + 'OPERATIONAL ERROR-unexpected disconnect or data source not found'+ ')' + ';'
	except MySQLdb.ProgrammingError, e:
		error = error + '(' + 'PROGRAMMING ERROR-table not found or already exists or a wrong number of parameters is given'')' + ';'
	except MySQLdb.Error, e:
		error = error + '(' + 'GENERAL ERROR'+')' + ';'
	
	return cursor,error

def getPrimaryKey(res):
	cursor,db = startDatabase('INFORMATION_SCHEMA',DATABASE_USER)
	sqlquery = "select column_name from key_column_usage where constraint_name = 'Primary' and table_name = " + "\'" + res + "\'"
	cursor,error,pk = errorHandlerForSQL(cursor,sqlquery,1)
	db.close()

	return pk[0],error

def getSelect(query_dict):
	select_clause = 'select '
	
	if(query_dict == {}):
		return 'select *'
	
	elif('$select' not in query_dict.keys()):
		return 'select *'

	elif(query_dict['$select'].strip() == '*'):
		return 'select *'

	else:
		return select_clause + query_dict['$select'].strip()

def getFrom(res_key_list):
	from_clause = 'from '	
	l = len(res_key_list[:-1])

	for res_index in range(l):
		res = res_key_list[res_index]
		from_clause = from_clause + res[0] + ','
		
	from_clause = from_clause + res_key_list[-1][0]

	return from_clause

def getWhere(res_key_list,query_dict):
	where_clause = 'where '
	l = len(res_key_list)
	
	for res_index in range(l-1):
		res = res_key_list[res_index]
		res_next = res_key_list[res_index+1]
		value = getValue(res[1]) 
		primaryKey,error1 = getPrimaryKey(res[0])
		if(error1 != NULL):
			return NULL,error1
		
		if(value != 'noarg'):
			where_clause = where_clause + res[0] + '.' + primaryKey + '=' + value + ' and '
		if(primaryKey != None):
			where_clause = where_clause + res[0] + '.' + primaryKey + '=' + res_next[0] + '.' + primaryKey + ' and '

	res = res_key_list[-1]
	value = getValue(res[1])
	if(value != 'noarg'):
		primaryKey,error2 = getPrimaryKey(res[0])
		if(error2 != NULL):
			return NULL,error2
	
	if(l != 1):
		if(value != 'noarg'): 
			where_clause = where_clause + res[0] + '.' + primaryKey + '=' + value
		elif(query_dict != {} and '$filter' in query_dict.keys()):
			where_clause = where_clause + evaluate(query_dict['$filter'])
		else:
			where_clause = where_clause[:-5]
	else:
		if(value != 'noarg'): 
			where_clause = where_clause + res[0] + '.' + primaryKey + '=' + value
		elif(query_dict != {} and '$filter' in query_dict.keys()):
			where_clause = where_clause + evaluate(query_dict['$filter'])
		else:
			where_clause = NULL
	
		
	return where_clause,NULL

def getOrderBy(query_dict):
	if(query_dict == {}):
		return NULL
	
	elif('$orderby' in query_dict.keys()):
		return ' order by ' + query_dict['$orderby']	

	else:
		return NULL

def getSQLQuery(res_key_list,query_dict):
	select_clause = getSelect(query_dict)
	from_clause = getFrom(res_key_list)
	where_clause,error = getWhere(res_key_list,query_dict)
	orderby_clause = getOrderBy(query_dict)

	if(error != NULL):
		return NULL,error
	else:
		return select_clause + '\n' + from_clause + '\n' + where_clause + '\n' + orderby_clause,NULL

def startDatabase(dbname,username):
	db = MySQLdb.connect(host = 'localhost', user = username , db = dbname )
	cursor = db.cursor()

	return cursor,db 

def startSQL(res_key_list,query_dict):
	cursor,db = startDatabase(DATABASE_NAME,DATABASE_USER)	
	sqlquery,primaryKeyError = getSQLQuery(res_key_list,query_dict)
	
	if(primaryKeyError != NULL):
		return cursor,db,primaryKeyError
	else:
		cursor,error = errorHandlerForSQL(cursor,sqlquery)		
		return cursor,db,error	

def getValue(string):
	if(string == 'noarg'):
		return string
	elif(string.isdigit()): 
		return string
	else:
		return '\'' + string + '\''

def getColumnNames(res_key_list,query_dict):
	data = NULL	

	if(query_dict != {} and '$select' in query_dict.keys()):
		sel_col_names =	query_dict['$select'].split(',')
		for col in sel_col_names:
			data = data + col + ';'
		return data

	cursor,db = startDatabase('INFORMATION_SCHEMA',DATABASE_USER)

	for res_key in res_key_list:
		sqlquery = "select COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = " + "\'" + res_key[0] + "\'"
		cursor,error = errorHandlerForSQL(cursor,sqlquery)
		temp = GET(cursor,[])
		temp = [res_key[0]+'.'+i[2:-3] for i in temp.split(";") if i != ""]
		data = data + ';'.join(temp) + ';'

	db.close()

	return data		
#----------------------------------------------------------------------------------------------------------------------------------------------
#Read functionalities
def GET(cursor,sel_col_names,noofrows=-1):
	data = NULL

	while(True):
		temp = cursor.fetchone()
		if(temp == None or noofrows == 0):
			break
		elif((sel_col_names != [] and temp[1:-2] in sel_col_names) or sel_col_names == []):
			data = data + str(temp) + ";"
			noofrows = noofrows - 1

	return data
#----------------------------------------------------------------------------------------------------------------------------------------------
#Driver functions
def printInFormat(query_dict,column_names,result):
	if(query_dict == {}):
		inJSONFormat(column_names,result)
	elif('$format' not in query_dict.keys()):
		inJSONFormat(column_names,result)	
	elif(query_dict['$format'].lower() == 'html'):	
		inHTMLFormat(column_names,result)
	elif(query_dict['$format'].lower() == 'xml'):
		inXMLFormat(column_names,result)
	elif(query_dict['$format'].lower() == 'json'):
		inJSONFormat(column_names,result)
	else:
		print "Content-Type: text/html"
		print
		print 'FORMAT ERROR: Specify Format Correctly'
		print '<br><br>HTTP_STATUS: 404'
	
def delegateResponsibilityToSQL(res_key_list,urlparts):
	query_dict = createQueryDict(urlparts.query)
	res = getResource(urlparts.path,SERVICE_PATH_LENGTH)
	
	if(res == ""):
		cursor,db = startDatabase('INFORMATION_SCHEMA',DATABASE_USER)
		cursor.execute("select TABLE_NAME,COLUMN_NAME from COLUMNS where table_schema =" + "\'" + DATABASE_NAME + "\'")
		result = GET(cursor,[])	
		db.close()
		column_names = 'Table;Column'

	elif(res == '$all'):
		cursor,db = startDatabase('INFORMATION_SCHEMA',DATABASE_USER)			
		cursor.execute("select table_name from tables where table_schema =" + "\'" + DATABASE_NAME + "\'")
		result = GET(cursor,[])	
		db.close()
		column_names = 'Table'	
	
	elif((urlparts.path).split('/')[-1] == '$count'):
		cursor,db,error = startSQL(res_key_list[:-1],query_dict)
		if(error != NULL):
			column_names = "Error"
			result = error
		else:
			records = GET(cursor,[])
			db.close()
			result = '(' + str(len(records.split(';')) - 1) + ')'
			column_names = 'Count'

	else:
		cursor,db,error = startSQL(res_key_list,query_dict)
		if(error != NULL):
			column_names = "Error"
			result = error
		else:
			if(query_dict != {} and '$top' in query_dict.keys()):
				result = GET(cursor,[],eval(query_dict['$top']))
			else:
				result = GET(cursor,[])
			db.close()
			column_names = getColumnNames(res_key_list,query_dict)	
	
	return query_dict,column_names,result
#----------------------------------------------------------------------------------------------------------------------------------------------	
def main():
	res_key_list,urlparts = startURL()
	query_dict,column_names,result = delegateResponsibilityToSQL(res_key_list,urlparts)
	printInFormat(query_dict,column_names,result)	
#----------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	main()
#----------------------------------------------------------------------------------------------------------------------------------------------
