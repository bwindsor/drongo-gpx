# drongo-gpx

Creates a GPX file in the shape of a DrongO, of specified track length, time, and location. This is useful if you are a member of DrongO orienteering club, and go for a run where you don't want to show where you actually went on Strava, for example because you were checking control sites for a competition. This means you can still put how far and how fast you ran on Strava, but with a fun shaped GPS track!

You can find a [working version here](http://drongo-gpx.s3-website-eu-west-1.amazonaws.com/).

## Files
* **make_gpx.py** is the Python code which generates the DrongO
* **index.html** is the basic web page to generate the request for a DrongO
* **infrastructure (directory)** contains the Terraform definition of AWS infrastructure to deploy the API and static S3 website bucket
