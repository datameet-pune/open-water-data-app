import React, { Component } from 'react';
import Sidebar from './sidebar';

export default class Navigation extends Component {
  render() {
    return (
      <div className="navbar navbar-default visible-xs">
        <div className="container-fluid">
          <button className="btn btn-default navbar-btn theme-color " data-toggle="collapse" data-target="#filter-sidebar">
            <i className="fa fa-tasks"></i> Filter
          </button>
          <ul className="nav navbar-nav header-links">
            <li><a target="_blank" href="https://datameet-pune.github.io/open-water-data/">Learn More</a></li>

          </ul>
        </div>
      </div>
    );
  }
}
