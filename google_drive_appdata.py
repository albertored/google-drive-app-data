import os
import sys
import time
import argparse
import requests
import httplib2
import datetime

import googleapiclient
from apiclient import discovery
from oauth2client import client

AUTH_URL = "https://android.clients.google.com/auth"
DRIVE_APPDATA_SCOPE = "https://www.googleapis.com/auth/drive.appdata"
DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"

DEVICE_ID = "0000000000000000"

GMS_SIG = "38918a453d07199354f8b19af05ec6562ced5788"
GMS_PKG = "com.google.android.gms"
GMS_VERSION = 11055440
GMS_UA = "GoogleAuth/1.4 (bullhead MTC20F); gzip"


def get_master_token(oauth_token):
    data = {
        "app": GMS_PKG,
        "client_sig": GMS_SIG,
        "google_play_services_version": GMS_VERSION,
        "androidId": DEVICE_ID,
        "lang": "en_US",
        "ACCESS_TOKEN": "1",
        "Token": oauth_token,
        "service": "ac2dm",
    }

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": GMS_UA,
        "device": DEVICE_ID,
        "Connection": "close",
    }

    r = requests.post(AUTH_URL, headers=headers, data=data)
    r.raise_for_status()

    token = None
    lines = r.text.split("\n")
    for l in lines:
        if l.startswith("Token"):
            token = l.split("=")[1].strip()
            break

    return token


def get_gdrive_access_token(account, master_token, app_id, app_sig):
    requestedService = "oauth2:https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.appdata https://www.googleapis.com/auth/drive.apps"

    data = {
        "androidId": DEVICE_ID,
        "lang": "en_US",
        "google_play_services_version": GMS_VERSION,
        "sdk_version": 23,
        "device_country": "us",
        "is_called_from_account_manager": 1,
        "client_sig": app_sig,
        "callerSig": GMS_SIG,
        "Email": account,
        "has_permission": 1,
        "service": requestedService,
        "app": app_id,
        "check_email": 1,
        "token_request_options": "CAA4AQ==",
        "system_partition": 1,
        "_opt_is_called_from_account_manager": 1,
        "callerPkg": GMS_PKG,
        "Token": master_token,
    }

    headers = {"Content-type": "application/x-www-form-urlencoded", "Connection": "close"}

    r = requests.post(AUTH_URL, headers=headers, data=data)
    r.raise_for_status()

    token = None
    lines = r.text.split("\n")
    for l in lines:
        if l.startswith("Auth"):
            token = l.split("=")[1].strip()
            break

    return token


def get_gdrive_service(gdrive_token):
    credentials = client.AccessTokenCredentials(gdrive_token, "Mozilla/5.0 compatible")
    credentials.scopes.add(DRIVE_FILE_SCOPE)
    credentials.scopes.add(DRIVE_APPDATA_SCOPE)

    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)

    return service


def download_files(service, app_name):
    result = (
        service.files()
        .list(
            spaces="appDataFolder",
            fields="nextPageToken, files(id, name, modifiedTime)",
            q="not trashed",
            pageSize=1000,
        )
        .execute()
    )

    files = result.get("files", [])
    nextPageToken = result.get("nextPageToken")

    while nextPageToken:
        result = (
            service.files()
            .list(
                spaces="appDataFolder",
                pageSize=1000,
                pageToken=nextPageToken,
                fields="nextPageToken, files(id, name, modifiedTime)",
            )
            .execute()
        )

        files.extend(result.get("files", []))
        nextPageToken = result.get("nextPageToken")

    if not files:
        print("No files found")
        return 0

    print(f"Found {len(files)} files, starting download")

    output_dir = f"{app_name}-{int(time.time())}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_item in files:
        print(f"Downloading file {file_item['name']} with id {file_item['id']}")
        req = service.files().get_media(fileId=file_item["id"])
        output_path = os.path.join(output_dir, f"{file_item['name']}-{file_item['id']}")
        with open(output_path, "wb") as f:
            downloader = googleapiclient.http.MediaIoBaseDownload(f, req)
            done = False
            while done is False:
                _status, done = downloader.next_chunk()

        modified_time = datetime.datetime.fromisoformat(file_item["modifiedTime"]).timestamp()
        os.utime(output_path, (modified_time, modified_time))

    return 0


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="task")

    parser_token = subparsers.add_parser("get-master-token", help="Retrieve master token from OAuth one")
    parser_token.add_argument(
        "-t",
        "--oauth-token",
        required=True,
        help="Your oauth token, it can be obtained on https://accounts.google.com/embedded/setup/v2/android",
    )

    parser_download = subparsers.add_parser("download", help="Download app data")
    parser_download.add_argument("-t", "--master-token", required=True, help="Master token")
    parser_download.add_argument(
        "-e",
        "--account-email",
        required=True,
        help="The email associated with the Google account where app data are stored",
    )
    parser_download.add_argument("-a", "--app-name", required=True, help="Application name")
    parser_download.add_argument("-sig", "--app-signature", required=True, help="Application signature")

    args = parser.parse_args()

    if args.task == "get-master-token":
        master_token = get_master_token(args.oauth_token)
        print(master_token)
        return 0

    if args.task == "download":
        gdrive_token = get_gdrive_access_token(args.account_email, args.master_token, args.app_name, args.app_signature)
        if gdrive_token is None:
            print("Failed to retrieve Google Drive access token")
            return 1

        service = get_gdrive_service(gdrive_token)
        download_files(service, args.app_name)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
