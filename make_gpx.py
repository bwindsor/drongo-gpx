import json
import datetime
import math
from functools import reduce
from itertools import accumulate


def lambda_handler(event, context):
    print(json.dumps(event))

    query = event.get("queryStringParameters", {})

    length_metres = int(query.get("length", "10000"))
    start_time = datetime.datetime.strptime(query["start_time"], '%Y%m%d%H%M')
    hours = int(query.get("hours", "0"))
    minutes = int(query.get("minutes", "0"))
    duration = datetime.timedelta(hours=hours) + datetime.timedelta(minutes=minutes)
    if duration == datetime.timedelta(seconds=0):
        raise Exception("Duration cannot be zero")

    lat = float(query["lat"])
    lon = float(query["lon"])

    assert length_metres > 0
    assert length_metres < 1000000
    assert duration.total_seconds() < 86400 * 10
    assert lat >= -90
    assert lat <= 90
    assert lon <= 180
    assert lon >= -180

    gpx_string = make_gpx(length_metres, start_time, duration, lat, lon)

    return {
        'statusCode': 200,
        'body': gpx_string
    }


def make_gpx(length_metres: int, start_time: datetime.datetime, duration: datetime.timedelta, lat: float, lon: float):
    lat_lon_scaled = calculate_coordinates(length_metres, example_lat_lons, lat, lon, duration)
    timestamps = [start_time + datetime.timedelta(seconds=x) for x in range(0, round(duration.total_seconds()))]
    assert len(timestamps) == len(lat_lon_scaled)

    s = XMLBuilder()
    s.add("""
<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="StravaGPX" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
""")
    s.open_tag("metadata")
    s.open_tag("time")
    s.add(format_date(start_time))
    s.close_tag("time")
    s.close_tag("metadata")
    s.open_tag("trk")
    s.open_tag("trkseg")
    for ts, lat_lon in zip(timestamps, lat_lon_scaled):
        lat, lon = lat_lon
        s.open_tag("trkpt", {'lat': "{0:.7f}".format(lat), 'lon': "{0:.7f}".format(lon)})
        s.open_tag("time")
        s.add(format_date(ts))
        s.close_tag("time")
        s.close_tag("trkpt")
    s.close_tag("trkseg")
    s.close_tag("trk")
    s.add("""
    </gpx>
    """)

    return s.to_string()


