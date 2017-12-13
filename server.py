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

# Check https://developers.google.com/drive/scopes for all available scopes.
# OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# The app's service account credentials (for Google Drive).
# APP_CREDENTIALS = oauth2client.service_account.ServiceAccountCredentials(
#     config.EE_ACCOUNT,
#     open(config.EE_PRIVATE_KEY_FILE, 'rb').read(),
#     OAUTH_SCOPE)

# APP_CREDENTIALS = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(config.EE_PRIVATE_KEY_FILE, OAUTH_SCOPE)
#
# # An authenticated Drive helper object for the app service account.
# APP_DRIVE_HELPER = drive.DriveHelper(APP_CREDENTIALS)
#
# # The decorator to trigger the user's Drive permissions request flow.
# OAUTH_DECORATOR = oauth2client.contrib.appengine.OAuth2Decorator(
#     client_id=config.OAUTH_CLIENT_ID,
#     client_secret=config.OAUTH_CLIENT_SECRET,
#     scope=OAUTH_SCOPE)
#
# # The frequency to poll for export EE task completion (seconds).
# TASK_POLL_FREQUENCY = 10


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
    # # //****** 6. Calculate: Area of River Basin  *****
    # # // Function declaration
    # # // This creates a new column, named 'area' which contains the calculated area (in m^2) for each polygon of the river basin
    print('boundary')
    print(boundary)
    boundary = ee.FeatureCollection(boundary)
    basinPolyArea = boundary.map(lambda f: f.set({'area': f.area()}))
    boundaryTotalArea = basinPolyArea.reduceColumns(
      reducer= ee.Reducer.sum(),
      selectors= ['area']
    )

    boundaryTotalArea_sqkm = ee.Number(boundaryTotalArea.get('sum')).divide(ee.Number(10).pow(6));
    print('boundaryTotalArea_sqkm.getInfo()');
    print(boundaryTotalArea_sqkm.getInfo())



    # // ****** 9. Prepare CSV for download *******
    unixTimeList = rainfall.aggregate_array('system:time_start');

    # // Function declaration
    # def getDateList(utList):
    #     dt = ee.Date(utList).format('YYYY-MM-dd')
    #     print(dt.getInfo())
    #     return dt.getInfo()
    #
    # def getTimeList(utList):
    #     time = ee.Date(utList).format('HH-mm')
    #     print(time.getInfo())
    #     return time.getInfo()

    # dates = map(getDateList, unixTimeList.getInfo())
    # times = map(getDateList, unixTimeList.getInfo())
    #
    # print(dates);
    # print(times);


    # print(datetime.now())
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
        # print(dateTimeObj[0])
        # print(dateTimeObj[1])
        dates.append(dateTimeObj[0])
        times.append(dateTimeObj[1])

    # print(dates)
    # print(times)
    try:
      downloadUrl = boundary.getDownloadUrl(
          filename='testfile'
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



# def _GetUniqueString():
#   """Returns a likely-to-be unique string."""
#   random_str = ''.join(
#       random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
#   date_str = str(int(time.time()))
#   return date_str + random_str


# def _SendMessageToClient(client_id, filename, params):
#   """Sends a message to the client using the Channel API.
#
#   Args:
#     client_id: The ID of the client to message.
#     filename: The name of the exported file the message is about.
#     params: The params to send in the message (as a Dictionary).
#   """
#   params['filename'] = filename
#   channel.send_message(client_id, json.dumps(params))


# def GetExportableImage():
#   """Crops and formats the image for export.
#
#   Args:
#     image: The image to make exportable.
#     coordinates: The coordinates to crop the image to.
#
#   Returns:
#     The export-ready image.
#   """
#   # The visualization parameters for the images.
#   VIZ_PARAMS = {
#     'min': 0,
#     'max': 63,
#   }
#   # Load a landsat image and select three bands.
#   landsat = ee.Image('LANDSAT/LC08/C01/T1_TOA/LC08_123032_20140515').select(['B4', 'B3', 'B2']);
#
#   # Create a geometry representing an export region.
#   geometry = ee.Geometry.Rectangle([116.2621, 39.8412, 116.4849, 40.01236]);
#
#   # Compute the image to export based on parameters.
#   clipped_image = landsat.clip(geometry)
#   return clipped_image.visualize(**VIZ_PARAMS)


# def _GiveFilesToUser(temp_file_prefix, email, user_id, filename):
#   """Moves the files with the prefix to the user's Drive folder.
#
#   Copies and then deletes the source files from the app's Drive.
#
#   Args:
#     temp_file_prefix: The prefix of the temp files in the service
#         account's Drive.
#     email: The email address of the user to give the files to.
#     user_id: The ID of the user to give the files to.
#     filename: The name to give the files in the user's Drive.
#
#   Returns:
#     A link to the files in the user's Drive.
#   """
#   files = APP_DRIVE_HELPER.GetExportedFiles(temp_file_prefix)
#
#   # Grant the user write access to the file(s) in the app service
#   # account's Drive.
#   for f in files:
#     APP_DRIVE_HELPER.GrantAccess(f['id'], email)
#
#   # Create a Drive helper to access the user's Google Drive.
#   user_credentials = oauth2client.contrib.appengine.StorageByKeyName(
#       oauth2client.contrib.appengine.CredentialsModel,
#       user_id, 'credentials').get()
#   user_drive_helper = drive.DriveHelper(user_credentials)
#
#   # Copy the file(s) into the user's Drive.
#   if len(files) == 1:
#     file_id = files[0]['id']
#     copied_file_id = user_drive_helper.CopyFile(file_id, filename)
#     trailer = 'open?id=' + copied_file_id
#   else:
#     trailer = ''
#     for f in files:
#       # The titles of the files include the coordinates separated by a dash.
#       coords = '-'.join(f['title'].split('-')[-2:])
#       user_drive_helper.CopyFile(f['id'], filename + '-' + coords)
#
#   # Delete the file from the service account's Drive.
#   for f in files:
#     APP_DRIVE_HELPER.DeleteFile(f['id'])
#
#   return 'https://drive.google.com/' + trailer
