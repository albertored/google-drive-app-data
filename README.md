<a href="https://www.buymeacoffee.com/albertored" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Google Drive App Data Extractor

Download hidden data that applications store in your Google Drive account.

## Installation

```
pip install -r requirements.txt
```

## Usage

In order to use this script you should first obtain a master token that will be used for the authentication. To do so:

1. Go to this Google [sign in](https://accounts.google.com/embedded/setup/v2/android) page
2. Open inspect tool on your browser (on Google Chrome right click everywhere on the page an click *Inspect* on the menu that appears)
3. Sign in and follow instructions on the web page
4. In the inspect tool search for a section named *Application* (*Storage* on Firefox)
5. Search for a section where page cookies are listed and copy the value of the `oauth_token` one, it is a string starting wiht `oauth2_4/`.
6. run the python script `google_drive_appdata.py` to obtain the master token from the OAuth one:
   ```
   python google_drive_appdata.py get-master-token --oauth-token <oauth token>
   ```
7. The scripts return the master token that should be used for downloading data, store it in a secure location.

After the master token has been obtained you can run the script to download data:
```
python google_drive_appdata.py download \
    --master-token <master token> \
    --account-email <youremail@gmail.com> \
    --app-name <app name> \
    --app-signature <app signature>
```

This will create a local folder where all the files belonging to the give app will be downloaded.
The script preserves the modification time of the files so a `ls -l` of the generated folder will show the Google Drive modification times of the downloaded files.