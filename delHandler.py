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

def del_Section(event, context):
    section_name = '{}'.format(event['pathParameters']['secName'])

    table = dynamodb.Table(SECTIONS_TABLE)
    resp = table.delete_item(
        Key={
            "name": section_name
        }
    )
    
    response = {
        'statusCode': 200,
        'body': "Successfully deleted section"
    }

    return response

def del_Text(event, context):
    txt_id = '{}'.format(event['pathParameters']['txtID'])
    section_name = '{}'.format(event['pathParameters']['secName'])

    table = dynamodb.Table(TEXT_TABLE)
    resp = table.delete_item(
        Key={
            "text_id": txt_id
        }
    )

    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))

    items = resp.get("Items", None)
    TextContent = items[0]['TextContent']
    
    for idx, val in enumerate(TextContent):
        if val == txt_id:
            client.update_item(
                TableName=SECTIONS_TABLE,
                Key={
                    'name': {'S': section_name}
                },
                UpdateExpression='REMOVE TextContent[%d]' % (idx)
            )
            break

    response = {
        'statusCode': 200,
        'body': "Successfully deleted Text Item"
    }

    return response

def del_Image(event, context):
    img_id = '{}'.format(event['pathParameters']['imgID'])
    section_name = '{}'.format(event['pathParameters']['secName'])

    table = dynamodb.Table(IMAGES_TABLE)
    resp = table.delete_item(
        Key={
            "img_id": img_id
        }
    )

    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))

    items = resp.get("Items", None)
    ImageContent = items[0]['ImageContent']
    
    for idx, val in enumerate(ImageContent):
        if val == img_id:
            client.update_item(
                TableName=SECTIONS_TABLE,
                Key={
                    'name': {'S': section_name}
                },
                UpdateExpression='REMOVE ImageContent[%d]' % (idx)
            )
            break

    response = {
        'statusCode': 200,
        'body': "Successfully deleted Image"
    }

    return response
