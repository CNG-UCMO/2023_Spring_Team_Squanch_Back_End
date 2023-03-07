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
   
   #this will be included in the response. It contains the html string
    body = {
        "name": {'S': name}
    }

    #this is what we will return to whoever called us.  
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

    newItem = { 'imgID': {}, 'imgHTML': {} }

    
    newItem['imgID']['S'] = img_id
    newItem['imgHTML']['S'] = html

    #updating the content column of the section we placed the image in. It will hold the string representing the html image element
    #need to figure out how to not overwrite what was previously in there 
    client.update_item(
        TableName=SECTIONS_TABLE,
        Key={
            'name': {'S': section}
        },
        UpdateExpression='SET ImageContent = list_append(if_not_exists(content, :empty_list), :imgContent)',
        ExpressionAttributeValues={
            ':imgContent': {'L': [{
                'M': newItem
            }]},
            ':empty_list':{'L': []}
        }
    )

    #this will be included in the response. It contains the html string. probably don't need to include all this info
    body = {
            "section": {'S': section},
            "img_id": {'S': img_id},
            'html' : {'S': html}
    }

    #this is what we will return to whoever called us. 
    response = {
        "statusCode": 200,
        "body": json.dumps(body),
    }

    return response


#this happens when the user adds a text element to the web page
def insert_Text(event, context):
    data = json.loads(event['body'])

    #retrieving the information about the text element from the data passed into the function
    section = '{}'.format(data['section'])
    text_id = '{}'.format(data['text_id'])
    
    content = '{}'.format(data['content'])

    unorderedList = data['ul'] #checks if the user requested an unordered list
    orderedList = data['ol'] 
    
    #if the user requested a list the data will have this information as well
    list_title = '{}'.format(data['list_title'])
    list_content = '{}'.format(data['list_content'])

    #here i'm splitting the string on the comma, so that we can access each element individually
    #if there is a better way to do this feel free to make changes
    item_list = list_content.split(", ")

    list_html = ''
    html = ''

    #checks if a list was requested. we are generating li elements for each element in the list
    if unorderedList or orderedList:
        for item in item_list:
            list_html += '<li>' + item + '</li>\n'
    
    #the html string will be made with either <p>, <ul>, or <ol> tags depending on what was requested
    if unorderedList and orderedList: 
        html = '<p>' + content + '</p>'
    elif unorderedList:
        html = '<ul>' +  list_html + '</ul>'
    elif orderedList:
        html = '<ol>' +  list_html + '</ol>'

    #places the item in the text table
    resp = client.put_item(
        TableName=TEXT_TABLE,
        Item={
            'section': {'S': section},
            'text_id': {'S': text_id},
            'content': {'S': content},
            'list_title': {'S': list_title},
            'list_content': {'S': list_content},
            'ul': {'BOOL': unorderedList},
            'ol': {'BOOL': orderedList}, 
            'html': {'S': html}
        }
    )

    newItem = { 'txtID': {}, 'txtHTML': {} }

    newItem['txtID']['S'] = text_id
    newItem['txtHTML']['S'] = html

    #updates the section table and its content attribute. We place the html string in there
    client.update_item(
        TableName=SECTIONS_TABLE,
        Key={
            'name': {'S': section}
        },
        UpdateExpression='SET TextContent = list_append(if_not_exists(content, :empty_list), :txtContent)',
        ExpressionAttributeValues={
            ':txtContent': {'L': [{ 
                'M' : newItem
            }]},
            ':empty_list':{'L': []}
        }
    )

    #this is included in the response
    body = {
            "section": {'S': section},
            "text_id": {'S': text_id},
            "html": {'S': html}
    }

    #this is what we're sending back to whoever called us
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

    table = dynamodb.Table(SECTIONS_TABLE)
    resp = table.query(KeyConditionExpression=Key('name').eq(section_name))

    items = resp.get("Items", None)
    
    response = {
        'statusCode': 200,
        'body': json.dumps(items[0])
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

    response = {
        'statusCode': 200,
        'body': "Successfully deleted Text Item"
    }

    return response