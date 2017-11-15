import React, { Component } from 'react';

export default class Header extends Component {
  render() {
    return (
      <nav className="navbar navbar-default navbar-fixed-top">
        <div id="message-box" className="message-box col-sm-4" />
        <div className="container-fluid">
          <div className="navbar-header">
            <a className="navbar-brand theme-color app-title" href="#">
              Open Water Data App
            </a>
          </div>
          <ul className="nav navbar-nav header-links hidden-xs">
            <li>
              <a
                target="_blank"
                href="https://datameet-pune.github.io/open-water-data/"
              >
                Learn More
              </a>
            </li>
          </ul>
        </div>
      </nav>
    );
  }
}
