Open Water Data App
==================================

The 'Open Water Data' platform, an initiative by Datameet and the Centre for Internet and Society (CIS), is an effort towards improvement of our collective knowledge of the water cycle.

[Live Demo](https://water-data-web-app.appspot.com/)

You can find the project blog [here] https://datameet-pune.github.io/open-water-data/

This app runs on Google App Engine that communicates with Google Earth Engine.

To set this app up locally,
1. Download the source code or clone this project.
2. Navigate to the 'static' folder and run 'npm install' and 'webpack' on command line.
3. Then follow the instructions in the Developer Docs to deploy an EE-based App Engine app. For the credentials section, you'll need a Service Account
4. Enter your service account details in 'config.py' and add your privatekey.json file to the root folder.
5. Also enter your Google Map API key in 'index.html' file in the root folder.
6. Visit the app on "http://localhost:8080"
