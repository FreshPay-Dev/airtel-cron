import json
import requests
from datetime import timedelta, datetime
import random, os, subprocess
from databases.Data import *
from config.configurations import *
import pymysql
import logging as logger
import datetime
from decimal import *



BASE_URL="https://openapi.airtel.africa"
url = "/auth/oauth2/token"
HEADERS = {
    'Content-Type': 'application/json'
    }
url = "/auth/oauth2/token"


def GetToken():
    payload = json.dumps({
    "client_id": "9918cbf7-38fe-4111-9518-ae179c7731e7",
    "client_secret": "43579758-72d4-498e-96dd-2f76bc4319f0",
    "grant_type": "client_credentials"
    })
    curl_command = [
        'curl',
        '-X', 'POST',  
        BASE_URL+url,  
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: /',
        '-d', payload 
            ]
    reponse=subprocess.run(curl_command,capture_output=True,text=True)
    if reponse.returncode == 0:
        repo=json.loads(reponse.stdout)
        return repo.get('access_token')
    else:
          logger.info("Erreur lors de l'exécution de la commande curl")
        #eturn repo["access_token"]
    
    response = requests.request("POST",BASE_URL+url, headers=HEADERS, data=payload)
    repo=response.json()
    return repo["access_token"]

conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
query = f"SELECT source_account_number, trans_ref_no, currency, callback, merchant_ref, cycle_count FROM transactionMigration WHERE financial_institution = 'airtel' and  (status = 'Pending' or status = 'Submitted') and trans_type = 'charge' and DATE(created_at) = DATE(SUBDATE(NOW(),0))"
transactions = executeQueryForGetData(conn, query)
ta = len(transactions)
logger.info(transactions)

