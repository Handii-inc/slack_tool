import requests
import json
import sys


def get_url(suffix):
    """
    get slack api url.

    :param suffix: string that is slack api name.(e.g. "api.test")
    """
    base_url = 'https://slack.com/api'
    ret = '/'.join([base_url, suffix])
    return ret


def to_json(response):
    """
    convert requests result to json object.

    :param response: requests result object.
    :return: returns json object.
    """
    return json.loads(response.text)


def create_channel_id_mapper(token):
    """
    create chennel id mapper. 
    almost slack api requires channel id not channel name.
    however we want to put just channel name as identifier.
    you can easily convert channel name to id with instance that create by it.

    :param token: string that is slack token.
    :return: returns closure that can convert channel name to id.
    """
    url = get_url('channels.list')
    payload = {'token': token}
    response = requests.post(url, params=payload)
    data = to_json(response)['channels']
    mapper = dict([(e['name'], e['id']) for e in data])

    def mapping(name):
        return mapper[name]
    return mapping


def get_delete_candidate(token, channel, count):
    """
    Get candidates of specific channel id.

    :param token: string that is slack token.
    :param channel: string that is the name of target channel. 
    :param count: integer that is the number of deleteion candidates.
    :return: returns list of (timestamp, text)
    """
    url = get_url('channels.history')
    get_channel_id = create_channel_id_mapper(token)
    channel_id = get_channel_id(channel)
    payload = {'token': token, 'channel': channel_id, 'count': count}
    response = requests.post(url, params=payload)
    ret = [(e['ts'], e['text']) for e in to_json(response)['messages']]
    return ret[::-1]


def delete_candidates(token, channel, candidates):
    """
    delete messages.

    :param token: string that is slack token.
    :param channel: string that is the name of target channel.
    :param candidates: object that is result of get_delete_candidate.
    """
    url = get_url('chat.delete')
    get_channel_id = create_channel_id_mapper(token)
    channel_id = get_channel_id(channel)
    for ts, _ in candidates:
        payload = {'token': token, 'channel': channel_id, 'ts': ts}
        requests.post(url, params=payload)

    return


def query_yes_no(question):
    """
    Ask a yes/no question via input() and return their answer.

    :parma question" string that is presented to the user.
    :return: returns value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    while True:
        print(question + '[y/N]')
        choice = input().lower()
        if choice == '':
            return valid['no']
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def main():
    token = 'your_token'
    channel_name = 'general'
    count = 25

    candidates = get_delete_candidate(token, channel_name, count)
    print('-' * 80)
    for _, text in candidates:
        print(text)
    print('-' * 80)
    is_continue = query_yes_no('Delete these?')

    if is_continue:
        delete_candidates(token, channel_name, candidates)
        print('delete messages.')
        return

    print('stop deletion.')
    return


if __name__ == '__main__':
    main()
