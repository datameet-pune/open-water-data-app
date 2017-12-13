import _ from 'lodash';
import React from 'react';
import LayerSwitch from '../containers/layer_switch';
import Datepicker from '../containers/Datepicker';

export default props => {
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
            tooltip="Dataset layer displaying rainfall information"
          />
          <LayerSwitch
            name="vegetation"
            id="crop"
            tooltip="Dataset layer displaying vegetation information"
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
};
