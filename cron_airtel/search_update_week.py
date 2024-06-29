import json
import requests
from datetime import timedelta, datetime
import random, os, subprocess
import xmltodict
from xml.etree import ElementTree
from lxml import etree
from databases.Data import *
from config.configurations import *
import pymysql
import sys
import logging as logger
conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
query = f"SELECT source_account_number, trans_ref_no, partID, callback, merchant_ref, cycle_count FROM transactions WHERE created_at >= NOW() + INTERVAL -7 DAY AND created_at <  NOW() + INTERVAL  0 DAY  and financial_institution = 'airtel' and status in ('Pending','Submitted') and trans_type = 'charge' and cycle_count <= 6 order by created_at DESC"
transactions = executeQueryForGetData(conn, query)
ta = len(transactions)
number = 0
if ta > 0:
    for transaction in transactions:
        source_account_number = transaction[0]
        transaction_id = transaction[1]
        partID = transaction[2]
        callback_url = transaction[3]
        paydrc = transaction[4]
        cycle_count = transaction[5]
        generatedAirtelVerif = subprocess.call('sudo php /var/www/html/airtel-cron/verify.php {}'.format(transaction_id),shell=True)
        generatedAirtelVerif = subprocess.call('sudo php /var/www/html/airtel-cron/run.php {}'.format(transaction_id),shell=True)
        try:
            responseAirtel = "response{}.xml".format(transaction_id)
            tree = etree.ElementTree(file=responseAirtel)
            root = tree.getroot()
            r = []
            err = ''
            FinancialInstitutionID = ''
            status = 'Submitted'
            statusDesc = ''
            for ee in root:
                if ee.tag == 'TXNID':
                    FinancialInstitutionID = ee.text
                elif ee.tag == 'TXNSTATUS':
                    status = ee.text
                elif ee.tag == 'MESSAGE':
                    statusDesc = ee.text
            if FinancialInstitutionID != "null":
                if status == 'TS':
                    status = 'Successful'
                elif status == 'TF':
                    status = 'Failed'
                else:
                    sys.exit()
                conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                updatedAt = str(datetime.now())
                cycle_count = cycle_count + 1
                query = "UPDATE transactions SET updated_at = %s, status = %s, financial_institution_transaction_id = %s, financial_institution_status_description = %s, cycle_count = %s WHERE trans_ref_no = %s"
                dataToInsert = (updatedAt, status, FinancialInstitutionID, statusDesc, cycle_count, transaction_id)
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
                status = 'Failed'
                conn = connectToDatabase(host='138.68.158.250', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                updatedAt = str(datetime.now())
                query = "UPDATE transactions SET updated_at = %s, status = %s, financial_institution_status_description = %s, cycle_count = %s  WHERE trans_ref_no = %s"
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
        except:
            pass        
        
