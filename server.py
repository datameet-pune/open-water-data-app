import json
import logging
import os
import random
import string
import time

import config
import drive
import ee
import jinja2
import oauth2client.contrib.appengine
import webapp2

from google.appengine.api import channel
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users

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
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# The app's service account credentials (for Google Drive).
# APP_CREDENTIALS = oauth2client.service_account.ServiceAccountCredentials(
#     config.EE_ACCOUNT,
#     open(config.EE_PRIVATE_KEY_FILE, 'rb').read(),
#     OAUTH_SCOPE)

APP_CREDENTIALS = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(config.EE_PRIVATE_KEY_FILE, OAUTH_SCOPE)

# An authenticated Drive helper object for the app service account.
APP_DRIVE_HELPER = drive.DriveHelper(APP_CREDENTIALS)

# The decorator to trigger the user's Drive permissions request flow.
OAUTH_DECORATOR = oauth2client.contrib.appengine.OAuth2Decorator(
    client_id=config.OAUTH_CLIENT_ID,
    client_secret=config.OAUTH_CLIENT_SECRET,
    scope=OAUTH_SCOPE)

# The frequency to poll for export EE task completion (seconds).
TASK_POLL_FREQUENCY = 10


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

  @OAUTH_DECORATOR.oauth_required
  def Handle(self, handle_function):
    """Responds with the result of the handle_function or errors, if any."""
    # Note: The fetch timeout is thread-local so must be set separately
    # for each incoming request.
    # urlfetch.set_default_fetch_deadline(URL_FETCH_TIMEOUT)
    try:
      response = handle_function()
    except Exception as e:  # pylint: disable=broad-except
      response = {'error': str(e)}
    if response:
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(json.dumps(response))

class MainHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the main web page."""
    @OAUTH_DECORATOR.oauth_required
    def get(self):
        print('MainHandler')
        # print(users.get_current_user().email())

        """Returns the main web page with Channel API details included."""
        client_id = _GetUniqueString()

        template = JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render({
        'channelToken': channel.create_channel(client_id),
        'clientId': client_id,
    }))


class RainfallHandler(DataHandler):
    def post(self):
        data = json.loads(self.request.body)

        startDate = data.get('from')
        endDate = data.get('to')
        region = data.get('region')

        """Returns the main web page, populated with Rainfall map"""
        mapid = GetRainfallMapId(startDate, endDate, region)
        content = {
            'mapid': mapid['mapid'],
            'token': mapid['token']
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(content))

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
  print('-----------ExportHandler------------')

  # @OAUTH_DECORATOR.oauth_required
  def DoPost(self):
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
    print('test')
    print(users.get_current_user().email())
    email = users.get_current_user().email()
    client_id = self.request.get('client_id')
    user_id = users.get_current_user().user_id()
    filename = 'OpenWaterDataExport'

    print(users.get_current_user().email())
    # Get the image for the year and region to export.
    # image = GetExportableImage()
    #
    # # Use a unique prefix to identify the exported file.
    temp_file_prefix = _GetUniqueString()
    #
    # # Create and start the task.
    # task = ee.batch.Export.image(
    #     image=image,
    #     description='Earth Engine Demo Export',
    #     config={
    #         'driveFileNamePrefix': temp_file_prefix
    #     })
    # Make a collection of points.
    # features = ee.FeatureCollection([
    #   ee.Feature(ee.Geometry.Point(30.41, 59.933), {name: 'Voronoi'}),
    #   ee.Feature(ee.Geometry.Point(-73.96, 40.781), {name: 'Thiessen'}),
    #   ee.Feature(ee.Geometry.Point(6.4806, 50.8012), {name: 'Dirichlet'})
    # ]);

    boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH')

    # // Export the FeatureCollection to a KML file.
    task = ee.batch.Export.table(
      collection= boundary,
      description='vectorsToDriveExample',
      config={
            'driveFileNamePrefix': temp_file_prefix
        })

    task.start()
    logging.info('Started EE task (id: %s).', task.id)

    # Wait for the task to complete (taskqueue auto times out after 10 mins).
    while task.active():
      logging.info('Polling for task (id: %s).', task.id)
      time.sleep(TASK_POLL_FREQUENCY)

    def _SendMessage(message):
      logging.info('Sent to client: ' + json.dumps(message))
      _SendMessageToClient(client_id, filename, message)

    # Make a copy (or copies) in the user's Drive if the task succeeded.
    state = task.status()['state']
    if state == ee.batch.Task.State.COMPLETED:
      logging.info('Task succeeded (id: %s).', task.id)
      try:
        link = _GiveFilesToUser(temp_file_prefix, email, user_id, filename)
        # Notify the user's browser that the export is complete.
        _SendMessage({'link': link})

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'rainfall': 'success',
            'link': link
        }))
      except Exception as e:  # pylint: disable=broad-except
        _SendMessage({'error': 'Failed to give file to user: ' + str(e)})
    else:
      _SendMessage({'error': 'Task failed (id: %s).' % task.id})

    ###############################################################################
#                           The task status poller.                           #
###############################################################################


class ExportRunnerHandler(webapp2.RequestHandler):
  print('-----------ExportRunnerHandler------------')
  """A servlet for handling async export task requests."""

  def post(self):
    """Exports an image for the year and region, gives it to the user.

    This is called by our trusted export handler and runs as a separate
    process.

    HTTP Parameters:
      email: The email address of the user who initiated this task.
      filename: The final filename of the file to create in the user's Drive.
      client_id: The ID of the client (for the Channel API).
      task: The pickled task to poll.
      temp_file_prefix: The prefix of the temp file in the service account's
          Drive.
      user_id: The ID of the user who initiated this task.
    """
    region = self.request.get('region')
    startDate = self.request.get('startDate')
    client_id = self.request.get('client_id')
    endDate = self.request.get('endDate')
    user_id = self.request.get('user_id')
    email = self.request.get('email')
    filename = 'OpenWaterDataExport'

    print(email)
    # Get the image for the year and region to export.
    image = GetExportableImage()

    # Use a unique prefix to identify the exported file.
    temp_file_prefix = _GetUniqueString()

    # Create and start the task.
    task = ee.batch.Export.image(
        image=image,
        description='Earth Engine Demo Export',
        config={
            'driveFileNamePrefix': temp_file_prefix
        })
    task.start()
    logging.info('Started EE task (id: %s).', task.id)

    # Wait for the task to complete (taskqueue auto times out after 10 mins).
    while task.active():
      logging.info('Polling for task (id: %s).', task.id)
      time.sleep(TASK_POLL_FREQUENCY)

    def _SendMessage(message):
      logging.info('Sent to client: ' + json.dumps(message))
      _SendMessageToClient(client_id, filename, message)

    # Make a copy (or copies) in the user's Drive if the task succeeded.
    state = task.status()['state']
    if state == ee.batch.Task.State.COMPLETED:
      logging.info('Task succeeded (id: %s).', task.id)
      try:
        link = _GiveFilesToUser(temp_file_prefix, email, user_id, filename)
        # Notify the user's browser that the export is complete.
        _SendMessage({'link': link})

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(link))
      except Exception as e:  # pylint: disable=broad-except
        _SendMessage({'error': 'Failed to give file to user: ' + str(e)})
    else:
      _SendMessage({'error': 'Task failed (id: %s).' % task.id})

# Define webapp2 routing from URL paths to web request handlers. See:
# http://webapp-improved.appspot.com/tutorials/quickstart.html
app = webapp2.WSGIApplication([
    # ('/export', ExportHandler),
    ('/exportRainfall', ExportHandler),
    ('/exportCrop', ExportHandler),
    # ('/exportrunner', ExportRunnerHandler),
    ('/rainfall', RainfallHandler),
    ('/crop', CropHandler),
    ('/', MainHandler),
    (OAUTH_DECORATOR.callback_path, OAUTH_DECORATOR.callback_handler()),
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

    #Visualization Parameters
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

def GetRainfallMapId(startDate, endDate, region):
    #  ***** Declare vector boundary *****
    boundary = ee.FeatureCollection('ft:17JOXbbYVVanIDQtR689Ia1j_blb85l7lwkmwG_KH');
    if region:
        boundary = _get_region(region)

    # ***** Filter rainfall data - by boundary, bands and date*****
    rainfall_GPM = ee.ImageCollection('NASA/GPM_L3/IMERG_V04')
    rainfall_India  = rainfall_GPM.filterBounds(boundary)
    rainfall_band = rainfall_India.select('precipitationCal')
    rainfall_timerange = rainfall_band.filterDate(startDate, endDate)

    #  ***** Make rainfall image *****
    rainfall = rainfall_timerange.sum().clip(boundary);

    # ***** Set Visualization Parameters *****
    vizParams = {
      'bands': 'precipitationCal',
      'min': 50,
      'max': 1000,
      'palette':"#bae4bc,#7bccc4,#43a2ca,#0868ac"
    }
    return rainfall.getMapId(vizParams)

def _GetUniqueString():
  """Returns a likely-to-be unique string."""
  random_str = ''.join(
      random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
  date_str = str(int(time.time()))
  return date_str + random_str


def _SendMessageToClient(client_id, filename, params):
  """Sends a message to the client using the Channel API.

  Args:
    client_id: The ID of the client to message.
    filename: The name of the exported file the message is about.
    params: The params to send in the message (as a Dictionary).
  """
  params['filename'] = filename
  channel.send_message(client_id, json.dumps(params))


def GetExportableImage():
  """Crops and formats the image for export.

  Args:
    image: The image to make exportable.
    coordinates: The coordinates to crop the image to.

  Returns:
    The export-ready image.
  """
  # The visualization parameters for the images.
  VIZ_PARAMS = {
    'min': 0,
    'max': 63,
  }
  # Load a landsat image and select three bands.
  landsat = ee.Image('LANDSAT/LC08/C01/T1_TOA/LC08_123032_20140515').select(['B4', 'B3', 'B2']);

  # Create a geometry representing an export region.
  geometry = ee.Geometry.Rectangle([116.2621, 39.8412, 116.4849, 40.01236]);

  # Compute the image to export based on parameters.
  clipped_image = landsat.clip(geometry)
  return clipped_image.visualize(**VIZ_PARAMS)


def _GiveFilesToUser(temp_file_prefix, email, user_id, filename):
  """Moves the files with the prefix to the user's Drive folder.

  Copies and then deletes the source files from the app's Drive.

  Args:
    temp_file_prefix: The prefix of the temp files in the service
        account's Drive.
    email: The email address of the user to give the files to.
    user_id: The ID of the user to give the files to.
    filename: The name to give the files in the user's Drive.

  Returns:
    A link to the files in the user's Drive.
  """
  files = APP_DRIVE_HELPER.GetExportedFiles(temp_file_prefix)

  # Grant the user write access to the file(s) in the app service
  # account's Drive.
  for f in files:
    APP_DRIVE_HELPER.GrantAccess(f['id'], email)

  # Create a Drive helper to access the user's Google Drive.
  user_credentials = oauth2client.contrib.appengine.StorageByKeyName(
      oauth2client.contrib.appengine.CredentialsModel,
      user_id, 'credentials').get()
  user_drive_helper = drive.DriveHelper(user_credentials)

  # Copy the file(s) into the user's Drive.
  if len(files) == 1:
    file_id = files[0]['id']
    copied_file_id = user_drive_helper.CopyFile(file_id, filename)
    trailer = 'open?id=' + copied_file_id
  else:
    trailer = ''
    for f in files:
      # The titles of the files include the coordinates separated by a dash.
      coords = '-'.join(f['title'].split('-')[-2:])
      user_drive_helper.CopyFile(f['id'], filename + '-' + coords)

  # Delete the file from the service account's Drive.
  for f in files:
    APP_DRIVE_HELPER.DeleteFile(f['id'])

  return 'https://drive.google.com/' + trailer
