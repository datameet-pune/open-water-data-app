import { UPDATE_TIMEPERIOD } from '../actions/index';

export default function(state = {}, action) {
  switch (action.type) {
    case UPDATE_TIMEPERIOD:
      return Object.assign(action.payload, ...state);
  }
  return state;
}