def format_date(d):
    return d.replace(microsecond=0, tzinfo=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def calculate_coordinates(length_metres: int, lat_lon, lat, lon, duration: datetime.timedelta):
    xy = lat_lon_to_xy(lat_lon)
    diffs = [math.sqrt((xy1[0] - xy2[0]) ** 2 + (xy1[1] - xy2[1]) ** 2) for xy1, xy2 in zip(xy[1:], xy[:-1])]
    total_length = sum(diffs)
    scale_factor = length_metres / total_length
    xy_scaled = [[x * scale_factor, y * scale_factor] for x, y in xy]
    xy_scaled = interpolate_coordinates(xy_scaled, diffs, round(duration.total_seconds()))
    lat_lon_scaled = xy_to_lat_lon(xy_scaled, lat, lon)
    return lat_lon_scaled


def interpolate_coordinates(xy, xy_diffs, num_points):
    num_new_points = num_points - len(xy)
    total_length = sum(xy_diffs)
    cumulative_length = list(accumulate(xy_diffs))
    distances = [i / (num_new_points - 1) * total_length for i in range(num_new_points)]

    current_segment = 0
    xy_interp = [xy[0]]
    for d in distances:
        while d > cumulative_length[current_segment]:
            current_segment += 1
            xy_interp.append(xy[current_segment].copy())
        segment_start = cumulative_length[current_segment - 1] if current_segment > 0 else 0
        segment_end = cumulative_length[current_segment]
        p = (d - segment_start) / (segment_end - segment_start)
        x = xy[current_segment][0] * (1 - p) + xy[current_segment + 1][0] * p
        y = xy[current_segment][1] * (1 - p) + xy[current_segment + 1][1] * p
        xy_interp.append([x, y])
    while current_segment < len(xy) - 1:
        current_segment += 1
        xy_interp.append(xy[current_segment].copy())
    assert len(xy_interp) == num_points
    return xy_interp


EARTH_CIRCUM_M = 40000 * 1000


def xy_to_lat_lon(xy, lat0, lon0):
    return [
        [
            y * 360 / EARTH_CIRCUM_M + lat0,
            x * 360 / EARTH_CIRCUM_M / math.cos(0.5 * (y * 360 / EARTH_CIRCUM_M + lat0 + lat0) * math.pi / 180) + lon0
        ] for x, y in xy
    ]


def lat_lon_to_xy(lat_lons):
    lat0 = lat_lons[0][0]
    lon0 = lat_lons[0][1]
    return [
        [(lon - lon0) * EARTH_CIRCUM_M * math.cos(0.5 * (lat + lat0) * math.pi / 180) / 360,
         (lat - lat0) * EARTH_CIRCUM_M / 360] for lat, lon in lat_lons
    ]


class XMLBuilder:
    def __init__(self):
        self.string = ""

    def add(self, s):
        self.string += s

    def open_tag(self, tag_name, attributes=None):
        if attributes is None:
            attributes = {}
        self.string += "<" + tag_name + reduce(lambda a, b: a + b,
                                               [" " + k + "=\"" + v + "\"" for k, v in attributes.items()], "") + ">"

    def close_tag(self, tag_name):
        self.string += "</" + tag_name + ">"

    def to_string(self):
        return self.string


example_lat_lons = [
    [50.6093190, -1.1961680],
    [50.6093030, -1.1963440],
    [50.6092870, -1.1965210],
    [50.6092700, -1.1966970],
    [50.6092540, -1.1968740],
    [50.6092380, -1.1970500],
    [50.6092220, -1.1972270],
    [50.6092060, -1.1974030],
    [50.6091900, -1.1975790],
    [50.6091740, -1.1977560],
    [50.6091570, -1.1979320],
    [50.6091410, -1.1981090],
    [50.6091710, -1.1982760],
    [50.6092550, -1.1984320],
    [50.6093380, -1.1985890],
    [50.6094210, -1.1987450],
    [50.6095040, -1.1989020],
    [50.6095880, -1.1990580],
    [50.6096710, -1.1992140],
    [50.6097540, -1.1993710],
    [50.6098370, -1.1995270],
    [50.6099200, -1.1996840],
    [50.6100040, -1.1998400],
    [50.6100870, -1.1999960],
    [50.6101700, -1.2001530],
    [50.6101990, -1.2003230],
    [50.6102010, -1.2005000],
    [50.6102020, -1.2006770],
    [50.6102430, -1.2008440],
    [50.6103300, -1.2009980],
    [50.6104170, -1.2011520],
    [50.6105040, -1.2013070],
    [50.6105910, -1.2014610],
    [50.6106780, -1.2016160],
    [50.6107650, -1.2017700],
    [50.6108520, -1.2019240],
    [50.6109060, -1.2020850],
    [50.6108860, -1.2022610],
    [50.6108650, -1.2024370],
    [50.6107860, -1.2025930],
    [50.6106940, -1.2027440],
    [50.6106010, -1.2028950],
    [50.6105090, -1.2030460],
    [50.6104160, -1.2031970],
    [50.6103230, -1.2033480],
    [50.6102310, -1.2034990],
    [50.6101380, -1.2036500],
    [50.6100460, -1.2038010],
    [50.6099530, -1.2039520],
    [50.6098600, -1.2041040],
    [50.6097680, -1.2042550],
    [50.6096750, -1.2044060],
    [50.6095830, -1.2045570],
    [50.6094900, -1.2047080],
    [50.6093970, -1.2048590],
    [50.6093050, -1.2050100],
    [50.6092120, -1.2051610],
    [50.6090880, -1.2052830],
    [50.6089470, -1.2053910],
    [50.6088070, -1.2054990],
    [50.6086660, -1.2056070],
    [50.6085030, -1.2055590],
    [50.6083380, -1.2054960],
    [50.6081730, -1.2054320],
    [50.6080070, -1.2053680],
    [50.6078420, -1.2053040],
    [50.6076770, -1.2052400],
    [50.6075000, -1.2052300],
    [50.6073230, -1.2052210],
    [50.6071460, -1.2052130],
    [50.6069690, -1.2052040],
    [50.6067920, -1.2051960],
    [50.6066150, -1.2051880],
    [50.6064380, -1.2051790],
    [50.6062610, -1.2051710],
    [50.6060840, -1.2051620],
    [50.6059070, -1.2051540],
    [50.6057300, -1.2051450],
    [50.6055530, -1.2051370],
    [50.6053760, -1.2051290],
    [50.6051990, -1.2051200],
    [50.6050220, -1.2051120],
    [50.6048460, -1.2051030],
    [50.6046690, -1.2050950],
    [50.6044920, -1.2050860],
    [50.6043150, -1.2050780],
    [50.6041380, -1.2050750],
    [50.6039630, -1.2051040],
    [50.6037880, -1.2051330],
    [50.6036140, -1.2051610],
    [50.6034540, -1.2052210],
    [50.6033250, -1.2053430],
    [50.6031960, -1.2054640],
    [50.6030670, -1.2055860],
    [50.6029060, -1.2056290],
    [50.6027290, -1.2056320],
    [50.6025520, -1.2056350],
    [50.6023750, -1.2056380],
    [50.6023630, -1.2054780],
    [50.6023680, -1.2053010],
    [50.6023730, -1.2051230],
    [50.6023780, -1.2049460],
    [50.6023830, -1.2047690],
    [50.6023890, -1.2045920],
    [50.6023940, -1.2044150],
    [50.6023990, -1.2042380],
    [50.6024760, -1.2041140],
    [50.6026430, -1.2040550],
    [50.6028110, -1.2039970],
    [50.6029780, -1.2039390],
    [50.6031450, -1.2038800],
    [50.6033120, -1.2038220],
    [50.6034800, -1.2037640],
    [50.6036500, -1.2037250],
    [50.6038270, -1.2037290],
    [50.6040040, -1.2037340],
    [50.6041820, -1.2037380],
    [50.6043590, -1.2037420],
    [50.6045360, -1.2037470],
    [50.6047130, -1.2037510],
    [50.6048900, -1.2037550],
    [50.6050670, -1.2037600],
    [50.6052440, -1.2037640],
    [50.6054210, -1.2037680],
    [50.6055990, -1.2037730],
    [50.6057760, -1.2037770],
    [50.6059530, -1.2037810],
    [50.6061250, -1.2038200],
    [50.6062960, -1.2038670],
    [50.6064670, -1.2039130],
    [50.6066380, -1.2039600],
    [50.6067850, -1.2040480],
    [50.6069110, -1.2041730],
    [50.6070370, -1.2042970],
    [50.6071630, -1.2044210],
    [50.6071000, -1.2043680],
    [50.6069680, -1.2042490],
    [50.6068360, -1.2041310],
    [50.6067020, -1.2040170],
    [50.6065410, -1.2039420],
    [50.6063810, -1.2038670],
    [50.6062200, -1.2037920],
    [50.6060600, -1.2037170],
    [50.6058900, -1.2036850],
    [50.6057130, -1.2036880],
    [50.6055360, -1.2036910],
    [50.6053580, -1.2036940],
    [50.6051810, -1.2036970],
    [50.6050040, -1.2037000],
    [50.6048270, -1.2037030],
    [50.6046500, -1.2037060],
    [50.6044730, -1.2037090],
    [50.6042960, -1.2037120],
    [50.6041180, -1.2037150],
    [50.6039410, -1.2037180],
    [50.6037640, -1.2037210],
    [50.6035870, -1.2037240],
    [50.6034150, -1.2037650],
    [50.6032440, -1.2038120],
    [50.6030730, -1.2038580],
    [50.6029020, -1.2039040],
    [50.6027310, -1.2039500],
    [50.6025600, -1.2039970],
    [50.6025830, -1.2039110],
    [50.6026900, -1.2037700],
    [50.6027960, -1.2036280],
    [50.6028420, -1.2035590],
    [50.6027230, -1.2036890],
    [50.6026030, -1.2038200],
    [50.6024840, -1.2039510],
    [50.6023350, -1.2040290],
    [50.6021610, -1.2040610],
    [50.6019870, -1.2040940],
    [50.6018120, -1.2041260],
    [50.6016380, -1.2041580],
    [50.6014640, -1.2041900],
    [50.6012910, -1.2042280],
    [50.6011180, -1.2042680],
    [50.6009460, -1.2043080],
    [50.6007730, -1.2043480],
    [50.6006000, -1.2043870],
    [50.6006110, -1.2042700],
    [50.6006770, -1.2041060],
    [50.6007430, -1.2039420],
    [50.6008420, -1.2037960],
    [50.6009490, -1.2036550],
    [50.6010560, -1.2035130],
    [50.6011620, -1.2033720],
    [50.6012690, -1.2032300],
    [50.6013760, -1.2030890],
    [50.6014830, -1.2029470],
    [50.6015890, -1.2028060],
    [50.6016960, -1.2026640],
    [50.6018450, -1.2025800],
    [50.6020110, -1.2025170],
    [50.6021770, -1.2024550],
    [50.6023420, -1.2023920],
    [50.6025090, -1.2023310],
    [50.6026760, -1.2022740],
    [50.6028440, -1.2022170],
    [50.6030120, -1.2021610],
    [50.6031800, -1.2021040],
    [50.6033480, -1.2020480],
    [50.6035160, -1.2019910],
    [50.6036920, -1.2019840],
    [50.6038690, -1.2019810],
    [50.6040470, -1.2019780],
    [50.6042240, -1.2019750],
    [50.6044010, -1.2019720],
    [50.6045640, -1.2020230],
    [50.6047180, -1.2021110],
    [50.6048710, -1.2021990],
    [50.6050250, -1.2022880],
    [50.6051790, -1.2023760],
    [50.6053390, -1.2024470],
    [50.6055130, -1.2024790],
    [50.6056870, -1.2025120],
    [50.6058610, -1.2025440],
    [50.6060350, -1.2025770],
    [50.6062090, -1.2026090],
    [50.6063830, -1.2026430],
    [50.6065570, -1.2026760],
    [50.6067310, -1.2027100],
    [50.6069050, -1.2027430],
    [50.6070820, -1.2027460],
    [50.6072590, -1.2027430],
    [50.6074360, -1.2027400],
    [50.6073150, -1.2027420],
    [50.6071380, -1.2027450],
    [50.6069610, -1.2027480],
    [50.6067830, -1.2027510],
    [50.6066060, -1.2027540],
    [50.6064290, -1.2027570],
    [50.6062520, -1.2027600],
    [50.6060790, -1.2027280],
    [50.6059070, -1.2026840],
    [50.6057360, -1.2026390],
    [50.6055640, -1.2025940],
    [50.6053930, -1.2025500],
    [50.6052280, -1.2024890],
    [50.6050750, -1.2024010],
    [50.6049210, -1.2023120],
    [50.6047670, -1.2022240],
    [50.6046140, -1.2021360],
    [50.6044580, -1.2020560],
    [50.6042810, -1.2020590],
    [50.6041040, -1.2020620],
    [50.6039270, -1.2020650],
    [50.6037490, -1.2020680],
    [50.6035720, -1.2020710],
    [50.6033950, -1.2020740],
    [50.6032230, -1.2021100],
    [50.6030550, -1.2021640],
    [50.6028860, -1.2022180],
    [50.6027170, -1.2022720],
    [50.6025490, -1.2023270],
    [50.6023740, -1.2023450],
    [50.6023560, -1.2021800],
    [50.6023490, -1.2020030],
    [50.6023420, -1.2018260],
    [50.6023350, -1.2016490],
    [50.6023280, -1.2014720],
    [50.6023210, -1.2012950],
    [50.6023140, -1.2011180],
    [50.6023070, -1.2009410],
    [50.6023000, -1.2007640],
    [50.6022930, -1.2005870],
    [50.6022860, -1.2004100],
    [50.6022790, -1.2002330],
    [50.6022720, -1.2000560],
    [50.6022650, -1.1998790],
    [50.6022580, -1.1997010],
    [50.6022580, -1.1995250],
    [50.6022680, -1.1993480],
    [50.6022780, -1.1991710],
    [50.6022890, -1.1989940],
    [50.6022990, -1.1988170],
    [50.6023090, -1.1986400],
    [50.6023390, -1.1984660],
    [50.6023700, -1.1982910],
    [50.6024010, -1.1981170],
    [50.6024320, -1.1979420],
    [50.6024630, -1.1977680],
    [50.6023790, -1.1976170],
    [50.6022820, -1.1974680],
    [50.6021850, -1.1973200],
    [50.6020890, -1.1971710],
    [50.6021310, -1.1970080],
    [50.6022200, -1.1968860],
    [50.6023940, -1.1969140],
    [50.6025690, -1.1969420],
    [50.6027200, -1.1970180],
    [50.6028450, -1.1971430],
    [50.6029710, -1.1972690],
    [50.6030480, -1.1974140],
    [50.6030490, -1.1975910],
    [50.6030510, -1.1977680],
    [50.6030520, -1.1979450],
    [50.6030530, -1.1981220],
    [50.6030540, -1.1983000],
    [50.6030550, -1.1984770],
    [50.6030570, -1.1986540],
    [50.6030580, -1.1988310],
    [50.6030590, -1.1990080],
    [50.6030600, -1.1991850],
    [50.6030610, -1.1993630],
    [50.6030630, -1.1995400],
    [50.6030640, -1.1997170],
    [50.6030650, -1.1998940],
    [50.6030660, -1.2000710],
    [50.6030680, -1.2002490],
    [50.6030690, -1.2004260],
    [50.6030700, -1.2006030],
    [50.6030710, -1.2007800],
    [50.6030720, -1.2009570],
    [50.6030740, -1.2011340],
    [50.6031040, -1.2011860],
    [50.6031830, -1.2010270],
    [50.6032610, -1.2008680],
    [50.6033400, -1.2007100],
    [50.6034190, -1.2005510],
    [50.6034980, -1.2003920],
    [50.6035760, -1.2002340],
    [50.6036990, -1.2001110],
    [50.6038390, -1.2000010],
    [50.6039780, -1.1998920],
    [50.6041170, -1.1997820],
    [50.6042560, -1.1996730],
    [50.6044230, -1.1996400],
    [50.6046000, -1.1996370],
    [50.6047730, -1.1996440],
    [50.6048990, -1.1997680],
    [50.6050260, -1.1998920],
    [50.6051520, -1.2000170],
    [50.6052790, -1.2001400],
    [50.6054080, -1.2002620],
    [50.6055370, -1.2003830],
    [50.6056660, -1.2005040],
    [50.6057950, -1.2006260],
    [50.6059030, -1.2007660],
    [50.6060090, -1.2009080],
    [50.6061150, -1.2010500],
    [50.6062210, -1.2011920],
    [50.6063930, -1.2012350],
    [50.6065650, -1.2012780],
    [50.6067240, -1.2013410],
    [50.6068380, -1.2014770],
    [50.6069510, -1.2016130],
    [50.6070650, -1.2017490],
    [50.6071780, -1.2018850],
    [50.6072920, -1.2020210],
    [50.6074520, -1.2020170],
    [50.6076240, -1.2019770],
    [50.6077970, -1.2019360],
    [50.6079690, -1.2018950],
    [50.6081410, -1.2018540],
    [50.6083040, -1.2017840],
    [50.6084660, -1.2017130],
    [50.6086290, -1.2016420],
    [50.6086700, -1.2014810],
    [50.6086900, -1.2013050],
    [50.6087100, -1.2011290],
    [50.6087270, -1.2009530],
    [50.6087010, -1.2007780],
    [50.6086750, -1.2006030],
    [50.6086500, -1.2004280],
    [50.6086240, -1.2002520],
    [50.6085980, -1.2000770],
    [50.6085210, -1.1999240],
    [50.6084110, -1.1997850],
    [50.6083010, -1.1996460],
    [50.6081910, -1.1995070],
    [50.6080810, -1.1993680],
    [50.6080230, -1.1992010],
    [50.6079650, -1.1990340],
    [50.6079070, -1.1988660],
    [50.6078490, -1.1986990],
    [50.6078220, -1.1985260],
    [50.6078210, -1.1983490],
    [50.6078200, -1.1981710],
    [50.6078180, -1.1979940],
    [50.6078170, -1.1978170],
    [50.6078160, -1.1976400],
    [50.6078150, -1.1974630],
    [50.6078130, -1.1972860],
    [50.6078120, -1.1971080],
    [50.6078110, -1.1969310],
    [50.6078100, -1.1967540],
    [50.6078090, -1.1965770],
    [50.6078070, -1.1964000],
    [50.6078060, -1.1962230],
    [50.6078050, -1.1960450],
    [50.6078040, -1.1958680],
    [50.6078030, -1.1956910],
    [50.6078010, -1.1955140],
    [50.6078000, -1.1953370],
    [50.6077990, -1.1951600],
    [50.6077980, -1.1949820],
    [50.6077170, -1.1948460],
    [50.6075740, -1.1947410],
    [50.6074310, -1.1946370],
    [50.6072760, -1.1946490],
    [50.6071140, -1.1947220],
    [50.6069540, -1.1947970],
    [50.6068190, -1.1949110],
    [50.6066840, -1.1950260],
    [50.6065490, -1.1951400],
    [50.6064320, -1.1952140],
    [50.6064310, -1.1950370],
    [50.6064300, -1.1948590],
    [50.6064290, -1.1946820],
    [50.6064270, -1.1945050],
    [50.6064720, -1.1943370],
    [50.6065380, -1.1941720],
    [50.6066040, -1.1940080],
    [50.6066700, -1.1938430],
    [50.6067360, -1.1936790],
    [50.6068020, -1.1935150],
    [50.6069550, -1.1934620],
    [50.6071300, -1.1934400],
    [50.6073060, -1.1934190],
    [50.6074820, -1.1933970],
    [50.6076580, -1.1933750],
    [50.6078010, -1.1932900],
    [50.6079210, -1.1931600],
    [50.6080370, -1.1930260],
    [50.6081440, -1.1928840],
    [50.6082500, -1.1927420],
    [50.6083560, -1.1926010],
    [50.6084620, -1.1924590],
    [50.6085690, -1.1923170],
    [50.6086940, -1.1922360],
    [50.6088630, -1.1922900],
    [50.6090320, -1.1923440],
    [50.6091340, -1.1923250],
    [50.6090940, -1.1921520],
    [50.6090550, -1.1919790],
    [50.6090150, -1.1918070],
    [50.6088970, -1.1917340],
    [50.6087200, -1.1917370],
    [50.6086990, -1.1919130],
    [50.6086780, -1.1920890],
    [50.6086580, -1.1922650],
    [50.6086950, -1.1923930],
    [50.6088720, -1.1924080],
    [50.6090480, -1.1924220],
    [50.6091880, -1.1925260],
    [50.6093240, -1.1926400],
    [50.6094600, -1.1927540],
    [50.6095960, -1.1928670],
    [50.6097320, -1.1929810],
    [50.6098680, -1.1930950],
    [50.6100040, -1.1932080],
    [50.6100680, -1.1933650],
    [50.6100810, -1.1935330],
    [50.6099750, -1.1936750],
    [50.6099390, -1.1938400],
    [50.6099400, -1.1940170],
    [50.6099410, -1.1941940],
    [50.6099430, -1.1943710],
    [50.6099440, -1.1945480],
    [50.6099820, -1.1947210],
    [50.6100220, -1.1948940],
    [50.6100390, -1.1950620],
    [50.6099450, -1.1952130],
    [50.6098510, -1.1953630],
    [50.6097510, -1.1954490],
    [50.6096280, -1.1953210],
    [50.6095050, -1.1951940],
    [50.6093930, -1.1950570],
    [50.6092930, -1.1949110],
    [50.6092400, -1.1947440],
    [50.6092000, -1.1945710],
    [50.6091610, -1.1943990],
    [50.6091850, -1.1942230],
    [50.6091610, -1.1940480],
    [50.6091350, -1.1938730],
    [50.6091290, -1.1936960],
    [50.6091270, -1.1935190],
    [50.6091260, -1.1933420],
    [50.6092470, -1.1932120],
    [50.6091700, -1.1931490],
    [50.6089950, -1.1931180],
    [50.6088210, -1.1930880],
    [50.6086460, -1.1930580],
    [50.6085470, -1.1931860],
    [50.6084790, -1.1933450],
    [50.6084800, -1.1935220],
    [50.6084810, -1.1936990],
    [50.6086330, -1.1937840],
    [50.6087900, -1.1938660],
    [50.6088230, -1.1937450],
    [50.6088180, -1.1935760],
    [50.6086700, -1.1936730],
    [50.6087330, -1.1937620],
    [50.6088890, -1.1938470],
    [50.6090440, -1.1939320],
    [50.6090900, -1.1940730],
    [50.6090340, -1.1942350],
    [50.6089290, -1.1943770],
    [50.6088230, -1.1945200],
    [50.6087180, -1.1946620],
    [50.6086120, -1.1948040],
    [50.6085450, -1.1949650],
    [50.6084950, -1.1951350],
    [50.6085580, -1.1952980],
    [50.6086410, -1.1953740],
    [50.6087350, -1.1952370],
    [50.6085770, -1.1951580],
    [50.6085700, -1.1952970],
    [50.6086360, -1.1954400],
    [50.6087960, -1.1955180],
    [50.6089570, -1.1954840],
    [50.6091200, -1.1954140],
    [50.6092510, -1.1952960],
    [50.6093770, -1.1951720],
    [50.6093560, -1.1952350],
    [50.6092660, -1.1953870],
    [50.6091750, -1.1955400],
    [50.6090850, -1.1956920],
    [50.6089950, -1.1958450],
    [50.6089050, -1.1959970],
    [50.6087400, -1.1960340],
    [50.6085630, -1.1960530],
    [50.6084390, -1.1961230],
    [50.6084260, -1.1963000],
    [50.6084130, -1.1964760],
    [50.6084000, -1.1966530],
    [50.6084930, -1.1967300],
    [50.6086630, -1.1967110],
    [50.6087930, -1.1965900],
    [50.6089220, -1.1964690],
    [50.6090520, -1.1963480],
    [50.6091810, -1.1962270],
    [50.6093100, -1.1961060],
    [50.6094310, -1.1959770],
    [50.6095450, -1.1958420],
    [50.6096590, -1.1957060],
    [50.6097730, -1.1955700],
    [50.6098870, -1.1954340],
]

if __name__ == "__main__":
    print(make_gpx(10000, datetime.datetime.utcnow() - datetime.timedelta(days=1), datetime.timedelta(hours=1), 51, 0))

