import _ from 'lodash';
import $ from 'jquery';
import React, { Component } from 'react';
import LayerSwitch from '../containers/layer_switch';
import Datepicker from '../containers/Datepicker';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { updateRainfallMap, updateCropMap } from '../actions/index';

class Sidebar extends Component {
  constructor(props) {
    super(props);
    this.state = {
      rainfall: false,
      crop: false
    };
    this.updateState = this.updateState.bind(this);
  }

  updateState(newState) {
    var key = Object.keys(newState)[0];
    if (key === 'rainfall') {
      this.state.rainfall = newState['rainfall'];
      // this.setState({ rainfall: newState['rainfall'] });
    } else if (key === 'crop') {
      this.state.crop = newState['crop'];
      // this.setState({ crop: newState['crop'] });
    }
    // console.log(this.state);
  }

  hideMessage() {
    $('#message-box').hide();
    $('#message-box').html('');
    $('#message-box').removeClass('alert-warning alert-success');
  }

  componentDidUpdate() {
    if (this.state.rainfall) {
      $('.tiles-loading-rainfall').text('Loading...');
      $('.overlay').show();
      this.hideMessage();
      $('.export-btn-rainfall').hide();
      this.props.updateRainfallMap(
        this.props.timeperiod,
        this.props.selectedArea
      );
    }
    if (this.state.crop) {
      $('.tiles-loading-crop').text('Loading...');
      $('.overlay').show();
      this.hideMessage();
      $('.export-btn-crop').hide();
      this.props.updateCropMap(this.props.timeperiod, this.props.selectedArea);
    }
  }

  render() {
    return (
      <div>
        <div
          id="filter-sidebar"
          className="col-xs-6 col-sm-3 visible-sm visible-md visible-lg collapse sliding-sidebar"
        >
          <div className="sidebar-label">Add Dataset Layer</div>
          <div className="list-group collapse in">
            <LayerSwitch
              name="rainfall"
              id="rainfall"
              tooltip="CHIRPS v2.0 daily precipitation"
              onLayerClick={this.updateState}
            />
            <LayerSwitch
              name="Crop Maps"
              id="crop"
              tooltip="Dataset layer displaying crops information"
              onLayerClick={this.updateState}
            />
          </div>

          <Datepicker label="Select Time period" />
          <div className="sidebar-label"> Select Watershed (click on map)</div>
          <div>
            <span>Watershed ID: </span>
            <span id="area_box">None</span>
          </div>
          <div className="tiles-loading" />
        </div>
      </div>
    );
  }
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      updateRainfallMap,
      updateCropMap
    },
    dispatch
  );
}

function mapStateToProps({ selectedArea, timeperiod }) {
  return { selectedArea, timeperiod };
}
export default connect(mapStateToProps, mapDispatchToProps)(Sidebar);
