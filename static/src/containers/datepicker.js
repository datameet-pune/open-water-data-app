/*
The Date Range picker in the Open Water Data App uses react-dates component for date range selection.

The MIT License (MIT)

Copyright (c) 2016 Airbnb

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import moment from 'moment';

import {
  DateRangePicker,
  SingleDatePicker,
  DayPickerRangeController
} from 'react-dates';

import 'react-dates/lib/css/_datepicker.css';

import { updateTimePeriod } from '../actions/index';

class Datepicker extends Component {
  constructor(props) {
    super(props);
    this.state = {
      focusedInput: null,
      // startDate: moment().add(-1, 'M'),
      startDate: moment().subtract(7, 'days'),
      endDate: moment()
    };

    this.props.updateTimePeriod({
      startDate: moment(this.state.startDate).format('YYYY-MM-DD'),
      endDate: moment(this.state.endDate).format('YYYY-MM-DD')
    });

    this.onDatesChange = this.onDatesChange.bind(this);
    this.onClose = this.onClose.bind(this);
  }

  onClose({ startDate, endDate }) {
    this.setState({ startDate, endDate });
    if (startDate && endDate) {
      this.props.updateTimePeriod({
        startDate: moment(startDate).format('YYYY-MM-DD'),
        endDate: moment(endDate).format('YYYY-MM-DD')
      });
    }
  }
  onDatesChange({ startDate, endDate }) {
    this.setState({ startDate, endDate });
  }

  render() {
    return (
      <div>
        <div className="sidebar-label">{this.props.label}</div>

        <DateRangePicker
          startDate={this.state.startDate} // momentPropTypes.momentObj or null,
          startDatePlaceholderText="From"
          endDatePlaceholderText="To"
          endDate={this.state.endDate} // momentPropTypes.momentObj or null,
          onDatesChange={this.onDatesChange}
          onClose={this.onClose}
          focusedInput={this.state.focusedInput} // PropTypes.oneOf([START_DATE, END_DATE]) or null,
          onFocusChange={focusedInput => this.setState({ focusedInput })}
          isOutsideRange={() => false}
        />
      </div>
    );
  }
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators({ updateTimePeriod }, dispatch);
}

export default connect(null, mapDispatchToProps)(Datepicker);
