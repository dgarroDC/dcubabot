from icalevents import icaldownload, icalparser
from datetime import datetime, timedelta
from pytz import timezone

urls = {
    'Labo 1': 'https://calendar.google.com/calendar/ical/s57pjfhll16pqpu456eonvb760%40group.calendar.google.com/public/basic.ics',
    'Labo 2': 'https://calendar.google.com/calendar/ical/bupjqrv2va0nb3bv3o1f1jqtc0%40group.calendar.google.com/public/basic.ics',
    'Labo 3 (Graduados)': 'https://calendar.google.com/calendar/ical/n3sd0tpdt0o5855evq8uvsi3vo%40group.calendar.google.com/public/basic.ics',
    'Labo 4': 'https://calendar.google.com/calendar/ical/4lbn08p17sv8s2pfqoophliag4%40group.calendar.google.com/public/basic.ics',
    'Labo 5': 'https://calendar.google.com/calendar/ical/fu35kvoh4i2looi4drjf17k1ts%40group.calendar.google.com/public/basic.ics',
    'Labo 6': 'https://calendar.google.com/calendar/ical/g3jdt9mmsrqllp7hqfotvttsck%40group.calendar.google.com/public/basic.ics',
    'Labo 7 (Turing)': 'https://calendar.google.com/calendar/ical/krs8uvil4o36kd3a3ad5qs57dg%40group.calendar.google.com/public/basic.ics'
}

calendars = {
    # 'name': (events: List[Event], loaded: Datetime, span: Timedelta, raw: Str)
    'Labo 1': (None,),
    'Labo 2': (None,),
    'Labo 3 (Graduados)': (None,),
    'Labo 4': (None,),
    'Labo 5': (None,),
    'Labo 6': (None,),
    'Labo 7 (Turing)': (None,),
}

tz = timezone('America/Buenos_Aires')


# Devuelve el momento actual con nuestra zona horaria.
def aware_now():
    return datetime.now(tz=tz)


# Decide si vale la pena o no recargar un calendario.
def should_reload(name):
    calendar = calendars[name]
    return aware_now() - timedelta(hours=12) > calendar[1]


# Carga un calendario desde una url y lo guarda con la fecha de carga.
def load_calendar(name, retries=3):
    url = urls[name]

    while retries > 0:
        try:
            now = aware_now()
            span = timedelta(weeks=4)
            calendar_raw = icaldownload.ICalDownload().data_from_url(url)
            events = icalparser.parse_events(calendar_raw,
                                             start=now - span,
                                             end=now + span)
            calendars[name] = (events, now, span, calendar_raw)
            return calendars[name]
        except Exception:
            retries -= 1

    # Debería levantar una excepción?
    return None


# Dado el nombre de un calendario lo devuelve (y recarga si es necesario).
def get_calendar(name):
    if calendars[name][0] is None:
        retries = 100
    elif should_reload(name):
        retries = 3
    else:
        retries = 0

    # Si load_calendar falló fallbackeo
    return load_calendar(name, retries) or calendars[name]


# Repite el siguiente valor del generador, útil para ver si un generador está
# vacío sin romperlo.
def repeat_next(generator):
    empty = object()
    _next = next(generator, empty)

    if _next is empty:
        return

    yield _next
    yield _next
    yield from generator


# Este sería el API que exponemos.
# El datetime no puede ser naive.
def events_at(time):
    for name in calendars:
        calendar = get_calendar(name)

        # Vemos si podemos usar los eventos en caché o tenemos que parsear raw
        if calendar[1] - calendar[2] <= time <= calendar[1] + calendar[2]:
            events_gen = (e for e in calendar[0] if e.start <= time <= e.end)
        else:
            events_gen = (e for e in icalparser.parse_events(calendar[3],
                                                             start=time,
                                                             end=time))
        events = repeat_next(events_gen)

        if next(events, None) is None:
            yield '[%s] No tiene nada reservado' % name

        for event in events:
            yield '[%s] %s' % (name, event.summary)


# Llamado periódicamente para forzar la actualización de los calendarios
def update(context):
    for name in calendars:
        load_calendar(name)
