import os, sys
import subprocess
from subprocess import Popen, PIPE
import time
from slackclient import SlackClient
import random as rand
from gsheets import GApp

commMood = [        "how are you",
                    "how is it going",
                    "how's it going",
                    "how are you doing"]

commDNs  = [        "what are my DN",
                    "tell me my DN",
                    "what are my stocks",
                    "what are my lines"
]

respUnknown = [     "Dunno, what you mean.",
                    "English. Do you speak it?",
                    "Please speak clearly.",
                    "What are you saying?",
                    "You don\'t make any sense.",
                    "I think you lost your mind.",
                    "You are loosing your mind.",
                    "Can you be a bit more precise?"]

respMood = [        "Meh.",
                    "I think you ought to know I\'m feeling very depressed.",
                    "Life? Don\'t talk to me about life!",
                    "Life. Loathe it or ignore it. You can't like it.",
                    "Ehh, mais ou menos.",
                    "Let\'s talk about more important things."]

# starterbot's ID as an environment variable
BOT_NAME = 'steve'
BOT_ID = os.environ.get("BOT_ID")
DEBUG = False

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# spreadsheet ids
MY_DNID = '12mzn6soIUlPeWOQINdXH7PzClHvmCD9HxAfAigSL0pY'
gsheets = GApp(MY_DNID)

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def direct(response):
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    if DEBUG:
        print(command)
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    elif any(word in command for word in commMood):
        response = rand.choice(respMood)
    elif command.startswith("start"):
        if "flypad" in command:
            response = "Starting flyPAD UI..."
            rc=start_flypad()
            if rc == None:
                response += "Done."
            else:
                response += "And it failed."
            print(rc)
    elif command.startswith("check"):
        if "dn" in command:
            rangeName = 'DNs A!A1:A66'
            values = gsheets.get_data(rangeName)
            if not values:
                direct('No data found.')
            else:
                direct('https://docs.google.com/a/neuro.fchampalimaud.org/spreadsheets/d/12mzn6soIUlPeWOQINdXH7PzClHvmCD9HxAfAigSL0pY/edit?usp=sharing')
    else:
        response = rand.choice(respUnknown)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def start_flypad():
    proc = Popen('python3 ~/workspace/flypad-flat-ui/flypadui.pyw ', stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = True)
    return proc.returncode

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
            if output and 'text' in output and BOT_NAME in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(BOT_NAME)[1].strip().lower(), \
                       output['channel']
    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print(BOT_NAME + " is connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
