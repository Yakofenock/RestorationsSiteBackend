from django.http import HttpRequest, Http404
from django.shortcuts import render
from copy import deepcopy
from Site.settings import ROUND


MOCK_RESTORATIONS = [
    {
        'id': 0,
        'name': 'Спасо-Преображенская церковь в Костомарово',
        'image': 'http://s4.fotokto.ru/photo/full/409/4097331.jpg',
        'description': 'Спасо-Преображенская церковь в Костомарово — деревянное храмовое сооружение, '
                       'построенное в 1721 году на месте старой деревянной церкви. '
                       'Это уникальный памятник русского народного зодчества, который был уцелевшим '
                       'после пожара в начале XIX века.',
        'works': [
            {
                'name': 'Реставрация иконостаса',
                'description': 'Планируется провести комплексную реставрацию иконостаса церкви, '
                               'включая восстановление потерянных элементов и очистку от слоев '
                               'грязи и патины, накопившихся за долгие годы.',
                'status': 'InProgress',
                'given_sum': 0,
                'total_sum': 500000
            },
            {
                'name': 'Ремонт кровли',
                'description': 'Необходимо выполнить ремонт кровли церкви с заменой поврежденных '
                               'и гнилых деревянных элементов и укреплением конструкции для '
                               'предотвращения дальнейших разрушений.',
                'status': 'NotStarted',
                'given_sum': 0,
                'total_sum': 350000
            }
        ],
        'given_sum': 0,
        'total_sum': 850000
    },
    {
        'id': 1,
        'name': 'Троицкий собор в Старой Ладоге',
        'image': 'https://sozvezdie-tour.ru/Images/articles_files/599/1509px_starayaladoga_stgeorgechurch_002_4547.jpg',
        'description': 'Троицкий собор в Старой Ладоге – это один из старейших храмов в России, '
                       'построенный в начале XII века на месте древних языческих культовых сооружений. '
                       'Этот собор имеет большое историческое значение как часть древнего города Старая Ладога, '
                       'одного из старейших поселений на территории России.',
        'works': [
            {
                'name': 'Реставрация фресок',
                'description': 'Планируется провести реставрацию фресок собора, '
                               'чтобы сохранить их уникальные изображения и остановить процесс разрушения '
                               'под воздействием времени и внешних факторов.',
                'status': 'NotStarted',
                'given_sum': 0,
                'total_sum': 800000
            }
        ],
        'given_sum': 0,
        'total_sum': 800000
    },
    {
        'id': 2,
        'name': "Васильевский остров, Колонна Жана д'Арк",
        'image': 'https://avatars.dzeninfra.ru/get-zen_doc/271828/pub_6570aad027981511f07e696c_6570ad7e4c41d70d9ae0e91e/scale_1200',
        'description': 'Колонна Жана д’Арк — это памятник, посвященный французской героине, '
                       'расположенный на Васильевском острове в Санкт-Петербурге. '
                       'Этот памятник был установлен в честь 100-летия рождения Жанны д’Арк и '
                       'становится одним из символов русско-французской дружбы и солидарности.',
        'works': [
            {
                'name': 'Восстановление пьедестала',
                'description': 'Планируется восстановление основания колонны, '
                               'включая устранение повреждений и замену отсутствующих элементов, '
                               'чтобы вернуть памятнику его первоначальный вид и стабильность.',
                'status': 'InProgress',
                'given_sum': 0,
                'total_sum': 450000
            },
            {
                'name': 'Очистка и консервация поверхности',
                'description': 'Проводится очистка и консервация мраморной поверхности колонны, '
                               'чтобы предотвратить дальнейшее разрушение и сохранить ее историческую ценность.',
                'status': 'Completed',
                'given_sum': 0,
                'total_sum': 300000
            }
        ],
        'given_sum': 0,
        'total_sum': 750000
    },
    {
        'id': 3,
        'name': 'Спасо-Преображенский собор в Нижнем Новгороде',
        'image': 'http://img.tourister.ru/files/2/4/1/3/5/6/8/3/original.jpg',
        'description': 'Спасо-Преображенский собор в Нижнем Новгороде — это каменный православный храм, '
                       'построенный в 1822–1827 годах на месте старого деревянного собора XVII века. '
                       'Этот собор является одним из главных архитектурных памятников города и '
                       'символом его исторического наследия.',
        'works': [
            {
                'name': 'Реставрация иконостаса',
                'description': 'Планируется провести комплексную реставрацию иконостаса собора, '
                               'включая реставрацию и восстановление изображений и декоративных элементов.',
                'status': 'InProgress',
                'given_sum': 0,
                'total_sum': 550000
            }
        ],
        'given_sum': 0,
        'total_sum': 550000
    },
    {
        'id': 4,
        'name': 'Казанский собор в Санкт-Петербурге',
        'image': 'https://i.pinimg.com/originals/e9/a4/8d/e9a48d09b6277c96d286d6bb5f857fdc.jpg',
        'description': 'Казанский собор — это крупный православный храм, расположенный на Красной площади в Москве. '
                       'Собор был построен в начале XIX века в стиле русского классицизма и является одним из '
                       'символов столицы России и ее исторического и культурного наследия.',
        'works': [
            {

                'name': 'Восстановление икон',
                'description': 'Планируется провести восстановление и реставрацию икон собора, '
                               'включая очистку, консервацию и восстановление изображений на панелях икон.',
                'status': 'NotStarted',
                'given_sum': 0,
                'total_sum': 700000
            },
            {
                'name': 'Ремонт куполов',
                'description': 'Планируется провести ремонт куполов собора, включая замену поврежденных '
                               'и окисленных металлических элементов и восстановление крепления крестов.',
                'status': 'InProgress',
                'given_sum': 0,
                'total_sum': 450000
            }
        ],
        'given_sum': 0,
        'total_sum': 1150000
    }
]
MOCK_DONORS = [
    {
        'name': 'Иван Иванов',
        'works': [
            {'name': 'Реставрация иконостаса', 'given_sum': 300, 'total_sum': 1000},
            {'name': 'Ремонт кровли', 'given_sum': 700, 'total_sum': 1000},
            {'name': 'Ремонт кровли1', 'given_sum': 700, 'total_sum': 1000}
        ],
        'restoration_sum': 100000 # Это сумма всей реставрации
    },
    {
        'name': 'Петр Петров',
        'works': [
            {'name': 'Реставрация иконостаса', 'given_sum': 500, 'total_sum': 1000}
        ],
        'restoration_sum': 100000
    },
    {
        'name': 'Мария Сидорова',
        'works': [
            {'name': 'Реставрация иконостаса', 'given_sum': 200, 'total_sum': 1000}
        ],
        'restoration_sum': 100000
    }
]

