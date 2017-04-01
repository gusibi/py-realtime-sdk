from realtime.client import RealtimeAPI, Conversation

from .test_config import app_id, app_key, master_key

client = RealtimeAPI(app_id=app_id,
                     app_key=app_key,
                     master_key=master_key)

# c = client.create_conversation(json_body={"name": "SDK_TEST", "m": ["BillGates", "SteveJobs"]})
# print c

# c = Conversation.init(client, convid='58de2d5e44d9040058bfb138')
# print c
#
# print c.add_members(['123', '234', '345', '456'])

# print c.remove_members(['456'])

# client.query_message()

# client.query_message(convid='58dcd5c31b69e60062aee271')

# client.query_message_by_from(**{'from': 'nsHaS37yQWOKXVjG3qAAcQ',
#                             'aaa': 'bbb'})

# client.query_all_message()

# conv = Conversation.init(client, convid='58dcd5c31b69e60062aee271')
# conv.query_message(limit=20)
# conv.query_message(limit=20, msgid='xU9TvbeBQGuaP2KFm3Y9Tg', max_ts='1490945250921')


client.delete_message(convid='58dcd5c31b69e60062aee271', msgid='jQTrEDQHQu+UEAzL4vq6dw', timestamp='1490950859958')

conv = Conversation.init(client, convid='58dcd5c31b69e60062aee271')
conv.query_message(limit=20)
