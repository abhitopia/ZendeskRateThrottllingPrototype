import datetime
import sys
import base64
import time

import click
import requests


@click.command()
@click.option('-s', '--subdomain', required=False, default="riotgames", type=str, help='Zendesk Subdomain')
@click.option('-u', '--username', required=True, type=str, help='Email of admin user')
@click.option('-p', '--password', required=True, type=str, help='Zendesk password for the user')
@click.option('-a', '--min-remaining-allowance', required=False, type=int, show_default=True,
              default=100, help='The API request allowance that must not exceed.')
@click.option('-r', '--retry-after-mins', required=False, default=5, type=int, show_default=True,
              help='Number of minutes to sleep before retrying.')
@click.option('-e', '--api-end-point', required=False, default='api/v2/users/me.json', show_default=True,
              help='The Zendesk end-point to make api calls.')
def cli(subdomain, username, password, min_remaining_allowance, retry_after_mins, api_end_point):
    session = requests.Session()
    auth = base64.b64encode(bytes(u"{}:{}".format(username, password), "utf-8")).decode('utf8')
    header = {'Authorization': "Basic {}".format(auth)}

    response = session.get('https://{}.zendesk.com/api/v2/users/me.json'.format(subdomain), headers=header)
    if response.status_code != 200:
        print('Received following error when trying to make Zendesk API call')
        sys.exit(1)
    elif 'Anonymous user' in str(response.content):
        print("Incorrect credentials or you have not enabled password access to API. To enable access, "
              "Go to Channels > API > Password Access")
        sys.exit(1)

    url = 'https://{subdomain}.zendesk.com/{api_end_point}'.format(subdomain=subdomain, api_end_point=api_end_point)
    api_quota = response.headers["X-Rate-Limit"]
    print('Sub-domain: {subdomain}\nURL: {url}\nQuota: {api_quota} per minute'.format(subdomain=subdomain, url=url,
                                                                                      api_quota=api_quota))

    print('Repeated calls made to {}.'.format(url))
    print(
        'However, if the remaining quota per minute falls below {min_remaining_allowance}, the program will sleep for {retry_after_mins} minutes before trying again'.format(
            min_remaining_allowance=min_remaining_allowance, retry_after_mins=retry_after_mins))

    print('You can terminate anytime by pressing Ctrl-C')
    time.sleep(5)
    try:
        while True:
            time_now = datetime.datetime.now()
            response = session.get(url=url, headers=header)
            if response.status_code == 200:
                quota_remaining = int(response.headers['X-Rate-Limit-Remaining'])
                print('Call at {time_now} | Quota Remaining: {quota_remaining}'.format(time_now=time_now,
                                                                                       quota_remaining=quota_remaining))
                if quota_remaining <= min_remaining_allowance:
                    print('Quota allowance hit. Sleeping for {retry_after_mins} minutes.'.format(
                        retry_after_mins=retry_after_mins))
                    time.sleep(retry_after_mins * 60)

    except KeyboardInterrupt as e:
        print('Terminating ...')
        sys.exit(0)


if __name__ == '__main__':
    cli()
