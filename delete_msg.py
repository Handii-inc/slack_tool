import requests
import json
import sys
import argparse
import os


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


def read_token(path):
    """
    get token string from file and check validation of token.

    :param path: string that token file path.
    :return: returns tuple (validation, token)
    """
    expanded_path = os.path.expanduser(path) if path[0] == '~' else path
    if not os.path.exists(expanded_path):
        return (False, '')
    with open(expanded_path, 'r') as f:
        token = f.read().strip()
    url = get_url('api.test')
    payload = {'token': token}
    response = requests.post(url, params=payload)
    is_vaild = to_json(response)['ok']
    return (is_vaild, token)


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
    :return: returns (is_success, list of (timestamp, text))
    """
    url = get_url('channels.history')
    get_channel_id = create_channel_id_mapper(token)
    channel_id = get_channel_id(channel)
    payload = {'token': token, 'channel': channel_id, 'count': count}
    response = requests.post(url, params=payload)
    response_data = to_json(response)
    if not response_data['ok']:
        return (False, [])
    ret = [(e['ts'], e['text']) for e in to_json(response)['messages']]
    return (True, ret[::-1])


def preview_candidates(candidates):
    """
    preview messages.

    :param candidates: object that is result of get_delete_candidate.
    """
    print('-' * 80)
    for _, text in candidates:
        print(text)
    print('-' * 80)

    return


def delete_candidates(token, channel, candidates, is_debug=False):
    """
    delete messages.

    :param token: string that is slack token.
    :param channel: string that is the name of target channel.
    :param candidates: object that is result of get_delete_candidate.
    :param is_debug: boolean that is debug or not. if this flag is True, do nothing.
    """
    url = get_url('chat.delete')
    get_channel_id = create_channel_id_mapper(token)
    channel_id = get_channel_id(channel)
    for ts, text in candidates:
        payload = {'token': token, 'channel': channel_id, 'ts': ts}
        if is_debug:
            print('[Debug] delete {}'.format(text))
        else:
            response = requests.post(url, params=payload)
            response_data = to_json(response)
            if not response_data['ok']:
                print('[Error] fail to delete {}'.format(text))

    print('Finish operation!!!')
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
    parser = argparse.ArgumentParser(description='Delete messages on slack.')
    parser.add_argument('--token', dest='token_path',           action='store',
                        required=True,                help='token file path.')
    parser.add_argument('--channel', dest='channel',           action='store',
                        required=True,                help='channel name.')
    parser.add_argument('--count', dest='count', type=int, action='store',
                        required=True,                help='count from latest.')
    parser.add_argument('--debug', dest='is_debug',           action='store_true',
                        default=False, help='debug mode. if this flag setted, do nothing.')
    args = parser.parse_args()

    is_valid, token = read_token(args.token_path)
    if not is_valid:
        print('[Error] Invalid token. Please check {}'.format(args.token_path))
        return

    is_success, candidates = get_delete_candidate(
        token, args.channel, args.count)
    if not is_success:
        print('[Error] Maybe invalid channel name. Please check {}'.format(
            args.channel))
        return

    preview_candidates(candidates)
    is_continue = query_yes_no('Delete these?')
    if not is_continue:
        print('[Warning] Stop deleting, do nothing.')
        return

    delete_candidates(token, args.channel, candidates, args.is_debug)
    return


if __name__ == '__main__':
    main()
