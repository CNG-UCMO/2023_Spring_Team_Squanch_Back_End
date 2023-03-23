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

def get_Sections(event, context):

    #Retrieves all the names of the sections in the section table that have the 'name' attribute (all of them)
    table = dynamodb.Table(SECTIONS_TABLE)
    resp = table.scan(ProjectionExpression = '#nme', ExpressionAttributeNames = {'#nme': 'name'})['Items']

    response = {
        'statusCode': 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': json.dumps(resp)
    }

    return response

def get_Section_Content(event, context):

    #We get the name of the section that was passed to this function
    section_name = '{}'.format(event['pathParameters']['secName'])

    #We retrieve the item from the section table that has the same name as what was passed into the function
    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))
    items = resp.get("Items", None)

    #these are the lists that hold the id's of the Image and Text Elements
    ImageContent = items[0]['ImageContent']
    TextContent = items[0]['TextContent']

    imgList = []
    txtList = []

    table1 = dynamodb.Table(IMAGES_TABLE)
    table2 = dynamodb.Table(TEXT_TABLE)

    #Searching through the Image Table to find the element id that matches the current value in ImageContent. We add the html of that element to imgList
    for val in ImageContent:
        resp1 = table1.query(KeyConditionExpression=Key('img_id').eq(val))
        items1 = resp1.get("Items", None)
        imgList.append({'id':val, 'html':items1[0]['html']})

    #Searching through the Text Table to find the element id that matches the current value in TextContent. We add the html of that element to txtList
    for val in TextContent:
        resp2 = table2.query(KeyConditionExpression=Key('text_id').eq(val))
        items2 = resp2.get("Items", None)
        txtList.append({'id':val, 'html':items2[0]['html']})

    sectionContent = {'images':imgList, 'text':txtList}

    response = {
        'statusCode': 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': json.dumps(sectionContent) 
    }

    return response