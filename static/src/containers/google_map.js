import $ from 'jquery';
import _ from 'lodash';
import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setSelectedArea } from '../actions/index';

import riverBasins from '!json!../data/RiverBasins_only_ID';

class GoogleMap extends Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedArea: null,
      rainfallMap: {
        mapid: null,
        token: null,
        legend: {
          colors: [],
          values: []
        }
      },
      cropMap: {
        mapid: null,
        token: null,
        legend: {
          colors: [],
          values: []
        }
      }
    };
    this.addEELayer = this.addEELayer.bind(this);
    this.removeEELayer = this.removeEELayer.bind(this);
    this.addLayer = this.addLayer.bind(this);
    this.removeLayer = this.removeLayer.bind(this);
    this.addGeoLayer = this.addGeoLayer.bind(this);
    this.createLegend = this.createLegend.bind(this);
    this.showError = this.showError.bind(this);
    this.removeError = this.removeError.bind(this);
  }

  showError() {
    $('.message-box')
      .show()
      .addClass('alert alert-danger');
    $('.message-box').html(
      'Data unavailable. Please try with different dates.'
    );
    $('.overlay').hide();
  }

  removeError() {
    $('.message-box')
      .hide()
      .removeClass('alert alert-danger');
    $('.message-box').html('');
  }

  addEELayer(index, eeMapConfig, name) {
    // Create the map type.
    var layerName = name + 'Layer';
    var className = 'tiles-loading-' + name;
    var exportName = 'export-btn-' + name;
    var overlay = new ee.MapLayerOverlay(
      'https://earthengine.googleapis.com/map',
      eeMapConfig.mapid,
      eeMapConfig.token,
      {}
    );
    overlay.setOpacity(1);

    // Show a count of the number of map tiles remaining.
    overlay.addTileCallback(function(event) {
      $('.' + className).text(event.count + ' tiles remaining.');
      if (event.count === 0) {
        $('.' + className).empty();
        $('.' + exportName).show();
        var tilesLoadingSpans = $('.tiles-loading');
        var isLoading = false;
        _.forEach(tilesLoadingSpans, function(el) {
          if ($(el).text() !== '') {
            isLoading = true;
          }
        });
        if (isLoading) {
          $('.overlay').show();
        } else {
          $('.overlay').hide();
        }
      }
    });
    this.map.overlayMapTypes.insertAt(index, overlay);
    var legendText = 'Total Rainfall (mm)';
    if (name === 'crop') {
      legendText = 'Vegetation Legend';
    }
    this.createLegend(eeMapConfig, legendText);
    // this.setState(eeMapConfig);
  }

  removeLegend() {
    console.log('remove legend');
    $('#legend-box').hide();
  }
  addLegendItem(color, value) {
    var item =
      '<i class="legend-color" class="col-xs-3 col-md-4 col-lg-6" style="background-color:' +
      color +
      '"></i>' +
      value.toFixed(0) +
      '<br>';
    return item;
  }

  createLegend(eeMapConfig, legendText) {
    console.log('creating legend...');
    var legendDiv = $('#legend-box');

    if (eeMapConfig.colors && eeMapConfig.colors.length > 0) {
      legendDiv.empty();
      legendDiv.show();
      legendDiv.append('<div class="legend-text"> ' + legendText + ' </div>');
      for (var i = 0; i < eeMapConfig.colors.length; i++) {
        var legendRow = this.addLegendItem(
          eeMapConfig.colors[i],
          eeMapConfig.values[i]
        );
        legendDiv.append(legendRow);
      }
    } else {
      legendDiv.empty();
      legendDiv.hide();
    }
  }

  removeEELayer(index, layerObj) {
    this.map.overlayMapTypes.setAt(index, null);
  }

  addLayer(layer) {
    switch (layer) {
      case 'rainfall':
        if (this.props.rainfallMap) {
          if (this.props.rainfallMap.error) {
            this.showError();
            $('.tiles-loading-rainfall').empty();

            return;
          }
          this.removeError();
          this.addEELayer(0, this.props.rainfallMap, 'rainfall');
        }

      case 'crop':
        if (this.props.cropMap) {
          if (this.props.cropMap.error) {
            this.showError();
            $('.tiles-loading-crop').empty();

            return;
          }
          this.removeError();
          this.addEELayer(1, this.props.cropMap, 'crop');
        }
    }
  }

  removeLayer(layer) {
    switch (layer) {
      case 'rainfall':
        this.removeEELayer(0);
      case 'crop':
        this.removeEELayer(1);
    }
  }

  get_region(geojson) {
    var polygon = geojson.coordinates,
      featureType = geojson.type,
      region;
    if (featureType.toLowerCase() === 'multipolygon') {
      region = ee.Geometry.MultiPolygon(polygon);
    } else {
      region = ee.Geometry.Polygon(polygon);
    }
    return region;
  }

  addGeoLayer() {
    this.map.data.addGeoJson(riverBasins);

    var self = this;
    this.map.data.addListener('mouseover', function(event) {
      let prevSelectedFeature = self.state.selectedArea,
        currentSelectedFeature = event.feature;
      // document.getElementById(
      //   'info-box'
      // ).textContent = event.feature.getProperty('AS_BAS_ID');
      // this.infowindow = new google.maps.InfoWindow({
      //   content: 'River Basin ID: ' + event.feature.getProperty('AS_BAS_ID'),
      //   map: this.map,
      //   position: event.latLng
      // });

      if (prevSelectedFeature) {
        if (
          prevSelectedFeature.getProperty('AS_BAS_ID') !==
          currentSelectedFeature.getProperty('AS_BAS_ID')
        ) {
          self.map.data.overrideStyle(event.feature, { fillColor: 'red' });
        }
      } else {
        self.map.data.overrideStyle(event.feature, { fillColor: 'red' });
      }
    });

    this.map.data.addListener('mouseout', function(event) {
      // if (self.state.selectedArea) {
      // if (event.feature.getProperty('AS_BAS_ID') !== self.state.selectedArea.getProperty('AS_BAS_ID')) {
      // this.infowindow.close();
      self.map.data.overrideStyle(event.feature, { fillColor: '#ccc' });
      // }
      // } else {
      // self.map.data.overrideStyle(event.feature, {fillColor: '#ccc'});
      // }
    });

    // Add some style.
    this.map.data.setStyle(function(feature) {
      return /** @type {google.maps.Data.StyleOptions} */ ({
        fillColor: '#ccc',
        strokeColor: '#337ab7',
        strokeWeight: 0.5
      });
    });

    this.map.data.addListener('click', function(event) {
      let prevSelectedFeature = self.state.selectedArea,
        currentSelectedFeature = event.feature;
      document.getElementById(
        'area_box'
      ).textContent = currentSelectedFeature.getProperty('AS_BAS_ID');

      if (prevSelectedFeature) {
        if (
          prevSelectedFeature.getProperty('AS_BAS_ID') !==
          currentSelectedFeature.getProperty('AS_BAS_ID')
        ) {
          self.setState({ selectedArea: currentSelectedFeature });

          currentSelectedFeature.toGeoJson(function(data) {
            self.props.setSelectedArea(data);
          });

          self.map.data.overrideStyle(prevSelectedFeature, {
            strokeWeight: 0.5
          });
          self.map.data.overrideStyle(currentSelectedFeature, {
            strokeWeight: 4,
            strokeColor: '#337ab7'
          });
          self.map.data.overrideStyle(currentSelectedFeature, {
            strokeWeight: 4
          });
        }
      } else {
        self.setState({ selectedArea: currentSelectedFeature });
        currentSelectedFeature.toGeoJson(function(data) {
          self.props.setSelectedArea(data);
        });

        self.map.data.overrideStyle(currentSelectedFeature, {
          strokeWeight: 4,
          strokeColor: '#337ab7'
        });
      }
    });
  }

  componentDidMount() {
    this.map = new google.maps.Map(this.refs.map, {
      center: { lat: 18.5, lng: 73 },
      zoom: 4,
      streetViewControl: false,
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
        position: google.maps.ControlPosition.TOP_CENTER
      },
      zoomControl: true,
      zoomControlOptions: {
        position: google.maps.ControlPosition.RIGHT_BOTTOM
      },
      fullscreenControl: true,
      fullscreenControlOptions: {
        position: google.maps.ControlPosition.RIGHT_TOP
      }
    });
    this.addGeoLayer();

    this.map.data.setStyle(function(feature) {
      return /** @type {google.maps.Data.StyleOptions} */ ({
        fillColor: '#ccc',
        strokeWeight: 0.5
      });
    });
  }

  componentDidUpdate() {
    var isMapShowing = false;
    Object.keys(this.props.layers.layers).map(key => {
      if (this.props.layers.layers[key]) {
        this.removeLayer(key);
        this.addLayer(key);
        isMapShowing = true;
      } else {
        this.removeLayer(key);
      }
    });
    if (!isMapShowing) {
      this.removeLegend();
    }
  }

  render() {
    return (
      <div className="map-wrapper">
        <div id="map" className="map" ref="map" />

        <div id="legend-box">dffr </div>
      </div>
    );
  }
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators({ setSelectedArea }, dispatch);
}

function mapStateToProps({ layers, rainfallMap, cropMap }) {
  return { layers, rainfallMap, cropMap };
}

export default connect(mapStateToProps, mapDispatchToProps)(GoogleMap);