number = 0
if ta > 0:
    for transaction in transactions:
        source_account_number = transaction[0]
        transaction_id = transaction[1]
        currency = transaction[2]
        callback_url = transaction[3]
        paydrc = transaction[4]
        cycle_count = transaction[5]

        token=GetToken()
        headers = {
        'Accept': '/',
        'X-Country': 'CD',
        'X-Currency': currency,
        'Authorization': 'Bearer '+token
        
        }
        
        
        try:
            urlxx = "https://openapi.airtel.africa/standard/v1/payments/{}".format(transaction_id)
            
             # La commande curl que vous voulez exécuter
            curl_command = [
            'curl',
            '-X', 'GET',  
            urlxx,  
            '-H', 'Content-Type: application/json',
            '-H', 'Accept: /',
            '-H', 'X-Country: CD',
            '-H', 'X-Currency: '+currency,
            '-H', 'Authorization: Bearer '+ token
                ]
            #r = requests.get(urlxx, headers = headers)
            #financial_institution_transaction_id =r.json()

            r=subprocess.run(curl_command,capture_output=True,text=True)
            data=r.stdout
            repo=json.loads(data)
            financial_institution_transaction_id =repo
            if r.returncode == 0:
               
                print(financial_institution_transaction_id)
                FinancialInstitutionStatusCode =financial_institution_transaction_id['status']['code']
                FinancialInstitutionReponseCode =financial_institution_transaction_id['status']['response_code']
                statusDesc =financial_institution_transaction_id['data']['transaction']['message']
                FinancialInstitutionID =financial_institution_transaction_id['data']['transaction']['airtel_money_id']
                status=financial_institution_transaction_id['data']['transaction']['status']
                
                if FinancialInstitutionID != "null":
                    if  status== 'TS':
                        status = 'Successful'
                    elif status == 'TF':
                        status = 'Failed'
                    
                    cycle_count = cycle_count + 1
                    updatedAt = str(datetime.datetime.now())
                    print(updatedAt)
                    queryx = "UPDATE transactionMigration SET updated_at = %s, status = %s, financial_institution_transaction_id = %s, financial_institution_status_description = %s, cycle_count = %s WHERE trans_ref_no = %s"
                    dataToInsertx = (updatedAt, status, FinancialInstitutionID, statusDesc, cycle_count, transaction_id)
                    conn1 = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                    updatedToSwitch = executeQueryForInsertDate(conn1, queryx, dataToInsertx)
                    

                    if callback_url != None:
                        dataToSend = {
                            "action":"debit",
                            "switch_reference" : transaction_id,
                            "telco_reference" : FinancialInstitutionID,
                            "status" : status,
                            "paydrc_reference" : paydrc,
                            "telco_status_description" : statusDesc
                        }
                        headers = {"Content-Type" : "application/json"}
                        response = requests.post(url=callback_url, headers=headers, data=json.dumps(dataToSend))
                
                elif FinancialInstitutionID == "null" and status!= "null":
                    if  status== 'TS':
                        status = 'Successful'
                    elif status == 'TF':
                        status = 'Failed'
                    
                    cycle_count = cycle_count + 1
                    updatedAt = str(datetime.datetime.now())
                    print(updatedAt)
                    queryx = "UPDATE transactionMigration SET updated_at = %s, status = %s, financial_institution_transaction_id = %s, financial_institution_status_description = %s, cycle_count = %s WHERE trans_ref_no = %s"
                    dataToInsertx = (updatedAt, status, FinancialInstitutionID, statusDesc, cycle_count, transaction_id)
                    conn1 = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                    updatedToSwitch = executeQueryForInsertDate(conn1, queryx, dataToInsertx)
                    

                    if callback_url != None:
                        dataToSend = {
                            "action":"debit",
                            "switch_reference" : transaction_id,
                            "telco_reference" : FinancialInstitutionID,
                            "status" : status,
                            "paydrc_reference" : paydrc,
                            "telco_status_description" : statusDesc
                        }
                        headers = {"Content-Type" : "application/json"}
                        response = requests.post(url=callback_url, headers=headers, data=json.dumps(dataToSend))
                elif FinancialInstitutionID == "null" and cycle_count >= 6:
                    status = 'Failed'
                    conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                    updatedAt = str(datetime.datetime.now())
                    
                    query = "UPDATE transactionMigration SET updated_at = %s, status = %s, financial_institution_status_description = %s, cycle_count = %s  WHERE trans_ref_no = %s and DATE(created_at) = DATE(SUBDATE(NOW(),0))"
                    dataToInsert = (updatedAt, status, statusDesc, cycle_count, transaction_id)
                    updatedToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
                    if callback_url != None:
                        dataToSend = {
                            "action":"debit",
                            "switch_reference" : transaction_id,
                            "telco_reference" : FinancialInstitutionID,
                            "status" : status,
                            "paydrc_reference" : paydrc,
                            "telco_status_description" : statusDesc
                        }
                        headers = {"Content-Type" : "application/json"}
                        response = requests.post(url=callback_url, headers=headers, data=json.dumps(dataToSend))
                        print(response.json())
                    
                elif FinancialInstitutionID == "null":
                    status = 'Pending'
                    conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                    updatedAt = str(datetime.datetime.now())
                    cycle_count = cycle_count+1
                    query = "UPDATE transactionMigration SET updated_at = %s, status = %s, financial_institution_status_description = %s, cycle_count = %s  WHERE trans_ref_no = %s"
                    dataToInsert = (updatedAt, status, statusDesc, cycle_count, transaction_id)
                    updatedToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
                    #if callback_url != None:
                    #    dataToSend = {
                    #        "action":"debit",
                    #        "switch_reference" : transaction_id,
                    #        "telco_reference" : FinancialInstitutionID,
                    #        "status" : status,
                    #        "paydrc_reference" : paydrc,
                    #        "telco_status_description" : statusDesc
                    #    }
                    #    headers = {"Content-Type" : "application/json"}
                    #    response = requests.post(url=callback_url, headers=headers, data=json.dumps(dataToSend))
                    #    print(response.json())    
        except Exception as e:
            logger.info(e)
            pass