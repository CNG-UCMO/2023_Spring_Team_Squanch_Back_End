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

#this happens when the user adds a section to the web page
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
        "name": {'S': name}
    }

    response = {
        "statusCode": 200,
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
            "section": {'S': section},
            "img_id": {'S': img_id},
            'html' : {'S': html}
    }

    response = {
        "statusCode": 200,
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
            "section": {'S': section},
            "text_id": {'S': text_id},
            "html": {'S': html}
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
    }

    return response

def get_Sections(event, context):
    table = dynamodb.Table(SECTIONS_TABLE)
    resp = table.scan(ProjectionExpression = '#nme', ExpressionAttributeNames = {'#nme': 'name'})['Items']
    response = {
        'statusCode': 200,
        'body': json.dumps(resp)
    }

    return response

def get_Section_Content(event, context):
    section_name = '{}'.format(event['pathParameters']['secName'])

    table0 = dynamodb.Table(SECTIONS_TABLE)
    resp = table0.query(KeyConditionExpression=Key('name').eq(section_name))

    items = resp.get("Items", None)

    ImageContent = items[0]['ImageContent']
    TextContent = items[0]['TextContent']

    imgList = []
    txtList = []

    table1 = dynamodb.Table(IMAGES_TABLE)
    table2 = dynamodb.Table(TEXT_TABLE)

    for val in ImageContent:
        resp1 = table1.query(KeyConditionExpression=Key('img_id').eq(val))
        items1 = resp1.get("Items", None)
        imgList.append({'id':val, 'html':items1[0]['html']})

    for val in TextContent:
        resp2 = table2.query(KeyConditionExpression=Key('text_id').eq(val))
        items2 = resp2.get("Items", None)
        txtList.append({'id':val, 'html':items2[0]['html']})

    sectionContent = {'images':imgList, 'text':txtList}

    response = {
        'statusCode': 200,
        'body': json.dumps(sectionContent) 
    }

    return response

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