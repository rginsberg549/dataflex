from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
import pandas as pd
import os

class Home(TemplateView):
    template_name = 'home.html'

def paul_chopra_upload(request):
    if request.method == 'POST':
        control_sheet = request.FILES['control_sheet_upload']
        control_sheet_df = pd.read_excel(control_sheet)
        
        report_group = request.FILES['report_group_upload']
        report_group_df = pd.read_excel(report_group)

        control_sheet_df.columns = control_sheet_df.iloc[2]
        control_sheet_df.drop(control_sheet_df.index[0:3],inplace=True)
        control_sheet_df = control_sheet_df.reset_index(drop=True)
        control_sheet_df = control_sheet_df.infer_objects()

        report_group_df.columns = report_group_df.iloc[6]
        report_group_df.drop(report_group_df.index[0:7],inplace=True)
        report_group_df = report_group_df.reset_index(drop=True)
        report_group_df = report_group_df[~report_group_df['Store'].str.contains("Total")]
        report_group_df = report_group_df[~report_group_df['Store'].str.contains("GRAND TOTAL")]

        if 'Tender APP' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender APP'] = 0
    
        if 'Tender RewardsCard' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender RewardsCard'] = 0

        if 'Tender OTHER A/R' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender OTHER A/R'] = 0
    


        roy_faf_ipc_df = control_sheet_df.copy(deep=True)
        roy_faf_ipc_df = roy_faf_ipc_df[[ 'Store Number',
                                            'Date',
                                            'Cashcards',
                                            'Cash Card Sales',
                                            'Catering Call Center',
                                            'PayPal',
                                            'Unit Sales',
                                            'Drinks Sales',
                                            'Misc Sales' ]]

        roy_faf_ipc_df= roy_faf_ipc_df.groupby(['Store Number'], as_index=False).sum()
        roy_faf_ipc_df['Total Sales'] = roy_faf_ipc_df['Unit Sales'] + roy_faf_ipc_df['Drinks Sales'] + roy_faf_ipc_df['Misc Sales']
        roy_faf_ipc_df['Royalty'] = roy_faf_ipc_df['Total Sales'] * .08
        roy_faf_ipc_df['Faf'] = roy_faf_ipc_df['Total Sales'] * .045
        roy_faf_ipc_df['Commission'] = roy_faf_ipc_df['Cash Card Sales'] * .025
        roy_faf_ipc_df['Fees'] = ((roy_faf_ipc_df['Catering Call Center'] * .07) + (roy_faf_ipc_df['Cashcards'] * .025) + (roy_faf_ipc_df['PayPal'] * .02))
        roy_faf_ipc_df['Net IPC'] = roy_faf_ipc_df['Catering Call Center'] + roy_faf_ipc_df['Cashcards'] - roy_faf_ipc_df['Cash Card Sales'] + roy_faf_ipc_df['Commission'] - roy_faf_ipc_df['Fees'] + roy_faf_ipc_df['PayPal']
        roy_faf_ipc_df['Cash Card Sales Commission'] = roy_faf_ipc_df['Cash Card Sales'] * .025
        roy_faf_ipc_df['Cash Card Redeemed Fee 2.5%'] = roy_faf_ipc_df['Cashcards'] * .025
        roy_faf_ipc_df['Paypal Fee 2%'] = roy_faf_ipc_df['PayPal'] * .02
        roy_faf_ipc_df['7% Call Center'] = roy_faf_ipc_df['Catering Call Center'] * .07
        roy_faf_ipc_df = roy_faf_ipc_df.round(4)

        delivery_data_df = report_group_df.copy(deep=True)
        delivery_data_df = delivery_data_df.infer_objects()
        delivery_data_df = delivery_data_df[[   'Date',
                                                'Store',
                                                'Tender Amex',
                                                'Tender APP',
                                                'Tender Cash',
                                                'Tender CashCard',
                                                'Tender Catering Center',
                                                'Tender DEL-DOORDASH',
                                                'Tender DEL-Grubhub',
                                                'Tender DEL-Postmates',
                                                'Tender DEL-UberEatS',
                                                'Tender Discover',
                                                'Tender EBT',
                                                'Tender MasterCard',
                                                'Tender No Tender Type',
                                                'Tender PayPal',
                                                'Tender RewardsCard',
                                                'Tender VISA',
                                                'Tender OTHER A/R']]

        delivery_data_df['Daily Delivery Sum'] = delivery_data_df['Tender DEL-DOORDASH'] + delivery_data_df['Tender DEL-Grubhub'] + delivery_data_df['Tender DEL-Postmates'] + delivery_data_df['Tender EBT']
        delivery_data_df['Other'] = delivery_data_df['Tender EBT']
        delivery_data_df = delivery_data_df.groupby(['Date','Store'], as_index=False).sum()
            
        trnsid = 'WCS-' + control_sheet_df['Store Number']
        delivery_trnsid = 'WCS-' + delivery_data_df['Store']
        class_list = control_sheet_df['Store Number']
        delivery_class_list = delivery_data_df['Store']
        date_list = control_sheet_df['Date']
        delivery_date_list = delivery_data_df['Date']
        class_list = control_sheet_df['Store Number']
        delivery_class_list = delivery_data_df['Store']
        store_number = control_sheet_df['Store Number']
        delivery_store_number = delivery_data_df['Store']

        df_batchimport = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': 0.00,
                               'Memo': 'Batch Import',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_deposits = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Deposit In Bank'],
                            'Memo': 'Cash-' + store_number , 
                            'Class' : class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                            'ACCNT': 1080})


        df_cashcards = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Cashcards'],
                             'Memo': 'Cashcards-' + store_number,
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                             'ACCNT': 2450 })

        df_cashcard_sales = pd.DataFrame({'TRNSID': trnsid,
                                      'Amount': control_sheet_df['Cash Card Sales'] * -1,
                                      'Memo': 'Cashcard Sales-' + store_number,
                                      'Class' : class_list,
                                      'TRNSTYPE': 'GENERAL JOURNAL',
                                      'Date': date_list,
                                  'ACCNT': 2450 })

        df_catering_call_center = pd.DataFrame({'TRNSID': trnsid,
                                      'Amount': (control_sheet_df['Catering Call Center']),
                                      'Memo': 'Catering Call Center-'+ store_number ,
                                      'Class' : class_list,
                                      'TRNSTYPE': 'GENERAL JOURNAL',
                                      'Date': date_list,
                                       'ACCNT': 1130})

        df_vmd_credit_sales = pd.DataFrame({'TRNSID': trnsid,
                                    'Amount': control_sheet_df['Visa And Mastercard'] + control_sheet_df['Discover'],
                                    'Memo': 'CC Deposits(VMD)-' + store_number,
                                    'Class' : class_list,
                                    'TRNSTYPE': 'GENERAL JOURNAL',
                                    'Date': date_list,
                                   'ACCNT': 1030})

        df_amex_credit_sales = pd.DataFrame({'TRNSID': trnsid,
                                     'Amount': control_sheet_df['American Express'],
                                     'Memo': 'Amex-' + store_number,
                                     'Class' : class_list,
                                     'TRNSTYPE': 'GENERAL JOURNAL',
                                     'Date': date_list,
                                    'ACCNT': 1030 })

        df_paid_outs = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Paidouts'],
                             'Memo': 'Paid Outs-'+ store_number ,
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 1060})

        df_over_short = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Over Short'] * -1,
                              'Memo': 'Over/Short',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 5730})

        df_opencash = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Opening Cash'] * -1,
                            'Memo': 'Open Cash',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 1155})

        df_closekeep = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Closing Keep'],
                             'Memo': 'Close Keep',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 1155})

        df_salestax = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Sales Tax'] * -1,
                            'Memo': 'Sales Tax',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                            'Name': 'SBOE',
                           'ACCNT': 2600})

        df_footlong = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Footlong'] * -1,
                            'Memo': 'Footlong',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 4105})

        df_sixinch = pd.DataFrame({'TRNSID': trnsid,
                           'Amount': control_sheet_df['Six Inch'] * -1, 
                           'Memo': 'Six Inch',
                           'Class' : class_list,
                           'TRNSTYPE': 'GENERAL JOURNAL',
                           'Date': date_list,
                          'ACCNT': 4110})

        df_threeinch = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Three Inch'] *-1,
                             'Memo': 'Three Inch',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4115})

        df_muffin = pd.DataFrame({'TRNSID': trnsid,
                          'Amount': control_sheet_df['Muffin'] *-1,
                          'Memo': 'Muffin',
                          'Class' : class_list,
                          'TRNSTYPE': 'GENERAL JOURNAL',
                          'Date': date_list,
                         'ACCNT': 4120})

        df_salad = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Salad'] *-1, 
                         'Memo': 'Salad',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4125})

        df_pizza = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Pizza'] *-1, 
                         'Memo': 'Pizza',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4130})

        df_othercarrier = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Other Carrier'] *-1,
                                'Memo': 'Other Carier',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4135})

        df_addon = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Add On'] *-1,
                         'Memo': 'Add On',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4140})

        df_catering_1 = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Catering'] *-1,
                              'Memo': 'Catering',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 4145})

        df_unitcouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                   'Amount': control_sheet_df['Unit Coupons Disc.'] *-1,
                                   'Memo': 'Unit Coupon Disc',
                                   'Class' : class_list,
                                   'TRNSTYPE': 'GENERAL JOURNAL',
                                   'Date': date_list,
                                  'ACCNT': 4150})

        df_unitrefunds = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Unit Refunds'] *-1,
                               'Memo': 'Unit Refunds',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4155})

        df_unitvoids = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Unit Voids'] *-1,
                             'Memo': 'Unit Voids',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4160 })

        df_fountain = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Fountain'] *-1,
                            'Memo': 'Fountain',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 4205})

        df_bottledbeverage = pd.DataFrame({'TRNSID': trnsid,
                                   'Amount': control_sheet_df['Bottled Beverage'] *-1,
                                   'Memo': 'Bottle Beverage',
                                   'Class' : class_list,
                                   'TRNSTYPE': 'GENERAL JOURNAL',
                                   'Date': date_list,
                                  'ACCNT': 4210})

        df_hotbeverage = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Hot Beverage'] *-1,
                               'Memo': 'Hot Beverage',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4215})

        df_otherbeverage = pd.DataFrame({'TRNSID': trnsid,
                                 'Amount': control_sheet_df['Other Beverage'] *-1,
                                 'Memo': 'Other Beverage',
                                 'Class' : class_list,
                                 'TRNSTYPE': 'GENERAL JOURNAL',
                                 'Date': date_list,
                                'ACCNT': 4220})

        df_drinkscouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                     'Amount': control_sheet_df['Drinks Coupons Disc.'] *-1,
                                     'Memo': 'Drinks Coupons Disc.',
                                     'Class' : class_list,
                                     'TRNSTYPE': 'GENERAL JOURNAL',
                                     'Date': date_list,
                                    'ACCNT': 4225})

        df_drinksrefund = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Drinks Refunds'] *-1,
                                'Memo': 'Drinks Refunds',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4230})

        df_drinksvoids = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Drinks Voids'] *-1,
                               'Memo': 'Drinks Voids',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4235})

        df_chips = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Chips'] *-1,
                         'Memo': 'Chips',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4305})

        df_cookies = pd.DataFrame({'TRNSID': trnsid,
                           'Amount': control_sheet_df['Cookies'] *-1,
                           'Memo': 'Cookies',
                           'Class' : class_list,
                           'TRNSTYPE': 'GENERAL JOURNAL',
                           'Date': date_list,
                          'ACCNT': 4310})

        df_soups = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Soups'] *-1,
                         'Memo': 'Soups',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4315})

        df_othermisc = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Other Misc'] *-1,
                             'Memo': 'Other Misc',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4320})

        df_othercouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                    'Amount': control_sheet_df['Other Coupons Disc.'] *-1,
                                    'Memo': 'Other Coupons Disc.',
                                    'Class' : class_list,
                                    'TRNSTYPE': 'GENERAL JOURNAL',
                                    'Date': date_list,
                                   'ACCNT': 4325})

        df_otherrefunds = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Other Refunds'] *-1,
                                'Memo': 'Other Refunds',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4330})

        df_othervoids = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Other Voids'] *-1,
                              'Memo': 'Other Voids',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 4335})

        df_otherreceipts = pd.DataFrame({'TRNSID': trnsid,
                                 'Amount': control_sheet_df['Other Receipts'] *-1,
                                 'Memo': 'Other Receipts',
                                 'Class' : class_list,
                                 'TRNSTYPE': 'GENERAL JOURNAL',
                                 'Date': date_list,
                                'ACCNT': 4400 })

        df_doordash = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-DOORDASH'],
                            'Memo': 'Doordash-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                           'ACCNT': 1124 })

        df_grubhub = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Grubhub'],
                            'Memo': 'GrubHub-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                          'ACCNT': 1122 })

        df_postmates = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Postmates'],
                            'Memo': 'Postmates-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                            'ACCNT': 1121})

        df_ubereats = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-UberEatS'],
                            'Memo': 'Uber Eats-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                           'ACCNT': 1123})

        df_delivery_daily_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                                        'Amount': delivery_data_df['Tender DEL-DOORDASH'] + delivery_data_df['Tender DEL-Grubhub'] + delivery_data_df['Tender DEL-Postmates'] + delivery_data_df['Tender DEL-UberEatS'],
                                        'Memo': 'Daily Delivery Sales Offset',
                                        'Class' : delivery_class_list, 
                                        'TRNSTYPE': 'GENERAL JOURNAL',
                                        'Date': delivery_date_list,
                                       'ACCNT': 4459})

        df_doordash_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-DOORDASH'] * -1,
                            'Memo': 'Doordash-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                 'ACCNT': 4451})

        df_grubhub_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Grubhub']  * -1,
                            'Memo': 'GrubHub-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                'ACCNT': 4452})

        df_postmates_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Postmates'] * -1,
                            'Memo': 'Postmates-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                  'ACCNT': 4453})

        df_ubereats_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-UberEatS'] *-1,
                            'Memo': 'Uber Eats-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                 'ACCNT': 4454})

        df_tender_paypal = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': delivery_data_df['Tender PayPal'],
                            'Memo': 'Tender Pay Pal-'+ store_number , 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                'ACCNT': 1165})

        df_tender_ebt = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender EBT'],
                            'Memo': 'EBT-' + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                             'ACCNT': 1030 })

        df_other_ar = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender OTHER A/R'],
                            'Memo': 'Other AR-' + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                             'ACCNT': 1196 })

        control_sheet_result = df_deposits.append([df_batchimport,
                                           df_catering_call_center,
                                           df_vmd_credit_sales, 
                                           df_amex_credit_sales,
                                           df_tender_ebt,
                                           df_cashcards,
                                           df_cashcard_sales,
                                           df_paid_outs,
                                           df_tender_paypal,
                                           df_other_ar,
                                           df_over_short, 
                                           df_opencash, 
                                           df_closekeep,
                                           df_salestax, 
                                           df_footlong, 
                                           df_sixinch, 
                                           df_threeinch, 
                                           df_muffin,
                                           df_salad,
                                           df_pizza,
                                           df_othercarrier,
                                           df_addon,
                                           df_catering_1,
                                           df_unitcouponsdisc,
                                           df_unitrefunds,
                                           df_unitvoids,
                                           df_fountain,
                                           df_bottledbeverage,
                                           df_hotbeverage,
                                           df_otherbeverage,
                                           df_drinkscouponsdisc,
                                           df_drinksrefund,
                                           df_drinksvoids,
                                           df_chips,
                                           df_cookies,
                                           df_soups,
                                           df_othermisc,
                                           df_othercouponsdisc,
                                           df_otherrefunds,
                                           df_othervoids,
                                           df_otherreceipts,
                                           df_doordash,
                                           df_grubhub,
                                           df_postmates,
                                           df_ubereats,
                                           df_delivery_daily_sales,
                                           df_doordash_sales,
                                           df_grubhub_sales,
                                           df_postmates_sales,
                                           df_ubereats_sales,])
                    

        control_sheet_result = control_sheet_result[['!TRNS',
                                                    'TRNSID', 
                                                    'TRNSTYPE',
                                                    'Date',
                                                    'Amount',
                                                    'ACCNT',
                                                    'Memo',
                                                    'Class',
                                                    'Name', ]]

        control_sheet_result = control_sheet_result.sort_values(by = [ 'Class',
                                                                        'Date', 
                                                                        '!TRNS'])

        roy_faf_transid = 'Combo-' + roy_faf_ipc_df['Store Number']
        faf_store_number = roy_faf_ipc_df['Store Number']

        WE_DATE = report_group_df['Date'].values[-1].strftime("%m/%d/%y").replace('/', '-')

        df_roy_faf_batchimport = pd.DataFrame({'TRNSID': roy_faf_transid,
                               'Amount': 0.00,
                               'Memo': 'Batch Import',
                               'Class' : faf_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_cash_faf = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Faf'] * -1,
                            'Memo': 'Faf-Royalty-' + faf_store_number , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 1030,
                           'Name': faf_store_number})

        df_royalty = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Royalty'] * -1,
                            'Memo': 'DAI Royalty-' + faf_store_number , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 1030,
                          'Name': faf_store_number})

        df_faf_fees = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Faf'],
                            'Memo': 'Fees-Faf' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5550})

        df_royalty_fees = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Royalty'] ,
                            'Memo': 'Fees-Royalty' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5370})

        df_loyalty_food_cost_REIM = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Food Cost REIM' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5090})

        df_loyalty_food_cost_free_REIM = pd.DataFrame({'TRNSID': roy_faf_transid,
                                               'Amount': 0,
                                               'Memo': 'Loyalty Food Cost Free REIM' , 
                                               'Class' : faf_store_number, 
                                               'TRNSTYPE': 'GENERAL JOURNAL',
                                               'Date': WE_DATE,
                                               'ACCNT': 5090})

        df_loyalty_sales_tax_payable = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Sales Tax Payable' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 2610})

        df_loyalty_sales_tax_payable = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Sales Tax Payable' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 2610})

        df_tbd_waiver_royalty = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'TBD-Waiver-ROI' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5375})

        df_tbd_waiver_advertising = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'TPD-Waiver_Ad-Fee' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5555})

        roy_faf_result = df_roy_faf_batchimport.append([df_cash_faf,
                                                df_royalty,
                                                df_faf_fees,
                                                df_royalty_fees,
                                                df_loyalty_food_cost_REIM,
                                                df_loyalty_food_cost_free_REIM,
                                                df_loyalty_sales_tax_payable,
                                                df_tbd_waiver_royalty,
                                                df_tbd_waiver_advertising])


        roy_faf_result = roy_faf_result[['!TRNS',
                                        'TRNSID', 
                                        'TRNSTYPE',
                                        'Date',
                                        'Amount',
                                        'ACCNT',
                                        'Memo',
                                        'Class',
                                        'Name']]

        roy_faf_result = roy_faf_result.sort_values(by = ['Class','Memo'])

        ipc_transid = 'IPC-' + roy_faf_ipc_df['Store Number']
        ipc_store_number = roy_faf_ipc_df['Store Number']


        df_ipc_batchimport = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': 0 ,
                               'Memo': 'Batch Import',
                               'Class' : faf_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_call_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['7% Call Center'],
                               'Memo': 'Call Fee',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5783 })

        df_cash_card_redeemed_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Redeemed Fee 2.5%'],
                               'Memo': 'Cash Card Redeemed Fee',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5782 })

        df_cash_card_comm = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Sales Commission'] * -1,
                               'Memo': 'Cash Card Sales Commission',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 8050 })

        df_paypal_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Paypal Fee 2%'],
                               'Memo': 'Paypal Fee-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5785 })

        df_ipc_catering_call_center = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Catering Call Center'] * -1,
                               'Memo': 'Catering Call Center-'+ ipc_store_number ,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1130 })

        df_ipc_cash_card_sales = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Sales'],
                               'Memo': 'Cash Card Sales-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 2450 })

        df_ipc_cash_card_redeeemed= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cashcards'] * -1,
                               'Memo': 'Cash Card Redeemed-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 2450 })

        df_ipc_net_deposit= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Net IPC'],
                               'Memo': 'IPC Net Deposit-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1030 })

        df_ipc_paypal= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['PayPal'] * -1,
                               'Memo': 'Paypal-'  + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1165 })

        df_cnp_fees= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': 0,
                               'Memo': 'CNP Fees-'  + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5787 })

        ipc_result = df_ipc_batchimport.append([df_ipc_net_deposit,
                                        df_call_fee,
                                        df_cash_card_redeemed_fee,
                                        df_cash_card_comm,
                                        df_paypal_fee,
                                        df_ipc_catering_call_center,
                                        df_ipc_cash_card_sales,
                                        df_ipc_cash_card_redeeemed,
                                        df_ipc_paypal,
                                        df_cnp_fees])

        ipc_result = ipc_result[['!TRNS',
                                'TRNSID',
                                'TRNSTYPE',
                                'Date', 
                                'Amount',
                                'ACCNT', 
                                'Memo', 
                                'Class']]

        ipc_result = ipc_result.sort_values(by = ['Class','Memo'])

        final_result = control_sheet_result.append([roy_faf_result,
                                           ipc_result])

        final_result['Date'] = pd.to_datetime(final_result['Date'])


        final_result = final_result[['!TRNS',
                             'TRNSID',
                             'TRNSTYPE',
                             'Date',
                             'Amount',
                             'ACCNT',
                             'Memo',
                             'Class',
                            'Name']]

        file_name = 'Media/Final Result Export-WE-' + str(WE_DATE) + '.xlsx'

        final_result_exlude_55799 = final_result.copy(deep=True)
        final_result_exlude_55799 = final_result_exlude_55799[final_result_exlude_55799['Class'] != str(55799)]
        final_result_exlude_55799['Date'] = final_result_exlude_55799['Date'].astype(str)
        final_result_exlude_55799['Class'] = final_result_exlude_55799['Class'].astype(int)

        final_result_exlude_55799.to_excel(file_name)
    
    return render(request, 'upload.html')

