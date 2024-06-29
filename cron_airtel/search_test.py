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
import logging as logger

conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
query = f"SELECT account_number, trans_ref_no, partID, callback, merchant_ref, trans_type FROM transactions WHERE DATE(created_at) = DATE(SUBDATE(NOW(), 0)) and financial_institution = 'orange' and `status` = 'Pending'"
transactions = executeQueryForGetData(conn, query)
ta = len(transactions)

number = 0
if ta > 0:
    for transaction in transactions:
        account_number = transaction[0]
        transaction_id = transaction[1]
        partID = transaction[2]
        callback_url = transaction[3]
        paydrc = transaction[4]
        if transaction[5] == 'charge':
            trans_type = 'debit'
        if transaction[5] == 'payout':
            trans_type = 'credit'
        
        generatedOrangeVerif = subprocess.call('php verify.php {} {} {}'.format(transaction_id, partID, account_number),shell=True)
        generatedOrangeVerif = subprocess.call('php run.php {}'.format(transaction_id),shell=True)

        try:
            responseOrange = "response{}.xml".format(transaction_id)
            tree = etree.ElementTree(file=responseOrange)
            root = tree.getroot()
            r = []
            resultCode = ''
            refPayement = ''
            resultDesc = ''
            status = 'Pending'
            statusDesc = ''

            for ee in root:
                if ee.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body":
                    for eee in ee.getchildren():
                        if eee.tag == "{http://services.ws1.com/}doCheckTransResponse":
                            for s in eee.getchildren():
                                if s.tag == "return":
                                    for rr in s.getchildren():
                                        if rr.tag == 'resultCode':
                                            if rr.text == "60019":
                                                status = 'Failed'
                                                resultCode = "60019"
                                            elif rr.text == "00332":
                                                status = 'Failed'
                                                resultCode = "00332"
                                        if rr.tag == 'resultDesc':
                                            resultDesc = rr.text
                                        if rr.tag == 'refPayment':
                                            refPayement = rr.text
                                        if rr.tag == 'txnstatus':
                                            if rr.text == '200':
                                                resultCode = "200"
                                                status = 'Successful'
                                                statusDesc = rr.text

            if resultCode == "00332":
                motif = resultDesc.find("transaction:")
                taille = len(resultDesc)
                FinancialInstitutionID = resultDesc[motif+13:taille-1]
            if resultCode == "60019":
                motif = resultDesc.find("transaction:")
                taille = len(resultDesc)
                FinancialInstitutionID = resultDesc[motif+13:taille-1]    
            if resultCode == "200":
                FinancialInstitutionID = refPayement
            

            if status == "Successful":
                conn = connectToDatabase(host='167.172.169.188', user='jbiola', password='gofreshbakeryproduction2020jb', db='switch', port=3306)
                updatedAt = str(datetime.now())
                query = "UPDATE transactions SET updated_at = %s, status = %s, financial_institution_transaction_id = %s, financial_institution_status_code = %s, financial_institution_status_description = %s WHERE trans_ref_no = %s"
                dataToInsert = (updatedAt, status, FinancialInstitutionID, resultCode, resultDesc, transaction_id)
                updatedToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)

                switch_reference = transaction_id
                telco_reference = FinancialInstitutionID
                status = status
                paydrc_reference = paydrc
                action = trans_type
                telco_status_description = resultDesc

                conn = connectToDatabase(host='161.35.29.153', user='root', password='gofreshbakeryproduction2020jb', db='gofreshdev_mer', port=3306)
                query = f"UPDATE drc_send_money_transac SET updated_at = '{date_updated}', status = '{status}', switch_reference = '{switch_reference}', telco_reference = '{telco_reference}', status_description = '{telco_status_description}' WHERE paydrc_reference = '{paydrc_reference}'"

                dataToInsert = (updatedAt, status, switch_reference, telco_reference, resultDesc, transaction_id)
                updatedToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)

                
            elif status == "Pending":
                conn = connectToDatabase(host='161.35.29.153', user='root', password='gofreshbakeryproduction2020jb', db='gofreshdev_mer', port=3306)
                updatedAt = str(datetime.now())
                query = "UPDATE transactions SET updated_at = %s, cycle_count = %s WHERE trans_ref_no = %s"
                dataToInsert = (updatedAt, cycle_count, transaction_id)
                updatedToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)

        except:
            pass
        
