import os
import logging
import json
import requests
import urllib

from googleapiclient.discovery import build

logger = logging.getLogger('translation')

MSTRANSLATE_LANGS = ['hi']
GOOGLE_LANGS = ['hi']

def translateGoogle(jobInfo, text, fromLang, toLang = 'en'):
  try:
    logger.info("Started google translation. %s", jobInfo);

    service = build('translate', 'v2',
            developerKey = os.environ['GOOGLE_DEV_KEY'])
    result = service.translations().list(
      source=fromLang,
      target=toLang,
      q=text).execute()['translations'][0]['translatedText']

    logger.info("Completed google translation. %s", jobInfo)
    return result
  except:
    logger.info("Google translation failed. %s", jobInfo)
    return ""

def translateMicrosoft(jobInfo, text, fromLang, toLang = 'en'):
  try:
    logger.info("Started microsoft translation. %s", jobInfo);

    # get the access token
    args = {
      'client_id': os.environ['MSTRANSLATE_CLIENT_ID'],
      'client_secret': os.environ['MSTRANSLATE_CLIENT_SECRET'],
      'scope': 'http://api.microsofttranslator.com',
      'grant_type': 'client_credentials'
    }
    oauth_url = 'https://datamarket.accesscontrol.windows.net/v2/OAuth2-13'
    oauth_response = json.loads(
      requests.post(oauth_url, data=urllib.urlencode(args)).content)

    # make the translate api call
    translation_args = {
      'text': text,
      'to': toLang,
      'from': fromLang
    }
    headers={'Authorization': 'Bearer '+ oauth_response['access_token']}
    translate_url = 'https://api.microsofttranslator.com/V2/Ajax.svc/Translate?'
    translation_result = requests.get(
      translate_url + urllib.urlencode(translation_args),
      headers=headers)

    if translation_result.status_code == 200:
      logger.info("Completed microsoft translation. %s", jobInfo)
      return translation_result.content
    else:
      logger.info(
        "Microsoft translation call returned with status code %i",
        translation_result.status_code)
      return ""
  except:
    logger.info("Microsoft translation failed. %s", jobInfo)
    return ""

def translate(jobId, text, fromLang, toLang = 'en'):
  jobInfo = "fromLang: " + fromLang + " toLang: " + toLang \
     + " Job id: " + jobId

  # clip text if too long to save costs
  if len(text) > 1200:
    text = text[:1200]

  if fromLang in MSTRANSLATE_LANGS and fromLang in GOOGLE_LANGS:
    msResult = translateMicrosoft(jobInfo, text, fromLang, toLang)
    if len(msResult) > 0:
      return msResult
    else:
      return translateGoogle(jobInfo, text, fromLang, toLang)