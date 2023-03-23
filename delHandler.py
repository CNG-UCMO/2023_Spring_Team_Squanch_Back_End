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
    #retrieving what was passed in to this function
    section_name = '{}'.format(event['pathParameters']['secName'])

    #deleting the item from the section table that has the same name as what was passed in as secName
    table = dynamodb.Table(SECTIONS_TABLE)
    resp = table.delete_item(
        Key={
            "name": section_name
        }
    )
    
    response = {
        'statusCode': 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': "Successfully deleted the section"
    }

    return response

def del_Text(event, context):
    #retrieving what was passed in to this function 
    txt_id = '{}'.format(event['pathParameters']['txtID'])
    section_name = '{}'.format(event['pathParameters']['secName'])

    #deleting the item from the text table that has the same id as what was passed in as txtID
    table = dynamodb.Table(TEXT_TABLE)
    resp = table.delete_item(
        Key={
            "text_id": txt_id
        }
    )

    #retrieves the item from the section table that has the same section name as the one passed into the function
    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))
    items = resp.get("Items", None)

    #This is the list of Text element id's that are within this section  
    TextContent = items[0]['TextContent']
    

    #iterating through the list of Text Element id's 
    for idx, val in enumerate(TextContent):
        #checking if the current id value in the list matches what was passed into the function
        #deletes it from the list if it matches
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
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': "Successfully deleted Image"
    }

    return response

def del_Image(event, context):
    #retrieving what was passed in to this function 
    img_id = '{}'.format(event['pathParameters']['imgID'])
    section_name = '{}'.format(event['pathParameters']['secName'])

    #deleting the item from the images table that has the same id as what was passed in as imgID
    table = dynamodb.Table(IMAGES_TABLE)
    resp = table.delete_item(
        Key={
            "img_id": img_id
        }
    )

    #retrieves the item from the section table that has the same section name as the one passed into the function
    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))
    items = resp.get("Items", None)

    #This is the list of Image Element id's that are within this section 
    ImageContent = items[0]['ImageContent']
    
    #iterating through the list of Image Element id's 
    for idx, val in enumerate(ImageContent):
        #checking if the current id value in the list matches what was passed into the function
        #deletes it from the list if it matches
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
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': "Successfully deleted Image"
    }

    return response
