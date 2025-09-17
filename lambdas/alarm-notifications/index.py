import base64
import zlib
import json
import requests
import os
import re
import boto3

discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL')

def get_color(value=None):
    if value in ['WARN', 'INSUFFICIENT_DATA']:
        return 16753920  # Orange
    elif value in ['DEBUG', 'scheduledChange', 'investigation']:
        return 16776960  # Yellow
    elif value in ['OK', 'RUNNING', 'accountNotification']:
        return 65280  # Green
    else:
        return 16711680  # Red (default)

def send_discord_message(discord_webhook_url, title, message, color):

    lines = []
    space_length = 21
    for key, value in message.items():
        lines.append(f"{key}:{' ' * (space_length - len(key))}{value}")
    message_text = "```\n" + "\n".join(lines) + "\n```"

    payload = {
        "embeds": [
            {
                "title": title,
                "description": message_text,
                "color": color
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(discord_webhook_url, data=json.dumps(payload), headers=headers)
    if response.status_code != 204:
        raise Exception(f"Failed to send Discord message. Status code: {response.status_code}, response: {response.text}")
    else:
        print("Discord message sent successfully.")

def send_teams_message(teams_webhook_url, title, message, color):
    
    def int_to_hex_color(color):
        return format(color, '06x')

    lines = []
    space_length = 21
    for key, value in message.items():
        padding = ' ' * (space_length - len(key))
        lines.append(f"{key}:{padding}{value}")

    message_text = "<pre>" + "\n".join(lines) + "</pre>"

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": int_to_hex_color(color),
        "title": title,
        "text": message_text
    }

    headers = {'Content-Type': 'application/json'}
    response = requests.post(teams_webhook_url, data=json.dumps(payload), headers=headers)
    
    if response.status_code != 204 and response.status_code != 200:
        raise Exception(f"Failed to send Teams message. Status code: {response.status_code}, response: {response.text}")
    else:
        print("Teams message sent successfully.")

def process_records(event, context):
    processed_events = []

    for record in event['Records']:
        record_timestamp = record['Sns']['Timestamp']
        try:
            record_message = json.loads(record['Sns']['Message'])  # Trying to convert to JSON
        except json.JSONDecodeError:
            record_message = record['Sns']['Message']  # If it's not JSON, it's plain text
            print(f"Non-JSON SNS message: {record_message}")
        
        if isinstance(record_message, dict) and 'AlarmName' in record_message:
            # It's a CloudWatch alarm
            processed_event = process_cloudwatch_alarm(record_timestamp, record_message)
        elif isinstance(record_message, dict) and 'detail' in record_message:
            # It's an EventBridge event
            processed_event = process_eventbridge_message(record_timestamp, record_message)
        elif isinstance(record_message, str) and 'AWS Budget Notification' in record_message:
            # It's a Budget event
            processed_event = process_budget_message(record_timestamp, record_message)
        elif isinstance(record_message, dict) and 'notificationType' in record_message:
            # It's an SES event
            processed_event = process_ses_message(record_timestamp, record_message)
        else:
            # It's an unknown event
            processed_event = process_unknown_message(record_timestamp, record_message, context)

        if processed_event:
            processed_events.append(processed_event)

    return processed_events

def extract_datapoints(reason_text):
    match = re.findall(r'\d+\.\d+', reason_text)
    rounded_numbers = [round(float(num), 1) for num in match]
    return f"[{', '.join(map(str, rounded_numbers))}]"

cloudwatch = boto3.client('cloudwatch')

# Get the tags corresponding to the alarm
def get_alarm_tags(alarm_arn):
    response = cloudwatch.list_tags_for_resource(
        ResourceARN=alarm_arn
    )
    return response.get('Tags', [])

# Get tags that start with alarm-
def get_alarm_metadata(tags):
    alarm_tags = {tag["Key"]: tag["Value"] for tag in tags if tag.get("Key", "").startswith("alarm-")}
    return alarm_tags

# BUILD THE ALARM MESSAGE
def process_cloudwatch_alarm(record_timestamp, record_message):

    # EXTRACT FIELDS THAT I AM GOING TO USE
    alarm_name = record_message['AlarmName']
    alarmdescription = record_message['AlarmDescription']
    newstatevalue = record_message['NewStateValue']
    newstatereason = record_message['NewStateReason']
    statechangetime = record_message['StateChangeTime']
    oldstatevalue = record_message['OldStateValue']

    if oldstatevalue == 'INSUFFICIENT_DATA':
        print(f"Alarm {alarm_name} has state INSUFFICIENT_DATA, not sending notification.")
        return None
        
    threshold = record_message['Trigger']['Threshold']
    resource = record_message['Trigger']['Namespace']
    region = record_message['Region']
    alarm_arn = record_message['AlarmArn']

    tags = get_alarm_tags(alarm_arn)
    alarm_tags = get_alarm_metadata(tags)

    # get the other tags that are not defaults
    remaining_tags = {
        key: value for key, value in alarm_tags.items()
        if key not in ("alarm-level", "alarm-service-name")
    }

    level = alarm_tags.get("alarm-level", "unknown")
    service_name = alarm_tags.get("alarm-service-name", "unknown")

    clean_alarm_name = '-'.join(record_message['AlarmName'].split('-')[1:])
    alarm_name_parts = alarm_name.split('-')
    metric = alarm_name_parts[0]
    reason = newstatereason.split(':')[0]
    datapoints = extract_datapoints(newstatereason)

    event_text = {
        'Level' : level,
        'Region' : region,
        'Resource' : resource,
        'Service Name' : service_name,
        'Metric' : metric,
        'Reason' : reason,
        'Alert Threshold' : threshold,
        'Datapoints' : datapoints,
        'State Change': f"{oldstatevalue} -> {newstatevalue}",
        **remaining_tags
    }

    # BUILD VARIABLES
    title = f"{record_timestamp} | {newstatevalue} - {clean_alarm_name}"
    message = event_text

    # LOG FROM LAMBDA
    print (f"{title}")
    print (f"{message}")

    return {
        'title': title,
        'message': message,
        'color': get_color(newstatevalue)
    }

# BUILD THE EVENTBRIDGE MESSAGE
def process_eventbridge_message(record_timestamp, record_message):

    region = record_message['region']
    source = record_message['source']
    time_stamp = record_timestamp
    
    if source == 'aws.ecs':

        metric = record_message['detail-type']

        if metric == 'ECS Task State Change':

            last_status = record_message['detail']['lastStatus']            
            containers_name = record_message['detail']['containers'][0]['name']
            service_name = record_message['detail']['group'].split(":")[-1]
            reason = record_message['detail']['stoppedReason']
            alarm_name = f"{metric}-{containers_name}"
            level, resource, desired_status = "CRIT", "AWS/ECS", "RUNNING"
        
            event_text = {
                'Level' : level,
                'Region' : region,
                'Resource' : resource,
                'Service Name' : service_name,
                'Metric' : metric,
                'Reason' : reason,
                'Alert Threshold' : desired_status,
                'State Change' : last_status
            }

        else:
            event_type = record_message['detail']['eventType']
            cluster_arn = record_message['detail']['clusterArn']
            capacity_provider = record_message['detail']['capacityProviderArns']
            reason = record_message['detail']['reason']
            alarm_name = f"{metric}"
            level, resource = "CRIT", "AWS/ECS"
            
            event_text = {
                'Level' : level,
                'Region' : region,
                'Resource' : resource,
                'Cluster Arn' : cluster_arn,
                'Event Type' : event_type,
                'Reason' : reason
            }

        title = f"{level} - {alarm_name} | {time_stamp}"
        return {
            'title': title,
            'message': event_text,
            'color': get_color()
        }

    elif source == 'aws.health':

        level = record_message['detail']['eventTypeCategory']
        resource = record_message['detail']['service']
        eventTypeCode = record_message['detail']['eventTypeCode'] 
        reason = record_message['detail']['eventDescription'][0]['latestDescription']
        account_id = record_message['account']

        event_text = {
            'Level' : level,
            'Account ID' : account_id,
            'Region' : region,
            'Resource' : resource,
            'Event Type Code' : eventTypeCode,
            'Reason' : reason
        }

        title = f"{level} - {resource} | {time_stamp}"
        return {
            'title': title,
            'message': event_text,
            'color': get_color(level)
        }

    else:
        title = f"Unknown EventBridge source: {source}"
        reason = record_message['detail']

        event_text = {
            'Reason': reason
        }
        return {
            'title': title,
            'message': event_text,
            'color': get_color()
        }

# BUILD BUDGET MESSAGE
def process_budget_message(record_timestamp, message_text):
        
    lines = message_text.splitlines()
    parsed_data = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            parsed_data[key.strip()] = value.strip()
        elif line.startswith("AWS Account"):
            account_id = line.split()[-1].strip()

    budget_name = parsed_data.get("Budget Name", "Unknown")
    budget_type = parsed_data.get("Budget Type", "Unknown")
    budgeted_amount = parsed_data.get("Budgeted Amount", "Unknown")
    alert_type = parsed_data.get("Alert Type", "Unknown")
    threshold = parsed_data.get("Alert Threshold", "Unknown")
    actual = parsed_data.get("ACTUAL Amount", "Unknown")

    title = f"{budget_type} - BUDGET | {record_timestamp}"
    event_text = {
        'Level' : budget_type,
        'Budget' : budget_name,
        'AccountID' : account_id,
        'Budgeted Amount' : budgeted_amount,
        'Alert Type' : alert_type,
        'Alert Threshold' : threshold,
        'Actual Amount' : actual
    }

    return {
        "title": title,
        "message": event_text,
        "color": get_color()
    }

def process_unknown_message(record_timestamp, record_message, context):

    arn = context.invoked_function_arn
    account_id = arn.split(":")[4]

    if isinstance(record_message, dict):
        region = record_message.get('Region', os.environ['AWS_REGION'])
        reason = json.dumps(record_message, indent=2)
    else:
        region = os.environ['AWS_REGION']
        reason = str(record_message)

    event_text = {
        'Level': UNKNOWN,
        'Region': region,
        'AccountID': account_id,
        'Reason': reason
    }    

    title = f"UNKNOWN MESSAGE | {record_timestamp}"     

    return {
        "title": title,
        "message": event_text,
        "color": get_color()
    }     

# BUILD SES MESSAGE
def process_ses_message(record_timestamp, record_message):

    region = os.environ['AWS_REGION']
    source = record_message['mail']['source']
    level = record_message['notificationType']
    bouncedRecipients = record_message.get('bounce', {}).get('bouncedRecipients', None)
    complainedRecipients = record_message.get('complaint', {}).get('complainedRecipients', None)
    deliveryRecipients = record_message.get('delivery', {}).get('recipients', None)

    bouncedRecipients_str = json.dumps(bouncedRecipients, indent=2, ensure_ascii=False) if bouncedRecipients else "Null"
    complainedRecipients_str = json.dumps(complainedRecipients, indent=2, ensure_ascii=False) if complainedRecipients else "Null"
    deliveryRecipients_str = json.dumps(deliveryRecipients, indent=2, ensure_ascii=False) if deliveryRecipients else "Null"

    if level == "Bounce":
        event_text = {
            'Level' : level,
            'Region' : region,
            'Source' : source,
            'Bounced Recipients' : bouncedRecipients_str
        }
    elif level == "Complaint":
        event_text = {
            'Level' : level,
            'Region' : region,
            'Source' : source,
            'Complained Recipients' : complainedRecipients_str
        }
    else:
        event_text = {
            'Level' : level,
            'Region' : region,
            'Source': source,
            'Delivery Recipients': deliveryRecipients_str
        }

    title = f"{level} - {source} | {record_timestamp}"
    
    return {
        'title': title,
        'message': event_text,
        'color': get_color()
    }

def lambda_handler(event, context):
    # SEND MESSAGE
    if 'Records' in event:
        processed_events = process_records(event, context)
    else:
        # Don't know the format
        print (event)
        pass
    
    for event_data in processed_events:
        if discord_webhook_url:
            send_discord_message(discord_webhook_url, event_data['title'], event_data['message'], event_data['color'])
        if teams_webhook_url:
            send_teams_message(teams_webhook_url, event_data['title'], event_data['message'], event_data['color'])

