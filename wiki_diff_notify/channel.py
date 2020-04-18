from typing import Dict, NamedTuple

import slack  # type: ignore
from slack.web.base_client import SlackResponse  # type: ignore


class Channel(NamedTuple):

    name: str
    id: str
    private: bool

    def assert_not_archived(self, client: slack.WebClient) -> None:
        if self.private:
            self.__assert_group_is_not_archived(client)
        else:
            self.__assert_channel_is_not_archived(client)

    # public channel
    def __assert_channel_is_not_archived(self, client: slack.WebClient) -> None:
        assert not self.private
        res = client.channels_info(channel=self.id)
        if not res['ok']:
            self.__raise(res, 'channels.info failed')
        if res['channel']['is_archived']:
            self.__raise(res, f'Channel #{self.name} have been archived')

    # private channel
    def __assert_group_is_not_archived(self, client: slack.WebClient) -> None:
        assert self.private
        res = client.groups_info(channel=self.id)
        if not res['ok']:
            self.__raise(res, 'groups.info failed')
        if res['group']['is_archived']:
            self.__raise(res, f'Channel #{self.name} have been archived')

    @classmethod
    def get_channels(cls, client: slack.WebClient) -> Dict[str, 'Channel']:
        channels: Dict[str, 'Channel'] = {}

        # public channel
        res = client.channels_list(exclude_archived=1)
        if not res['ok']:
            cls.__raise(res, 'channels.list failed')
        for channel in res['channels']:
            name = channel['name']
            channels[name] = Channel(name=name, id=channel['id'], private=False)

        # private channel
        res = client.groups_list(exclude_archived=1)
        if not res['ok']:
            cls.__raise(res, 'groups.list failed')
        for group in res['groups']:
            name = group['name']
            channels[name] = Channel(name=name, id=group['id'], private=True)

        return channels

    @staticmethod
    def __raise(res: SlackResponse, message: str) -> None:
        print(res)
        raise RuntimeError(message)
