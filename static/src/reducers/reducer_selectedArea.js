import { UPDATE_SELECTEDAREA } from '../actions/index';

export default function(state = null, action) {
  switch (action.type) {
    case UPDATE_SELECTEDAREA:
      return action.payload;
  }
  return state;
}
