from flask import Flask,jsonify,request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")

db = client.BankAPI
users = db["Users"]

def UserExist(username):
	if users.find({"Username":username}).count()==0:
		return False
	else:
		return True


class Register(Resource):
	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]

		if UserExist(username):
			retJson = {
				"status": 301,
				"msg": "Invalid Username"
			}
			return jsonify(retJson)

		hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

		users.insert({
				"Username":username,
				"Password":hashed_pw,
				"Own": 0,
				"Debt": 0
			})

		retJson = {
			"status":200,
			"msg":"Successfully Signed up for API"
		}

		return jsonify(retJson)

def verifyPw(username, password):
	if not UserExist(username):
		return False

	hashed_pw = users.find({
			"Username":username
		})[0]["Password"]

	if bcrypt.hashpw(password.encode('utf8'),hashed_pw)==hashed_pw:
		return True
	else:
		return False

def cashWithUser(username):
	cash = users.find({
			"Username":username
		})[0]["Own"]

	return cash

def debtWithUser(username):
	debt = users.find({
			"Username":username
		})[0]["Debt"]

	return debt


def generateRetDict(status,msg):
	retJson = {
		"status":status,
		"msg":msg
	}
	return retJson

 # errordict,True/False
def verifyCredentials(username,password):
	if not UserExist(username):
		return generateRetDict(301,"Invalid Username"), True

	correct_pw = verifyPw(username,password)

	if not correct_pw:
		return generateRetDict(302,"Invalid Password"), True

	else:
		return None,False


def updateAccount(username,balance):
	users.update({
			"Username":username
		},{
			"$set":{
				"Own":balance
			}
		})

def updateDebt(username,balance):
	users.update({
			"Username":username
		},{
			"$set":{

				"Debt":balance
			}
		})

class Add(Resource):

	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]
		money = postedData["amount"]


		retJson,error = verifyCredentials(username,password)

		if error:
			return jsonify(retJson)


		if money<=0:
			return jsonify(generateRetDict(304,"Money Can't be negative"))


		cash = cashWithUser(username)
		money-=1
		bank_cash = cashWithUser("BANK")

		updateAccount("BANK",bank_cash+1)

		updateAccount(username,cash+money)

		return jsonify(generateRetDict(200,"Amount Added to account"))



class Trasnfer(Resource):

	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]
		to = postedData["to"]
		money = postedData["amount"]


		retJson,error = verifyCredentials(username,password)

		if error:
			return jsonify(retJson)

		cash = cashWithUser(username)

		if cash<=0:
			return jsonify(generateRetDict(304,"Money Can't be negative"))

		if not UserExist(to):
			return jsonify(generateRetDict(301,"Receiver not found"))

		cash_from = cashWithUser(username)
		cash_to = cashWithUser(to)
		bank_cash = cashWithUser("BANK")
		updateAccount("BANK",bank_cash+1)
		updateAccount(to,cash_to+money-1)
		updateAccount(username,cash_from-money)


		return jsonify(generateRetDict(200,"Amount Trasnfer done!"))



class Balance(Resource):
	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]

		retJson,error = verifyCredentials(username,password)
		if error:
			return jsonify(retJson)


		retJson = users.find({
				"Username":username},
				{
				"Password":0,
				"_id":0
				})[0]


		return jsonify(retJson)



class TakeLoan(Resource):
	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]
		money =    postedData["amount"]

		retJson,error = verifyCredentials(username,password)
		if error:
			return jsonify(retJson)

		cash = cashWithUser(username)
		debt = debtWithUser(username)
		updateAccount(username, cash+money)
		updateDebt(username, debt+money)

		return jsonify(generateRetDict(200,"Loan taken Successfully"))



class PayLoan(Resource):
	def post(self):
		postedData = request.get_json()
		username = postedData["username"]
		password = postedData["password"]
		money =    postedData["amount"]

		retJson,error = verifyCredentials(username,password)
		if error:
			return jsonify(retJson)

		cash = cashWithUser(username)

		if cash < money:
			return jsonify(generateRetDict(303,"Not enough money to pay this moron!"))

		debt = debtWithUser(username)
		updateAccount(username, cash-money)
		updateDebt(username, debt-money)

		return jsonify(generateRetDict(200,"Loan paid Successfully"))



api.add_resource(Register,'/register')
api.add_resource(Add,'/add')
api.add_resource(Trasnfer,'/trasnfer')
api.add_resource(Balance,'/balance')
api.add_resource(TakeLoan,'/takeloan')
api.add_resource(PayLoan,'/payloan')

if __name__=="__main__":
	app.run(host="0.0.0.0")