# Technical:
# For lab1 only:
def filter_restorations(restorations, search):
    filtered_restorations = []
    for restoration in restorations:
        if (
                search.lower() in restoration['name'].lower() or
                search.lower() in [work['name'].lower() for work in restoration['works']] or
                search.lower() in restoration['description'].lower()
        ): filtered_restorations.append(restoration)
    return filtered_restorations


# For all:
def count_percent(val1, val2):
    return round(val1/val2*100, ROUND)


def get_restoration_data(restoration, works=False):
    if not restoration and works:
        raise Http404()

    if not works:
        restoration['description'] = restoration['description'][:100] + '...'
        del restoration['works']

    else:
        for i, work in enumerate(restoration['works']):
            restoration['works'][i].update(
                {'percent': count_percent(work['given_sum'], work['total_sum'])}
            )
    restoration.update(
        {'percent': count_percent(restoration['given_sum'],restoration['total_sum'])}
    )
    return restoration


def get_donater_data(donation):
    total_sum = 0
    for i, work in enumerate(donation['works']):
        donation['works'][i].update(
            {'percent': count_percent(work['given_sum'], work['total_sum'])}
        )
        total_sum += work['given_sum']
    donation.update({'given_sum': total_sum,
                     'percent': count_percent(total_sum, donation['restoration_sum'])})
    return donation


# Views:
def info(request: HttpRequest):
    search = request.POST.get('search')
    return render(request, 'Restorations/info.html', {'search_text': search if search else ''})


def catalog(request: HttpRequest):
    restorations_l = deepcopy(MOCK_RESTORATIONS)

    # Searching:
    search = request.POST.get('search')
    if search:
        restorations_l = filter_restorations(restorations_l, search)

    # Adapting for view:
    restoration_list = [get_restoration_data(restoration) for restoration in restorations_l]

    return render(request, 'Restorations/catalog.html', {'restore_list': restoration_list,
                                                         'search_text': search if search else ''})


def restoration(request: HttpRequest, restore_id):
    search = request.POST.get('search')

    restoration = next(
        (obj for obj in deepcopy(MOCK_RESTORATIONS)
         if obj['id'] == restore_id), None
    )
    restoration = get_restoration_data(restoration, works=True)
    donations = [get_donater_data(donation) for donation in deepcopy(MOCK_DONORS)]
    return render(request, 'Restorations/card.html', {'restoration': restoration,
                                                      'donors': donations,
                                                      'search_text': search if search else ''})
