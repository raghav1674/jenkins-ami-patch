import json
import os
import requests

class Section:
    '''
        describes the section of a custom message in slack
    '''

    def create_header(self,heading):
        '''
            @purpose: to create a header field
            @input: heading: str
            @returns: a header field json 
        '''
        return {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": heading
                }
            }
    
    def create_section(self,messages):
        '''
            @purpose: to create a section field
            @input: messages: str[]
            @returns: a section field json 
        '''
        section = {'type': 'section','fields':[]}
        for message in messages:
            section['fields'].append({'type':'mrkdwn','text':message})
        return section

    def create_link_button(self,label,url,style):
        '''
            @purpose: to create a link button field
            @input: label: str : label of the button, 
                    url: str : link to redirect to, 
                    style: str: style of the button
            @returns: a link button
        '''

        return {
                "type": "actions",
                    "elements":[

                        {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": label
                        },
                        "url": url,
                        "style":style
                    }
                ]
            }

    def create_standard_button(self,label,value,style):

        '''
            @purpose: to create a normal button field
            @input: label: str : label of the button, 
                    value: str : value of the button,
                    style: str: style of the button
            @returns: a normal button
        '''

        return {
                "type": "actions",
                    "elements":[

                        {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": label
                        },
                        "value": value,
                        "style": style

                    }
                ]
            }



class SlackAPI:
    '''
        slack api class
    '''
    
    def __init__(self,webhook_url):
        self.webhook_url = webhook_url
        self.blocks = []

    def create_section(self):
        '''
            @purpose: to create custom section
            @returns: a Section object
        '''
        return Section()

    def add_section(self,section):
        '''
            @purpose: to add a section to the blocks
            @input: section: Section
            @returns: None
        '''
        self.blocks.append(section)

    def send_simple_message(self,text):
        '''
            @purpose: to send a simple text message
            @input: text
            @returns: response status 
        '''
        body = {
            'text': text
        }
        return self.__send_message(body)

    def send_customized_message(self):
        '''
            @purpose: to send a custom message 
            @returns: response status 
        '''
        body = {
            'blocks': self.blocks 
        }        
        return self.__send_message(body)


    def __send_message(self,body):
        '''
            @purpose: to send the message using webhook integration with Slack
            @returns: response status 
        '''
        response = requests.post(self.webhook_url,data=json.dumps(body))
        self.blocks = []
        if response.text == 'ok':
            return {'message': 'message sent successfully','success':True}
        return {'message': f'Unable to send message {response.text}','success':False}



if __name__  == '__main__':


    # Steps to create a slack app 
    '''
        1. Click on Workspace
        2. Click on Setting & Administration
        3. Manage Apps
        4. Build a App (from the top right corner)
        5. Provide some details
        6. Webhook Integration
        7. Keep the Webhook Url somewhere safe.
    '''

    # examples using slackapi

    URL= 'https://hooks.slack.com/services/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'
    slackuse = SlackAPI(os.getenv('WEBHOOK_URL') or URL)
    # slackuse.send_simple_message('test-v1')

    section  =  slackuse.create_section()

    header = section.create_header('Test v1')
    # section1 = section.create_section(['<https://google.com|Approve>','<https://wikipedia.com|Deny>'])
    # section2 = section.create_section(['test v1-c'])

    button1 = section.create_link_button('Approve','https://google.com','primary')
    button2  = section.create_link_button('Deny','https://google.com','danger')

    slackuse.add_section(header)
    slackuse.add_section(button1)
    slackuse.add_section(button2)

    print(slackuse.send_customized_message())



