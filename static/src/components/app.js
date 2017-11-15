import React, { Component } from 'react';
import Header from '../components/header';
import Navigation from '../components/navigation_bar';
import SideBar from '../components/sidebar';
import GoogleMap from '../containers/google_map';
import Footer from '../components/footer';

export default class App extends Component {
  render() {
    return (
      <div>
        <Header />
        <Navigation />
        <div className="overlay">
          <div id="loading-img">
            <i className="fa fa-circle-o-notch fa-spin fa-5x" />
          </div>
        </div>
        <div className="row">
          <SideBar />
          <GoogleMap />
        </div>
        <Footer />
      </div>
    );
  }
}
