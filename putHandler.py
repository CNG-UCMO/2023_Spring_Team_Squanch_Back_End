import json
import os
import boto3
import botocore
from boto3.dynamodb.conditions import Key

#These are our Dynamodb tables
SECTIONS_TABLE = os.environ['SECTIONS_TABLE']
IMAGES_TABLE = os.environ['IMAGES_TABLE']
TEXT_TABLE = os.environ['TEXT_ELEMENTS_TABLE']

dynamodb = boto3.resource('dynamodb', 'us-east-1')

client = boto3.client('dynamodb')

def update_Text(event, context):
    data = json.loads(event['body'])

    #retrieving the information about the text element from the data passed into the function
    text_id = '{}'.format(data['text_id'])
    content = '{}'.format(data['content'])

    table = dynamodb.Table(TEXT_TABLE)
    resp = table.query(KeyConditionExpression=Key('text_id').eq(text_id))
    items = resp.get("Items", None)

    if items[0]['ol'] or items[0]['ul']:
        content = content.split(", ")

    list_html = ''
    html = ''

    #checks if a list was requested. we are generating li elements for each element in the list
    if items[0]['ol'] or items[0]['ul']:
        for item in content:
            list_html += '<li>' + item + '</li>\n'
    
    #the html string will be made with either <p>, <ul>, or <ol> tags depending on what was requested
    if items[0]['ul'] == False and items[0]['ol'] == False and items[0]['header'] == False: 
        html = '<p>' + content + '</p>'
    elif items[0]['ul']:
        html = '<ul>' +  list_html + '</ul>'
    elif items[0]['ol']:
        html = '<ol>' +  list_html + '</ol>'
    elif items[0]['header']:
        html = '<h3>' + content + '</h3>'

    #updates the section table and its content attribute. We place the html string in there
    client.update_item(
        TableName=TEXT_TABLE,
        Key={
            'text_id': {'S': text_id}
        },
        UpdateExpression='SET html = :txtHTML',
        ExpressionAttributeValues={
            ':txtHTML': { 
                'S' : html
            }
        },
    )

    body = {
            "text_id": {'S': text_id},
            "html": {'S': html}
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
    }

    return response