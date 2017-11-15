import React, { Component } from 'react';

export default class Footer extends Component {
  render() {
    return (
        <footer className ="footer">
          <div className ="container">
          <div className="row">
            <a className="col-md-4 logo arghyam-logo" href="http://www.arghyam.org/" target="_blank">
            </a>
            <a className="col-md-4 logo datameet-logo" href="http://datameet.org/" target="_blank">
            </a>

            <a className="col-md-4 logo cis-logo" href="https://cis-india.org/" target="_blank"></a>
          </div>

          </div>
          </footer>
    );
  }
}
