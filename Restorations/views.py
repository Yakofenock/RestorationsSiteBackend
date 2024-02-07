from django.http import HttpRequest, Http404
from django.shortcuts import render

from Restorations.models import *
from collections import defaultdict
from django.db.models import Sum, Q

from Site.settings import ROUND, CONFIG
from psycopg2 import connect

con = connect(
    database=CONFIG.get('Postgres DB', 'name'),
    user=CONFIG.get('Postgres DB', 'user'),
    password=CONFIG.get('Postgres DB', 'password'),
    host=CONFIG.get('Postgres DB', 'host'),
    port=CONFIG.get('Postgres DB', 'port')
)
con.set_isolation_level(0)


cur = con.cursor()
cur.execute('SELECT * FROM "Payments"')
results = cur.fetchall()
print('Payments:')
[print(paiment) for paiment in results]
print()

cur.execute('SELECT * FROM "Restorations"')
results = cur.fetchall()
print('Restorations:')
[print(soft) for soft in results]


def count_percent(val1, val2):
    return round(val1/val2*100, ROUND) if val2 else 0


def short_field(value):
    return value[:100] + ('...' if len(value) > 100 else '')


def get_work_data(work, deep=False):
    given_sum = work.donation_set.aggregate(sum=Sum('sum'))['sum'] or 0
    total_sum = work.sum or 0

    if not deep:
        return [None, given_sum, total_sum]

    work_data = {
        'name': work.name,
        'given_sum': given_sum,
        'total_sum': total_sum,
        'status': work.status,
        'percent': count_percent(given_sum, total_sum),
    }

    return [work_data, given_sum, total_sum]


def get_restoration_data(restoration, deep=False):
    if not restoration and deep:
        raise Http404()

    works = restoration.work_set.all()

    # To handle case of empty works restoration:
    works_data, given_sum, total_sum = \
        zip(*[get_work_data(work, deep=deep) for work in works]) \
            if works else ([], [0], [0])

    given_sum = sum(given_sum)
    total_sum = sum(total_sum)

    restoration_data = {
        'id': restoration.id,
        'name': restoration.name,
        'image': restoration.image.url if restoration.image else None,
        'description': restoration.description if deep else short_field(restoration.description),
        'given_sum': given_sum,
        'total_sum': total_sum,
    }
    if deep:
        restoration_data.update({'works': works_data,
                                 'percent': count_percent(given_sum, total_sum),})
    return restoration_data


def get_donaters_data(restore_id):
    donors_data = defaultdict(dict)
    total_sum_all = 0

    for donation in Donation.objects.filter(work__restore=restore_id):
        donor = donation.payment.user.username
        if 'works' not in donors_data[donor]:
            donors_data[donor]['works'] = []

        donors_data[donor]['works'].append(
            {'work': donation.work.name,
             'given_sum': donation.sum,
             'percent': count_percent(donation.sum, donation.work.sum)}
        )
        total_sum_all += donation.work.sum

    for donor, data in donors_data.items():
        donor_sum = sum(work['given_sum'] for work in data['works'])
        donors_data[donor].update({
            'total_sum': donor_sum,
            'percent_of_total': count_percent(donor_sum, total_sum_all)
        })

    return dict(donors_data)


# Views:
def info(request: HttpRequest):
    search = request.POST.get('search')
    return render(request, 'Restorations/info.html', {'search_text': search if search else ''})


def catalog(request: HttpRequest):
    restoration_statuses = list(RESTORATION_STATUSES.keys())

    # Processing deleting:
    restore_id = request.POST.get('delete')
    if restore_id:
        with con.cursor() as curs:
            curs.execute(f"UPDATE \"Restorations\" SET status='{restoration_statuses[-1]}' WHERE id = {restore_id}")
        print('Deletion done,', restore_id)

    restorations_l = Restoration.objects.filter(status=restoration_statuses[1])

    # Searching:
    search = request.POST.get('search')
    if search:
        restorations_l = restorations_l.filter(
            Q(name__icontains=search) | Q(description__icontains=search) |
            Q(work__name__icontains=search)
        ).distinct()

    restoration_list = [get_restoration_data(restoration) for restoration in restorations_l]

    return render(request, 'Restorations/catalog.html', {'restore_list': restoration_list,
                                                         'search_text': search if search else ''})


def restoration(request: HttpRequest, restore_id):
    search = request.POST.get('search')
    restoration = get_restoration_data(Restoration.objects.filter(id=restore_id).first(), deep=True)
    donaters = get_donaters_data(restore_id)
    return render(request, 'Restorations/card.html', {'restoration': restoration,
                                                      'donors':  donaters,
                                                      'search_text': search if search else ''})
