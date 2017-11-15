import { EXPORT_CROP } from '../actions/index';
import { EXPORT_RAINFALL } from '../actions/index';

export default function(
  state = {
    rainfall: { status: false, link: '' },
    crop: { status: false, link: '' }
  },
  action
) {
  switch (action.type) {
    case EXPORT_CROP:
      if (action.payload.data.crop === 'success') {
        state = {
          ...state,
          crop: {
            ...state.crop,
            status: action.payload.data.crop,
            link: action.payload.data.link
          }
        };
        return state;
      }
    case EXPORT_RAINFALL:
      if (action.payload.data.rainfall === 'success') {
        state = {
          ...state,
          crop: {
            ...state.crop,
            status: action.payload.data.rainfall,
            link: action.payload.data.link
          }
        };
        return state;
      }
  }
  return state;
}
