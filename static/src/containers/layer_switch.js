import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import {
  updateRainfallMap,
  updateCropMap,
  updateLayers,
  exportRainfall,
  exportCrop
} from '../actions/index';

class layerSwitch extends Component {
  constructor(props) {
    super(props);
    this.state = { name: this.props.id };
    this.onInputChange = this.onInputChange.bind(this);
    this.onExportClick = this.onExportClick.bind(this);
  }

  hideMessage() {
    $('#message-box').hide();
    $('#message-box').html('');
    $('#message-box').removeClass('alert-warning alert-success');
  }

  showMessage(className, text) {
    $('#message-box').removeClass('alert-warning alert-success');
    $('#message-box').addClass(className);
    $('#message-box').html(text);
    $('#message-box').show();
  }
  onExportClick() {
    this.showMessage('alert-warning', 'Export in progress...');

    if (this.state.name === 'rainfall') {
      this.props.exportRainfall(this.props.timeperiod, this.props.selectedArea);
    } else {
      this.props.exportCrop(this.props.timeperiod, this.props.selectedArea);
    }
  }

  onInputChange(event) {
    let val = event.target.checked;
    this.state.checked = val;
    if (this.state.name === 'rainfall' && this.state.checked === true) {
      $('.tiles-loading-rainfall').text('Loading...');
      $('.export-btn-rainfall').hide();
      $('.overlay').show();
      this.props.updateRainfallMap(
        this.props.timeperiod,
        this.props.selectedArea
      );
    } else {
      $('.export-btn-rainfall').hide();
      $('.tiles-loading-rainfall').empty();
    }

    if (this.state.name === 'crop' && this.state.checked === true) {
      $('.tiles-loading-crop').text('Loading...');
      $('.overlay').show();
      $('.export-btn-crop').hide();
      this.props.updateCropMap(this.props.timeperiod, this.props.selectedArea);
    } else {
      $('.tiles-loading-crop').empty();
      $('.export-btn-crop').hide();
    }

    let obj = {};
    obj[this.props.id] = val;

    this.props.updateLayers(obj);
  }

  componentDidUpdate() {
    if (this.state.name === 'rainfall' && this.state.checked === true) {
      $('.tiles-loading-rainfall').text('Loading...');
      $('.overlay').show();
      $('.export-btn-rainfall').hide();
      this.props.updateRainfallMap(
        this.props.timeperiod,
        this.props.selectedArea
      );
    }
    if (this.state.name === 'crop' && this.state.checked === true) {
      $('.tiles-loading-crop').text('Loading...');
      $('.overlay').show();
      $('.export-btn-crop').hide();
      this.props.updateCropMap(this.props.timeperiod, this.props.selectedArea);
    }
    const exportStatus = this.props.exportStatus[this.state.name];
    if (
      exportStatus['status'] === 'success' &&
      exportStatus['link'] !== undefined
    ) {
      var msgText =
        '<span class="close-btn"><i class="fa fa-close"></i></span><span>Exported successfully! Open in Drive:  <a target="_blank" href="' +
        exportStatus['link'] +
        '">Link</a></span>';
      var self = this;
      self.showMessage('alert-success', msgText);
      $('.fa-close').on('click', function() {
        self.hideMessage();
      });
    }
  }

  render() {
    const tilesLoadingClass = `tiles-loading tiles-loading-${this.props.id}`;
    const exportClass = `export-btn export-btn-${this.props
      .id} layer-info blue-tooltip`;
    let exportBtn = null;
    if (this.state.name === 'rainfall') {
      // adding export btn only for rainfall until crop export is implemented in GEE
      exportBtn = (
        <span
          className={exportClass}
          onClick={this.onExportClick}
          data-toggle="tooltip"
          data-placement="left"
          title="Export to Google Drive"
        >
          <i className="fa fa-download" aria-hidden="true" />
        </span>
      );
    }

    return (
      <div className="layer-list-item">
        <span className="slider-label">{this.props.name}</span>
        <span
          className="layer-info blue-tooltip"
          data-toggle="tooltip"
          data-placement="right"
          title={this.props.tooltip}
        >
          <i className="fa fa-info-circle" aria-hidden="true" />
        </span>
        <label className="switch">
          <input
            type="checkbox"
            onChange={this.onInputChange}
            name={this.props.id}
          />
          <span className="slider round" />
        </label>
        <span className={tilesLoadingClass} />
        {exportBtn}
      </div>
    );
  }
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      updateRainfallMap,
      updateCropMap,
      updateLayers,
      exportRainfall,
      exportCrop
    },
    dispatch
  );
}

function mapStateToProps({ timeperiod, selectedArea, exportStatus }) {
  return { timeperiod, selectedArea, exportStatus };
}

export default connect(mapStateToProps, mapDispatchToProps)(layerSwitch);
