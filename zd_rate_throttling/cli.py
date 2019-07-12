import datetime
import sys
import time

import click
import requests


@click.command()
@click.option('-s', '--subdomain', required=False, default="riotgames", type=str, help='Zendesk Subdomain')
@click.option('-t', '--token', required=True, type=str, help='Authentication Token of Zendesk admin')
@click.option('-a', '--min-remaining-allowance', required=False, type=int, show_default=True,
              default=100, help='The API request allowance that must not exceed.')
@click.option('-r', '--retry-after-mins', required=False, default=5, type=int, show_default=True,
              help='Number of minutes to sleep before retrying.')
@click.option('-e', '--api-end-point', required=False, default='api/v2/users/me.json', show_default=True,
              help='The Zendesk end-point to make api calls.')
def cli(subdomain, token, min_remaining_allowance, retry_after_mins, api_end_point):
    bearer_token = 'Bearer ' + token
    header = {'Authorization': bearer_token}
    url = f'https://{subdomain}.zendesk.com/{api_end_point}'

    response = requests.get(url, headers=header)
    if response.status_code != 200:
        print('Received following error when trying to make Zendesk API call')
        sys.exit(0)

    api_quota = response.headers["X-Rate-Limit"]
    quota_remaining = response.headers['X-Rate-Limit-Remaining']
    print(f'Sub-domain: {subdomain}\nURL: {url}\nQuota: {api_quota} per minute')

    print(f'Repeated calls with me made to {url}.')
    print(f'However, if the remaining quota per minute falls below {min_remaining_allowance},'
          f' the program will sleep for {retry_after_mins} minutes before trying again')

    print('You can terminate anytime by pressing Ctrl-C')

    time.sleep(5)

    try:
        while True:
            time_now = datetime.datetime.now()
            response = requests.get(url=url, headers=header)
            if response.status_code == 200:
                quota_remaining = int(response.headers['X-Rate-Limit-Remaining'])
                print(f'Call at {time_now} | Quota Remaining: {quota_remaining}')
                if quota_remaining <= min_remaining_allowance:
                    print(f'Quota allowance hit. Sleeping for {retry_after_mins} minutes.')
                    time.sleep(retry_after_mins * 60)

    except KeyboardInterrupt as e:
        print('Terminating ...')
        sys.exit(0)


if __name__ == '__main__':
    cli()
