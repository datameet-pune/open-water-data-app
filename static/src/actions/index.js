import axios from 'axios';

export const UPDATE_LAYERS = 'UPDATE_LAYERS';
export const UPDATE_TIMEPERIOD = 'UPDATE_TIMEPERIOD';
export const UPDATE_SELECTEDAREA = 'UPDATE_SELECTEDAREA';
export const UPDATE_CROP_MAP = 'UPDATE_CROP_MAP';
export const UPDATE_RAINFALL_MAP = 'UPDATE_RAINFALL_MAP';
export const EXPORT_RAINFALL = 'EXPORT_RAINFALL';
export const EXPORT_CROP = 'EXPORT_CROP';

const RAINFALL_URL = `/rainfall`;
const CROP_URL = `/crop`;
const EXPORT_CROP_URL = `/exportCrop`;
const EXPORT_RAINFALL_URL = `/exportRainfall`;

export function updateRainfallMap(timePeriod, selectedArea) {
  axios.defaults.headers.post['Content-Type'] = 'application/json';

  const request = axios({
    method: 'post',
    url: `${RAINFALL_URL}`,
    data: {
      from: timePeriod.startDate,
      to: timePeriod.endDate,
      region: selectedArea
    }
  });

  return {
    type: UPDATE_RAINFALL_MAP,
    payload: request
  };
}

export function updateCropMap(timePeriod, selectedArea) {
  axios.defaults.headers.post['Content-Type'] = 'application/json';

  const request = axios({
    method: 'post',
    url: `${CROP_URL}`,
    data: {
      from: timePeriod.startDate,
      to: timePeriod.endDate,
      region: selectedArea
    }
  });

  return {
    type: UPDATE_CROP_MAP,
    payload: request
  };
}

export function setUser(user) {}

export function exportRainfall(timePeriod, selectedArea) {
  axios.defaults.headers.post['Content-Type'] = 'application/json';

  const request = axios({
    method: 'post',
    url: `${EXPORT_RAINFALL_URL}`,
    data: {
      from: timePeriod.startDate,
      to: timePeriod.endDate,
      region: selectedArea
    }
  });

  return {
    type: EXPORT_RAINFALL,
    payload: request
  };
}

export function exportCrop(timePeriod, selectedArea) {
  axios.defaults.headers.post['Content-Type'] = 'application/json';

  const request = axios({
    method: 'post',
    url: `${EXPORT_CROP_URL}`,
    data: {
      from: timePeriod.startDate,
      to: timePeriod.endDate,
      region: selectedArea
    }
  });

  return {
    type: EXPORT_CROP,
    payload: request
  };
}

export function updateLayers(data) {
  return {
    type: UPDATE_LAYERS,
    payload: data
  };
}

export function updateTimePeriod(data) {
  return {
    type: UPDATE_TIMEPERIOD,
    payload: data
  };
}

export function setSelectedArea(data) {
  return {
    type: UPDATE_SELECTEDAREA,
    payload: data
  };
}
