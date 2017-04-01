# -*-coding: utf-8 -*-

import time

import leancloud
from leancloud.errors import LeanCloudError

from .oauth2 import OAuth2API
from .bind import bind_method, RealtimeAPIError
from .helper import md5_constructor as md5


SUPPORTED_FORMATS = ['json']


class RealtimeAPI(OAuth2API):

    host = 'api.leancloud.cn'
    base_path = '/1.1'
    access_token_field = 'access_token'
    protocol = 'https'
    api_name = 'Realtime'
    x_ratelimit_remaining  = None
    x_ratelimit = None

    def __init__(self, *args, **kwargs):
        format = kwargs.get('format', 'json')
        self.json_body = kwargs.get('json_body', None)
        if format in SUPPORTED_FORMATS:
            self.format = format
        else:
            raise Exception("Unsupported format")
        super(RealtimeAPI, self).__init__(**kwargs)

    create_conversation = bind_method(
        method="POST",
        path='/classes/_Conversation',
        signature=False,
        accepts_parameters=['json_body'],
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#增删普通对话成员
    manage_members = bind_method(
        method="PUT",
        path='/classes/_Conversation/{convid}',
        signature=False,
        accepts_parameters=['convid', 'json_body'],
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#获取某个对话的聊天记录
    query_message = bind_method(
        method="GET",
        path="/rtm/messages/history",
        signature=False,
        include_secret=True,
        accepts_parameters=['convid', 'max_ts', 'msgid', 'limit',
                            'reversed', 'peerid', 'nonce',
                            'signature_ts', 'signature'],
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#获取某个用户发送的聊天记录
    query_message_by_from = bind_method(
        method="GET",
        path="/rtm/messages/history",
        signature=False,
        include_secret=True,
        include_signed=True,
        accepts_parameters=['from', 'max_ts', 'msgid', 'limit']
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#获取应用的所有聊天记录
    query_all_message = bind_method(
        method="GET",
        path="/rtm/messages/history",
        signature=False,
        include_secret=True,
        include_signed=True,
        accepts_parameters=['max_ts', 'msgid', 'limit']
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#通过_REST_API_发消息
    send_message = bind_method(
        method='POST',
        path="/rtm/messages",
        include_secret=True,
        accepts_parameters=['json_body']
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#删除聊天记录
    delete_message = bind_method(
        method='DELETE',
        path="/rtm/messages/logs",
        include_secret=True,
        accepts_parameters=['convid', 'msgid', 'timestamp']
    )

    # https://leancloud.cn/docs/realtime_rest_api.html#强制修改聊天记录
    update_message = bind_method(
        method='PUT',
        path="/rtm/messages/logs",
        include_secret=True,
        accepts_parameters=['json_body']
    )

    client_kick = bind_method(
        method="POST",
        path='/rtm/client/kick',
        signature=False,
        accepts_parameters=['json_body'],
    )



class Conversation(object):

    def __init__(self, client, convid):
        '''
        :param client:  realtime client
        :param convid: conversation id
        '''
        self.client = client
        self.convid = convid

    def _get_conversation_by_id(self, id):
        leancloud.init(self.client.app_id, self.client.app_key)
        _Conversation = leancloud.Object.extend('_Conversation')
        # query = leancloud.Query('_Conversation')
        # 也可以获取 Todo 的 query 属性
        query = _Conversation.query

        # 这里填入需要查询的 objectId
        try:
            conversation = query.get(id)
        except LeanCloudError as e:
            raise RealtimeAPIError(e.code, e.error)
        return conversation

    @classmethod
    def init(cls, client, convid=None, name=None, m=None, c=None, mu=None):
        '''
        :param client:  realtime client
        :param convid: conversation id
        :param name:    conversation name
        :param m:       conversation members
        :param c:       conversation creator clientid
        :param mu:      对话中设置了静音的成员，仅针对 iOS 以及 Windows Phone 用户有效。
        '''
        instance = cls(client=client, convid=convid)
        if convid:
            conversation = instance._get_conversation_by_id(convid)
            if not conversation:
                raise RealtimeAPIError('404', 'Conversation not found')
            return cls(client=client, convid=convid)
        else:
            params = {
                "name": name,
                "m": m,
                "mu": mu,
            }
            conversation = self.client.create_conversation(json_body=params)
            return cls(client=client, convid=conversation.get('objectId'))

    def add_members(self, client_ids=None):
        params = {
            "m": {
                "__op": "AddUnique",
                "objects": client_ids
            }
        }
        return self.client.manage_members(convid=self.convid, json_body=params)

    def remove_members(self, client_ids=None):
        params = {
            "m": {
                "__op": "Remove",
                "objects": client_ids
            }
        }
        return self.client.manage_members(convid=self.convid, json_body=params)

    def query_message(self, max_ts=None, msgid=None, limit=20, reversed=False,
                      peerid=None, nonce=None, signature_ts=None):
        '''
        :param max_ts:       可选  查询起始的时间戳，返回小于这个时间(不包含)的记录。默认是当前时间。
        :param msgid:        可选  起始的消息 id，使用时必须加上对应消息的时间戳 max_ts 参数，一起作为查询的起点。
        :param limit:        可选  返回条数限制，可选，默认 20 条，最大 1000 条。
        :param reversed:     可选  以默认排序相反的方向返回结果。布尔值，默认为 false
        :param peerid:       可选  查看者 id（签名参数）
        :param nonce:        可选  签名随机字符串（签名参数）
        :param signature_ts: 可选  签名时间戳（签名参数）
        :param signature:    可选  签名
        :return: message list
        '''
        params = dict(
            max_ts=max_ts,
            msgid=msgid,
            limit=limit,
            reversed=reversed,
            peerid=peerid,
            nonce=nonce,
            signature_ts=signature_ts,
        )
        if peerid:
            timestamp = signature_ts or '%d' % (time.time() * 1000)
            nonce = nonce or timestamp
            sign_str = '{appid}:{peerid}:{convid}:{nonce}:{sign_ts}'.format(
                appid=self.client.app_id,
                peerid=peerid,
                convid=self.convid,
                nonce=nonce,
                sign_ts=timestamp
            )
            signature = md5(sign_str).hexdigest()
            params.update({
                'nonce': nonce,
                'signature_ts': timestamp,
                'signature': signature,
            })
        messages = self.client.query_message(**params)
        return messages

    def send(self, from_peer, message, transient=True, no_sync=False, push_data={}):
        '''
        :param from_peer: 必填  消息的发件人 client Id
        :param message:   必填	消息内容（这里的消息内容的本质是字符串，但是我们对字符串内部的格式没有做限定，
                                理论上开发者可以随意发送任意格式，只要大小不超过 5 KB 限制即可。）
        :param transient: 可选	是否为暂态消息（由于向后兼容的考虑，默认为 true，请注意设置这个值。
        :param no_sync:   可选	默认情况下消息会被同步给在线的 from_peer 用户的客户端，设置为 true 禁用此功能。
        :param push_data: 可选	以消息附件方式设置本条消息的离线推送通知内容。
                                如果目标接收者使用的是 iOS 设备并且当前不在线，我们会按照该参数填写的内容来发离线推送。
        :return:  {}
        '''
        pass


    def send_text(self, from_peer, message, transient=True, no_sync=False, push_data={}):
        pass
