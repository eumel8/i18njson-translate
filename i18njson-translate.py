#!/usr/bin/python

import os
import io
import click
import polib
from collections import OrderedDict
import commentjson as json
try:
    import urllib2 as request
    from urllib import quote
except:
    from urllib import request
    from urllib.parse import quote

AGENT = u"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:36.0) Gecko/20100101 Firefox/36.0"
URL = u"http://translate.google.com/translate_a/t?client=p&ie=UTF-8&oe=UTF-8" + \
      u"&source={lang}&target={to}&q={text}"

def call_api(message, lang, to, apikey):
    from googleapiclient.discovery import build
    service = build('translate', 'v2', developerKey=apikey)
    res = service.translations().list(source=lang, target=to, q=message).execute()
    return res['translations'][0]['translatedText']


@click.command()
@click.argument('inputfile', type=click.Path())
@click.argument('output', type=click.Path())
@click.option('--lang', help="From what language text should be translated." + \
    " Use one of Google Translate languages codes. Example: 'en'")
@click.option('--to', help='Target language should be in result file')
@click.option('--apikey', help='Use API with key')
@click.option('--ftype', help='Accept input file in json, po, or text format',
    type=click.Choice(['json', 'po', 'text']))
def process(inputfile, output, lang, to, apikey, ftype):
    """ Process and translate .po or JSON files and generate translated .po
    file in result. Can work with exist .po files and if in initial file
    msgid dissapear then mark translaed string as obsolete. Try to play nice
    with version control systems and follow initial file order format,
    you will get predicteable diffs.

    """

    if ftype == 'text':
        with open(inputfile) as fp:  
            for line in fp:
                entries = line.split('\r\r')

        with io.open(output, 'w', encoding='utf-8') as f:
            for entry in entries:
                translated = call_api(entry, lang, to, apikey)
                f.write(translated)
    else:
        if ftype == 'json':
            items = json.load(open(inputfile), object_pairs_hook=OrderedDict)
        else:
            items = OrderedDict()
            ifile = polib.pofile(inputfile)
            for entry in ifile:
                items[entry.msgid] = entry.msgstr


        created = False
        if os.path.exists(output):
            po = polib.pofile(output)
        else:
            po = polib.POFile()
            created = True
            po.metadata = {
                'Project-Id-Version': '1.0',
                'Report-Msgid-Bugs-To': 'you@example.com',
                'POT-Creation-Date': '2007-10-18 14:00+0100',
                'PO-Revision-Date': '2007-10-18 14:00+0100',
                'Last-Translator': 'you <you@example.com>',
                'Language-Team': 'English <yourteam@example.com>',
                'MIME-Version': '1.0',
                'Content-Type': 'text/plain; charset=utf-8',
                'Content-Transfer-Encoding': '8bit',
            }

        for k, v in items.items():
            if apikey:
                translated = call_api(k, lang, to, apikey)
            entry = po.find(k, by="msgid", include_obsolete_entries=True)
            if entry:
                entry.msgstr = translated
                entry.obsolete = False  # mark not obsolete anymore
            else:
                entry = polib.POEntry(msgid=k, msgstr=translated)
                po.append(entry)

        for entry in po:
            if not entry.msgid in items:
                click.echo("msgid '{}' marked as obsolete".format(entry.msgid))
                entry.obsolete = True

        if created:
            po.save(fpath=output)
        else:
            po.save()


if __name__ == '__main__':
    process()
