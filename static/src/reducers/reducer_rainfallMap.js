import { UPDATE_RAINFALL_MAP } from '../actions/index';

export default function(state = null, action) {
  switch (action.type) {
    case UPDATE_RAINFALL_MAP:
      if (action.payload) {
        console.log(action.payload.data);
        return action.payload.data;
      } else {
        return false;
      }
  }
  return state;
}
