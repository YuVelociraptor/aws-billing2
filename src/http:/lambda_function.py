import json
import boto3
import urllib
import urllib.request
import os
from datetime import date, timedelta
import calendar

ce = boto3.client("ce")

aws_account_disp = os.getenv('AWS_ACCOUNT_DISP')
slack_url = os.getenv('SLACK_WEBHOOK_URL')

def get_cost_and_usage(start_date, end_date):

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )

    return response

def formated_cost(start_date, end_date, header_message):
    info = get_cost_and_usage(start_date, end_date)

    d = info['ResultsByTime'][0]
    

    term = d['TimePeriod']['Start'] + ' -> ' + d['TimePeriod']['End'] + '\n'
    costs = f"{float(d['Total']['UnblendedCost']['Amount']):.4f}" + ' ' + d['Total']['UnblendedCost']['Unit']

    return header_message + term + costs

def post_slack(message):
    
    send_data = {
        "text": str(message),
    }
    
    send_text = json.dumps(send_data)
    request = urllib.request.Request(
        slack_url, 
        data=send_text.encode('utf-8'), 
        method="POST"
    )
    with urllib.request.urlopen(request) as response:
        response.read().decode('utf-8')


def lambda_handler(event, context):

    today = date.today()

    this_month_first = today.replace(day=1)
    this_month_first_str = this_month_first.strftime("%Y-%m-%d")

    this_month_last_str = today.replace(
        day=calendar.monthrange(today.year, today.month)[1]
    ).strftime("%Y-%m-%d")

    prev_month_last = this_month_first - timedelta(days=1)
    prev_month_first = prev_month_last.replace(day=1)

    prev_month_first_str = prev_month_first.strftime("%Y-%m-%d")
    prev_month_last_str = prev_month_last.strftime("%Y-%m-%d")

    prev_cost = formated_cost(prev_month_first_str, prev_month_last_str, 'Previous Month Cost\n')
    current_cost = formated_cost(this_month_first_str, this_month_last_str, 'Current Month Cost\n')

    post_slack('`' + aws_account_disp + '`' + '\n\n' + prev_cost + '\n\n' + current_cost)

