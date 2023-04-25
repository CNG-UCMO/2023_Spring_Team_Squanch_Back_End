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

#this happens when the user creates a section
def add_section(event, context):
    data = json.loads(event['body']) 

    name = '{}'.format(data['name'])   #retrieves the name that was passed into this function, and formats it to a string 
    
    imgContent = []
    txtContent = []

    #here we are adding an item to the Sections table
    resp = client.put_item(
        TableName=SECTIONS_TABLE,
        Item={
            'name': {'S': name },
            'ImageContent': {'L': imgContent },
            'TextContent': {'L' : txtContent }
        },
        ConditionExpression='attribute_not_exists(#name)',     #this checks if the name already exists
        ExpressionAttributeNames={"#name": "name"}
    )
   
    body = {
        "name": name
    }

    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body)
    }

    return response


#this happens when the user adds an image to the web page
def insert_Image(event, context):
    data = json.loads(event['body'])

    #retrieves the information about the image that was passed into the function
    section = '{}'.format(data['section'])

    img_id = '{}'.format(data['img_id'])
    name = '{}'.format(data['name'])
    description = '{}'.format(data['description'])

    height = '{}'.format(data['height'])
    width = '{}'.format(data['width'])
    url = '{}'.format(data['url'])
    
    #the string representing our html element
    html = '<img src="'+ url +'" alt="'+ description + '" width="' + width + '" height="' + height + '" />'

    #here we are adding an item to the images table
    resp = client.put_item(
        TableName=IMAGES_TABLE,
        Item={
            'section': {'S': section},
            'img_id': {'S': img_id},
            'name': {'S': name},
            'description': {'S': description},
            'height': {'S': height},
            'width': {'S': width},
            'url': {'S': url},
            'html': {'S': html}
        }
    )

    #updating the content column of the section we placed the image in. It will hold the string representing the html image element
    client.update_item(
        TableName=SECTIONS_TABLE,
        Key={
            'name': {'S': section}
        },
        UpdateExpression='SET ImageContent = list_append(if_not_exists(ImageContent, :empty_list), :imgContent)',
        ExpressionAttributeValues={
            ':imgContent': {'L': [{
                'S': img_id
            }]},
            ':empty_list':{'L': []}
        }
    )

    body = {
            "section": section,
            "img_id": img_id,
            'html' : html
    }

    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }

    return response


def insert_Text(event, context):
    data = json.loads(event['body'])

    #retrieving the information about the text element from the data passed into the function
    section = '{}'.format(data['section'])
    text_id = '{}'.format(data['text_id'])
    
    content = '{}'.format(data['content'])

    unorderedList = data['ul'] #checks if the user requested an unordered list
    orderedList = data['ol']
    header = data['header']
    
    #here i'm splitting the string on the comma, so that we can access each element individually
    #if there is a better way to do this feel free to make changes
    if orderedList or unorderedList:
        content = content.split(", ")

    list_html = ''
    html = ''

    #checks if a list was requested. we are generating li elements for each element in the list
    if unorderedList or orderedList:
        for item in content:
            list_html += '<li>' + item + '</li>\n'
    
    #the html string will be made with either <p>, <ul>, or <ol> tags depending on what was requested
    if unorderedList == False and orderedList == False and header == False: 
        html = '<p>' + content + '</p>'
    elif unorderedList:
        html = '<ul>' +  list_html + '</ul>'
    elif orderedList:
        html = '<ol>' +  list_html + '</ol>'
    elif header:
        html = '<h3>' + content + '</h3>'

    #places the item in the text table
    resp = client.put_item(
        TableName=TEXT_TABLE,
        Item={
            'section': {'S': section},
            'text_id': {'S': text_id},
            'header': {'BOOL': header},
            'ul': {'BOOL': unorderedList},
            'ol': {'BOOL': orderedList}, 
            'html': {'S': html}
        }
    )

    #updates the section table and its content attribute. We place the html string in there
    client.update_item(
        TableName=SECTIONS_TABLE,
        Key={
            'name': {'S': section}
        },
        UpdateExpression='SET TextContent = list_append(if_not_exists(TextContent, :empty_list), :txtContent)',
        ExpressionAttributeValues={
            ':txtContent': {'L': [{ 
                'S' : text_id
            }]},
            ':empty_list':{'L': []}
        }
    )

    body = {
            "section": section,
            "text_id": text_id,
            "html": html
    }

    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }

    return response