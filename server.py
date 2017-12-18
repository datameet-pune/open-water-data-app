import json
import logging
import os
import random
import string
import time

import config
# import drive
import ee
import jinja2
# import oauth2client.contrib.appengine
import webapp2

# from google.appengine.api import channel
# from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
# from google.appengine.api import users

from datetime import date, datetime, timedelta

urlfetch.set_default_fetch_deadline(120000)
ee.data.setDeadline(60000)

###############################################################################
#                               Initialization.                               #
###############################################################################


# Use our App Engine service account's credentials.
EE_CREDENTIALS = ee.ServiceAccountCredentials(
    config.EE_ACCOUNT, config.EE_PRIVATE_KEY_FILE)

# Create the Jinja templating system we use to dynamically generate HTML. See:
# http://jinja.pocoo.org/docs/dev/
JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

# Initialize the EE API.
ee.Initialize(EE_CREDENTIALS)


###############################################################################
#                             Web request handlers.                           #
###############################################################################
class DataHandler(webapp2.RequestHandler):
  """A servlet base class for responding to data queries.

  We use this base class to wrap our web request handlers with try/except
  blocks and set per-thread values (e.g. URL_FETCH_TIMEOUT).
  """

  def get(self):
    self.Handle(self.DoGet)

  def post(self):
    self.Handle(self.DoPost)

  def DoGet(self):
    """Processes a GET request and returns a JSON-encodable result."""
    raise NotImplementedError()

  def DoPost(self):
    """Processes a POST request and returns a JSON-encodable result."""
    raise NotImplementedError()

  # @OAUTH_DECORATOR.oauth_required
  def Handle(self, handle_function):
    """Responds with the result of the handle_function or errors, if any."""
    # Note: The fetch timeout is thread-local so must be set separately
    # for each incoming request.
    urlfetch.set_default_fetch_deadline(120000)
    try:
      response = handle_function()
    except Exception as e:  # pylint: disable=broad-except
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      logging.info(type(e).__name__)
      logging.info(e.args)
      response = {'error': message}
    if response:
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(json.dumps(response))

class MainHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the main web page."""
    # @OAUTH_DECORATOR.oauth_required
    def get(self):
        print('MainHandler')
        template = JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render())

class RainfallHandler(DataHandler):
    def post(self):
        data = json.loads(self.request.body)

        startDate = data.get('from')
        endDate = data.get('to')
        region = data.get('region')

        """Returns the main web page, populated with Rainfall map"""
        try:
            rainfallObj = GetRainfallMapId(startDate, endDate, region)
            response = {
                'mapid': rainfallObj.get('mapId').get('mapid'),
                'token': rainfallObj.get('mapId').get('token'),
                'colors': rainfallObj.get('colors'),
                'values': rainfallObj.get('values')
            }
        except Exception as e:  # pylint: disable=broad-except
          template = "An exception of type {0} occurred. Arguments:\n{1!r}"
          message = template.format(type(e).__name__, e.args)
          logging.info(type(e).__name__)
          logging.info(e.args)
          response = {
          'error': type(e).__name__,
          'message': e.args
          }

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(response))

class CropHandler(DataHandler):
    def post(self):
        data = json.loads(self.request.body)

        startDate = data.get('from')
        endDate = data.get('to')
        region = data.get('region')
        """Returns the main web page, populated with Rainfall map"""
        mapid = GetCropMapId(startDate, endDate, region)
        content = {
            'mapid': mapid['mapid'],
            'token': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))

class ExportHandler(DataHandler):
  """A servlet to handle requests for image exports."""
  logging.info('-----------ExportHandler------------')
  def post(self):
    """Kicks off export of an image for the specified year and region.

    HTTP Parameters:
      startDate: start date
      endDate: end date
      region: river basin geometry
      client_id: The ID of the client (for the Channel API).

    """
    data = json.loads(self.request.body)

    startDate = data.get('from')
    endDate = data.get('to')
    region = data.get('region')
    response = GetExportUrl(startDate, endDate, region)


    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(response))


# Define webapp2 routing from URL paths to web request handlers. See:
# http://webapp-improved.appspot.com/tutorials/quickstart.html
app = webapp2.WSGIApplication([
    ('/exportRainfall', ExportHandler),
    ('/exportCrop', ExportHandler),
    ('/rainfall', RainfallHandler),
    ('/crop', CropHandler),
    ('/', MainHandler)
])


###############################################################################
#                                   Helpers.                                  #
###############################################################################

def _get_coords(geojson):
    return geojson.get('geometry').get('coordinates')

def _get_region(geom):
    """Return ee.Geometry from supplied GeoJSON object."""
    poly = _get_coords(geom)
    ptype = geom.get('geometry').get('type')
    if ptype.lower() == 'multipolygon':
        region = ee.Geometry.MultiPolygon(poly)
    else:
        region = ee.Geometry.Polygon(poly)
    return region

def GetCropMapId(startDate, endDate, region):
    # ***** Declare vector boundary(here example India Boundary *****
    boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH')
    if region:
        boundary = _get_region(region)

    # ***** Filter precipitation data by boundary and date*****
    L8 = (ee.ImageCollection("LANDSAT/LC8_L1T_TOA")
        .filterBounds(boundary)
        .filterDate(startDate, endDate))

    # Visualization Parameters
    vizParams = {
        'bands': "ndvi",
        'min':0,
        'max':1,
        'palette': "0000FF,D2691E,FFFF00,009500,FF0000,FFFFFF"
    }


    # Compute the mean brightness in the region in each image.
    def NormalizedDifference(image):
        result = image.normalizedDifference(['B5', 'B4']).rename(['ndvi'])
        return image.addBands(result)

    ndvi = L8.map(NormalizedDifference)
    medianNDVI = ndvi.median().clip(boundary)
    return medianNDVI.getMapId(vizParams)

def getLegendColors(image, boundary, vizParams):
    buckets = 5;
    scale = 10000;

    histogram = image.reduceRegion(
        reducer=ee.Reducer.histogram(buckets),
        geometry=boundary,
        scale=image.projection().nominalScale()
        ).get('precipitationCal').getInfo()
    values = histogram.get('bucketMeans');

    # Compute the mean brightness in the region in each image.
    def getRGBColors(v):
        color = ee.Image.constant(v).visualize(
            min=50,
            max=1000,
            palette="#ffffff,#b8e4ff,#73aeff,#307be1,#001245"
        ).reduceRegion(ee.Reducer.first(), ee.Algorithms.GeometryConstructors.Point([0,0]), 1);
        return color.getInfo()

    colors = map(getRGBColors, values)

    def getHexColors(color):
        r = color['vis-red'];
        g = color['vis-green'];
        b = color['vis-blue'];
        return ('#%02x%02x%02x' % (r, g, b))

    hexColors = map(getHexColors, colors)
    print(hexColors)
    print(values)
    return {
        'colors': hexColors,
        'values': values
    }

def GetRainfallMapId(startDate, endDate, region):
    rainfallObj = GetRainfallMap(startDate, endDate, region)
    rainfall_masked = rainfallObj.get('rainfall_masked')
    boundary = rainfallObj.get('boundary')
    # ***** Set Visualization Parameters *****
    vizParams = {
      'bands': 'precipitationCal',
      'min': 50,
      'max': 1000,
      'palette':"#ffffff,#b8e4ff,#73aeff,#307be1,#001245"
    }

    legendConfig = getLegendColors(rainfall_masked, boundary, vizParams)
    response = {
        'mapId': rainfall_masked.getMapId(vizParams),
        'colors': legendConfig.get('colors'),
        'values': legendConfig.get('values')
    }
    return response

def GetExportUrl(startDate, endDate, region):
    # boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH')
    rainfallObj = GetRainfallMap(startDate, endDate, region)
    boundary = rainfallObj.get('boundary')
    rainfall = rainfallObj.get('rainfall')
    rainfall_sum = rainfallObj.get('rainfall_sum')

    # # //****** 6. Calculate: Area of River Basin  *****
    # # // Function declaration
    # # // This creates a new column, named 'area' which contains the calculated area (in m^2) for each polygon of the river basin
    boundary = ee.FeatureCollection(boundary)
    basinPolyArea = boundary.map(lambda f: f.set({'area': f.area()}))
    boundaryTotalArea = basinPolyArea.reduceColumns(
      reducer= ee.Reducer.sum(),
      selectors= ['area']
    )

    boundaryTotalArea_sqkm = ee.Number(boundaryTotalArea.get('sum')).divide(ee.Number(10).pow(6));

  # // ***** 7. Calculate: Median of rainfall (in mm) for all pixels within the basin for one image *******
        # // ****** Note: The rainfall data comes in half-hourly (hh) timesteps, i.e. one new raster image for every half hour ******

    def hhMedian(image):
        median = image.reduceRegion(
            reducer= ee.Reducer.median(),
            geometry= boundary,
            scale= 10000,
            bestEffort= True
            )
        return image.set('medianRain', median);

    def extractList(obj):
        value = ee.Dictionary(obj).get('precipitationCal');
        return value;

    # // Function call
    rainfall_median = rainfall.map(hhMedian);
    hhRain = rainfall_median.aggregate_array('medianRain');
    # //pass hhRain to a function that extracts values from objects
    hhRainList = ee.List(hhRain).map(extractList);
    # //Length of the list is required later to create a csv for export in Section 9
    listLen = hhRainList.length().getInfo()
    hhRainList = hhRainList.getInfo()

    # // ****** 8. Calculate: Total volume of rainfall in River Basin for each time step ******

    # /* Make image where each pixel's rainfall value is multiplied by area of pixel (10^8 m^2) so we finally get
    # a rainfall map where each pixel shows a volume of rain in Million Cubic Metres (MCM) */
    # // Step 1: divide rainfall by 10^3 (mm to metre conversion), then multiply by area of pixel (10^8 m^2), then divide by 10^6 (m^3 to MCM conversion)
    # // Step 2: sum all the volume (MCM) values for the pixels in the basin to get the total volume, add this to the image properties
    def hhVolume(image):
        vol_image = image.divide(ee.Number(10).pow(3)).multiply(ee.Number(10).pow(8)).divide(ee.Number(10).pow(6));
        vol = vol_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry= boundary,
            scale= 10000,
            bestEffort= False
            )
        return image.set('volRain', vol)


    # // Function call
    # // Pass each image from the 'rainfall' collection to estimate the volume of rain that fell in the half hour period
    rainfallVol = rainfall.map(hhVolume);
    # // Extract rainfall volume from each image of the collection and prepare a list
    hhVol = rainfallVol.aggregate_array('volRain');
    # //The prepared list hhVol is a list of objects
    # // We pass hhVol to a function that extracts rainfall values from these objects and converts to a plain list
    hhVolList = ee.List(hhVol).map(extractList).getInfo();

    # // 8.1 Calculate the total rainfall in the basin by summing all pixels of rainfall volume

    totalVolume = rainfall_sum.divide(ee.Number(10).pow(3)).multiply(ee.Number(10).pow(8)).divide(ee.Number(10).pow(6));

    # // ****** 9. Prepare CSV for download *******
    unixTimeList = rainfall.aggregate_array('system:time_start');
    def perdelta(start, end, delta):
        curr = start
        # print(curr)
        while curr < end:
            yield curr
            curr += delta

    start = datetime.strptime(startDate, '%Y-%m-%d')
    end = datetime.strptime(endDate, '%Y-%m-%d') + timedelta(days=1)
    dates = []
    times = []
    for result in perdelta(start, end, timedelta(minutes = 30)):
        result = result.strftime('%Y-%m-%d %H-%M')
        dateTimeObj = result.split()
        dates.append(dateTimeObj[0])
        times.append(dateTimeObj[1])


    # // ******* 10. Merge all lists and Export ******* //
    csvList = []
    for x in range(0, listLen):
        date = ee.Date(dates[x]);
        time = ee.String(times[x]);
        rain = ee.Number(hhRainList[x]);
        vol = ee.Number(hhVolList[x]);
        eeFeatureObj = ee.Feature(None, {
            "Date": date,
            "Time": time,
            "Rain (in mm)": rain,
            "Rain (in MCM)": vol
            })
        csvList.append(eeFeatureObj)

    csv = ee.FeatureCollection(csvList)

    try:
        downloadUrl = ee.FeatureCollection(csv).getDownloadUrl(
            filename='OWD_Rainfall'
          )
        response = {
            'status': 'success',
            'downloadUrl': downloadUrl
        }
        logging.info('Download URL: %s', downloadUrl)

    except Exception as e:  # pylint: disable=broad-except
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      logging.info(type(e).__name__)
      logging.info(e.args)
      response = {'message': e.args, 'error': type(e).__name__}
    return response

def GetRainfallMap(startDate, endDate, region):
    #  ***** Declare vector boundary *****
    India_boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH');
    boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH');
    if region:
        boundary = _get_region(region)


    # ***** Filter rainfall data - by boundary, bands and date*****
    rainfall_GPM = ee.ImageCollection('NASA/GPM_L3/IMERG_V04')
    rainfall_India  = rainfall_GPM.filterBounds(India_boundary)
    rainfall_band = rainfall_India.select('precipitationCal')
    rainfall_timerange = rainfall_band.filterDate(startDate, endDate)
    rainfall = rainfall_timerange.filterBounds(boundary);

    #  ***** Make rainfall image *****
    rainfall_sum = rainfall_timerange.sum().clip(boundary);
    rainfall_masked = rainfall_sum.updateMask(rainfall_sum.gt(0));
    return {
        'rainfall': rainfall,
        'rainfall_sum': rainfall_sum,
        'rainfall_masked': rainfall_masked,
        'boundary': boundary
        }
