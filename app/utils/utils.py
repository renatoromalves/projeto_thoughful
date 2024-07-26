import re
from datetime import datetime

def has_value(text) -> dict:
    pattern = re.compile('(\$\d{1,3}?\,?\d{1,3}\.\d{1,2})|((\d{1,3}\,)?\d{1,3}( dollars| USD))')
    matches = re.findall(pattern, text)
    if matches:
        return True
    return False

def adjust_date(date_raw:str) -> str:
    clean_date_raw = date_raw.replace('.','').replace(',','')
    months = {'Jan': '1',
              'Feb': '2',
              'Mar': '3',
              'March': '3',
              'Apr': '4',
              'April': '4',
              'May': '5',
              'Jun': '6',
              'June': '6',
              'Jul': '7',
              'July': '7',
              'Aug': '8',
              'Sep': '9',
              'Sept': '9',
              'Oct': '10',
              'Nov': '11',
              'Dec': '12',
              }
    month,day, year = clean_date_raw.split(' ')
    adjusted_month = months.get(month)
    return ' '.join([adjusted_month,day, year])

def convert_date_to_datetime(date_raw:str) -> datetime:
    if 'ago' in date_raw:
        return datetime.now()
    new_date = adjust_date(date_raw)
    date = datetime.strptime(new_date, '%m %d %Y')

    return date