def steve_ginsberg_upload(request):
    if request.method == 'POST':
        control_sheet = request.FILES['control_sheet_upload']
        control_sheet_df = pd.read_excel(control_sheet)
        
        report_group = request.FILES['report_group_upload']
        report_group_df = pd.read_excel(report_group)

        control_sheet_df.columns = control_sheet_df.iloc[2]
        control_sheet_df.drop(control_sheet_df.index[0:3],inplace=True)
        control_sheet_df = control_sheet_df.reset_index(drop=True)
        control_sheet_df = control_sheet_df.infer_objects()

        report_group_df.columns = report_group_df.iloc[5]
        report_group_df.drop(report_group_df.index[0:6],inplace=True)
        report_group_df = report_group_df.reset_index(drop=True)
        report_group_df = report_group_df[~report_group_df.Store.str.contains("Total")]
        report_group_df = report_group_df[~report_group_df.Store.str.contains("GRAND TOTAL")]

        if 'Tender APP' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender APP'] = 0
    
        if 'Tender RewardsCard' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender RewardsCard'] = 0

        if 'Tender OTHER A/R' in report_group_df.columns:
            pass
        else:
            report_group_df['Tender OTHER A/R'] = 0
    


        roy_faf_ipc_df = control_sheet_df.copy(deep=True)
        roy_faf_ipc_df = roy_faf_ipc_df[[ 'Store Number',
                                            'Date',
                                            'Cashcards',
                                            'Cash Card Sales',
                                            'Catering Call Center',
                                            'PayPal',
                                            'Unit Sales',
                                            'Drinks Sales',
                                            'Misc Sales' ]]

        roy_faf_ipc_df= roy_faf_ipc_df.groupby(['Store Number'], as_index=False).sum()
        roy_faf_ipc_df['Total Sales'] = roy_faf_ipc_df['Unit Sales'] + roy_faf_ipc_df['Drinks Sales'] + roy_faf_ipc_df['Misc Sales']
        roy_faf_ipc_df['Royalty'] = roy_faf_ipc_df['Total Sales'] * .08
        roy_faf_ipc_df['Faf'] = roy_faf_ipc_df['Total Sales'] * .045
        roy_faf_ipc_df['Commission'] = roy_faf_ipc_df['Cash Card Sales'] * .025
        roy_faf_ipc_df['Fees'] = ((roy_faf_ipc_df['Catering Call Center'] * .07) + (roy_faf_ipc_df['Cashcards'] * .025) + (roy_faf_ipc_df['PayPal'] * .02))
        roy_faf_ipc_df['Net IPC'] = roy_faf_ipc_df['Catering Call Center'] + roy_faf_ipc_df['Cashcards'] - roy_faf_ipc_df['Cash Card Sales'] + roy_faf_ipc_df['Commission'] - roy_faf_ipc_df['Fees'] + roy_faf_ipc_df['PayPal']
        roy_faf_ipc_df['Cash Card Sales Commission'] = roy_faf_ipc_df['Cash Card Sales'] * .025
        roy_faf_ipc_df['Cash Card Redeemed Fee 2.5%'] = roy_faf_ipc_df['Cashcards'] * .025
        roy_faf_ipc_df['Paypal Fee 2%'] = roy_faf_ipc_df['PayPal'] * .02
        roy_faf_ipc_df['7% Call Center'] = roy_faf_ipc_df['Catering Call Center'] * .07
        roy_faf_ipc_df = roy_faf_ipc_df.round(4)

        delivery_data_df = report_group_df.copy(deep=True)
        delivery_data_df = delivery_data_df.infer_objects()
        delivery_data_df = delivery_data_df[[   'Date',
                                                'Store',
                                                'Tender Amex',
                                                'Tender APP',
                                                'Tender Cash',
                                                'Tender CashCard',
                                                'Tender Catering Center',
                                                'Tender DEL-DOORDASH',
                                                'Tender DEL-Grubhub',
                                                'Tender DEL-Postmates',
                                                'Tender DEL-UberEatS',
                                                'Tender Discover',
                                                'Tender EBT',
                                                'Tender MasterCard',
                                                'Tender No Tender Type',
                                                'Tender PayPal',
                                                'Tender RewardsCard',
                                                'Tender VISA',
                                                'Tender OTHER A/R']]

        delivery_data_df['Daily Delivery Sum'] = delivery_data_df['Tender DEL-DOORDASH'] + delivery_data_df['Tender DEL-Grubhub'] + delivery_data_df['Tender DEL-Postmates'] + delivery_data_df['Tender EBT']
        delivery_data_df['Other'] = delivery_data_df['Tender EBT']
        delivery_data_df = delivery_data_df.groupby(['Date','Store'], as_index=False).sum()
            
        trnsid = 'WCS-' + control_sheet_df['Store Number']
        delivery_trnsid = 'WCS-' + delivery_data_df['Store']
        class_list = control_sheet_df['Store Number']
        delivery_class_list = delivery_data_df['Store']
        date_list = control_sheet_df['Date']
        delivery_date_list = delivery_data_df['Date']
        class_list = control_sheet_df['Store Number']
        delivery_class_list = delivery_data_df['Store']
        store_number = control_sheet_df['Store Number']
        delivery_store_number = delivery_data_df['Store']

        df_batchimport = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': 0.00,
                               'Memo': 'Batch Import',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_deposits = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Deposit In Bank'],
                            'Memo': 'Cash-' + store_number , 
                            'Class' : class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                            'ACCNT': 1080})


        df_cashcards = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Cashcards'],
                             'Memo': 'Cashcards-' + store_number,
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                             'ACCNT': 2450 })

        df_cashcard_sales = pd.DataFrame({'TRNSID': trnsid,
                                      'Amount': control_sheet_df['Cash Card Sales'] * -1,
                                      'Memo': 'Cashcard Sales-' + store_number,
                                      'Class' : class_list,
                                      'TRNSTYPE': 'GENERAL JOURNAL',
                                      'Date': date_list,
                                  'ACCNT': 2450 })

        df_catering_call_center = pd.DataFrame({'TRNSID': trnsid,
                                      'Amount': (control_sheet_df['Catering Call Center']),
                                      'Memo': 'Catering Call Center-'+ store_number ,
                                      'Class' : class_list,
                                      'TRNSTYPE': 'GENERAL JOURNAL',
                                      'Date': date_list,
                                       'ACCNT': 1130})

        df_vmd_credit_sales = pd.DataFrame({'TRNSID': trnsid,
                                    'Amount': control_sheet_df['Visa And Mastercard'] + control_sheet_df['Discover'],
                                    'Memo': 'CC Deposits(VMD)-' + store_number,
                                    'Class' : class_list,
                                    'TRNSTYPE': 'GENERAL JOURNAL',
                                    'Date': date_list,
                                   'ACCNT': 1030})

        df_amex_credit_sales = pd.DataFrame({'TRNSID': trnsid,
                                     'Amount': control_sheet_df['American Express'],
                                     'Memo': 'Amex-' + store_number,
                                     'Class' : class_list,
                                     'TRNSTYPE': 'GENERAL JOURNAL',
                                     'Date': date_list,
                                    'ACCNT': 1030 })

        df_paid_outs = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Paidouts'],
                             'Memo': 'Paid Outs-'+ store_number ,
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 1060})

        df_over_short = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Over Short'] * -1,
                              'Memo': 'Over/Short',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 5730})

        df_opencash = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Opening Cash'] * -1,
                            'Memo': 'Open Cash',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 1155})

        df_closekeep = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Closing Keep'],
                             'Memo': 'Close Keep',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 1155})

        df_salestax = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Sales Tax'] * -1,
                            'Memo': 'Sales Tax',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                            'Name': 'SBOE',
                           'ACCNT': 2600})

        df_footlong = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Footlong'] * -1,
                            'Memo': 'Footlong',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 4105})

        df_sixinch = pd.DataFrame({'TRNSID': trnsid,
                           'Amount': control_sheet_df['Six Inch'] * -1, 
                           'Memo': 'Six Inch',
                           'Class' : class_list,
                           'TRNSTYPE': 'GENERAL JOURNAL',
                           'Date': date_list,
                          'ACCNT': 4110})

        df_threeinch = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Three Inch'] *-1,
                             'Memo': 'Three Inch',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4115})

        df_muffin = pd.DataFrame({'TRNSID': trnsid,
                          'Amount': control_sheet_df['Muffin'] *-1,
                          'Memo': 'Muffin',
                          'Class' : class_list,
                          'TRNSTYPE': 'GENERAL JOURNAL',
                          'Date': date_list,
                         'ACCNT': 4120})

        df_salad = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Salad'] *-1, 
                         'Memo': 'Salad',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4125})

        df_pizza = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Pizza'] *-1, 
                         'Memo': 'Pizza',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4130})

        df_othercarrier = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Other Carrier'] *-1,
                                'Memo': 'Other Carier',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4135})

        df_addon = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Add On'] *-1,
                         'Memo': 'Add On',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4140})

        df_catering_1 = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Catering'] *-1,
                              'Memo': 'Catering',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 4145})

        df_unitcouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                   'Amount': control_sheet_df['Unit Coupons Disc.'] *-1,
                                   'Memo': 'Unit Coupon Disc',
                                   'Class' : class_list,
                                   'TRNSTYPE': 'GENERAL JOURNAL',
                                   'Date': date_list,
                                  'ACCNT': 4150})

        df_unitrefunds = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Unit Refunds'] *-1,
                               'Memo': 'Unit Refunds',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4155})

        df_unitvoids = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Unit Voids'] *-1,
                             'Memo': 'Unit Voids',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4160 })

        df_fountain = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': control_sheet_df['Fountain'] *-1,
                            'Memo': 'Fountain',
                            'Class' : class_list,
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': date_list,
                           'ACCNT': 4205})

        df_bottledbeverage = pd.DataFrame({'TRNSID': trnsid,
                                   'Amount': control_sheet_df['Bottled Beverage'] *-1,
                                   'Memo': 'Bottle Beverage',
                                   'Class' : class_list,
                                   'TRNSTYPE': 'GENERAL JOURNAL',
                                   'Date': date_list,
                                  'ACCNT': 4210})

        df_hotbeverage = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Hot Beverage'] *-1,
                               'Memo': 'Hot Beverage',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4215})

        df_otherbeverage = pd.DataFrame({'TRNSID': trnsid,
                                 'Amount': control_sheet_df['Other Beverage'] *-1,
                                 'Memo': 'Other Beverage',
                                 'Class' : class_list,
                                 'TRNSTYPE': 'GENERAL JOURNAL',
                                 'Date': date_list,
                                'ACCNT': 4220})

        df_drinkscouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                     'Amount': control_sheet_df['Drinks Coupons Disc.'] *-1,
                                     'Memo': 'Drinks Coupons Disc.',
                                     'Class' : class_list,
                                     'TRNSTYPE': 'GENERAL JOURNAL',
                                     'Date': date_list,
                                    'ACCNT': 4225})

        df_drinksrefund = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Drinks Refunds'] *-1,
                                'Memo': 'Drinks Refunds',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4230})

        df_drinksvoids = pd.DataFrame({'TRNSID': trnsid,
                               'Amount': control_sheet_df['Drinks Voids'] *-1,
                               'Memo': 'Drinks Voids',
                               'Class' : class_list,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': date_list,
                              'ACCNT': 4235})

        df_chips = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Chips'] *-1,
                         'Memo': 'Chips',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4305})

        df_cookies = pd.DataFrame({'TRNSID': trnsid,
                           'Amount': control_sheet_df['Cookies'] *-1,
                           'Memo': 'Cookies',
                           'Class' : class_list,
                           'TRNSTYPE': 'GENERAL JOURNAL',
                           'Date': date_list,
                          'ACCNT': 4310})

        df_soups = pd.DataFrame({'TRNSID': trnsid,
                         'Amount': control_sheet_df['Soups'] *-1,
                         'Memo': 'Soups',
                         'Class' : class_list,
                         'TRNSTYPE': 'GENERAL JOURNAL',
                         'Date': date_list,
                        'ACCNT': 4315})

        df_othermisc = pd.DataFrame({'TRNSID': trnsid,
                             'Amount': control_sheet_df['Other Misc'] *-1,
                             'Memo': 'Other Misc',
                             'Class' : class_list,
                             'TRNSTYPE': 'GENERAL JOURNAL',
                             'Date': date_list,
                            'ACCNT': 4320})

        df_othercouponsdisc = pd.DataFrame({'TRNSID': trnsid,
                                    'Amount': control_sheet_df['Other Coupons Disc.'] *-1,
                                    'Memo': 'Other Coupons Disc.',
                                    'Class' : class_list,
                                    'TRNSTYPE': 'GENERAL JOURNAL',
                                    'Date': date_list,
                                   'ACCNT': 4325})

        df_otherrefunds = pd.DataFrame({'TRNSID': trnsid,
                                'Amount': control_sheet_df['Other Refunds'] *-1,
                                'Memo': 'Other Refunds',
                                'Class' : class_list,
                                'TRNSTYPE': 'GENERAL JOURNAL',
                                'Date': date_list,
                               'ACCNT': 4330})

        df_othervoids = pd.DataFrame({'TRNSID': trnsid,
                              'Amount': control_sheet_df['Other Voids'] *-1,
                              'Memo': 'Other Voids',
                              'Class' : class_list,
                              'TRNSTYPE': 'GENERAL JOURNAL',
                              'Date': date_list,
                             'ACCNT': 4335})

        df_otherreceipts = pd.DataFrame({'TRNSID': trnsid,
                                 'Amount': control_sheet_df['Other Receipts'] *-1,
                                 'Memo': 'Other Receipts',
                                 'Class' : class_list,
                                 'TRNSTYPE': 'GENERAL JOURNAL',
                                 'Date': date_list,
                                'ACCNT': 4400 })

        df_doordash = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-DOORDASH'],
                            'Memo': 'Doordash-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                           'ACCNT': 1124 })

        df_grubhub = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Grubhub'],
                            'Memo': 'GrubHub-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                          'ACCNT': 1122 })

        df_postmates = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Postmates'],
                            'Memo': 'Postmates-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                            'ACCNT': 1121})

        df_ubereats = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-UberEatS'],
                            'Memo': 'Uber Eats-'  + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                           'ACCNT': 1123})

        df_delivery_daily_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                                        'Amount': delivery_data_df['Tender DEL-DOORDASH'] + delivery_data_df['Tender DEL-Grubhub'] + delivery_data_df['Tender DEL-Postmates'] + delivery_data_df['Tender DEL-UberEatS'],
                                        'Memo': 'Daily Delivery Sales Offset',
                                        'Class' : delivery_class_list, 
                                        'TRNSTYPE': 'GENERAL JOURNAL',
                                        'Date': delivery_date_list,
                                       'ACCNT': 4459})

        df_doordash_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-DOORDASH'] * -1,
                            'Memo': 'Doordash-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                 'ACCNT': 4451})

        df_grubhub_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Grubhub']  * -1,
                            'Memo': 'GrubHub-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                'ACCNT': 4452})

        df_postmates_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-Postmates'] * -1,
                            'Memo': 'Postmates-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                  'ACCNT': 4453})

        df_ubereats_sales = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender DEL-UberEatS'] *-1,
                            'Memo': 'Uber Eats-Sales', 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                 'ACCNT': 4454})

        df_tender_paypal = pd.DataFrame({'TRNSID': trnsid,
                            'Amount': delivery_data_df['Tender PayPal'],
                            'Memo': 'Tender Pay Pal-'+ store_number , 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                                'ACCNT': 1165})

        df_tender_ebt = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender EBT'],
                            'Memo': 'EBT-' + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                             'ACCNT': 1030 })

        df_other_ar = pd.DataFrame({'TRNSID': delivery_trnsid,
                            'Amount': delivery_data_df['Tender OTHER A/R'],
                            'Memo': 'Other AR-' + delivery_store_number, 
                            'Class' : delivery_class_list, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': delivery_date_list,
                             'ACCNT': 1196 })

        control_sheet_result = df_deposits.append([df_batchimport,
                                           df_catering_call_center,
                                           df_vmd_credit_sales, 
                                           df_amex_credit_sales,
                                           df_tender_ebt,
                                           df_cashcards,
                                           df_cashcard_sales,
                                           df_paid_outs,
                                           df_tender_paypal,
                                           df_other_ar,
                                           df_over_short, 
                                           df_opencash, 
                                           df_closekeep,
                                           df_salestax, 
                                           df_footlong, 
                                           df_sixinch, 
                                           df_threeinch, 
                                           df_muffin,
                                           df_salad,
                                           df_pizza,
                                           df_othercarrier,
                                           df_addon,
                                           df_catering_1,
                                           df_unitcouponsdisc,
                                           df_unitrefunds,
                                           df_unitvoids,
                                           df_fountain,
                                           df_bottledbeverage,
                                           df_hotbeverage,
                                           df_otherbeverage,
                                           df_drinkscouponsdisc,
                                           df_drinksrefund,
                                           df_drinksvoids,
                                           df_chips,
                                           df_cookies,
                                           df_soups,
                                           df_othermisc,
                                           df_othercouponsdisc,
                                           df_otherrefunds,
                                           df_othervoids,
                                           df_otherreceipts,
                                           df_doordash,
                                           df_grubhub,
                                           df_postmates,
                                           df_ubereats,
                                           df_delivery_daily_sales,
                                           df_doordash_sales,
                                           df_grubhub_sales,
                                           df_postmates_sales,
                                           df_ubereats_sales,])
                    

        control_sheet_result = control_sheet_result[['!TRNS',
                                                    'TRNSID', 
                                                    'TRNSTYPE',
                                                    'Date',
                                                    'Amount',
                                                    'ACCNT',
                                                    'Memo',
                                                    'Class',
                                                    'Name', ]]

        control_sheet_result = control_sheet_result.sort_values(by = [ 'Class',
                                                                        'Date', 
                                                                        '!TRNS'])

        roy_faf_transid = 'Combo-' + roy_faf_ipc_df['Store Number']
        faf_store_number = roy_faf_ipc_df['Store Number']

        WE_DATE = report_group_df['Date'].values[-1].strftime("%m/%d/%y").replace('/', '-')

        df_roy_faf_batchimport = pd.DataFrame({'TRNSID': roy_faf_transid,
                               'Amount': 0.00,
                               'Memo': 'Batch Import',
                               'Class' : faf_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_cash_faf = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Faf'] * -1,
                            'Memo': 'Faf-Royalty-' + faf_store_number , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 1030,
                           'Name': faf_store_number})

        df_royalty = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Royalty'] * -1,
                            'Memo': 'DAI Royalty-' + faf_store_number , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 1030,
                          'Name': faf_store_number})

        df_faf_fees = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Faf'],
                            'Memo': 'Fees-Faf' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5550})

        df_royalty_fees = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': roy_faf_ipc_df['Royalty'] ,
                            'Memo': 'Fees-Royalty' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5370})

        df_loyalty_food_cost_REIM = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Food Cost REIM' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5090})

        df_loyalty_food_cost_free_REIM = pd.DataFrame({'TRNSID': roy_faf_transid,
                                               'Amount': 0,
                                               'Memo': 'Loyalty Food Cost Free REIM' , 
                                               'Class' : faf_store_number, 
                                               'TRNSTYPE': 'GENERAL JOURNAL',
                                               'Date': WE_DATE,
                                               'ACCNT': 5090})

        df_loyalty_sales_tax_payable = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Sales Tax Payable' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 2610})

        df_loyalty_sales_tax_payable = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'Loyalty Sales Tax Payable' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 2610})

        df_tbd_waiver_royalty = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'TBD-Waiver-ROI' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5375})

        df_tbd_waiver_advertising = pd.DataFrame({'TRNSID': roy_faf_transid,
                            'Amount': 0,
                            'Memo': 'TPD-Waiver_Ad-Fee' , 
                            'Class' : faf_store_number, 
                            'TRNSTYPE': 'GENERAL JOURNAL',
                            'Date': WE_DATE,
                            'ACCNT': 5555})

        roy_faf_result = df_roy_faf_batchimport.append([df_cash_faf,
                                                df_royalty,
                                                df_faf_fees,
                                                df_royalty_fees,
                                                df_loyalty_food_cost_REIM,
                                                df_loyalty_food_cost_free_REIM,
                                                df_loyalty_sales_tax_payable,
                                                df_tbd_waiver_royalty,
                                                df_tbd_waiver_advertising])


        roy_faf_result = roy_faf_result[['!TRNS',
                                        'TRNSID', 
                                        'TRNSTYPE',
                                        'Date',
                                        'Amount',
                                        'ACCNT',
                                        'Memo',
                                        'Class',
                                        'Name']]

        roy_faf_result = roy_faf_result.sort_values(by = ['Class','Memo'])

        ipc_transid = 'IPC-' + roy_faf_ipc_df['Store Number']
        ipc_store_number = roy_faf_ipc_df['Store Number']


        df_ipc_batchimport = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': 0 ,
                               'Memo': 'Batch Import',
                               'Class' : faf_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                               '!TRNS': 'Yes',
                              'ACCNT': 1155})

        df_call_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['7% Call Center'],
                               'Memo': 'Call Fee',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5783 })

        df_cash_card_redeemed_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Redeemed Fee 2.5%'],
                               'Memo': 'Cash Card Redeemed Fee',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5782 })

        df_cash_card_comm = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Sales Commission'] * -1,
                               'Memo': 'Cash Card Sales Commission',
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 8050 })

        df_paypal_fee = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Paypal Fee 2%'],
                               'Memo': 'Paypal Fee-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5785 })

        df_ipc_catering_call_center = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Catering Call Center'] * -1,
                               'Memo': 'Catering Call Center-'+ ipc_store_number ,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1130 })

        df_ipc_cash_card_sales = pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cash Card Sales'],
                               'Memo': 'Cash Card Sales-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 2450 })

        df_ipc_cash_card_redeeemed= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Cashcards'] * -1,
                               'Memo': 'Cash Card Redeemed-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 2450 })

        df_ipc_net_deposit= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['Net IPC'],
                               'Memo': 'IPC Net Deposit-' + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1030 })

        df_ipc_paypal= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': roy_faf_ipc_df['PayPal'] * -1,
                               'Memo': 'Paypal-'  + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 1165 })

        df_cnp_fees= pd.DataFrame({'TRNSID': ipc_transid,
                               'Amount': 0,
                               'Memo': 'CNP Fees-'  + ipc_store_number,
                               'Class' : ipc_store_number,
                               'TRNSTYPE': 'GENERAL JOURNAL',
                               'Date': WE_DATE,
                              'ACCNT': 5787 })

        ipc_result = df_ipc_batchimport.append([df_ipc_net_deposit,
                                        df_call_fee,
                                        df_cash_card_redeemed_fee,
                                        df_cash_card_comm,
                                        df_paypal_fee,
                                        df_ipc_catering_call_center,
                                        df_ipc_cash_card_sales,
                                        df_ipc_cash_card_redeeemed,
                                        df_ipc_paypal,
                                        df_cnp_fees])

        ipc_result = ipc_result[['!TRNS',
                                'TRNSID',
                                'TRNSTYPE',
                                'Date', 
                                'Amount',
                                'ACCNT', 
                                'Memo', 
                                'Class']]

        ipc_result = ipc_result.sort_values(by = ['Class','Memo'])

        final_result = control_sheet_result.append([roy_faf_result,
                                           ipc_result])

        final_result['Date'] = pd.to_datetime(final_result['Date'])


        final_result = final_result[['!TRNS',
                             'TRNSID',
                             'TRNSTYPE',
                             'Date',
                             'Amount',
                             'ACCNT',
                             'Memo',
                             'Class',
                            'Name']]

        file_name = 'Media/Final Result Export-WE-' + str(WE_DATE) + '.xlsx'

        final_result_exlude_55799 = final_result.copy(deep=True)
        final_result_exlude_55799 = final_result_exlude_55799[final_result_exlude_55799['Class'] != str(55799)]
        final_result_exlude_55799['Date'] = final_result_exlude_55799['Date'].astype(str)
        final_result_exlude_55799['Class'] = final_result_exlude_55799['Class'].astype(int)

        final_result_exlude_55799.to_excel(file_name)
    
    return render(request, 'upload.html')
