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
        ).get('precipitation').getInfo()
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
      'bands': 'precipitation',
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
    rainfallColl = rainfallObj.get('rainfall')
    rainfallTotal = rainfallObj.get('rainfallTotal')
    rainfallCollwDt = rainfallObj.get('rainfallCollwDt')

    prj = ee.Image(rainfallColl.first()).projection()
    pixelArea = ee.Image.pixelArea().reproject(prj).clip(boundary)

    # # //****** 6. Calculate: Area of River Basin  *****
    # # // Function declaration
    # # // This creates a new column, named 'area' which contains the calculated area (in m^2) for each polygon of the river basin
    boundary = ee.FeatureCollection(boundary)
    basinPolyArea = boundary.map(lambda f: f.set({'area': f.area()}))
    boundaryTotalArea = basinPolyArea.reduceColumns(
      reducer= ee.Reducer.sum(),
      selectors= ['area']
    )

    print(ee.Number(boundaryTotalArea.get('sum')).getInfo())
    boundaryTotalArea_sqkm = ee.Number(boundaryTotalArea.get('sum')).divide(10 ** 6);
    print(boundaryTotalArea_sqkm.getInfo())

  # // ***** 7. Calculate: Median of rainfall (in mm) for all pixels within the basin for one image *******
        # // ****** Note: The rainfall data comes in half-hourly (hh) timesteps, i.e. one new raster image for every half hour ******

    def mmMedian(image):
      median = image.reduceRegion(
        reducer= ee.Reducer.median(),
        geometry= boundary,
        scale= 10000,
        bestEffort= False
      ).get('precipitation');
      return image.set({'medianRain': median});


    def mcmVolume(image):
      vol_image = (image
        .divide(1e3)            #// convert mm to metres
        .multiply(pixelArea)    #// multiply metres by pixelArea (mts) to get volume in metre^3
        .divide(1e6)           #// convert m^3 to Million Cubic Metres (MCM)
        )
      vol = vol_image.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= boundary,
        scale= 10000,
        bestEffort= False
      ).get('precipitation')
      return image.set({'volRain': vol})

    # // Function call - #7.1 and #8.1
    rainfall_mm = rainfallCollwDt.map(mmMedian);
    # print(rainfall_mm);
    rainfall_vol = rainfallCollwDt.map(mcmVolume);
    # print(rainfall_vol);

    # // Calculate a list of daily values - #7.2 and #8.2
    daily_mm = rainfall_mm.reduceColumns(
        selectors= ['medianRain','date'],         # // select these two properties of each image we created before
        reducer= ee.Reducer.sum().group(groupField= 1, groupName= 'Date')
    ).get('groups');

    daily_mcm = rainfall_vol.reduceColumns(
        selectors= ['volRain','date'],
        reducer= ee.Reducer.sum().group(groupField= 1, groupName= 'Date')
    ).get('groups');

    mmList = ee.List(daily_mm);
    mcmList = ee.List(daily_mcm);

    ll = mmList.length().getInfo();             #//List length
    li = ll-1;   #//List index (Length -1)

    csvList = []
    for x in range(0, ll):
        date = ee.Date(ee.Dictionary(mmList.get(x)).get('Date'));
        mm = ee.Number(ee.Dictionary(mmList.get(x)).get('sum'));
        mcm = ee.Number(ee.Dictionary(mcmList.get(x)).get('sum'));
        eeFeatureObj = ee.Feature(None, {
            "Date": date,
            "Rain (in mm)": mm,
            "Rain (in MCM)": mcm
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

    rainfallColl = (
        ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
        .filterBounds(boundary)
        .filterDate(startDate, endDate)
        .select('precipitation')
    )

    def setRainfallDate(img):
        dt = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return img.set({'date': dt})

    rainfallCollwDt = rainfallColl.map(setRainfallDate)

    #  ***** Make rainfall image *****
    rainfallTotal = rainfallCollwDt.sum().clip(boundary);
    rainfall_masked = rainfallTotal.updateMask(rainfallTotal.gt(0));
    return {
        'rainfall': rainfallColl,
        'rainfallTotal': rainfallTotal,
        'rainfallCollwDt': rainfallCollwDt,
        'rainfall_masked': rainfall_masked,
        'boundary': boundary
        }
